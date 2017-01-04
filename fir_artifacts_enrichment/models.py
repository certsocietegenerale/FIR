from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from fir_artifacts.models import Artifact


class ArtifactEnrichment(models.Model):
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    email = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100)
    raw = models.TextField()

    def __unicode__(self):
        return self.name


@receiver(post_save, sender=Artifact)
def analyze_artifacts(sender, instance=None, created=False, **kwargs):
    types_to_enrich = ['hostname', 'email', 'ip', 'url']

    if created and instance.type in types_to_enrich:
        enrich_artifact.apply_async(args=[instance.id], task_id=str(instance.id))


from fir_artifacts_enrichment.tasks import enrich_artifact
