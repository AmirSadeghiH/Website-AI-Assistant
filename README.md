## AI Support Platform

این پروژه یک سرویس Django برای پاسخ‌گویی RAG و یک ویجت قابل Embed در سایت‌های دیگر است.

### اجرای محلی

```powershell
python manage.py runserver
```

سپس صفحه‌ی تست در `/demo/` یا `/static/demo.html` در دسترس است. endpoint اصلی:

```text
POST /api/chat/
Content-Type: application/json
```

بدنه:

```json
{
  "message": "سوال کاربر",
  "site_id": "demo",
  "conversation_id": "optional-session-id"
}
```

`site_id` و `conversation_id` در نسخه‌ی فعلی برای سازگاری آینده پذیرفته و از سمت ویجت ارسال می‌شوند؛ RAG فعلی همچنان از مجموعه‌ی داده‌ی موجود در `Data/` استفاده می‌کند.

پاسخ موفق:

```json
{
  "answer": "پاسخ تولیدشده توسط RAG"
}
```

### Embed ویجت

```html
<script
  src="https://YOUR-API-DOMAIN/static/widget/widget.js"
  data-api="https://YOUR-API-DOMAIN/api/chat/"
  data-site-id="YOUR-SITE-ID"
  defer>
</script>
```

یا با تنظیمات سراسری:

```html
<script>
  window.AI_WIDGET_CONFIG = {
    apiEndpoint: "https://YOUR-API-DOMAIN/api/chat/",
    siteId: "YOUR-SITE-ID",
    title: "پشتیبانی هوشمند"
  };
</script>
<script src="https://YOUR-API-DOMAIN/static/widget/widget.js" defer></script>
```

ویجت پاسخ‌های `answer`، `reply`، `response` و `message` را می‌خواند، timeout دارد و در خطای واقعی پیام خطا نشان می‌دهد؛ پاسخ ساختگی فقط در فایل قدیمی `index.html` و با `demoMode: true` فعال می‌شود.

برای سایت‌های خارجی، در محیط production مقدار `CORS_ALLOW_ALL_ORIGINS=False` و `CORS_ALLOWED_ORIGINS` را با originهای واقعی تنظیم کنید.

### پنل مدیریت و داده‌های محصول

برای ساخت مدیر پنل:

```powershell
python manage.py createsuperuser
```

سپس به `/admin/` بروید. از بخش `Sites` می‌توانید سایت مشتری، دامنه و تنظیمات ویجت را مدیریت کنید. هر سایت شامل تنظیمات مستقل زیر است:

- عنوان، زیرعنوان و پیام خوش‌آمدگویی
- رنگ اصلی و ثانویه، فونت و محل نمایش
- نمایش یا مخفی‌کردن تاریخچه
- فعال‌بودن feedback
- پیشنهادهای آماده‌ی ویجت
- promptهای اختصاصی و دمای مدل برای اتصال مرحله‌ی بعدی

در بخش‌های `Conversations`، `Messages` و `Analytics events` می‌توان تاریخچه و eventهای مصرف را بررسی کرد. API فعلی نیز این مسیرها را دارد:

```text
GET  /api/widget-config/?site_id=demo
GET  /api/history/?site_id=demo&conversation_id=...
POST /api/events/
POST /api/feedback/
```

در حالت `DEBUG=True` اگر سایت `demo` وجود نداشته باشد، اولین درخواست آن را خودکار ایجاد می‌کند. در production باید سایت را از پنل بسازید و `site_id` همان slug یا public key سایت باشد.

ساختار فعلی داده‌ها برای multi-tenant آماده است، اما index برداری هنوز از corpus مشترک `Data/` استفاده می‌کند. مرحله‌ی بعدی، ساخت `Document` و pipeline پردازش/embedding مستقل برای هر `Site` است.
