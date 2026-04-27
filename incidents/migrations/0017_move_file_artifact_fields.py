from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("incidents", "0016_confidentiality_to_tlp_and_more"),
        ("fir_artifacts", "0007_move_artifact_file_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name="incident",
                    name="artifacts",
                ),
            ],
        ),
    ]
