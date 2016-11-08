# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.contenttypes.models import ContentType

def migrate_artifacts(apps, schema_editor):
    Artifact = apps.get_model("fir_artifacts", "Artifact")
    IncidentsArtifact = apps.get_model("incidents", "Artifact")
    db_alias = schema_editor.connection.alias
    olds = IncidentsArtifact.objects.using(db_alias).all()
    for old in olds:
        artifact = Artifact.objects.using(db_alias).create(id=old.id,type=old.type, value=old.value)
        for incident in old.incidents.all():
            artifact.incidents.add(incident)

def migrate_files(apps, schema_editor):
    File = apps.get_model("fir_artifacts", "File")
    IncidentsFile = apps.get_model("incidents", "File")
    Incidents = apps.get_model("incidents", "Incident")
    Artifact = apps.get_model("fir_artifacts", "Artifact")
    db_alias = schema_editor.connection.alias
    olds = IncidentsFile.objects.using(db_alias).all()
    incident_type = ContentType.objects.get_for_model(Incidents)
    for old in olds:
        file = File.objects.using(db_alias).create(id=old.id,description=old.description, date=old.date, file=old.file)
        file.content_type_id = incident_type.pk
        file.object_id = old.incident.pk
        file.save()
        for old_hash in old.hashes.all():
            new_hash = Artifact.objects.using(db_alias).get(pk=old_hash.pk)
            file.hashes.add(new_hash)



class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0002_link_incidents_to_artifacts'),
        ('fir_artifacts', '0002_create_artifacts'),
    ]

    operations = [
        migrations.RunPython(
            migrate_artifacts,
        ),
        migrations.RunPython(
            migrate_files, atomic=False
        ),
    ]
