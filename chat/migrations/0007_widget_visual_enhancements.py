from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0006_adminnotification_remove_analyticsevent_conversation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="widgetconfig",
            name="dark_mode",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("auto", "Auto (system)"),
                    ("light", "Light"),
                    ("dark", "Dark"),
                ],
                default="auto",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="accent_color",
            field=models.CharField(default="#a78bfa", max_length=20),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="font_size",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("small", "Small"),
                    ("normal", "Normal"),
                    ("large", "Large"),
                ],
                default="normal",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="bubble_style",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("rounded", "Rounded"),
                    ("sharp", "Sharp"),
                    ("pill", "Pill"),
                ],
                default="rounded",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="show_timestamp",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="show_avatar",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="enable_sounds",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="enable_animations",
            field=models.BooleanField(default=True),
        ),
        # Update defaults for existing fields
        migrations.AlterField(
            model_name="widgetconfig",
            name="panel_width",
            field=models.PositiveIntegerField(default=400),
        ),
        migrations.AlterField(
            model_name="widgetconfig",
            name="panel_height",
            field=models.PositiveIntegerField(default=640),
        ),
        migrations.AlterField(
            model_name="widgetconfig",
            name="border_radius",
            field=models.PositiveIntegerField(default=24),
        ),
        migrations.AlterField(
            model_name="widgetconfig",
            name="font_family",
            field=models.CharField(
                max_length=200,
                default="'Vazirmatn', 'Inter', 'IRANSansX', ui-sans-serif, system-ui, sans-serif",
            ),
        ),
        migrations.RemoveField(
            model_name="widgetconfig",
            name="show_history",
        ),
        migrations.RemoveField(
            model_name="widgetconfig",
            name="allow_feedback",
        ),
    ]
