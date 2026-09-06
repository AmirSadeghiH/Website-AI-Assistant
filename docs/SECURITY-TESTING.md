# سند امنیت و تست‌ها — AI Support Platform

> آخرین به‌روزرسانی: ۲۰۲۶-۰۹-۰۵ · نسخه محصول: 1.0.0 · مبنای ممیزی: [prodcheck](https://github.com/FarzamHabibi/pre-production-checklist) (۴٬۳۵۲ آیتم؛ gate فیلترشده برای Django/any: ۳۲۵ آیتم در `BLOCKERS.md`)

این سند دو چیز را پوشش می‌دهد: **(۱)** مدل امنیتی محصول و نتایج ممیزی بلاکرهای انتشار، **(۲)** نقشهٔ کامل مجموعه تست‌ها (۱۰۸ تست) و نتایج load test. مسیر کار ممیزی: `BLOCKERS.md` در ریشهٔ ریپو — هر آیتم باید یا با `file:line` تأیید شود یا UNKNOWN بماند؛ هیچ آیتمی خودجوش «تأییدشده» نمی‌شود.

---

## ۱) معماری مواجه با اینترنت (Threat Model خلاصه)

```text
مرورگر بازدیدکننده سایت مشتری
   │  <script src="/static/widget/widget[-<theme>].js">
   ▼
ویجت (Shadow DOM، بدون فریم‌ورک) ── CORS + X-Widget-Key + X-Conversation-Token ──▶ Django/DRF
   ├── /api/chat/  ,  /api/chat/stream/   ← سطح عمومی (کلید + origin + throttle)
   ├── /api/history|feedback|leads|handoff|events|widget-config|health
   ├── /demo/                             ← دموی تم‌دار (رندر داینامیک)
   ├── /panel/*  (۱۹ مسیر)                ← @staff_member_required + CSRF
   └── /admin/                            ← جلسهٔ Django + rate-limit لاگین

Worker جدا: crawl (گارد SSRF) و document/embedding pipeline
ذخیره‌سازی: SQLite (توسعه) / PostgreSQL (پروداکشن) + Redis (throttle اشتراکی) + media/
```

**سطح‌های اعتماد:**
| سطح | احراز هویت | شواهد |
|---|---|---|
| بازدیدکننده ویجت | کلید عمومی نصب + allowlist دامنه + HMAC توکن مکالمه | `chat/api_permissions.py:159-205`، `chat/conversation_tokens.py:29-33` |
| ادمین پنل | جلسهٔ Django + `staff_member_required` + CSRF | `chat/panel_urls.py:10-28` |
| Worker | فقط از صف داخلی spawn می‌شود؛ argv ثابت، بدون shell | `chat/crawler.py:437-442` |

---

## ۲) کنترل‌های امنیتی تأییدشده (با شاهد file:line)

| کنترل | شاهد |
|---|---|
| کلید ویجت با مقایسهٔ constant-time | `chat/api_permissions.py:195-198` — `hmac.compare_digest` |
| bypass حلقهٔ محلی فقط در DEBUG | `chat/api_permissions.py:187-188` + پیش‌فرض `WIDGET_REQUIRE_KEY=True` در غیر DEBUG (`config/settings.py:236-239`) |
| توکن مکالمه HMAC-SHA256 | `chat/conversation_tokens.py:20-26`؛ history/feedback/lead/handoff همه توکن را چک می‌کنند (`chat/views.py:754,837,896,956`) |
| سند آپلودی از وب سرو نمی‌شود | `chat/middleware.py:220-225` — `Http404` برای `/media/documents/` (+ تست `test_media_documents_returns_404`) |
| گارد SSRF کرالر (per-hop) | `chat/crawler.py:54-92` فقط IP عمومی؛ re-check در هر ریدایرکت (`crawler.py:250-252`)؛ سقف ۳MB و robots.txt (`crawler.py:37,219-244`) |
| رمزنگاری کلیدهای provider در DB | `chat/encrypted_fields.py` — Fernet با کلید PBKDF2(200k) از `FIELD_ENCRYPTION_KEY`/`SECRET_KEY`؛ فرمت `enc:v1:` |
| بدون اجرای shell | `grep shell=True/os.system/eval` → صفر؛ subprocess فقط argv لیستی (`crawler.py:437-442`, `document_pipeline.py:353-356`) |
| محدودیت بدنهٔ API | ۶۴KB روی `/api/` (`chat/middleware.py:152-205`) + ۲۵MB آپلود پنل (`config/settings.py:168`) |
| throttle چندلایه | chat 30/min + کلید 1000/min + events 120/min + leads/handoff 10/min (`config/settings.py:248-253`) |
| rate-limit لاگین ادمین | ۵ تلاش (`chat/middleware.py:49-56`) |
| CORS صریح | `CORS_URLS_REGEX ^/api/`؛ `CORS_ALLOW_ALL_ORIGINS` پیش‌فرض False در غیر DEBUG (`config/settings.py:223-226,233`) |
| امنیت کوکی/هدر در پروداکشن | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, nosniff, referrer-policy (`config/settings.py`) |
| Healthcheck بدون کلید ویجت | `/api/health/` عمومی با payload بولینِ حداقلی (`chat/views.py` — `@permission_classes([])`)؛ در strict mode هم 200 می‌دهد تا healthcheck پلتفرم deploy را fail نکند |
| گیرندهٔ اعلان‌ها ثابت | `mail_admins` + `chat_id` پنل (`chat/notify.py:27-57`) — visitor ایمیل‌فرست نیست |

---

## ۳) یافته‌های ممیزی و وضعیت رفع

### 🔴 یافتهٔ بحرانی: نشت کلید API از طریق zip کامیت‌شده (رفع شد — چرخش کلید با ادمین است)
- **شرح:** فایل `ai-support-platform.zip` (شامل کپی `.env` با کلید واقعی LLM و لاگ خطاها) **track شده** و در commitهای `af996d7` و `49abad9` به GitHub push شده بود.
- **رفع انجام‌شده:** untrack (`git rm --cached`)، حذف محلی، افزودن `*.zip` و فایل‌های قراضه به `.gitignore`، و افزودن **گارد secret-scan** به تست‌ها (بخش ۴) تا بازگشت آن زنگ بخورد.
- **اقدام باقی‌مانده برای ادمین (نمی‌توانم به‌جایت انجام دهم):**
  1. **کلید LLM/embedding را rotate کن** (پنل → AI settings یا `.env`) — کلید فعلی در تاریخچهٔ GitHub است.
  2. `SECRET_KEY` پروداکشن را **متمایز** از کلیدهای API انتخاب کن (هرگز یک مقدار برای هر دو نباشد) — قالب هشدار در `.env` گذاشته شد.
  3. اگر ریپو public است، پاک‌سازی تاریخچه (BFG/`git filter-repo`) یا خصوصی‌کردن ریپو را تصمیم بگیر.

### ⚠️ یافتهٔ متوسط: یکسان‌بودن `SECRET_KEY` با کلید LLM (رفع شد در سند؛ تعویض با ادمین)
- `.env` قبلی یک مقدار واحد را هم برای امضای Django و هم کلید LLM می‌گذاشت. اکنون `SECRET_KEY` جدا انتخاب شود؛ کلیدهای ذخیره‌شدهٔ provider با `FIELD_ENCRYPTION_KEY` قابل انتقال‌اند (`chat/encrypted_fields.py:24-30`).

### ⚪ موارد UNKNOWN/N-A (بلاک‌کننده نیست، ولی قبل از انتشار باید تصمیم بگیرند)
| موضوع | وضعیت |
|---|---|
| TLS/DNS/IAM پروداکشن | UNKNOWN تا انتخاب سرور — بلاکرهای ۳ بخش ۳ در `BLOCKERS.md` |
| فرایند deploy بدون review | UNKNOWN — فعلاً deploy دستی است، CI وجود ندارد |
| بازیابی رمز ادمین | نیازمند SMTP پروداکشن (`config/settings.py:296-315`) |
| DAST / SAST رسمی | اجرا نشده؛ گارد secret-scan و ۳۷ تست امنیتی خودکار جایگزین حداقلی‌اند |

---

## ۴) مجموعه تست‌ها — ۱۰۸ تست سبز

اجرای کامل:

```powershell
.\.venv\Scripts\python.exe manage.py test        # 108 tests, OK
python scripts/panel_smoke.py                     # smoke صفحات پنل
```

| فایل | تعداد | پوشش |
|---|---|---|
| `chat/tests.py` | ۵۲ مؤثر | endpointهای API، خطاهای 400/411/413/503، رمزنگاری کلیدها در DB، singleton کانفیگ، widget-key/origin (از env و پنل)، CORS + preflight، اعلان خطا، formهای provider، فرم سند، **ZIP bomb**، **XML entity expansion**، **sniff فایل**، retriever (dimension mismatch/corpus خالی)، worker صف، بازخورد، origin matcher (exact/wildcard/referer)، media 404، تحلیل‌های staff. *چهار کلاس تست که دوباره تعریف شده بودند (شادوینگ) در همین پاس تمیزکاری شدند.* |
| `chat/tests_security.py` | ۳۷ | **HMAC توکن مکالمه** (history/feedback/lead/handoff: معتبر/جعلی/ناموجود)، honeypot سرنخ (پاسخ جعلی بدون ذخیره)، rate-limit سرنخ، کانال‌های handoff، قرارداد استریم SSE (meta/token/done، fallback، bind مکالمه)، **گارد SSRF** (loopback/private/scheme/userinfo)، تشخیص نیت + نرمال‌سازی، احراز پنل (anonymous redirect، staff dashboard) |
| `chat/tests_secretscan.py` | ۳ | **گارد ضد نشت راز:** scan ریپو برای الگوهای `sk-…`/`ghp_…`/AWS/Google/key-block، ممنوعیت فایل کلید روی دیسک، الزام gitignore بودن `.env` و آرشیوها |
| `chat/tests_deploy.py` | ۱۶ | **آمادگی استقرار:** پارس `DATABASE_URL` (postgres/sqlite/خطا)، endpoint سلامت بدون کلید ویجت در پروداکشن، هم‌راستایی مسیرهای corpus با `settings.CORPUS_DATA_DIR`، self-heal corpus (fresh/partial/mismatch/consistent — روی دایرکتوری temp ایزوله)، سیاست spawn ورکر (auto/explicit/کانتینر/دستگاه توسعه) |

**نتایج load test** (`loadtest/LOADTEST.md`): ۲۰۰ کاربر هم‌زمان → `widget-config`/`health` با p50=۱۵ms، **صفر خطای 5xx**؛ چت واقعی p50≈۳.۲s که سقفش توسط API ارائه‌دهندهٔ LLM تعیین می‌شود نه Django.

---

## ۵) وضعیت بلاکرهای prodcheck (خلاصهٔ ۳۲۵ آیتم)

| بخش | وضعیت |
|---|---|
| ۱ — یافته‌های بلاک‌کننده (۲۰) | ۱۶ تأیید، ۱ یافته (zip/کلید — رفع شد)، ۱ UNKNOWN، ۲ N/A |
| ۲ — موارد ممنوع پرخطر (۲۰) | ✅ همه بررسی شد (بالا) — تنها اکشن: چرخش کلید |
| ۳.. — کانفیگ پروداکشن، جداسازی staging، اتوماسیون تست، سناریوهای pen-test، sign-off، دروازهٔ AI، Vibe-Coding، مقیاس، پرفورمنس، post-launch | فهرست خام در `BLOCKERS.md` — بررسی بخش‌به‌بخش ادامه دارد |

**قانون کار:** هیچ آیتمی بدون شاهد `file:line` تیک نمی‌خورد؛ «UNKNOWN» پاسخ معتبری است و به معنی «بازبینی انسانی لازم دارد» است.
