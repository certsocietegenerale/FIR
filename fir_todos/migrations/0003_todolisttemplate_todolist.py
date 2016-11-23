# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fir_todos', '0002_auto_20160110_0223'),
    ]

    operations = [
        migrations.AddField(
            model_name='todolisttemplate',
            name='todolist',
            field=models.ManyToManyField(to='fir_todos.TodoItem', null=True, blank=True),
            preserve_default=True,
        ),
    ]
