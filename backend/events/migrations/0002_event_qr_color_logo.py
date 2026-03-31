from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="qr_color",
            field=models.CharField(blank=True, default="#0f172a", max_length=7),
        ),
        migrations.AddField(
            model_name="event",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="event_logos/"),
        ),
    ]
