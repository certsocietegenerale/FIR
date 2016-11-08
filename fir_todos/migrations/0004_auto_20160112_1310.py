# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fir_todos', '0003_todolisttemplate_todolist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todoitem',
            name='business_line',
            field=models.ForeignKey(blank=True, to='incidents.BusinessLine', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='todoitem',
            name='category',
            field=models.ForeignKey(blank=True, to='incidents.IncidentCategory', null=True),
            preserve_default=True,
        ),
    ]
