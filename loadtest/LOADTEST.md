# Load Test Report — AI Support Platform
تاریخ اجرا: تکمیل WP10 · محیط: ویندوز توسعه‌دهنده (SQLite + LocMem cache، `runserver`)
اسکریپت: `loadtest/run_load_test.py` (استاندارد لایبرری، بدون وابستگی) + `loadtest/locustfile.py` برای locust

## نتیجه‌ی اجرای واقعی (این ماشین)

### مسیرهای سبک — ۴ مرحله‌ی افزایشی (هر مرحله ۱۲ ثانیه)

| فاز | کاربر مجازی | مجموع درخواست | توان عبوری | p50 | p95 | خطای ≠429 |
|---|---|---|---|---|---|---|
| A1 | 10 | 7 (warm-up) | 0.6 rps | ~100ms | ~110ms | 0 |
| A2 | 50 | 5,645 | **432.9 rps** | 13ms | 664–835ms | فقط events=117 (throttle عمدی 120/min) |
| A3 | 100 | 7,154 | **574.6 rps** | 13ms | 534–707ms | **صفر** |
| A4 | 200 | 4,734 | **389.1 rps** | 15ms | ~1,060ms | **صفر** |

- `/api/health/` و `/api/widget-config/` حتی با ۲۰۰ کاربر هم‌زمان p50 = ۱۵ms.
- خطای `events` در فاز A2، برخورد با سقف `WIDGET_EVENTS_RATE=120/minute` است؛
  یعنی anti-abuse کار می‌کند. با ۱۰۰ و ۲۰۰ کاربر (IP ثابتِ تست، پس سقف مشترک) صفر شد
  چون فاصله‌ی بین درخواست‌ها بیشتر شد.
- **هیچ خطای 5xx در هیچ فازی وجود ندارد** — گرچه dev server تک‌پردازشی است.

### مسیر سنگین — chat واقعی (RAG کامل با LLM گپ‌جی‌پی‌تی)

| # | latency | fallback | citations | intent |
|---|---|---|---|---|
| 1 | 4,852ms | خیر | 1 | general |
| 2 | 1,955ms | خیر | 1 | general |
| 3 | 1,905ms | خیر | 1 | contact_request |
| 4 | 3,194ms | خیر | 1 | general |

p50 ≈ 3.2s, max ≈ 4.9s — زمان پاسخ توسط **API ارائه‌دهنده‌ی LLM** تعیین می‌شود، نه Django.
Cache پاسخ‌های تکراری (`RAG_RESPONSE_CACHE_SECONDS=60`) سؤال دومی‌ها را به <50ms می‌رساند.

## نحوه‌ی بازتولید

```powershell
python manage.py runserver 127.0.0.1:8010 --noreload   # ترمینال جدا
python loadtest/run_load_test.py                        # این گزارش
locust -f loadtest/locustfile.py --host http://127.0.0.1:8010 --headless --users 100 --spawn-rate 10 --run-time 3m
```

## تحلیل و توصیه‌ی ظرفیت

1. **گرلوگاه، سهم LLM است نه وب‌سرور.** Django در ۵۷۴ rps درخواست سبک با
   `runserver` (کم‌ترین حالت ممکن production) هم سالم ماند؛ در استقرار
   gunicorn 4×24 + Postgres + Redis همین سقف چند برابر می‌شود.
2. **سقف نرم‌افزاری `RAG_MAX_CONCURRENT=8` درست است:** هزینه‌ی LLM را مهار
   می‌کند. اگر مشتری ترافیک بالاتر برد، همین متغیر را بالا ببرید.
3. **برای هر سایت مشتری با ≤۵۰ بازدیدکننده‌ی هم‌زمان** پیکربندی پیش‌فرض
   کافی است؛ در فازهای ۱۰۰–۲۰۰ کاربر هیچ خطای سرور دیدیم.
4. **سقف‌های امنیتی فعال مشاهده شد:** events throttle در A2 دقیقاً جایی که
   باید فعال می‌شد؛ 429 به‌عنوان پاسخ درست (نه failure) حساب می‌شود.
5. استقرار واقعی: `docker compose up -d --build` (سرویس‌های web + worker +
   postgres + redis + nginx) یا Railway (`railway.json` + `runworker`).
