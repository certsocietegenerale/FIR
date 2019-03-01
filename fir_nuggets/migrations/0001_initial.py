# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Nugget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('raw_data', models.TextField()),
                ('source', models.TextField()),
                ('start_timestamp', models.DateTimeField(default=datetime.datetime.now, null=True, blank=True)),
                ('end_timestamp', models.DateTimeField(null=True, blank=True)),
                ('interpretation', models.TextField()),
                ('found_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('incident', models.ForeignKey(to='incidents.Incident')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
