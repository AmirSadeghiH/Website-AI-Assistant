# AI Support Platform — ویجت پشتیبانی هوشمند مبتنی بر RAG

یک پلتفرم کامل و آماده‌ی فروش برای افزودن دستیار پشتیبانی هوشمند (RAG) به
سایت مشتری. مشتری فقط یک تگ اسکریپت را در سایتش قرار می‌دهد و همه‌چیز —
ظاهر ویجت، کلیدهای API مدل‌ها، مدل LLM، مدل embedding، اسناد دانش و
محدودیت‌ها — از پنل مدیریت اختصاصی (`/panel/`) مدیریت می‌شود.

- **بک‌اند:** Django 6.1 + Django REST Framework
- **موتور RAG:** FAISS (بازیابی برداری) + مدل embedding مبتنی بر API
- **مدل پاسخ‌دهنده:** هر API سازگار با OpenAI (پیش‌فرض: GapGPT / DeepSeek)
- **ویجت:** جاوااسکریپت بدون وابستگی، Shadow DOM، استریم SSE، بدون فریم‌ورک —
  **۱۱ نسخه‌ی رابط کاربری** (کلاسیک، Onyx، Linen، Clay، Atomic، Fluen،
  Glassmo، Material 3، Minimal، Neu، Skuerdo) که همه از یک کانال
  شخصی‌سازی مشترک استفاده می‌کنند
- **پنل اختصاصی:** RTL فارسی در `/panel/` با داشبورد Chart.js و پیش‌نمایش زنده
- **پنل فنی:** Django admin در `/admin/` برای کارهای عمیق‌تر

---

## فهرست

1. [امکانات](#امکانات)
2. [معماری](#معماری)
3. [شروع سریع (محلی)](#شروع-سریع-محلی)
4. [نصب آسان ویجت روی سایت مشتری](#نصب-آسان-ویجت-روی-سایت-مشتری)
5. [راهنمای پنل ادمین](#راهنمای-پنل-ادمین)
6. [مرجع API](#مرجع-api)
7. [استقرار Production](#استقرار-production) — 🚀 [راهنمای Railway ۱۰ دقیقه‌ای](docs/RAILWAY-DEPLOY.md)
8. [مدل امنیتی](#مدل-امنیتی)
9. [عملکرد و مقیاس‌پذیری (۲۰۰+ کاربر هم‌زمان)](#عملکرد-و-مقیاسپذیری)
10. [متغیرهای محیطی](#متغیرهای-محیطی)
11. [تست](#تست)
12. [امنیت و تست‌ها (سند کامل)](#امنیت-و-تستها-سند-کامل)
13. [عیب‌یابی](#عیبیابی)

---

## امکانات

- **۱۱ نسخه‌ی رابط کاربری ویجت (Theme Picker):** انتخاب نسخه از تب
  «هویت برند» در طراحی ویجت با کارت‌های تصویری؛ کد نصب، دموی زنده (`/demo/`)
  و پیش‌نمایش پنل همه همان نسخه را سرو می‌کنند.
- **استریم پاسخ (SSE):** پاسخ توکن‌به‌توکن در `/api/chat/stream/` با دکمه‌ی
  توقف؛ در صورت عدم پشتیبانیِ پروکسی، خودکار به مسیر JSON برمی‌گردد.
- **حافظه‌ی مکالمه هوشمند:** پنجره‌ی زمینه (context window) قابل تنظیم در
  پنل + سوئیچ روشن/خاموش؛ ویجت روی سؤالاتی مثل «مشخصاتش رو بگو» از جملات
  قبلی سر در می‌آورد.
- **حافظه‌ی محلی مرورگر:** تاریخچه‌ی گفتگو (۷ روز، حداکثر ۲۲ پیام، با
  جداکننده‌ی روز) در `localStorage` — با پاک شدن session هم از بین نمی‌رود.
- **ارجاع به کارشناس انسانی:** سه کانال (تلگرام / واتساپ / فرم تماس) +
  فرم درون‌ویجتی؛ پس از هر پاسخ جایگزین (fallback) پیشنهاد می‌شود و در
  پنل ثبت می‌گردد.
- **جذب سرنخ (Lead capture):** فرم نام + ایمیل/تلفن با honeypot ضد ربات،
  اتصال به مکالمه، اعلان ایمیلی/تلگرامی به مدیر.
- **سؤالات بی‌پاسخ:** هر fallback با کلید پرسش نرمال‌شده تجمیع و در پنل
  قابل علامت‌گذاری «حل‌شده» است — نقشه‌ی تقویت دانش.
- **تشخیص نیت (Intent):** قانون‌محور (تماس/قیمت/سفارش/شکایت/سلام و…) با
  نرمال‌سازی فارسی؛ روی مکالمات و داشبورد گزارش می‌شود.
- **موتور قوانین کسب‌وکار (Business Rules):** trigger→action (چیپ لینک،
  پیام راهنما، ارجاع انسانی) با حداکثر ۲ قانون فعال — مدیریت کامل در پنل.
- **کرالر سایت (Website Crawler):** ورود فقط یک URL؛ BFS تا `max_pages`،
  رعایت robots.txt، محدودیت ۳MB/صفحه، و **گارد SSRF** (رد IPهای خصوصی/
  loopback/link-local، ریدایرکت‌ها دوباره اعتبارسنجی می‌شوند).
- **پنل اختصاصی `/panel/`:** داشبورد KPI + نمودار (حجم روزانه، توزیع نیت،
  fallback)، مکالمات با ترنسکریپت کامل، سرنخ‌ها، درخواست‌های پشتیبانی،
  پایگاه دانش (آپلود چند فایلی + کرال چند URL)، **طراحی ویجت با
  پیش‌نمایش زنده و انتخاب تم**، **کد نصب با دکمه‌ی کپی**، ویزارد ۶ مرحله‌ای
  راه‌اندازی و تنظیمات AI.
- **دموی زنده‌ی تم‌دار:** `/demo/` همیشه نسخه‌ی رابط کاربری انتخاب‌شده در
  پنل را نشان می‌دهد (رندر داینامیک، بدون کش).
- **نصب آسان ویجت:** فقط یک تگ `<script>`؛ تنظیمات ظاهری و رفتاری به‌صورت
  خودکار از `/api/widget-config/` خوانده می‌شود.
- **مدیریت کامل از پنل:**
  - کلید API مدل LLM، آدرس (Base URL)، نام مدل، حداکثر توکن، تایم‌اوت و
    تعداد تلاش مجدد — رمزنگاری‌شده در پایگاه داده.
  - کلید API، آدرس و مدل embedding + توکن تلگرام برای اعلان‌ها.
  - ظاهر ویجت: عنوان، رنگ، فونت، موقعیت، اندازه، لوگو، پیام خوش‌آمد،
    پیشنهادها، لینک FAQ / Privacy / ایمیل پشتیبانی.
  - رفتار: استریم، منابع (citations)، فرم سرنخ، ارجاع انسانی، بازخورد،
    پنجره‌ی تاریخچه (context window) و حافظه‌ی مکالمه.
  - پرامپت‌ساز: پرامپت سیستمی خودکار + دستورهای اضافه‌ی دستی.
- **اسناد دانش:** آپلود PDF / TXT / DOCX تا ۲۵ مگابایت (چند فایل هم‌زمان
  از پنل)، پردازش در پس‌زمینه، وضعیت
  `Uploaded → Queued → Processing → Ready/Failed`، chunk بندی جمله‌ای با
  overlap.
- **مکالمه و بازخورد:** ذخیره‌ی مکالمه + توکن HMAC، بازیابی تاریخچه در
  بازدید بعدی، بازخورد مفید/نامفید به‌ازای هر پیام، رویدادهای تحلیلی.
- **امنیت:** کلیدهای provider فقط روی سرور و رمزنگاری‌شده؛ allowlist دامنه؛
  کلید عمومی نصب؛ throttling چندلایه؛ honeypot؛ جلوگیری از payload بزرگ،
  ZIP bomb و XML bomb؛ SSRF-gard کرالر؛ بدون XSS؛ **گارد secret-scan در
  تست‌ها**.
- **عملکرد:** کش پاسخ، همزمانی محدود و قابل تنظیم، ایندکس‌های دیتابیس،
  Redis برای throttling اشتراکی.

---

## معماری

```text
سایت مشتری (carsanj.ir و امثال آن)
        │  <script src="https://api.example.com/static/widget/widget[-<theme>].js"
        │         data-api="https://api.example.com/api/chat/" data-widget-key="...">
        ▼
   widget-<theme>.js (Shadow DOM، بدون وابستگی — ۱۱ نسخه)
        │  fetch (CORS + X-Widget-Key + X-Conversation-Token)
        ▼
   Django + DRF  (nginx → gunicorn → Django)
        │
        ├── /api/chat/          → RAGService → Retriever(FAISS) → LLM API
        ├── /api/chat/stream/   → همان مسیر با استریم SSE (meta/token/done)
        ├── /api/widget-config/ → تنظیمات ظاهری (کش‌شده)
        ├── /api/history/       → تاریخچه مکالمه (نیازمند توکن HMAC)
        ├── /api/feedback/      → بازخورد مفید/نامفید به‌ازای پیام
        ├── /api/leads/         → فرم سرنخ (honeypot + throttle)
        ├── /api/handoff/       → ارجاع به کارشناس انسانی
        ├── /api/events/        → رویدادهای تحلیلی
        ├── /demo/              → دموی زنده با تم انتخابی پنل
        ├── /panel/             → پنل اختصاصی (داشبورد، دانش، طراحی، نصب)
        └── /admin/             → پنل فنی Django (CRUD عمیق)

  worker (docker compose سرویس worker / runworker):
         ├── CrawlJob  → کرال سایت مشتری با SSRF-gard
         └── Document  → پردازش و ساخت embedding

ذخیره‌سازی:
  PostgreSQL (یا SQLite برای توسعه) + Redis (کش و throttling)
  Data/  → chunks.json ، metadata.json ، embeddings.npy (خروجی FAISS)
  media/ → فایل‌های آپلودشده اسناد
```

هنگام ساخت embedding، سرویس RAG به‌صورت خودکار corpus جدید را بارگذاری
می‌کند؛ درخواست‌های بعدی بدون ری‌استارت، از دانش جدید استفاده می‌کنند.

---

## شروع سریع (محلی)

پیش‌نیاز: Python 3.12

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# یک فایل .env بر اساس .env.example بسازید
# برای توسعه‌ی محلی کافی است:
#   DEBUG=True  و  SECRET_KEY=یک-مقدار-تصادفی

.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver

# در ترمینال جدا — worker پردازش اسناد و کرال:
.\.venv\Scripts\python.exe manage.py runworker --loop
```

- **پنل اختصاصی:** `http://127.0.0.1:8000/panel/` (نقطه‌ی ورود اصلی محصول)
- صفحه تست ویجت: `http://127.0.0.1:8000/demo/`
- پنل فنی: `http://127.0.0.1:8000/admin/`
- سلامت سرویس: `http://127.0.0.1:8000/api/health/`

> بدون `.env` و در حالت غیر DEBUG، پروژه با خطای واضح «SECRET_KEY is
> required» اجرا نمی‌شود؛ این رفتار عمدی است تا استقرار اشتباه غیرممکن شود.

---

## نصب آسان ویجت روی سایت مشتری

فقط این تگ را قبل از `</body>` سایت مشتری قرار دهید (پنل کد را با فایل
نسخه‌ی انتخابی تولید می‌کند — مثلاً `widget-onyx.js`):

```html
<script
  src="https://api.example.com/static/widget/widget.js"
  data-api="https://api.example.com/api/chat/"
  data-widget-key="install-key-از-پنل-یا-env"
  defer></script>
```

کلید نصب (`data-widget-key`) و دامنه‌ی سایت مشتری از پنل ادمین
(**AI provider settings → نصب ویجت و کنترل دسترسی**) ثبت می‌شوند و تا چند
ثانیه بعد روی API و CORS اعمال می‌شوند؛ بنابراین برای هر مشتری جدید نیازی
به دسترسی به سرور نیست.

مشتری هیچ‌چیز دیگری لازم ندارد. ویجت:

1. تنظیمات ظاهر را از `/api/widget-config/` می‌خواند (عنوان، رنگ، لوگو،
   پیشنهادها، لینک‌ها و…).
2. یک مکالمه را در `sessionStorage` نگه می‌دارد و در بازدید بعدی تاریخچه را
   از `/api/history/` بازیابی می‌کند.
3. پیام‌ها را به `/api/chat/` می‌فرستد و پاسخ (Markdown محدود و امن) را
   نمایش می‌دهد.

**پارامترهای تگ:**
| پارامتر | توضیح |
| --- | --- |
| `data-api` | آدرس کامل `/api/chat/` (اختیاری؛ پیش‌فرض هم‌دستگاه اسکریپت) |
| `data-widget-key` | کلید عمومی نصب (X-Widget-Key) در صورت فعال بودن |
| `data-title` / `data-primaryColor` | بازنویسی موقت مقادیر پیش‌فرض (اختیاری) |

پاسخ‌های دستیار فقط این Markdown امن را پشتیبانی می‌کنند: `**bold**` ،
`*italic*` ، `[لینک](https://...)` و فهرست bullet. لینک‌های `javascript:` و
schemeهای ناشناخته نمایش داده نمی‌شوند و تمام متن‌ها escape می‌شوند
(بدون XSS).

---

## راهنمای پنل ادمین

### ۱) AI provider settings (کلیدها و مدل‌ها)

در پنل: **AI provider settings** → «Add».

- **LLM:** کلید API، Base URL، نام مدل، حداکثر توکن، تایم‌اوت (ثانیه) و
  تعداد تلاش مجدد. اگر فیلدی خالی بماند مقدار معادل از متغیر محیطی خوانده
  می‌شود.
- **Embedding:** کلید API، Base URL و نام مدل embedding + تایم‌اوت و تلاش مجدد.
- **ظرفیت:** حداکثر درخواست هم‌زمان به LLM در هر process و مدت کش پاسخ.
- **نصب ویجت و کنترل دسترسی:** کلید عمومی نصب (X-Widget-Key) و دامنه‌های
  مجاز (هر دامنه در یک خط). این مقادیر روی دسترسی API و CORS اعمال
  می‌شوند و تا چند ثانیه پس از ذخیره مؤثرند؛ متغیرهای محیطی فقط fallback
  هستند.

نکات:
- کلیدها با کلید مشتق‌شده از `SECRET_KEY` رمزنگاری می‌شوند و هرگز به
  مرورگر ارسال نمی‌شوند. در فرم ادمین، کلیدها به‌صورت `••••` نمایش داده
  می‌شوند و برای حفظ مقدار فعلی کافی است خالی بمانند.
- ⚠️ اگر `SECRET_KEY` عوض شود، کلیدهای ذخیره‌شده قابل رمزگشایی نیستند و
  باید دوباره وارد شوند.
- ⚠️ اگر **مدل embedding** را تغییر دهید، ابعاد بردارها عوض می‌شود؛ باید
  همه اسناد را دوباره پردازش کنید (Action «ساخت embedding» روی هر سند).
  تا آن زمان API خطای `corpus_config` برمی‌گرداند.

### ۲) اسناد دانش (Knowledge documents)

1. «Add» → عنوان و فایل (PDF / TXT / DOCX، حداکثر ۲۵MB).
2. سند را در لیست انتخاب کنید → Action «شروع پردازش و ساخت embedding».
3. پردازش در یک worker جداگانه اجرا می‌شود (برای تغییر ندادن هم‌زمان
   corpus، اسناد به‌صورت ترتیبی پردازش می‌شوند).
4. وضعیت‌ها: `Uploaded → Queued → Processing → Ready` و در صورت خطا
   `Failed` همراه متن خطا.

اجرای دستی همان worker:

```powershell
.\.venv\Scripts\python.exe manage.py process_documents 12 13
```

فایل‌های نمونه در `Data/` موجودند (سه PDF دمو). برای شروع تمیز، آن‌ها را
حذف کنید یا اسناد کسب‌وکار خودتان را جایگزین کنید.

### ۳) طراحی ویجت (Customizer) — تم و پیش‌نمایش زنده

- **تب «هویت برند» → «نسخه رابط کاربری»:** انتخاب بین ۱۱ تم با کارت‌های
  تصویری؛ با تغییر تم، پیش‌نمایش زنده همان لحظه با باندل جدید ریلود
  می‌شود و کد نصب هم فایل همان تم را تولید می‌کند.
- بقیه‌ی تب‌ها (ظاهر، موقعیت، رفتار، سرنخ): رنگ، فونت، گرادیان/ساده/شیشه‌ای،
  موقعیت، اندازه، پیام خوش‌آمد، پیشنهادها، لینک FAQ/Privacy/ایمیل،
  حافظه‌ی مکالمه (روشن/خاموش + اندازه پنجره) و پرامپت‌ها — همه پس از ذخیره
  حداکثر ۱۰ ثانیه بعد روی سایت مشتری اعمال می‌شوند.

---

## مرجع API

همه پاسخ‌ها JSON هستند. بدنه‌های بزرگ‌تر از ۶۴KB یا بدون `Content-Length`
رد می‌شوند. همه‌ی endpointهای ویجت تحت `WidgetAccessPermission` (کلید +
origin) و throttling هستند.

| Method | مسیر | توضیح |
| --- | --- | --- |
| POST | `/api/chat/` | ارسال پیام و دریافت پاسخ JSON |
| POST | `/api/chat/stream/` | همان درخواست با استریم SSE |
| GET | `/api/widget-config/` | تنظیمات عمومی ویجت (کش عمومی ۱۰ ثانیه) |
| GET | `/api/history/?conversation_id=...` | حداکثر ۱۰۰ پیام آخر (نیازمند `X-Conversation-Token`) |
| POST | `/api/feedback/` | بازخورد مفید/نامفید روی یک پیام (`message_id` + توکن) |
| POST | `/api/leads/` | ثبت سرنخ (honeypot: فیلد `website`) |
| POST | `/api/handoff/` | درخواست ارجاع به کارشناس (`channel`: email/telegram/whatsapp/contact_form) |
| POST | `/api/events/` | رویداد تحلیلی (فقط انواع client-writable) |
| GET | `/api/health/` | سلامت دیتابیس و corpus |

**درخواست چت:**

```json
{
  "message": "سؤال کاربر",
  "conversation_id": "conv_abc123",
  "page_url": "https://customer.example/product/1"
}
```

**پاسخ چت:**

```json
{
  "answer": "پاسخ دستیار",
  "conversation_id": "conv_abc123",
  "conversation_token": "hmac-token",
  "message_id": 42,
  "citations": [{"title": "سؤالات متداول", "url": "https://…", "page_number": 1}],
  "intent": "pricing",
  "fallback": false,
  "latency_ms": 1830
}
```

**رویدادهای استریم (`/api/chat/stream/`):**

```text
event: meta   data: {"conversation_id": "…", "conversation_token": "…", "intent": "pricing"}
event: token  data: {"t": "پاسخ "}
event: token  data: {"t": "دستیار…"}
event: done   data: {"message_id": 42, "citations": [...], "fallback": false, "latency_ms": 1830}
event: error  data: {"code": "capacity_limited", "message": "…"}   (فقط در خطا)
```

توکن مکالمه با HMAC از `SECRET_KEY` ساخته می‌شود و فقط در صورت تنظیم
`WIDGET_PUBLIC_KEY` الزامی است؛ این توکن اجازه‌ی خواندن تاریخچه و ثبت
بازخورد همان مکالمه را می‌دهد و از خواندن مکالمات دیگران جلوگیری می‌کند.

**خطاهای متداول:**
| وضعیت | error | معنی |
| --- | --- | --- |
| 400 | `invalid_json` / `message_required` / `invalid_message` | ورودی نامعتبر |
| 403 | `Widget access is not authorized.` | کلید یا origin مجاز نیست |
| 411 | `content_length_required` / `chunked_not_allowed` | بدنه بدون Content-Length |
| 413 | `message_too_long` / `payload_too_large` | ورودی بیش از حد مجاز |
| 429 | `capacity_limited` | صف LLM پر است (به‌همراه `Retry-After`) |
| 503 | `corpus_config` | corpus نیاز به بازپردازش دارد (تغییر مدل embedding) |
| 503 | `backend_error` | خطای موقت سرویس |

---

## استقرار Production

> 🚀 **ساده‌ترین راه: Railway در ۱۰ دقیقه** — راهنمای قدم‌به‌قدم کامل:
> [`docs/RAILWAY-DEPLOY.md`](docs/RAILWAY-DEPLOY.md)
> یک سرویس، بدون nginx، بدون کانفیگ TLS؛ فقط `SECRET_KEY` بگذار و Volume وصل کن.

### گزینه‌ی الف) Railway / PaaS (تک‌کانتینر — توصیه‌شده)

1. ریپو را به Railway وصل کنید — تمام؛ `railway.json` + `Dockerfile` +
   `deploy/entrypoint.sh` بقیه‌ی کار را می‌کنند: بیلد، migrate،
   collectstatic، تعمیر corpus، اجرای ورکر پس‌زمینه و gunicorn روی `$PORT`.
2. از Railway دیتابیس **PostgreSQL** و **Redis** اضافه کنید (متغیرهای
   `DATABASE_URL` و `REDIS_URL` خودکار تزریق می‌شوند — کانفیگ دستی لازم نیست).
3. یک **Volume** با مسیر `/data` به سرویس وصل کنید و `PERSIST_DIR=/data`
   بگذارید تا دانش و فایل‌ها با هر deploy باقی بمانند.
4. فقط `SECRET_KEY` را دستی وارد کنید؛ دامنه‌ی Railway، HTTPS و CSRF
   خودکار شناسایی می‌شوند.
5. سلامت: `/api/health/` (بدون کلید ویجت، خروجی بولین).

### گزینه‌ی ب) Docker Compose روی VPS

```bash
# ۱) .env را بسازید (بر اساس .env.example)
# ۲) دامنه در nginx.conf را عوض کنید
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
# سرویس‌ها: web (gunicorn + ورکر داخلی) + postgres + redis + nginx + certbot
```

### دستی (VPS بدون Docker)

### پیش‌نیازها

- PostgreSQL (برای ۲۰۰+ کاربر هم‌زمان توصیه می‌شود)
- Redis (کش و throttling اشتراکی بین workerها)
- nginx (یا caddy) برای TLS و سرو استاتیک/مدیا
- gunicorn

### ۱) متغیرهای محیطی

یک `.env` بر اساس `.env.example` بسازید و مقادیر production را بگذارید
(حداقل: `SECRET_KEY` قوی، `DEBUG=False`، `ALLOWED_HOSTS`،
`WIDGET_PUBLIC_KEY`، `WIDGET_ALLOWED_ORIGINS`، `CORS_ALLOWED_ORIGINS`،
`DB_*`، `CACHE_BACKEND=redis`، `TRUST_PROXY_SSL=True`).

### ۲) دیتابیس و فایل‌های استاتیک

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### ۳) اجرای gunicorn

پیکربندی آماده در `gunicorn.conf.py`:

```bash
gunicorn config.wsgi:application -c gunicorn.conf.py
```

گزینه‌های قابل تنظیم: `GUNICORN_WORKERS`، `GUNICORN_THREADS`،
`GUNICORN_BIND`، `GUNICORN_TIMEOUT`.

### ۴) nginx

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # استاتیک و مدیا
    location /static/  { alias /srv/ai-support/staticfiles/; expires 7d; }
    location /media/   { alias /srv/ai-support/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # nginx مقدار قبلی را پاک می‌کند تا اسپویل ممکن نباشد:
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

> `TRUST_X_FORWARDED_FOR=True` فقط وقتی فعال کنید که nginx مقدار
> `X-Forwarded-For` را بازنویسی کند (خط بالا)؛ در غیر این صورت مهاجم می‌تواند
> با هدر جعلی محدودیت نرخ را دور بزند.

### ۵) systemd

```ini
[Unit]
Description=AI Support Platform
After=network.target postgresql.service redis-server.service

[Service]
User=www-data
WorkingDirectory=/srv/ai-support
EnvironmentFile=/srv/ai-support/.env
ExecStart=/srv/ai-support/.venv/bin/gunicorn config.wsgi:application -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### ۶) HTTPS

- `SECURE_SSL_REDIRECT=True` و `SECURE_HSTS_SECONDS=31536000`
- `TRUST_PROXY_SSL=True` (چون TLS در nginx خاتمه می‌یابد)
- پس از اطمینان از کارکرد کامل HTTPS، HSTS را فعال کنید.

---

## مدل امنیتی

| ریسک | راه‌حل |
| --- | --- |
| دزدیده‌شدن کلید LLM/embedding | کلیدها هرگز در مرورگر نیستند؛ فقط روی سرور و رمزنگاری‌شده در DB (`enc:v1:` + Fernet) |
| استفاده از API توسط سایت‌های دیگر | کلید و دامنه‌های مجاز (از پنل یا env) + throttling چندلایه |
| خواندن مکالمه دیگران | `conversation_token` (HMAC با SECRET_KEY) برای history و feedback و اتصال lead |
| جعل سرنخ/اسپم فرم تماس | honeypot فیلد `website` (پذیرش جعلی بدون ذخیره) + `WIDGET_LEADS_RATE` / `WIDGET_HANDOFF_RATE` |
| SSRF از طریق کرالر | فقط http/https، بدون userinfo، DNS باید public/global باشد، ریدایرکت‌ها دوباره اعتبارسنجی، سقف ۳MB و رعایت robots.txt |
| XSS در ویجت | Shadow DOM + escape کامل متن‌ها + Markdown محدود؛ لینک‌های غیر http(s)/mailto نمایش داده نمی‌شوند |
| ZIP bomb / XML bomb در DOCX | محدودیت تعداد/حجم بخش‌های zip + `defusedxml` |
| فایل جعلی با پسوند مجاز | بررسی magic bytes (sniff) پیش از پردازش |
| کلید ضعیف یا گم‌شده | در Production بدون `SECRET_KEY` پروژه اجرا نمی‌شود |
| حملات بدنه‌ی chunked | رد درخواست‌های بدنه‌دار بدون `Content-Length` |
| سرقت کوکی ادمین | `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` در Production |
| نشت اطلاعات از کش/CDN | پاسخ‌های چت/تاریخچه/بازخورد با `Cache-Control: no-store` |
| Prompt injection در اسناد | پرامپت سیستمی صریحاً دستور می‌دهد دستورهای داخل متن را اجرا نکند |
| نشت راز در سورس/تاریخچه | گارد secret-scan در تست‌ها + gitignore `.env`/آرشیوها؛ روند ممیزی در `docs/SECURITY-TESTING.md` |

**محدودیت شناخته‌شده:** کلید نصب (`WIDGET_PUBLIC_KEY`) یک کلید عمومی است
و داخل جاوااسکریپت ویجت قرار می‌گیرد؛ به‌تنهایی جلوی کپی کامل اسکریپت را
نمی‌گیرد. محافظت واقعی با allowlist دامنه، throttling، محدودیت مصرف و
نگه‌داشتن کلیدهای provider در بک‌اند انجام می‌شود. پنل ادمین نیز فقط با
HTTPS و گذرواژه‌ی قوی در دسترس باشد.

---

## عملکرد و مقیاس‌پذیری

ظرفیت نهایی باید با provider واقعی و benchmark staging اندازه‌گیری شود؛
عدد ثابت «کاربر هم‌زمان» بدون دانستن latency و rate-limit سرویس LLM قابل تضمین نیست.

1. **محدودیت همزمانی LLM (semaphore):** در هر process حداکثر
   `RAG_MAX_CONCURRENT` (پیش‌فرض ۸) فراخوانی هم‌زمان به LLM. درخواست‌های
   مازاد بلافاصله با `429 + Retry-After` پاسخ داده می‌شوند و ویجت پیام
   «مشغول است، دوباره تلاش کنید» را نشان می‌دهد؛ هیچ درخواستی روی صف
   بی‌نهایت گیر نمی‌کند و حافظه/threadها اشباع نمی‌شوند.
2. **کش پاسخ:** سؤال‌های تکراری بدون history (مثلاً پرتکرارترین سؤالات در
   لحظات پیک) تا `RAG_RESPONSE_CACHE_SECONDS` (پیش‌فرض ۶۰ ثانیه) از کش
   پاسخ داده می‌شوند و اصلاً به LLM نمی‌روند.
3. **کش embedding کوئری:** هر کوئری تکراری در یک process دوباره
   embedding نمی‌گیرد (`lru_cache`).
4. **Redis برای throttling اشتراکی:** بدون Redis هر worker شمارنده‌ی
   جداگانه دارد؛ با Redis همه workerها یک سقف مشترک دارند.
5. **ایندکس‌های دیتابیس:** `Message (conversation, created_at)` و
   `AnalyticsEvent (event_type, created_at)`؛ تاریخچه‌ی برگشتی به ۱۰۰ پیام
   آخر محدود شده است.
6. **پیکربندی gunicorn:** مقدار پیش‌فرض محافظه‌کارانه‌ی worker/thread در
   `gunicorn.conf.py` قرار دارد؛ FAISS در هر worker یک نسخه دارد، پس افزایش worker
   مستقیماً RAM را بالا می‌برد و باید با benchmark انجام شود.
7. **بدون بار سنگین اضافی:** `sentence-transformers`/torch فقط در حالت
   embedding محلی lazy-import می‌شوند؛ در حالت API هیچ مدل محلی در حافظه
   workerها نیست.
8. **فایل‌های corpus اتمی:** بازنویسی corpus با `os.replace` و قفل
   `FileLock` انجام می‌شود تا خواننده‌ها هرگز وضعیت نیمه‌کاره نبینند.

### توصیه‌های تیونینگ برای پیک‌های سنگین‌تر

- `RAG_MAX_CONCURRENT` را متناسب با محدودیت rate سرویس‌دهنده‌ی LLM تنظیم
  کنید (مثلاً ۱۰–۲۰ اگر سرویس‌دهنده اجازه می‌دهد).
- `RAG_RESPONSE_CACHE_SECONDS` را برای سؤالات پرتکرار بالا ببرید (۶۰–۳۰۰).
- PostgreSQL + Redis روی همان سرور، و `CONN_MAX_AGE` را بالا نگه دارید.
- اگر فراخوانی LLM با 429 سرویس‌دهنده مواجه شد، `LLM_MAX_RETRIES=1` بگذارید
  (پیش‌فرض ۰ برای تأخیر قابل پیش‌بینی است).

---

## متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
| --- | --- | --- |
| `DEBUG` | `False` | در Production حتماً False |
| `SECRET_KEY` | — (الزامی در Production) | کلید امضای Django و رمزنگاری کلیدهای provider |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | هاست‌های مجاز، جدا شده با کاما |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | — / gapgpt / deepseek-v4-pro | پیش‌فرض مدل پاسخ‌دهنده |
| `LLM_MAX_TOKENS` / `LLM_TIMEOUT_SECONDS` / `LLM_MAX_RETRIES` | 700 / 30 / 0 | محدودیت‌های LLM |
| `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` | — / gapgpt / text-embedding-3-small | پیش‌فرض embedding |
| `EMBEDDING_TIMEOUT_SECONDS` / `EMBEDDING_MAX_RETRIES` | 15 / 0 | محدودیت‌های embedding |
| `WIDGET_PUBLIC_KEY` / `WIDGET_REQUIRE_KEY` | — / True در Production | کلید عمومی نصب (fallback؛ از پنل هم قابل تنظیم است) |
| `WIDGET_ALLOWED_ORIGINS` | — | دامنه‌های مجاز میزبان ویجت (fallback؛ از پنل هم قابل تنظیم است) |
| `WIDGET_RATE` / `WIDGET_EVENTS_RATE` / `WIDGET_FEEDBACK_RATE` | 30/minute / 120/minute / 60/minute | سقف نرخ بر اساس IP |
| `WIDGET_LEADS_RATE` / `WIDGET_HANDOFF_RATE` | 10/minute / 10/minute | سقف ضداسپم فرم سرنخ و ارجاع انسانی |
| `RAG_MAX_CONCURRENT` | 8 | حداکثر LLM هم‌زمان در هر process |
| `RAG_RESPONSE_CACHE_SECONDS` | 60 | مدت کش پاسخ‌های تکراری |
| `RAG_SEMANTIC_CACHE_SECONDS` / `RAG_SEMANTIC_CACHE_SIMILARITY` | 180 / 0.975 | کش معنایی پرسش‌های نزدیک؛ فقط برای سؤال بدون history |
| `RAG_INDEX_TYPE` | auto | Flat برای corpus کوچک و HNSW برای corpus بزرگ |
| `LLM_MAX_ESTIMATED_TOKENS_PER_MINUTE` | 20000 | سقف تخمینی توکن LLM در دقیقه |
| `LLM_MAX_ESTIMATED_TOKENS_PER_CLIENT_MINUTE` | 4000 | سقف تخمینی هر IP/بازدیدکننده در دقیقه |
| `WIDGET_REQUIRE_ORIGIN` | True در Production | الزام دامنه‌ی allowlist شده برای درخواست‌های widget |
| `DB_NAME` و… | — | در صورت تنظیم DB_NAME از PostgreSQL استفاده می‌شود |
| `CACHE_BACKEND` / `CACHE_LOCATION` | LocMem / ai-support-cache | در Production Redis |
| `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | False در Production | CORS برای API ویجت |
| `TRUST_PROXY_SSL` | False | هدر `X-Forwarded-Proto` معتبر است |
| `TRUST_X_FORWARDED_FOR` | False | throttling بر اساس IP واقعی کاربر |
| `SECURE_SSL_REDIRECT` / `SECURE_HSTS_SECONDS` | False / 0 | HTTPS و HSTS |
| `MAIL_BACKEND` و `MAIL_*` | console در DEBUG / SMTP در Production | ایمیل |

---

## تست

```powershell
.\.venv\Scripts\python.exe manage.py test
```

**۱۰۸ تست** شامل: endpointهای API، استریم SSE (قرارداد meta/token/done)،
تاریخچه و بازخورد با توکن HMAC، سرنخ‌ها (honeypot + throttle + اتصال
مکالمه)، ارجاع انسانی، گارد SSRF کرالر، تشخیص نیت، احراز هویت کلید/origin
(از env و پنل)، CORS و preflight، محدودیت حجم بدنه و chunked، رمزنگاری
کلیدها، ZIP bomb / XML bomb، sniff فایل، corpus خالی، احراز هویت پنل
`/panel/` و پنل ادمین — به‌علاوه **گارد secret-scan** که وجود راز/کلید در
سورس را به‌عنوان خطای تست گزارش می‌کند، و **تست‌های آمادگی استقرار**
(`tests_deploy.py`): پارس `DATABASE_URL`، سلامت endpoint بدون کلید در حالت
پروداکشن، self-heal Corpus و سیاست spawn ورکر در کانتینر.

Smoke test صفحات پنل (خارج از test runner):

```powershell
python scripts/panel_smoke.py
```

Load test: `loadtest/locustfile.py` (locust) یا `loadtest/run_load_test.py`
(بدون وابستگی) — گزارش واقعی در `loadtest/LOADTEST.md`: در ۲۰۰ کاربر
هم‌زمان p50 سبک ۱۵ms، صفر خطای 5xx؛ زمان چت واقعی توسط LLM (~۲ تا ۵
ثانیه) تعیین می‌شود.

---

## امنیت و تست‌ها (سند کامل)

جزئیات کامل مدل امنیتی، ممیزی بلاکرهای انتشار prodcheck (با شاهد
`file:line` برای هر آیتم)، یافته‌های امنیتی و وضعیت رفع آن‌ها، و نقشه‌ی
کامل مجموعه تست‌ها در سند مستقل
[`docs/SECURITY-TESTING.md`](docs/SECURITY-TESTING.md) آمده است. این سند
به‌عنوان ضمیمه‌ی رسمی امنیت محصول نگهداری می‌شود و با هر تغییر امنیتی
به‌روز می‌گردد. فهرست خام ۳۲۵ آیتم gate نیز در [`BLOCKERS.md`](BLOCKERS.md)
قابل پیگیری است.

---

## عیب‌یابی

| مشکل | راه‌حل |
| --- | --- |
| `SECRET_KEY is required in production` | `SECRET_KEY` را در `.env` بگذارید |
| ویجت روی سایت مشتری کار نمی‌کند | دامنه‌ی سایت و کلید نصب را در پنل (`/panel/installation/`) ثبت کنید؛ اگر `WIDGET_REQUIRE_KEY=True` است `data-widget-key` را در تگ بگذارید |
| استریم کار نمی‌کند (پاسخ یکجا می‌آید) | پروکسی واسط buffering می‌کند؛ در nginx بلاک `location = /api/chat/stream/` با `proxy_buffering off` لازم است (در nginx.conf آماده است) |
| فرم سرنخ ثبت نمی‌شود | حداقل یکی از ایمیل یا تلفن لازم است؛ نام ≥۲ کاراکتر |
| اعلان تلگرام نمی‌آید | توکن ربات و chat id را در `/panel/ai-settings/` وارد کنید؛ در نبود آن، اعلان ایمیلی ارسال می‌شود |
| کرالر «دامنه غیرعمومی» می‌گوید | کرالر به آدرس‌های داخلی/loopback اجازه نمی‌دهد (گارد SSRF)؛ URL عمومی بدهید |
| دمو تم جدید را نشان نمی‌دهد | `/demo/` برو (نه `/static/demo.html` که فقط ریدایرکت است)؛ تم از پنل خوانده می‌شود — سرور را ری‌استارت نکن، فقط صفحه را رفرش کن |
| پاسخ «اطلاعات مرتبطی پیدا نشد» | اسناد را در `/panel/knowledge/` آپلود یا سایت را کرال کنید؛ سؤالات بی‌پاسخ در پنل تجمیع می‌شوند |
| خطای `corpus_config` | مدل embedding تغییر کرده است؛ همه اسناد را دوباره پردازش کنید |
| همه کاربران یکجا 429 می‌گیرند | پشت proxy هستید؛ `TRUST_X_FORWARDED_FOR=True` + بازنویسی هدر در nginx |
| `RAG_MAX_CONCURRENT` را عوض کردم ولی اثر نکرد | سقف semaphore هنگام اولین استفاده ساخته می‌شود؛ workerها را ری‌استارت کنید |
| آپلود سند با خطای «محتوای فایل با پسوند آن هم‌خوانی ندارد» | فایل واقعاً PDF/TXT/DOCX است؟ پسوند و محتوا باید یکی باشند |
| اسناد/کرال پردازش نمی‌شوند | در استقرار تک‌کانتینری ورکر داخلی هر ۵ ثانیه صف را چک می‌کند؛ روی VPS `runworker --loop` را جدا اجرا کنید |
| پاسخ‌ها خیلی کندند | `LLM_MAX_RETRIES` را ۰ نگه دارید، کش پاسخ را بالا ببرید، و `RAG_MAX_CONCURRENT` را بررسی کنید |
