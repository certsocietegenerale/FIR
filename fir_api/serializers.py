from django.apps import apps
from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from collections import OrderedDict

from incidents.models import (
    Incident,
    Artifact,
    Label,
    LabelGroup,
    File,
    IncidentCategory,
    BusinessLine,
    Comments,
    Attribute,
    ValidAttribute,
    STATUS_CHOICES,
    CONFIDENTIALITY_LEVEL,
    PrettyJSONEncoder,
)

if apps.is_installed("fir_todos"):
    from fir_todos.models import TodoItem

    class TodoSerializer(serializers.ModelSerializer):
        """
        Serializer for Todo items
        """

        category = serializers.SlugRelatedField(
            many=False, read_only=True, slug_field="name"
        )
        business_line = serializers.SlugRelatedField(
            slug_field="name",
            queryset=BusinessLine.objects.all(),
            required=False,
            default=None,
        )

        class Meta:
            model = TodoItem
            fields = [
                "id",
                "description",
                "incident",
                "category",
                "business_line",
                "done",
                "done_time",
            ]
            read_only_fields = ["id"]


if apps.is_installed("fir_nuggets"):
    from fir_nuggets.models import Nugget

    class NuggetSerializer(serializers.ModelSerializer):
        class Meta:
            model = Nugget
            fields = (
                "id",
                "raw_data",
                "source",
                "start_timestamp",
                "end_timestamp",
                "interpretation",
                "incident",
                "found_by",
            )
            read_only_fields = ("id", "found_by")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "url", "username", "email", "groups")
        read_only_fields = ("id",)
        extra_kwargs = {"url": {"view_name": "api:user-detail"}}


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
        read_only=True, view_name="api:incident-detail"
    )

    class Meta:
        model = File
        fields = ("id", "description", "url", "incident")
        read_only_fields = ("id",)
        extra_kwargs = {"url": {"view_name": "api:file-detail"}}


class AttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attribute
        fields = ("id", "name", "value", "incident")
        read_only_fields = ("id",)


class LabelSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(
        many=False,
        queryset=LabelGroup.objects.all(),
        slug_field="name",
    )
    dynamic_config = serializers.JSONField(encoder=PrettyJSONEncoder, initial={})

    class Meta:
        model = Label
        fields = ("id", "name", "group", "dynamic_config")
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
        queryset=Label.objects.filter(group__name="severity"),
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
    attributes = AttributeSerializer(many=True, read_only=True)
    file_set = FileSerializer(many=True, read_only=True)
    comments_set = CommentsSerializer(many=True, read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, required=False
    )

    if apps.is_installed("fir_todos"):
        todoitem_set = TodoSerializer(many=True, read_only=True)

    if apps.is_installed("fir_nuggets"):
        nugget_set = NuggetSerializer(many=True, read_only=True)

    class Meta:
        model = Incident
        exclude = ["main_business_lines"]
        read_only_fields = ("id", "opened_by")

    def __init__(self, *args, **kwargs):
        if "context" in kwargs and kwargs["context"]["view"].action != "retrieve":
            del self.fields["artifacts"]
            del self.fields["comments_set"]
            del self.fields["file_set"]
            if "nugget_set" in self.fields:
                del self.fields["nugget_set"]
            if "todoitem_set" in self.fields:
                del self.fields["todoitem_set"]
        super().__init__(*args, **kwargs)

    def validate_owner(self, owner):
        try:
            if owner != "":
                User.objects.get(username=owner)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"User with name {owner} does not exist")
        return owner


class ValidAttributeSerializer(serializers.ModelSerializer):

    categories = serializers.SlugRelatedField(
        many=True, queryset=IncidentCategory.objects.all(), slug_field="name"
    )

    class Meta:
        model = ValidAttribute
        fields = ["id", "name", "unit", "description", "categories"]
        read_only_fields = ["id"]


class IncidentCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentCategory
        fields = ("id", "name", "is_major")
        read_only_fields = ("id", "name", "is_major")
