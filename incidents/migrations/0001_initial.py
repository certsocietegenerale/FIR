# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import incidents.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BaleCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('category_number', models.IntegerField()),
                ('parent_category', models.ForeignKey(blank=True, to='incidents.BaleCategory', null=True)),
            ],
            options={
                'verbose_name_plural': 'Bale categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BusinessLine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, to='incidents.BusinessLine', null=True)),
            ],
            options={
                'ordering': ['parent__name', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comments',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('comment', models.TextField()),
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
                ('file', models.FileField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('hashes', models.ManyToManyField(to='incidents.Artifact', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('is_starred', models.BooleanField(default=False)),
                ('subject', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('severity', models.IntegerField(choices=[(1, b'1'), (2, b'2'), (3, b'3'), (4, b'4')])),
                ('is_incident', models.BooleanField(default=False)),
                ('is_major', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'Open', max_length=20, choices=[(b'O', b'Open'), (b'C', b'Closed'), (b'B', b'Blocked')])),
                ('confidentiality', models.IntegerField(default=b'1', choices=[(0, b'C0'), (1, b'C1'), (2, b'C2'), (3, b'C3')])),
            ],
            options={
                'permissions': (('handle_incidents', 'Can handle incidents'), ('view_statistics', 'Can view statistics')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IncidentCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('is_major', models.BooleanField(default=False)),
                ('bale_subcategory', models.ForeignKey(to='incidents.BaleCategory')),
            ],
            options={
                'verbose_name_plural': 'Incident categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IncidentTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('subject', models.CharField(max_length=256, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('severity', models.IntegerField(blank=True, null=True, choices=[(1, b'1'), (2, b'2'), (3, b'3'), (4, b'4')])),
                ('is_incident', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LabelGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('what', models.CharField(max_length=100, choices=[(b'O', b'Open'), (b'C', b'Closed'), (b'B', b'Blocked')])),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(blank=True, to='incidents.Comments', null=True)),
                ('incident', models.ForeignKey(blank=True, to='incidents.Incident', null=True)),
                ('who', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('incident_number', models.IntegerField(default=50)),
                ('hide_closed', models.BooleanField(default=False)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValidAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('unit', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=500, null=True, blank=True)),
                ('categories', models.ManyToManyField(to='incidents.IncidentCategory')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='label',
            name='group',
            field=models.ForeignKey(to='incidents.LabelGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incidenttemplate',
            name='actor',
            field=models.ForeignKey(related_name='+', blank=True, to='incidents.Label', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incidenttemplate',
            name='category',
            field=models.ForeignKey(blank=True, to='incidents.IncidentCategory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incidenttemplate',
            name='concerned_business_lines',
            field=models.ManyToManyField(to='incidents.BusinessLine', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incidenttemplate',
            name='detection',
            field=models.ForeignKey(blank=True, to='incidents.Label', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incidenttemplate',
            name='plan',
            field=models.ForeignKey(related_name='+', blank=True, to='incidents.Label', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='actor',
            field=models.ForeignKey(related_name='actor_label', blank=True, to='incidents.Label', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='category',
            field=models.ForeignKey(to='incidents.IncidentCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='concerned_business_lines',
            field=models.ManyToManyField(to='incidents.BusinessLine', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='detection',
            field=models.ForeignKey(related_name='detection_label', to='incidents.Label'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='main_business_lines',
            field=models.ManyToManyField(related_name='incidents_affecting_main', null=True, to='incidents.BusinessLine', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='opened_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incident',
            name='plan',
            field=models.ForeignKey(related_name='plan_label', blank=True, to='incidents.Label', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='incident',
            field=models.ForeignKey(to='incidents.Incident'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comments',
            name='action',
            field=models.ForeignKey(related_name='action_label', to='incidents.Label'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comments',
            name='incident',
            field=models.ForeignKey(to='incidents.Incident'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comments',
            name='opened_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attribute',
            name='incident',
            field=models.ForeignKey(to='incidents.Incident'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='artifact',
            name='incidents',
            field=models.ManyToManyField(to='incidents.Incident'),
            preserve_default=True,
        ),
    ]
