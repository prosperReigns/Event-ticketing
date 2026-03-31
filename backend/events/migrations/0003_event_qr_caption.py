from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0002_event_qr_color_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="qr_caption",
            field=models.CharField(blank=True, default="Scan to check in", max_length=120),
        ),
    ]
