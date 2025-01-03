# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django import forms
from django.contrib.auth.models import User

from incidents.models import Incident
from incidents.fields import DateTimeLocalField


class Nugget(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now, blank=True)

    raw_data = models.TextField()
    source = models.TextField()
    start_timestamp = models.DateTimeField(default=datetime.datetime.now, blank=True, null=True)
    end_timestamp = models.DateTimeField(blank=True, null=True)
    interpretation = models.TextField()

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    found_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return u"Nugget: {} in {} ({})".format(self.source, self.incident, self.interpretation)


class NuggetForm(forms.ModelForm):
    date = DateTimeLocalField()
    start_timestamp = DateTimeLocalField()
    end_timestamp = DateTimeLocalField()

    class Meta:
        model = Nugget
        exclude = ('incident', 'found_by')
        widgets = {
            'source': forms.TextInput(attrs={'placeholder': 'NTUSER, $MFT, %APPDATA%, RAM, etc...'}),
            'interpretation': forms.Textarea(attrs={'cols': 100, 'rows': 5, 'placeholder': 'What the raw data means to the case.'}),
            'raw_data': forms.Textarea(attrs={'placeholder': 'Raw data: log lines, directory listings, registry keys...'}),
            'end_timestamp': forms.TextInput(attrs={'placeholder': 'Leave blank if atomic event'}),
        }
