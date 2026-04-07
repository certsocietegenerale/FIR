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


class Artifact(models.Model):
    type = models.CharField(max_length=20)
    value = models.TextField()

    def __str__(self):
        display = self.value
        if self.incident.count() > 1:
            display += " (%s)" % self.incident.count()
        return display


def upload_path(instance, filename):
    return "%s_%s/%s" % (instance.content_type.model, instance.object_id, filename)


class File(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")
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
