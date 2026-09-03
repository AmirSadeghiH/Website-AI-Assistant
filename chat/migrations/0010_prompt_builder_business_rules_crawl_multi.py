# Generated for iteration: prompt builder + business rules + multi-url crawl
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_conversation_crawljob_document_source_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_mode',
            field=models.CharField(choices=[('auto', 'سازنده هوشمند'), ('manual', 'ویرایش دستی')], default='auto', max_length=10),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_tone',
            field=models.CharField(choices=[('friendly', 'دوستانه و صمیمی'), ('formal', 'رسمی و حرفه‌ای'), ('concise', 'مختصر و مستقیم'), ('playful', 'شوخ و خلاق'), ('supportive', 'حمایتی و همدل')], default='friendly', max_length=20),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_assistant_name',
            field=models.CharField(blank=True, default='دستیار هوشمند', max_length=60),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_business_context',
            field=models.TextField(blank=True, help_text='معرفی کوتاه کسب\u200cوکار: چه می\u200cفروشید، مخاطب کیست، چه لحنی مناسب است. سازنده از همین متن پرامپت حرفه\u200cای می\u200cسازد.'),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_language',
            field=models.CharField(choices=[('fa', 'فارسی'), ('en', 'English'), ('auto', 'خودکار (FA/EN)')], default='fa', max_length=20),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_use_emoji',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='widgetconfig',
            name='prompt_answer_length',
            field=models.CharField(choices=[('short', 'کوتاه'), ('balanced', 'متعادل'), ('detailed', 'مفصل و توضیحی')], default='balanced', max_length=20),
        ),
        migrations.AddField(
            model_name='crawljob',
            name='max_pages_per_url',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='crawljob',
            name='crawl_mode',
            field=models.CharField(default='single', max_length=20),
        ),
        migrations.AddField(
            model_name='crawljob',
            name='source_urls',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='BusinessRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='نام داخلی قانون، مثلا «قیمت → صفحه محصولات»', max_length=120)),
                ('enabled', models.BooleanField(db_index=True, default=True)),
                ('priority', models.PositiveSmallIntegerField(default=100, help_text='عدد کمتر = اولویت بالاتر')),
                ('trigger_type', models.CharField(choices=[('intent', 'نیت (intent)'), ('keyword', 'کلیدواژه'), ('sentiment_negative', 'لحن منفی / عصبانیت'), ('fallback', 'فقط هنگام بی\u200cپاسخی')], max_length=20)),
                ('trigger_value', models.CharField(blank=True, help_text='برای intent: کد intent؛ برای keyword: عبارت؛ برای sentiment/fallback خالی بگذارید', max_length=200)),
                ('action_type', models.CharField(choices=[('suggest_link', 'پیشنهاد لینک'), ('suggest_text', 'پیشنهاد متن'), ('handoff', 'اتصال به کارشناس')], max_length=20)),
                ('action_payload', models.CharField(blank=True, help_text='برای link: URL؛ برای text: متن پیشنهادی؛ برای handoff: توضیح کوتاه', max_length=1000)),
                ('action_label', models.CharField(blank=True, help_text='متن دکمه/چیپ که کاربر می\u200cبیند', max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Business rule',
                'verbose_name_plural': 'Business rules',
                'ordering': ('priority', '-updated_at'),
            },
        ),
    ]
