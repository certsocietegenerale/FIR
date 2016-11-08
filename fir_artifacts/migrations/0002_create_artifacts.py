# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import fir_artifacts.models

class Migration(migrations.Migration):

    dependencies = [
        ('fir_artifacts', '0001_initial'),
        ('incidents', '0001_initial')
    ]

    operations = [
        migrations.CreateModel(
            name='Artifact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=20)),
                ('value', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=256)),
                ('file', models.FileField(upload_to=fir_artifacts.models.upload_path)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='File',
            name='hashes',
            field=models.ManyToManyField(to='fir_artifacts.Artifact', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='object_id',
            field=models.PositiveIntegerField(null=True),
            preserve_default=True,
        ),
    ]
