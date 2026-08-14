# AI Support Platform — Beta

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
