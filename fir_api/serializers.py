import importlib
from django.apps import apps
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    ValidationError,
)
from django.utils.translation import gettext_lazy as _
from collections import OrderedDict
from copy import deepcopy

from incidents.models import (
    Incident,
    Label,
    IncidentCategory,
    BusinessLine,
    Comments,
    Attribute,
    ValidAttribute,
    SeverityChoice,
    BaleCategory,
    IncidentStatus,
    get_initial_status,
    CONFIDENTIALITY_LEVEL,
)
from fir_plugins.templatetags.markdown import render_markdown
from fir.config.base import INSTALLED_APPS


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:users-detail")
    groups = serializers.SlugRelatedField(
        many=True, read_only=False, queryset=Group.objects.all(), slug_field="name"
    )

    class Meta:
        model = User
        fields = ("id", "url", "username", "email", "groups")
        read_only_fields = ("id",)


class AttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attribute
        fields = ("id", "name", "value", "incident")
        read_only_fields = ("id",)


class LabelSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")

    class Meta:
        model = Label
        fields = ("id", "name", "group")
        read_only_fields = ("id",)


class CommentsSerializer(serializers.ModelSerializer):
    opened_by = UserSerializer(many=False, read_only=True)
    action = serializers.SlugRelatedField(
        queryset=Label.objects.filter(group__name="action"), slug_field="name"
    )
    parsed_comment = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    def get_parsed_comment(self, obj):
        return render_markdown(obj.comment)

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        fields["opened_by"] = serializers.SlugRelatedField(
            many=False, read_only=True, slug_field="username"
        )
        return fields

    def to_representation(self, value):
        # Remove some fields unless we are viewing a specific comment
        if not self.is_details():
            if "parsed_comment" in self.fields:
                del self.fields["parsed_comment"]

        return super().to_representation(value)

    def is_details(self):
        if self._kwargs.get("context"):
            context = self._kwargs.get("context")
            if (
                context.get("request")
                and context["request"].method != "DELETE"
                and context["request"].META["PATH_INFO"].endswith("{id}")
            ):
                return True
            if context.get("view") and context["view"].action not in ["list", "delete"]:
                return True
        return False

    def get_can_edit(self, obj):
        try:
            has_permission = Incident.authorization.for_user(
                self.context["request"].user,
                ["incidents.report_events", "incidents.handle_incidents"],
            ).get(pk=obj.incident.id)
            return True
        except Incident.DoesNotExist:
            return False

    class Meta:
        model = Comments
        fields = [
            "id",
            "comment",
            "incident",
            "opened_by",
            "date",
            "action",
            "parsed_comment",
            "can_edit",
        ]
        read_only_fields = ["id", "opened_by", "can_edit"]


class StatusSlugField(serializers.SlugRelatedField):
    def to_representation(self, instance):
        return _(super().to_representation(instance))

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        reverse_map = {
            _(getattr(obj, self.slug_field)): getattr(obj, self.slug_field)
            for obj in queryset
        }
        original_value = reverse_map.get(data, data)
        try:
            return queryset.get(**{self.slug_field: original_value})
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"Status '{data}' does not exist")


class BusinessLineSlugField(serializers.SlugRelatedField):
    """Custom Businessline Slug serializer field."""

    def to_representation(self, instance):
        return_object = super().to_representation(instance)
        if hasattr(instance, "depth") and instance.depth > 1:
            ancestors = instance.get_ancestors()
            for ancestor in reversed(ancestors):
                return_object = ancestor.name + " > " + return_object
        return return_object

    def to_internal_value(self, data):
        if " > " in data:
            data = data.split(" > ")[-1]
        return super(BusinessLineSlugField, self).to_internal_value(data)


class BusinessLineSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return_object = super().to_representation(instance)
        if return_object["depth"] > 1:
            ancestors = instance.get_ancestors()
            for ancestor in reversed(ancestors):
                return_object["name"] = ancestor.name + " > " + return_object["name"]
        return return_object

    class Meta:
        model = BusinessLine
        exclude = []
        read_only_fields = ["id", "name", "path", "depth", "numchild"]


class ValueChoiceField(serializers.ChoiceField):
    """Custom ChoiceField serializer field."""

    def __init__(self, choices, **kwargs):
        """init."""
        self._savedchoices = OrderedDict(choices)
        super(ValueChoiceField, self).__init__(choices=choices, **kwargs)
        self._set_choices([(v, v) for v in self._savedchoices.values()])

    def to_representation(self, obj):
        """Used while retrieving value for the field."""
        return self._savedchoices[obj]

    def to_internal_value(self, data):
        """Used while storing value for the field."""
        for i in self._savedchoices:
            if self._savedchoices[i] == data or i == data:
                return i
        raise serializers.ValidationError(
            "Acceptable values are {0}.".format(list(self._savedchoices.values()))
        )


class IncidentSerializer(serializers.ModelSerializer):
    detection = serializers.SlugRelatedField(
        many=False,
        slug_field="name",
        queryset=Label.objects.filter(group__name="detection"),
        required=True,
    )
    actor = serializers.SlugRelatedField(
        many=False,
        slug_field="name",
        queryset=Label.objects.filter(group__name="actor"),
        required=False,
    )
    plan = serializers.SlugRelatedField(
        many=False,
        slug_field="name",
        queryset=Label.objects.filter(group__name="plan"),
        required=False,
    )
    severity = serializers.SlugRelatedField(
        slug_field="name",
        queryset=SeverityChoice.objects.all(),
        required=True,
    )
    category = serializers.SlugRelatedField(
        many=False,
        slug_field="name",
        queryset=IncidentCategory.objects.all(),
        required=True,
    )
    status = StatusSlugField(
        many=False,
        slug_field="name",
        queryset=IncidentStatus.objects.all(),
        default=get_initial_status,
    )
    concerned_business_lines = BusinessLineSlugField(
        many=True,
        slug_field="name",
        queryset=BusinessLine.objects.all(),
        required=False,
    )
    confidentiality = ValueChoiceField(choices=CONFIDENTIALITY_LEVEL, required=True)
    opened_by = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="username"
    )

    attribute_set = AttributeSerializer(many=True, read_only=True)
    comments_set = CommentsSerializer(many=True, read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, required=False
    )
    last_comment_date = serializers.DateTimeField(read_only=True)
    last_comment_action = serializers.CharField(read_only=True)

    can_edit = serializers.SerializerMethodField()

    _additional_fields = {}

    class Meta:
        model = Incident
        exclude = ["main_business_lines"]
        read_only_fields = ("id", "opened_by")

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)

        if type(instance).__name__ != "IncidentSerializer":
            return instance

        # Load Additional incident fields defined in plugins via a hook
        for app in INSTALLED_APPS:
            if app.startswith("fir_"):
                try:
                    h = importlib.import_module(f"{app}.hooks")
                except ImportError:
                    continue

                for field in h.hooks.get("incident_fields", []):
                    if field[2] is not None:
                        instance._declared_fields.update({field[0]: field[2]})
                        instance._additional_fields.update({field[0]: field[2]})

        return instance

    def is_retrieve(self):
        if self._kwargs.get("context"):
            context = self._kwargs.get("context")
            if (
                context.get("request")
                and context["request"].method == "GET"
                and context["request"].META["PATH_INFO"].endswith("{id}")
            ):
                return True
            if context.get("view") and context["view"].action == "retrieve":
                return True
        return False

    def to_representation(self, value):
        to_remove = [f for f in self.fields if f.endswith("_set")]
        to_remove.extend(["artifacts"])

        # Remove some fields unless we are getting details of a specific incident
        if not self.is_retrieve():
            for elem in to_remove:
                if elem in self.fields:
                    del self.fields[elem]

        return super().to_representation(value)

    def validate_owner(self, owner):
        try:
            if owner != "":
                User.objects.get(username=owner)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"User with name {owner} does not exist")
        return owner

    def create(self, validated_data):
        field_to_create = {}
        for f in self._additional_fields:
            field_data = validated_data.pop(f, {})
            if f.endswith("_set") or f == "artifacts":
                # OneToMany creation is not supported
                continue
            field_serializer = deepcopy(self._additional_fields[f])
            field_to_create[field_serializer] = field_data

        instance = super().create(validated_data)

        for field_serializer in field_to_create:
            data = field_to_create[field_serializer]
            setattr(field_serializer, "initial_data", data)
            if field_serializer.is_valid(raise_exception=True):
                field_serializer.save(incident=instance)
        return instance

    def update(self, instance, validated_data):
        for f in self._additional_fields:
            field_data = validated_data.pop(f, {})
            if f.endswith("_set") or f == "artifacts":
                # OneToMany update is not supported
                continue
            field_serializer = deepcopy(self._additional_fields[f])
            setattr(field_serializer, "initial_data", field_data)
            if field_serializer.is_valid(raise_exception=True):
                field_serializer.instance = getattr(instance, f, None)
                field_serializer.save(incident=instance)

        return super().update(instance, validated_data)

    def get_can_edit(self, obj):
        try:
            has_permission = Incident.authorization.for_user(
                self.context["request"].user,
                ["incidents.report_events", "incidents.handle_incidents"],
            ).get(pk=obj.id)
            return True
        except Incident.DoesNotExist:
            return False


class ValidAttributeSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        many=True, queryset=IncidentCategory.objects.all(), slug_field="name"
    )

    class Meta:
        model = ValidAttribute
        fields = ["id", "name", "unit", "description", "categories"]
        read_only_fields = ["id"]


class BaselCategoryField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        if "(" in data and ")" in data:
            category = data.split("(")[1].split(")")[0]
            name = data.split(")", 1)[1]
            if ">" in category:
                category = category.split(">").pop()
            try:
                return BaleCategory.objects.get(
                    category_number=category.strip(), name=name.strip()
                )
            except (MultipleObjectsReturned, ObjectDoesNotExist):
                pass
        return super().to_internal_value(data)

    def to_representation(self, instance):
        if isinstance(instance, str):
            try:
                instance = BaleCategory.objects.get(name=instance)
            except (MultipleObjectsReturned, ObjectDoesNotExist):
                pass
        return str(instance)


class CategorySerializer(serializers.ModelSerializer):
    bale_subcategory = BaselCategoryField(
        many=False,
        read_only=False,
        slug_field="name",
        queryset=BaleCategory.objects.all(),
    )

    class Meta:
        model = IncidentCategory
        fields = ["id", "name", "is_major", "bale_subcategory"]
        read_only_fields = ["id"]


class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeverityChoice
        fields = ["id", "name", "color"]
        read_only_fields = ["id"]


class StatusSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = _(instance.name)
        return representation

    def to_internal_value(self, data):
        if "name" in data:
            reverse_map = {
                _(obj.name): obj.name for obj in IncidentStatus.objects.all()
            }
            _mutable = data._mutable
            data._mutable = True
            data["name"] = reverse_map.get(data["name"], data["name"])
            data._mutable = _mutable
        return super().to_internal_value(data)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except ValidationError as e:
            raise serializers.ValidationError("; ".join(e.messages))

    class Meta:
        model = IncidentStatus
        fields = ["id", "name", "icon", "flag"]
        read_only_fields = ["id"]
