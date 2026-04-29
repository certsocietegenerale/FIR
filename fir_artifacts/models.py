import hashlib
import os
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ArtifactBlacklistItem(models.Model):
    type = models.CharField(max_length=20)
    value = models.CharField(max_length=200)

    def __str__(self):
        return self.value


class IncidentArtifact(models.Model):
    incident = models.ForeignKey(
        "incidents.Incident",
        on_delete=models.CASCADE,
    )
    artifact = models.ForeignKey(
        "fir_artifacts.Artifact",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "incidents_incident_artifacts"
        unique_together = ("incident", "artifact")


class Artifact(models.Model):
    type = models.CharField(max_length=20)
    value = models.TextField()
    incidents = models.ManyToManyField(
        "incidents.Incident",
        through="fir_artifacts.IncidentArtifact",
        related_name="artifact_set",
    )

    def __str__(self):
        display = self.value
        if self.incident.count() > 1:
            display += " (%s)" % self.incident.count()
        return display


def upload_path(instance, filename):
    return f"{instance._meta.model_name}_{instance.incident_id}/{filename}"


class File(models.Model):
    incident = models.ForeignKey(
        "incidents.Incident",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    hashes = models.ManyToManyField("fir_artifacts.Artifact", blank=True)
    description = models.CharField(max_length=256)
    file = models.FileField(upload_to=upload_path)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def getfilename(self):
        return os.path.basename(self.file.name)

    def get_hashes(self):
        hashes = dict((k, None) for k in ["md5", "sha1", "sha256"])
        content = self.file.read()
        for algo in hashes:
            m = hashlib.new(algo)
            m.update(content)
            hashes[algo] = m.hexdigest()
        return hashes
