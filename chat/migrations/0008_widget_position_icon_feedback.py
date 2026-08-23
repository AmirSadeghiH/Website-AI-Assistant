from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0007_widget_visual_enhancements"),
    ]

    operations = [
        migrations.AddField(
            model_name="widgetconfig",
            name="position_vertical_offset",
            field=models.PositiveIntegerField(
                default=24,
                help_text="Distance from top/bottom edge in pixels",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="position_horizontal_offset",
            field=models.PositiveIntegerField(
                default=24,
                help_text="Distance from left/right edge in pixels",
            ),
        ),
        migrations.AlterField(
            model_name="widgetconfig",
            name="position",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("bottom-right", "Bottom right"),
                    ("bottom-left", "Bottom left"),
                    ("top-right", "Top right"),
                    ("top-left", "Top left"),
                ],
                default="bottom-right",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="icon_type",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("default", "Default icon"),
                    ("custom", "Custom icon upload"),
                ],
                default="default",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="default_icon_choice",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("chat-bubble", "Chat bubble \U0001f4ac"),
                    ("message-circle", "Message circle \U0001f4e9"),
                    ("robot", "Robot \U0001f916"),
                    ("headset", "Headset \U0001f3a7"),
                    ("sparkle", "Sparkle \u2728"),
                    ("lightning", "Lightning \u26a1"),
                ],
                default="chat-bubble",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="custom_icon_file",
            field=models.FileField(
                blank=True,
                help_text="Upload a PNG or SVG file (max 200KB)",
                upload_to="widget-icons/",
            ),
        ),
        migrations.AddField(
            model_name="widgetconfig",
            name="show_feedback",
            field=models.BooleanField(default=True),
        ),
    ]
