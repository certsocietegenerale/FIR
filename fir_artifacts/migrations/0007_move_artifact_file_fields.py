from django.db import migrations, models


def files_genericrelation_to_fk(apps, schema_editor):
    File = apps.get_model("fir_artifacts", "File")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Incident = apps.get_model("incidents", "Incident")

    incident_ct = ContentType.objects.get_for_model(Incident)

    for f in File.objects.filter(content_type=incident_ct):
        f.incident_id = f.object_id
        f.save(update_fields=["incident"])


class Migration(migrations.Migration):
    dependencies = [
        ("fir_artifacts", "0006_auto_20170110_1415"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="IncidentArtifact",
                    fields=[
                        (
                            "id",
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "incident",
                            models.ForeignKey(
                                to="incidents.Incident",
                                on_delete=models.CASCADE,
                            ),
                        ),
                        (
                            "artifact",
                            models.ForeignKey(
                                to="fir_artifacts.Artifact",
                                on_delete=models.CASCADE,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "incidents_incident_artifacts",
                        "unique_together": {("incident", "artifact")},
                    },
                ),
                migrations.AddField(
                    model_name="artifact",
                    name="incidents",
                    field=models.ManyToManyField(
                        to="incidents.Incident",
                        related_name="artifacts",
                        through="fir_artifacts.IncidentArtifact",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="file",
            name="incident",
            field=models.ForeignKey(
                to="incidents.Incident",
                null=True,
                blank=True,
                on_delete=models.CASCADE,
                related_name="files",
            ),
        ),
        migrations.RunPython(files_genericrelation_to_fk),
        migrations.RemoveField(
            model_name="file",
            name="content_type",
        ),
        migrations.RemoveField(
            model_name="file",
            name="object_id",
        ),
    ]
