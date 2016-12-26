from django.db import models
from django import forms

from incidents.models import IncidentCategory, BusinessLine
from fir_artifacts.models import Artifact


class AbuseTemplate(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    body = models.TextField()
    subject = models.TextField()
    incident_category = models.ForeignKey(IncidentCategory)

    def __unicode__(self):
        return self.name


class ArtifactEnrichment(models.Model):
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    email = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100)
    raw = models.TextField()

    def __unicode__(self):
        return self.name


class AbuseContact(models.Model):
    name = models.CharField(max_length=100)
    to = models.CharField(max_length=100)
    cc = models.CharField(max_length=100, null=True)
    bcc = models.CharField(max_length=100, null=True)
    incident_category = models.ForeignKey(IncidentCategory)
    type = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
