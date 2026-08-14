# AI Support Platform — Beta 0.9.9

نسخه Beta این محصول برای یک کسب‌وکار و یک نصب مستقل طراحی شده است. هر مشتری
روی سرور خودش یک نمونه از Django، دیتابیس، corpus و ویجت اختصاصی دارد.
در این نسخه SaaS، tenant، `site_id` و مدیریت چند سایت وجود ندارد.

## اجرای محلی

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

صفحه تست ویجت:

```text
http://127.0.0.1:8000/demo/
```

پنل مدیریت:

```text
http://127.0.0.1:8000/admin/
```

## مدیریت اسناد و ساخت embedding

از پنل به بخش `Knowledge documents` بروید، یک فایل PDF، TXT یا DOCX با حجم
حداکثر ۲۵ مگابایت آپلود کنید و ذخیره کنید. سپس سند را در لیست انتخاب کرده و
از منوی Actions گزینه‌ی ساخت embedding را اجرا کنید.

پردازش در یک worker جداگانه اجرا می‌شود و پنل این وضعیت‌ها را نشان می‌دهد:

```text
Uploaded → Queued → Processing → Ready
```

در صورت خطا، وضعیت `Failed` و متن خطا روی همان سند ذخیره می‌شود. chunkها و
embeddingهای سند به corpus فعلی `Data/` اضافه می‌شوند و سرویس RAG در درخواست
بعدی corpus جدید را دوباره بارگذاری می‌کند.

برای اجرای دستی همان worker:

```powershell
.\.venv\Scripts\python.exe manage.py process_documents 12 13
```

پردازش چند سند به‌صورت ترتیبی انجام می‌شود تا فایل‌های corpus هم‌زمان توسط
چند process تغییر نکنند.

## API اصلی

```text
POST /api/chat/
GET  /api/widget-config/
GET  /api/history/?conversation_id=...
POST /api/events/
POST /api/feedback/
GET  /api/health/
```

نمونه درخواست:

```json
{
  "message": "سؤال کاربر",
  "conversation_id": "optional-session-id",
  "history": []
}
```

## Embed ویجت

```html
<script
  src="https://YOUR-API-DOMAIN/static/widget/widget.js"
  data-api="https://YOUR-API-DOMAIN/api/chat/"
  defer>
</script>
```

ویجت تنظیمات ظاهری و رفتاری را از `/api/widget-config/` می‌خواند؛ بنابراین
عنوان، رنگ، فونت، موقعیت، پیام خوش‌آمد، پیشنهادها، لینک FAQ، Privacy و ایمیل
پشتیبانی از پنل قابل تغییر هستند.

پاسخ‌های دستیار Markdown محدود و امن را پشتیبانی می‌کنند:

- `**bold**`
- `*italic*`
- `[لینک](https://example.com)`
- فهرست‌های bullet

لینک‌های `javascript:` و schemeهای ناشناخته نمایش داده نمی‌شوند.

## تنظیمات محیط

مقادیر LLM و embedding را در `.env` قرار دهید. حداقل تنظیمات معمول:

```env
DEBUG=True
SECRET_KEY=change-me
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.gapgpt.app/v1
LLM_MODEL=deepseek-v4-pro
EMBEDDING_API_KEY=your-api-key
EMBEDDING_MODEL=text-embedding-3-small
```

در production مقدار `DEBUG=False`، `ALLOWED_HOSTS` و
`CORS_ALLOWED_ORIGINS` را دقیق تنظیم کنید.

## API و سخت‌سازی نسخه 0.9.9

APIهای ویجت در این نسخه با Django REST Framework، serializer، محدودیت حجم
درخواست، throttling و پاسخ‌های JSON استاندارد اجرا می‌شوند. کلیدهای LLM و
embedding فقط روی سرور باقی می‌مانند و هرگز داخل widget قرار نمی‌گیرند.

برای deployment production یک کلید عمومی اختصاصی برای همان نصب تعریف کنید:

```env
WIDGET_PUBLIC_KEY=replace-with-a-random-installation-key
WIDGET_ALLOWED_ORIGINS=https://carsanj.ir,https://www.carsanj.ir
```

و آن را در embed ویجت قرار دهید:

```html
<script
  src="https://api.example.com/static/widget/widget.js"
  data-api="https://api.example.com/api/chat/"
  data-widget-key="replace-with-a-random-installation-key"
  defer></script>
```

این کلید secret نیست و به‌تنهایی جلوی کپی کامل JavaScript را نمی‌گیرد؛
محافظت واقعی با allowlist دامنه، rate limit، محدودیت مصرف و نگهداری کلیدهای
provider فقط در backend انجام می‌شود.

در Production برای مشترک‌بودن throttling بین workerها از Redis استفاده کنید:

```env
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/10
```
