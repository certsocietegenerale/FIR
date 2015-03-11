from django.db import models
from django import forms

from incidents.models import Incident, IncidentCategory, BusinessLine


class TodoItem(models.Model):
	description = models.CharField(max_length=140)
	incident = models.ForeignKey(Incident)
	category = models.ForeignKey(IncidentCategory)
	business_line = models.ForeignKey(BusinessLine)
	done = models.BooleanField(default=False)
	done_time = models.DateTimeField(null=True, blank=True)
	deadline = models.DateField(null=True, blank=True)

	def __unicode__(self):
		return self.description


class TodoItemForm(forms.ModelForm):
	class Meta:
		model = TodoItem
		exclude = ('incident', 'category', 'done_time')
		widgets = {
			'description': forms.TextInput(attrs={'placeholder': 'Task'}),
		}
