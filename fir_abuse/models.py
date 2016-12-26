from django.db import models
from django import forms

from incidents.models import IncidentCategory, BusinessLine


class Abuse(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    body = models.TextField()
    subject = models.TextField()
    incident_category = models.ForeignKey(IncidentCategory)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'incidents_abuse'


class EmailForm(forms.Form):
    behalf = forms.CharField()
    to = forms.CharField()
    cc = forms.CharField()
    bcc = forms.CharField()
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)


class AbuseInfo(models.Model):
    pass
