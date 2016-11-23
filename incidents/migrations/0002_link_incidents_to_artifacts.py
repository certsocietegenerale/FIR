# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0001_initial'),
        ('fir_artifacts', '0002_create_artifacts'),
    ]

    operations = [
        migrations.AddField(
            model_name='Incident',
            name='artifacts',
            field=models.ManyToManyField(to='fir_artifacts.Artifact', related_name='incidents'),
            preserve_default=True,
        ),
    ]
