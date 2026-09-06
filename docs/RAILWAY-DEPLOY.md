# استقرار روی Railway — راهنمای ۱۰ دقیقه‌ای

این راهنما برای نسخه‌ی **تک‌کانتینری** پروژه است: یک سرویس، همه‌چیز داخل آن
(وب + ورکر پس‌زمینه + استاتیک). دیگر نیازی به سرویس worker جدا، nginx،
کانفیگ TLS یا متغیرهای زیاد نیست.

---

## معماری استقرار (چه چیزی ساده شد؟)

```text
Railway Project
 ├── سرویس «app»  ←  از همین ریپو، Dockerfile خودکار ساخته می‌شود
 │     ├── migrate + collectstatic + تعمیر corpus (خودکار، هر استقرار)
 │     ├── worker loop (کرال + پردازش اسناد)
 │     └── gunicorn روی 0.0.0.0:$PORT  +  Whitenoise (استاتیک)
 ├── PostgreSQL   ←  یک کلیک از Railway (متغیر DATABASE_URL خودش ست می‌شود)
 ├── Redis        ←  یک کلیک از Railway (متغیر REDIS_URL خودش ست می‌شود)
 └── Volume       ←  یک کلیک، مانت روی /data (دانش + فایل‌ها ماندگار می‌شوند)
```

---

## قدم به قدم

### ۱) پروژه را بساز
1. ریپو را روی GitHub push کن (یا از همین ریپو استفاده کن).
2. در [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → ریپو را انتخاب کن.
3. Railway خودش `Dockerfile` را می‌سازد و `deploy/entrypoint.sh` را اجرا می‌کند (از `railway.json` می‌خواند). اولین بیلد چند دقیقه طول می‌کشد (torch/faiss سنگین‌اند).

### ۲) دیتابیس و کش را اضافه کن
در همان پروژه: **+ New** → **Database** → **Add PostgreSQL**
دوباره: **+ New** → **Database** → **Add Redis**

تمام شد. Railway دو متغیر `DATABASE_URL` و `REDIS_URL` را خودش به سرویس
«app» تزریق می‌کند (از تب Variables هر دیتابیس، گزینه‌ی Link را بزن یا
Reference Variable بساز: `DATABASE_URL=${{Postgres.DATABASE_URL}}`).

### ۳) حجم ماندگار (Volume) را وصل کن
سرویس «app» → تب **Settings** → **Volumes** → **+ New Volume** →
Mount path: `/data`

بدون این قدم، فایل‌های دانش (corpus) و مدیاهای آپلودی با هر deploy پاک
می‌شوند. با این قدم، `PERSIST_DIR` را هم ست می‌کنیم (قدم ۴).

### ۴) فقط این متغیرها را در تب Variables سرویس «app» بگذار

| متغیر | مقدار | توضیح |
|---|---|---|
| `SECRET_KEY` | یک رشته‌ی تصادفی ۵۰+ کاراکتری | **الزامی** — `python -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `PERSIST_DIR` | `/data` | با Volume قدم ۳ — ماندگاری دانش/مدیا |
| `DJANGO_SUPERUSER_USERNAME` | مثلا `admin` | اختیاری — ساخت خودکار ادمین در اولین بوت |
| `DJANGO_SUPERUSER_EMAIL` | ایمیل تو | اختیاری |
| `DJANGO_SUPERUSER_PASSWORD` | رمز قوی | اختیاری |

**همه‌چیز دیگر خودکار است:** `DATABASE_URL` و `REDIS_URL` (تزریق Railway)،
`ALLOWED_HOSTS` و `CSRF_TRUSTED_ORIGINS` (از `RAILWAY_PUBLIC_DOMAIN` خودکار)،
تشخیص HTTPS پشت پروکسی (خودکار)، `USE_WHITENOISE` و `SPAWN_WORKERS`
(داخل Dockerfile ست شده‌اند).

اختیاری برای سخت‌گیری بیشتر: `SECURE_SSL_REDIRECT=True` و
`SECURE_HSTS_SECONDS=31536000` (فقط وقتی مطمئنی HTTPS نهایی است).

### ۵) Deploy را بزن و سلامت را چک کن
- Railway بعد از بیلد، `/api/health/` را صدا می‌زند؛ باید `200` بگیرد
  (این endpoint عمداً بدون کلید ویجت جواب می‌دهد و فقط بولین برمی‌گرداند).
- دامنه‌ی عمومی: تب Settings → Networking → **Generate Domain**.
- `https://<دامنه>/api/health/` را در مرورگر باز کن → `{"status": "ok"}`.

### ۶) اولین ورود به پنل
- اگر superuser خودکار نساختی: تب سرویس → **Deployments** → آخرین deploy →
  در три‌نقطه‌ی آن **Open Shell** (یا `railway shell` با CLI) و:
  ```bash
  python manage.py createsuperuser
  ```
- برو به `https://<دامنه>/panel/` → با اکانتت لاگین کن →
  تب «هوش مصنوعی»: کلیدهای LLM/Embedding را وارد کن
  → تب «دانش»: سایت را کرال کن یا فایل بده.

### ۷) ویجت را روی سایت مشتری بگذار
در پنل → «نصب و راه‌اندازی»: اسنیپت آماده را کپی کن و قبل از `</body>`
سایت مشتری بگذار. حواست باشد دامنه‌ی سایت مشتری در پنل
(تنظیمات → دامنه‌های مجاز) اضافه شده باشد — وگرنه مرورگر درخواست را
(CORS) بلاک می‌کند.

---

## خراب شد؟ عیب‌یابی سریع

| علامت | علت | راه‌حل |
|---|---|---|
| Deploy در healthcheck گیر می‌کند | دیتابیس هنوز بالا نیامده | ورک‌فلوی entrypoint تا ۵ بار retry می‌کند؛ یک redeploy بزن. اگر مکرر است لاگ سرویس را ببین |
| `DisallowedHost` | دامنه‌ی سفارشی داری | آن دامنه را به `ALLOWED_HOSTS` در Variables اضافه کن |
| چت می‌گوید corpus/paas error | مدل embedding تغییر کرده ولی اسناد قدیمی‌اند | پنل → دانش → دکمه‌ی «پردازش مجدد» همه‌ی اسناد |
| استاتیک‌ها (CSS/ویجت) ۴۰۴ | collectstatic رد شده | لاگ استقرار را ببین؛ `python manage.py collectstatic --noinput` را در Shell بزن |
| کرال/پردازش انجام نمی‌شود | ورکر همان لحظه مشغول است | ورکر داخل همان کانتینر هر ۵ ثانیه صف را چک می‌کند؛ در پنل وضعیت را ببین |
| Memory OOM در پلن کوچک | workerهای gunicorn زیاد | Variables: `GUNICORN_WORKERS=1` |

---

## تفاوت‌های این معماری با قبل

- **یک سرویس به‌جای دو سرویس** — web و worker در همان کانتینر (ورکر داخل
  کانتینر به‌جای subprocess جداسازی‌شده اجرا می‌شود؛ `SPAWN_WORKERS=auto`).
- **استاتیک با Whitenoise** از خود Django سرو می‌شود؛ nginx فقط در سناریوی
  VPS (docker-compose) استفاده می‌شود و آنجا هم استاتیک را پروکسی می‌کند.
- **self-heal corpus**: اگر استقرار وسط نوشتن corpus قطع شود، `ensure_deploy`
  فایل‌های ناقص را پاک می‌کند تا پلتفرم به‌جای ۵۰۳ ابدی، با corpus خالی بالا
  بیاید و از پنل پردازش مجدد بدهی.
- **نام فایل‌های استاتیک hash نمی‌شوند** تا اسنیپت نصب مشتری‌ها
  (`widget-<theme>.js`) پایدار بماند.
