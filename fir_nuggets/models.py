# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django import forms
from django.contrib.auth.models import User

from incidents.models import Incident


class Nugget(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now, blank=True)

    raw_data = models.TextField()
    source = models.TextField()
    start_timestamp = models.DateTimeField(default=datetime.datetime.now, blank=True, null=True)
    end_timestamp = models.DateTimeField(blank=True, null=True)
    interpretation = models.TextField()

    incident = models.ForeignKey(Incident)
    found_by = models.ForeignKey(User)

    def __unicode__(self):
        return u"Nugget: {} in {} ({})".format(self.source, self.incident, self.interpretation)


class NuggetForm(forms.ModelForm):

    class Meta:
        model = Nugget
        exclude = ('incident', 'found_by')
        widgets = {
            'source': forms.TextInput(attrs={'placeholder': 'NTUSER, $MFT, %APPDATA%, RAM, etc...'}),
            'interpretation': forms.Textarea(attrs={'cols': 100, 'rows': 5, 'placeholder': 'What the raw data means to the case.'}),
            'raw_data': forms.Textarea(attrs={'placeholder': 'Raw data: log lines, directory listings, registry keys...'}),
            'end_timestamp': forms.TextInput(attrs={'placeholder': 'Leave blank if atomic event'}),
        }
