# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0003_copy_file_artifact_data'),
        ('fir_artifacts', '0002_create_artifacts'),
    ]

    operations = [
        migrations.DeleteModel('File'),
        migrations.DeleteModel('Artifact'),
    ]
