from django.db.models.signals import pre_save, post_delete, post_save
from django.contrib.auth.models import User
from django.dispatch import receiver, Signal

from two_factor.plugins.webauthn.models import WebauthnDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice
from otp_yubikey.models import RemoteYubikeyDevice
from two_factor.signals import user_verified

from incidents.models import Log


backup_token_viewed = Signal()
backup_token_generated = Signal()


@receiver(pre_save, sender=WebauthnDevice)
@receiver(pre_save, sender=TOTPDevice)
@receiver(pre_save, sender=RemoteYubikeyDevice)
def log_new_otp(sender, instance, **kwargs):
    inst_type = type(instance)
    action = "updated"
    try:
        existing = inst_type.objects.get(id=instance.id)
    except inst_type.DoesNotExist:
        action = "created"
    else:
        # Ignore attributes updated during each login
        attribute_update_allowed = [
            "_state",
            "throttling_failure_timestamp",
            "throttling_failure_count",
            "sign_count",
            "drift",
            "last_used_at",
            "created_at",
            "last_t",
            "throttling_enabled",
        ]
        if all(
            [
                a in attribute_update_allowed
                or (
                    hasattr(existing, a)
                    and hasattr(instance, a)
                    and getattr(existing, a) == getattr(instance, a)
                )
                for a in vars(existing).keys()
            ]
        ):
            return

    user = User.objects.get(id=instance.user_id)
    Log.log(f"2FA: {inst_type.__name__} {action}", user)


@receiver(post_delete, sender=WebauthnDevice)
@receiver(post_delete, sender=TOTPDevice)
@receiver(post_delete, sender=RemoteYubikeyDevice)
def log_delete_otp(sender, instance, *args, **kwargs):
    user = User.objects.get(id=instance.user_id)
    Log.log(f"2FA: {type(instance).__name__} deleted", user)


@receiver(user_verified)
def user_verified(request, user, device, **kwargs):
    Log.log(f"2FA: Login success via {type(device).__name__}", user)


@receiver(backup_token_viewed)
def log_backup_token_viewed(user, **kwargs):
    Log.log(f"2FA: Backup codes viewed", user)


@receiver(backup_token_generated)
def log_backup_token_generated(user, **kwargs):
    Log.log(f"2FA: Backup codes re-generated", user)
