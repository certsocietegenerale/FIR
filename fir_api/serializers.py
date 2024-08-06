from django.apps import apps
from django.contrib.auth.models import User
from rest_framework import serializers

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
)


# serializes data from the FIR User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "url", "username", "email", "groups")
        read_only_fields = ("id",)
        extra_kwargs = {"url": {"view_name": "api:user-detail"}}


# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    incidents = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="api:incident-detail"
    )

    class Meta:
        model = Artifact
        fields = ("id", "type", "value", "incidents")
        read_only_fields = ("id",)


# FIR File model


class AttachedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ("id", "description", "url")
        read_only_fields = ("id",)
        extra_kwargs = {"url": {"view_name": "api:file-detail"}}


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="api:incident-detail"
    )

    class Meta:
        model = File
        fields = ("id", "description", "incident", "url", "file", "date")
        read_only_fields = ("id",)
        extra_kwargs = {"url": {"view_name": "api:file-download"}}
        depth = 2


# FIR Comment Model


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


# FIR Label Model


class LabelSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")

    class Meta:
        model = Label
        fields = ("id", "name", "group")
        read_only_fields = ("id",)


# FIR Incident model


class IncidentSerializer(serializers.ModelSerializer):
    detection = serializers.PrimaryKeyRelatedField(
        queryset=Label.objects.filter(group__name="detection")
    )
    actor = serializers.PrimaryKeyRelatedField(
        queryset=Label.objects.filter(group__name="actor")
    )
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Label.objects.filter(group__name="plan")
    )
    severity = serializers.PrimaryKeyRelatedField(
        queryset=SeverityChoice.objects.all(), allow_null=False
    )
    file_set = AttachedFileSerializer(many=True, read_only=True)
    comments_set = CommentsSerializer(many=True, read_only=True)

    class Meta:
        model = Incident
        exclude = ["main_business_lines", "artifacts"]
        read_only_fields = ("id", "opened_by", "main_business_lines", "file_set")


# FIR attribute model


class AttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attribute
        fields = ("id", "name", "value", "incident")
        read_only_fields = ("id",)


class ValidAttributeSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        many=True, queryset=IncidentCategory.objects.all(), slug_field="name"
    )

    class Meta:
        model = ValidAttribute
        fields = ["id", "name", "unit", "description", "categories"]
        read_only_fields = ["id"]


class BusinessLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessLine
        fields = ("id", "name")
        read_only_fields = ("id", "name")


class IncidentCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentCategory
        fields = ("id", "name", "is_major")
        read_only_fields = ("id", "name", "is_major")


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
            required=False, many=False, read_only=False, slug_field="name", default=None
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
