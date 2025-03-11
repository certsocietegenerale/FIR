import importlib
from django.apps import apps
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from collections import OrderedDict
from copy import deepcopy

from incidents.models import (
    Incident,
    Artifact,
    Label,
    File,
    IncidentCategory,
    BusinessLine,
    Comments,
    Attribute,
    ValidAttribute,
    SeverityChoice,
    STATUS_CHOICES,
    CONFIDENTIALITY_LEVEL,
)
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


class ArtifactSerializer(serializers.ModelSerializer):
    incidents_count = serializers.IntegerField(source="incidents.count", read_only=True)

    def __init__(self, *args, **kwargs):
        if "context" in kwargs and kwargs["context"]["view"].action != "retrieve":
            del self.fields["incidents"]
        super().__init__(*args, **kwargs)

    class Meta:
        model = Artifact
        fields = ("id", "type", "value", "incidents_count", "incidents")
        read_only_fields = ("id", "type", "value", "incidents_count")


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="api:incidents-detail"
    )
    url = serializers.HyperlinkedIdentityField(view_name="api:files-detail")

    class Meta:
        model = File
        fields = ("id", "description", "url", "incident")
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

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        fields["opened_by"] = serializers.SlugRelatedField(
            many=False, read_only=True, slug_field="username"
        )
        return fields

    class Meta:
        model = Comments
        fields = ("id", "comment", "incident", "opened_by", "date", "action")
        read_only_fields = ("id", "opened_by")


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
    status = ValueChoiceField(choices=STATUS_CHOICES, default="O")
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

    artifacts = ArtifactSerializer(many=True, read_only=True)
    attribute_set = AttributeSerializer(many=True, read_only=True)
    file_set = FileSerializer(many=True, read_only=True)
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
                    try:
                        if field[2] is not None and (
                            not field[0].endswith("_set")
                            or kwargs["context"]["view"].action == "retrieve"
                        ):
                            instance._declared_fields.update({field[0]: field[2]})
                            instance._additional_fields.update({field[0]: field[2]})
                    except KeyError as e:
                        continue

        try:
            if kwargs["context"]["view"].action != "retrieve":
                del instance.fields["artifacts"]
                del instance.fields["comments_set"]
                del instance.fields["file_set"]
                del instance.fields["attribute_set"]
        except KeyError as e:
            pass

        return instance

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
            if f.endswith("_set"):
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
            if f.endswith("_set"):
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
                self._context["request"].user, "incidents.handle_incidents"
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


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentCategory
        fields = ["id", "name", "is_major"]
        read_only_fields = ["id"]


class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeverityChoice
        fields = ["name", "color"]


class StatsSerializer(serializers.ModelSerializer):
    year = serializers.DateTimeField(required=False, format="%Y")
    month = serializers.DateTimeField(required=False, format="%Y-%m")
    day = serializers.DateTimeField(required=False, format="%Y-%m-%d")
    hour = serializers.DateTimeField(required=False, format="%Y-%m-%d %H:%M")
    count = serializers.IntegerField(required=False)
    category = serializers.CharField(required=False, source="category__name")
    severity = serializers.CharField(required=False, source="severity__name")
    actor = serializers.CharField(required=False, source="actor__name")
    detection = serializers.CharField(required=False, source="detection__name")
    entity = serializers.CharField(
        required=False, source="concerned_business_lines__name"
    )

    class Meta:
        model = Incident
        fields = [
            "year",
            "month",
            "day",
            "hour",
            "category",
            "severity",
            "actor",
            "detection",
            "entity",
            "count",
        ]
