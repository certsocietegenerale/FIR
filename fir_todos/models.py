from django.conf import settings
from django.db import models
from django import forms

from incidents.models import Incident, IncidentCategory, BusinessLine, Label


class TodoItem(models.Model):
    description = models.CharField(max_length=140)
    incident = models.ForeignKey(Incident, blank=True, null=True)
    category = models.ForeignKey(IncidentCategory, blank=True, null=True)
    business_line = models.ForeignKey(BusinessLine, blank=True, null=True)
    done = models.BooleanField(default=False)
    done_time = models.DateTimeField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return self.description


class TodoItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('for_user', None)
        super(TodoItemForm, self).__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['business_line'].queryset = BusinessLine.authorization.for_user(self.user,
                                                                                        'incidents.handle_incidents')

    class Meta:
        model = TodoItem
        exclude = ('incident', 'category', 'done_time')
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Task'}),
        }


# Templating =================================================================

class TodoListTemplate(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(IncidentCategory, null=True, blank=True)
    concerned_business_lines = models.ManyToManyField(BusinessLine, blank=True)
    detection = models.ForeignKey(Label, limit_choices_to={'group__name': 'detection'}, null=True, blank=True)
    todolist = models.ManyToManyField(TodoItem, blank=True, limit_choices_to={"incident__isnull": True})

    def __unicode__(self):
        return self.name
