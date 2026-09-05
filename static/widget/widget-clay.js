/**
 * AI Support Widget v6.0 — "Lumina" Commercial Edition
 * ─────────────────────────────────────────────────────────────────────────
 * Frontend completely redesigned, 3 levels up:
 *   · Animated gradient border-beam around the glass panel (@property)
 *   · Ambient light glow, cinematic blur-in open, staggered panel chrome
 *   · AI staged thinking statuses with shimmer text
 *   · Buttery rAF typewriter streaming + gradient caret
 *   · Voice input with live waveform visualizer (Web Speech, progressive)
 *   · Professional contact bottom-sheet: brand channel cards, labeled form,
 *     inline validation, spinner state, animated success checkmark
 *   · Hero welcome with orbiting particles, unread badge, title flash,
 *     teaser bubble, day separators, retry-on-error, offline banner
 *   · Full RTL, deep dark mode, reduced-motion, safe-area, a11y rings
 *
 * Backend / API layer (unchanged contract):
 *   · JSON chat fallback + SSE streaming (meta/token/done/error)
 *   · Remote config, events, feedback, history, leads, handoff
 *   · Session (server token) + local (7-day) history persistence
 *   · postMessage live-preview channel for the admin customizer
 */
(function () {
  "use strict";

  if (window.AISupportWidget) return;

  var scriptElement = document.currentScript;
  var scriptConfig = scriptElement && scriptElement.dataset ? scriptElement.dataset : {};

  /* ─────────────── DEFAULTS ─────────────── */
  var DEFAULTS = {
    apiEndpoint: "/api/chat/",
    configEndpoint: "",
    eventsEndpoint: "",
    feedbackEndpoint: "",
    widgetPublicKey: "",
    title: "دستیار هوش مصنوعی",
    subtitle: "آنلاین • پاسخ فوری",
    greeting: "سلام! 👋 چطور می‌توانم کمکتان کنم؟",
    timeoutMs: 45000,
    primaryColor: "#6366f1",
    secondaryColor: "#8b5cf6",
    accentColor: "#a78bfa",
    headerBadge: "آنلاین",
    botAvatarText: "✦",
    inputPlaceholder: "پیام خود را بنویسید...",
    themeMode: "gradient",
    darkMode: "auto",
    panelWidth: 400,
    panelHeight: 640,
    borderRadius: 24,
    mobileFullscreen: true,
    logoUrl: "",
    fontFamily: "'Vazirmatn', 'Inter', 'IRANSansX', ui-sans-serif, system-ui, sans-serif",
    fontSize: "normal",
    showPoweredBy: true,
    showTimestamp: true,
    showAvatar: true,
    showFeedback: true,
    enableSounds: false,
    enableAnimations: true,
    bubbleStyle: "rounded",
    position: "bottom-right",
    positionVerticalOffset: 24,
    positionHorizontalOffset: 24,
    iconType: "default",
    defaultIconChoice: "chat-bubble",
    customIconUrl: "",
    suggestions: [],
    faqUrl: "",
    privacyUrl: "",
    supportEmail: "",
    sessionId: "",
    /* v4 — streaming, citations, lead capture, human handoff */
    enableStreaming: true,
    showCitations: true,
    enableLeadCapture: true,
    leadFormTitle: "تماس با کارشناسان ما",
    leadFormDescription: "راه دلخواه‌تان را انتخاب کنید یا فرم را پر کنید؛ در اسرع وقت پاسخ می‌دهیم.",
    enableHandoff: true,
    handoffTrigger: "low_confidence",
    handoffMessage: "پاسخ این سؤال در دانش دستیار نبود؛ یک کارشناس انسانی بررسی می‌کند.",
    handoffUrls: {},
    handoffLabel: "گفتگو با کارشناس",
    /* v5 — engagement */
    showTeaser: true,
    teaserText: "معمولاً در کمتر از یک دقیقه پاسخ می‌دهیم.",
    /* v6 — product polish */
    enableVoiceInput: true,
    fabLabel: "سوالی دارید؟ همین حالا بپرسید",
    supportPhone: "",
  };

  /* ─────────────── SVG ICONS ─────────────── */
  var FAB_ICONS = {
    "chat-bubble": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
    "message-circle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    "robot": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="9" cy="16" r="1"/><circle cx="15" cy="16" r="1"/><path d="M12 11V7"/><path d="M8 7h8"/><path d="M8 3l2 4M16 3l-2 4"/></svg>',
    "headset": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    "sparkle": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z"/></svg>',
    "lightning": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
  };

  var ICONS = {
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>',
    arrowUp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>',
    copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    thumbUp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>',
    thumbDown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>',
    thumbUpFilled: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>',
    thumbDownFilled: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>',
    link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="m2 7 10 7L22 7"/></svg>',
    user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    stop: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"/><path d="M3 3v5h5"/></svg>',
    chevronDown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    chevronLeft: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>',
    sparkles: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c.9 4.6 2.4 6.1 7 7-4.6.9-6.1 2.4-7 7-.9-4.6-2.4-6.1-7-7 4.6-.9 6.1-2.4 7-7z"/><path d="M19 14.5c.4 2 1.05 2.65 3 3-1.95.35-2.6 1-3 3-.4-2-1.05-2.65-3-3 1.95-.35 2.6-1 3-3z" opacity=".7"/></svg>',
    mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v1a7 7 0 0 0 14 0v-1"/><path d="M12 18v4"/></svg>',
    wifiOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.4a5 5 0 0 1 7 0"/><path d="M5 12.9a10 10 0 0 1 5.17-2.69"/><path d="M19 12.9a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>',
  };

  var THINKING_STATUSES = [
    "در حال تحلیل سؤال شما…",
    "جستجو در منابع دانش…",
    "مرتب‌سازی اطلاعات پیدا شده…",
    "نوشتن پاسخ…",
  ];

  /* ─────────────── CSS ─────────────── */
  var CSS = `
    /* ═══════════════════════════════════════════════════════════════════════
       AI Support Widget — CLAYMORPHISM
       ───────────────────────────────────────────────────────────────────────
       Every element is a piece of soft, matte modelling clay: puffy,
       rounded, pressable. The recipe applied to each shape:

         1. HUGE RADII    · corners rounded far past normal UI values, so
                            shapes read as squishy volumes, not rectangles
         2. DOUBLE INSET  · a bright inset from the top-left (light hitting
                            the rounded lip) + a darker inset from the
                            bottom-right (the shape curving away)
         3. SOFT DROP     · a wide, tinted, low-opacity outer shadow — clay
                            sits ON the surface, it does not float
         4. MATTE PASTEL  · desaturated candy colours, never a gradient
                            sheen and never a specular highlight
         5. SQUISH        · pressing deforms the clay: it scales down
                            slightly and its inner shadows deepen

       The clay vocabulary is expressed as reusable tokens:
            --clay      raised piece, resting
            --clay-up   raised piece, lifted on hover
            --clay-in   pressed piece, pushed into the surface
            --clay-deep a well carved out of the surface

       Class names, IDs and state hooks are IDENTICAL to the original build,
       so the API, SSE streaming, memory, events and admin preview channel
       are completely untouched — only the presentation layer is new.
       ═══════════════════════════════════════════════════════════════════════ */
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    :host{all:initial;--asw-font:'Vazirmatn','Vazir','IRANSans','Nunito',ui-rounded,system-ui,sans-serif}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

    /* ═══════════════════════════════════════════════════════════════════
       TOKENS — the clay palette
       ═══════════════════════════════════════════════════════════════════ */
    .asw{
      --asw-primary:#8b7cf6;--asw-secondary:#5eddc0;--asw-accent:#ffa9c9;
      --accent:var(--asw-primary);
      --accent-2:var(--asw-secondary);
      --accent-3:var(--asw-accent);

      /* the tabletop the clay rests on */
      --room:#f0edfb;
      --room-2:#e8e4f7;

      /* clay bodies — matte pastels */
      --clay-body:#faf8ff;
      --clay-body-2:#f2eefc;
      --clay-body-3:#e9e4f8;
      --clay-lilac:#c8bdf5;
      --clay-mint:#a8e6d5;
      --clay-peach:#ffd0c4;
      --clay-butter:#ffe6a8;
      --clay-rose:#ffc4dc;

      /* the two lights baked into every piece */
      --lip:rgba(255,255,255,.9);        /* top-left lip catching light */
      --curve:rgba(140,120,190,.22);     /* bottom-right curving away  */
      --drop:rgba(126,105,190,.18);      /* tinted contact shadow      */
      --drop-2:rgba(126,105,190,.26);

      /* ── the clay vocabulary ── */
      --clay:
        inset 4px 4px 10px var(--lip),
        inset -5px -5px 12px var(--curve),
        8px 10px 22px -6px var(--drop);
      --clay-up:
        inset 5px 5px 12px var(--lip),
        inset -6px -6px 14px var(--curve),
        14px 20px 34px -8px var(--drop-2);
      --clay-in:
        inset -4px -4px 10px var(--lip),
        inset 5px 5px 12px var(--curve),
        3px 4px 10px -4px var(--drop);
      --clay-deep:
        inset 7px 7px 16px var(--curve),
        inset -6px -6px 14px var(--lip);
      --clay-sm:
        inset 3px 3px 7px var(--lip),
        inset -3px -3px 8px var(--curve),
        5px 6px 14px -5px var(--drop);

      /* ink — warm and soft, never pure black */
      --ink:#4a3f6b;
      --ink-2:#7a6f9c;
      --ink-3:#a79dc4;
      --on-accent:#ffffff;

      --ok:#4cbf9a;--err:#f4708f;--warn:#e8a838;--online:#4cbf9a;

      /* geometry — clay is very, very round */
      --r-sm:16px;--r-md:24px;--r-lg:32px;--r-xl:42px;--r-blob:50px;--r-pill:999px;

      --sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:20px;--sp-6:24px;--sp-8:32px;--sp-10:40px;

      --t-xs:11px;--t-sm:12.5px;--t-md:14px;--t-lg:16px;--t-xl:20px;
      --w-reg:500;--w-med:600;--w-bold:800;

      /* motion — bouncy, like squeezing something soft */
      --ms:170ms;--mm:280ms;--ml:420ms;
      --ease:cubic-bezier(.4,0,.2,1);
      --squish:cubic-bezier(.34,1.56,.64,1);

      /* aliases consumed by the unchanged JS */
      --asw-bg:var(--room);--asw-surface:var(--clay-body);--asw-surface-2:var(--clay-body-2);
      --asw-text:var(--ink);--asw-text-secondary:var(--ink-2);--asw-text-muted:var(--ink-3);
      --asw-border:transparent;--asw-border-strong:var(--curve);
      --asw-bot-bg:var(--clay-body);--asw-bot-text:var(--ink);
      --asw-user-bg:var(--clay-lilac);--asw-user-bg-2:var(--clay-lilac);--asw-user-text:#3d3168;
      --asw-input-bg:var(--room-2);--asw-input-focus-bg:var(--room-2);
      --asw-shadow:var(--clay-up);--asw-header-bg:transparent;
      --asw-radius:var(--r-xl);--asw-radius-sm:var(--r-md);--asw-radius-xs:var(--r-sm);
      --asw-success:var(--ok);--asw-error:var(--err);--asw-warning:var(--warn);
      --asw-panel-w:392px;--asw-panel-h:640px;
      --asw-spring:var(--squish);--asw-out:var(--squish);

      font-family:var(--asw-font);
      font-size:var(--asw-font-size,14px);
      direction:rtl;line-height:1.8;
      color:var(--ink);
      font-weight:var(--w-reg);
      -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
    }

    /* ─── night clay: darker plasticine, same soft physics ─── */
    .asw.dark{
      --room:#221f35;
      --room-2:#1b1930;
      --clay-body:#2e2a45;
      --clay-body-2:#332f4d;
      --clay-body-3:#3a3557;
      --clay-lilac:#6d5fc4;
      --clay-mint:#3f9e88;
      --clay-peach:#c47f6f;
      --clay-butter:#c9a355;
      --clay-rose:#c26f96;

      --lip:rgba(255,255,255,.07);
      --curve:rgba(0,0,0,.42);
      --drop:rgba(0,0,0,.42);
      --drop-2:rgba(0,0,0,.55);

      --ink:#ece8fb;
      --ink-2:#b3aad4;
      --ink-3:#8279a8;

      --ok:#5fd6ac;--err:#ff8ba6;--warn:#f0bc5e;--online:#5fd6ac;
      --asw-user-text:#ffffff;
    }

    /* ═══════════════════════════════════════════════════════════════════
       ROOT
       ═══════════════════════════════════════════════════════════════════ */
    .asw-root{position:fixed;z-index:2147483647;width:0;height:0;pointer-events:none}
    .asw-root>*{pointer-events:auto}
    .asw-root *{box-sizing:border-box}

    .asw-glow{position:fixed;z-index:0;width:320px;height:320px;border-radius:var(--r-pill);pointer-events:none;
      background:radial-gradient(circle at 35% 35%,color-mix(in srgb,var(--accent) 45%,transparent),transparent 62%),
                 radial-gradient(circle at 68% 68%,color-mix(in srgb,var(--accent-2) 40%,transparent),transparent 60%);
      filter:blur(70px);opacity:0;transform:scale(.7);
      transition:opacity var(--ml) var(--ease),transform var(--ml) var(--squish)}
    .asw-glow.show{opacity:.55;transform:scale(1)}

    /* ═══════════════════════════════════════════════════════════════════
       LAUNCHER — a fat blob of lilac clay
       ═══════════════════════════════════════════════════════════════════ */
    .asw-fab{position:fixed;width:66px;height:66px;border:none;cursor:pointer;z-index:2;
      display:grid;place-items:center;
      border-radius:var(--r-blob);
      background:var(--clay-lilac);
      color:#fff;
      box-shadow:var(--clay);
      transition:transform var(--mm) var(--squish),box-shadow var(--mm) var(--ease),border-radius var(--mm) var(--squish);
      animation:cl-plop var(--ml) var(--squish) 100ms both}
    .asw-fab:hover{transform:translateY(-4px) scale(1.05);box-shadow:var(--clay-up);
      border-radius:44% 56% 52% 48% / 50% 46% 54% 50%}
    /* squish on press */
    .asw-fab:active{transform:translateY(0) scale(.93);box-shadow:var(--clay-in);
      border-radius:52% 48% 46% 54% / 48% 52% 48% 52%;transition-duration:var(--ms)}
    .asw-fab.active{background:var(--clay-body);color:var(--ink-2);box-shadow:var(--clay-in)}
    .asw-fab svg{width:26px;height:26px;position:relative}
    .asw-fab-shine{position:absolute;inset:0;border-radius:inherit;pointer-events:none;
      background:radial-gradient(58% 42% at 32% 24%,rgba(255,255,255,.32),transparent 68%)}
    .asw-fab-icon-main,.asw-fab-icon-close{position:absolute;inset:0;display:grid;place-items:center;
      transition:opacity var(--ms) var(--ease),transform var(--mm) var(--squish)}
    .asw-fab-icon-close{opacity:0;transform:rotate(-90deg) scale(.5)}
    .asw-fab.active .asw-fab-icon-main{opacity:0;transform:rotate(90deg) scale(.5)}
    .asw-fab.active .asw-fab-icon-close{opacity:1;transform:rotate(0) scale(1)}
    .asw-fab-custom-icon{width:30px;height:30px;border-radius:var(--r-sm);object-fit:contain}
    .asw-fab-pulse{position:absolute;inset:-6px;border-radius:inherit;
      border:3px solid color-mix(in srgb,var(--clay-lilac) 55%,transparent);
      opacity:0;animation:cl-ping 2.9s var(--ease) 1.4s infinite;pointer-events:none}
    .asw-fab.active .asw-fab-pulse{display:none}

    /* badge — a little rose bead */
    .asw-fab-badge{position:absolute;top:-3px;inset-inline-end:-3px;min-width:24px;height:24px;padding:0 var(--sp-2);
      border-radius:var(--r-pill);background:var(--clay-rose);color:#7a2f4e;
      font-size:11px;font-weight:var(--w-bold);line-height:1;display:grid;place-items:center;
      box-shadow:var(--clay-sm);pointer-events:none;z-index:2}
    .asw.dark .asw-fab-badge{color:#fff}
    .asw-fab-badge[hidden]{display:none}
    .asw-fab-badge.asw-pop{animation:cl-plop var(--mm) var(--squish)}

    /* tooltip — a soft pill */
    .asw-fab-label{position:absolute;inset-inline-end:calc(100% + var(--sp-4));top:50%;
      transform:translateY(-50%) translateX(8px) scale(.9);white-space:nowrap;
      padding:var(--sp-2) var(--sp-4);border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink);box-shadow:var(--clay-sm);
      font-family:inherit;font-size:var(--t-sm);font-weight:var(--w-med);
      opacity:0;pointer-events:none;
      transition:opacity var(--ms) var(--ease),transform var(--mm) var(--squish)}
    .corner-bl .asw-fab-label,.corner-tl .asw-fab-label{inset-inline-end:auto;inset-inline-start:calc(100% + var(--sp-4));
      transform:translateY(-50%) translateX(-8px) scale(.9)}
    .asw-fab:hover .asw-fab-label,.asw-fab:focus-visible .asw-fab-label{opacity:1;
      transform:translateY(-50%) translateX(0) scale(1)}
    .asw-fab.active .asw-fab-label{display:none}

    /* ═══════════════════════════════════════════════════════════════════
       TEASER — a puffy card
       ═══════════════════════════════════════════════════════════════════ */
    .asw-teaser{position:fixed;z-index:1;max-width:276px;display:flex;align-items:flex-start;gap:var(--sp-3);
      padding:var(--sp-4) var(--sp-5);border:none;border-radius:var(--r-lg);
      background:var(--clay-body);box-shadow:var(--clay);
      cursor:pointer;opacity:0;transform:translateY(14px) scale(.94);
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--squish),box-shadow var(--mm) var(--ease);
      pointer-events:none}
    .asw-teaser.show{opacity:1;transform:translateY(0) scale(1);pointer-events:auto}
    .asw-teaser:hover{transform:translateY(-3px) scale(1.02);box-shadow:var(--clay-up)}
    .asw-teaser-orb{width:40px;height:40px;flex:none;border-radius:var(--r-sm);display:grid;place-items:center;
      background:var(--clay-mint);color:#1f6b58;box-shadow:var(--clay-sm)}
    .asw.dark .asw-teaser-orb{color:#eafff8}
    .asw-teaser-orb svg{width:17px;height:17px}
    .asw-teaser-body{min-width:0;padding-inline-end:var(--sp-4)}
    .asw-teaser-title{font-size:var(--t-md);font-weight:var(--w-bold);color:var(--ink)}
    .asw-teaser-text{font-size:var(--t-sm);color:var(--ink-2);line-height:1.7;margin-top:2px}
    .asw-teaser-close{position:absolute;top:var(--sp-2);inset-inline-start:var(--sp-2);width:28px;height:28px;
      border:none;border-radius:var(--r-pill);background:var(--clay-body-2);color:var(--ink-3);
      display:grid;place-items:center;cursor:pointer;opacity:0;box-shadow:var(--clay-sm);
      transition:opacity var(--ms) var(--ease),box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-teaser:hover .asw-teaser-close,.asw-teaser-close:focus-visible{opacity:1}
    .asw-teaser-close:active{box-shadow:var(--clay-in);transform:scale(.9)}
    .asw-teaser-close svg{width:11px;height:11px}
    @media(max-width:520px){.asw-teaser{display:none}}

    /* ═══════════════════════════════════════════════════════════════════
       PANEL — one big slab of clay
       ═══════════════════════════════════════════════════════════════════ */
    .asw-panel{position:fixed;z-index:3;width:var(--asw-panel-w);height:var(--asw-panel-h);
      max-width:calc(100vw - var(--sp-5));max-height:calc(100dvh - 104px);
      display:flex;flex-direction:column;overflow:hidden;
      border:none;border-radius:var(--r-xl);
      background:var(--room);
      box-shadow:var(--clay-up);
      opacity:0;transform:translateY(20px) scale(.93);transform-origin:bottom right;
      pointer-events:none;visibility:hidden;
      transition:opacity var(--ms) var(--ease),transform var(--ms) var(--ease),visibility 0s linear var(--ms)}
    .asw-panel.open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;visibility:visible;
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--squish),visibility 0s}
    .asw-panel.no-anim{transition:none}
    .asw-root.corner-br .asw-panel{transform-origin:bottom right}
    .asw-root.corner-bl .asw-panel{transform-origin:bottom left}
    .asw-root.corner-tr .asw-panel{transform-origin:top right}
    .asw-root.corner-tl .asw-panel{transform-origin:top left}
    .asw-root.corner-tr .asw-panel,.asw-root.corner-tl .asw-panel{transform:translateY(-20px) scale(.93)}
    .asw-root.corner-tr .asw-panel.open,.asw-root.corner-tl .asw-panel.open{transform:translateY(0) scale(1)}

    /* ═══════════════════════════════════════════════════════════════════
       HEADER
       ═══════════════════════════════════════════════════════════════════ */
    .asw-header{position:relative;z-index:4;flex:none;display:flex;align-items:center;gap:var(--sp-3);
      padding:var(--sp-5) var(--sp-5) var(--sp-4);background:transparent;border:none}
    .asw-heading{position:relative;display:flex;align-items:center;gap:var(--sp-3);min-width:0;flex:1}
    .asw-avatar-wrap{position:relative;flex:none}
    .asw-avatar{width:44px;height:44px;border-radius:var(--r-sm);display:grid;place-items:center;overflow:hidden;
      background:var(--clay-lilac);color:#fff;
      font-size:var(--t-lg);font-weight:var(--w-bold);
      box-shadow:var(--clay-sm)}
    .asw-avatar img{width:100%;height:100%;border-radius:inherit;object-fit:cover}
    .asw-status{position:absolute;bottom:-2px;inset-inline-end:-2px;width:14px;height:14px;border-radius:var(--r-pill);
      background:var(--clay-mint);border:2.5px solid var(--room);box-shadow:var(--clay-sm)}
    .asw-info{min-width:0;flex:1}
    .asw-title-row{display:flex;align-items:center;gap:var(--sp-2);min-width:0}
    .asw-title{font-size:var(--t-lg);font-weight:var(--w-bold);line-height:1.4;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink)}
    .asw-subtitle{font-size:var(--t-xs);font-weight:var(--w-reg);color:var(--ink-2);margin-top:1px;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

    /* chips — tiny pressed beads */
    .asw-ai-chip,.asw-badge{display:inline-flex;align-items:center;gap:var(--sp-1);flex:none;height:24px;
      padding:0 var(--sp-3);border:none;border-radius:var(--r-pill);
      background:var(--room-2);box-shadow:var(--clay-in);
      font-size:10px;font-weight:var(--w-bold);letter-spacing:.02em;white-space:nowrap;color:var(--ink-2)}
    .asw-ai-chip{background:color-mix(in srgb,var(--clay-lilac) 40%,var(--room-2));
      color:color-mix(in srgb,var(--ink) 80%,var(--clay-lilac))}
    .asw.dark .asw-ai-chip{color:#e6e0ff}
    .asw-ai-chip svg{width:10px;height:10px}
    .asw-badge-dot{width:7px;height:7px;border-radius:var(--r-pill);background:var(--online);flex:none}

    /* header buttons — round clay pebbles */
    .asw-actions{position:relative;display:flex;gap:var(--sp-2);flex:none}
    .asw-header-btn{width:36px;height:36px;border:none;border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink-2);display:grid;place-items:center;cursor:pointer;
      box-shadow:var(--clay-sm);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),color var(--ms) var(--ease)}
    .asw-header-btn:hover{color:var(--ink);transform:translateY(-2px)}
    .asw-header-btn:active{box-shadow:var(--clay-in);transform:scale(.9)}
    .asw-header-btn svg{width:16px;height:16px;transition:transform var(--ml) var(--squish)}
    #asw-clear-history:hover svg{transform:rotate(-180deg)}

    /* ═══════════════════════════════════════════════════════════════════
       OFFLINE — a butter-coloured strip
       ═══════════════════════════════════════════════════════════════════ */
    .asw-netstatus{position:relative;z-index:3;flex:none;display:flex;align-items:center;justify-content:center;
      gap:var(--sp-2);margin:0 var(--sp-5) var(--sp-2);padding:var(--sp-2) var(--sp-4);
      background:var(--clay-butter);border:none;border-radius:var(--r-sm);
      box-shadow:var(--clay-sm);
      color:#7a5510;font-size:var(--t-xs);font-weight:var(--w-bold)}
    .asw.dark .asw-netstatus{color:#fff5dd}
    .asw-netstatus[hidden]{display:none}
    .asw-netstatus svg{width:14px;height:14px;flex:none}

    /* ═══════════════════════════════════════════════════════════════════
       MESSAGES — a well pressed into the slab
       ═══════════════════════════════════════════════════════════════════ */
    .asw-messages{position:relative;z-index:1;flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;
      overscroll-behavior:contain;
      margin:0 var(--sp-4);padding:var(--sp-5) var(--sp-4);
      display:flex;flex-direction:column;gap:var(--sp-4);
      background:var(--room-2);border-radius:var(--r-lg);
      box-shadow:var(--clay-deep);
      scroll-behavior:smooth;scrollbar-width:thin;scrollbar-color:var(--clay-lilac) transparent}
    .asw-messages::-webkit-scrollbar{width:10px}
    .asw-messages::-webkit-scrollbar-track{background:transparent}
    .asw-messages::-webkit-scrollbar-thumb{border-radius:var(--r-pill);background:var(--clay-lilac);
      border:3px solid transparent;background-clip:padding-box}

    .asw-row{position:relative;z-index:1;display:flex;flex-wrap:wrap;align-items:flex-end;gap:var(--sp-2);
      max-width:88%;animation:cl-pop-in var(--ml) var(--squish) both}
    .asw-row.user{align-self:flex-end;flex-direction:row-reverse}
    .asw-row.bot{align-self:flex-start}
    .asw-row.bot + .asw-row.bot,.asw-row.user + .asw-row.user{margin-top:calc(var(--sp-3) * -1)}
    .asw-row.asw-cont .asw-msg-avatar{visibility:hidden}
    .asw-row.no-anim{animation:none}

    .asw-msg-avatar{width:32px;height:32px;flex:0 0 32px;border-radius:var(--r-sm);display:grid;place-items:center;
      font-size:10px;font-weight:var(--w-bold);overflow:hidden;box-shadow:var(--clay-sm)}
    .asw-row.bot .asw-msg-avatar{background:var(--clay-mint);color:#1f6b58}
    .asw.dark .asw-row.bot .asw-msg-avatar{color:#eafff8}
    .asw-row.bot .asw-msg-avatar img{width:100%;height:100%;object-fit:cover}
    .asw-row.user .asw-msg-avatar{background:var(--clay-peach);color:#8a4634}
    .asw.dark .asw-row.user .asw-msg-avatar{color:#ffe9e2}
    .asw-no-avatar .asw-msg-avatar{display:none}

    .asw-divider{position:relative;z-index:1;align-self:center;display:flex;align-items:center;gap:var(--sp-2);
      margin:var(--sp-1) 0;padding:var(--sp-1) var(--sp-4);border:none;border-radius:var(--r-pill);
      background:var(--room-2);box-shadow:var(--clay-in);
      color:var(--ink-3);font-size:10px;font-weight:var(--w-bold);letter-spacing:.03em;
      animation:cl-fade var(--mm) var(--ease) both}

    /* ── BUBBLES: pillows of clay ── */
    .asw-col{max-width:100%;min-width:0}
    .asw-bubble{max-width:100%}
    .asw-bubble img,.asw-bubble video,.asw-bubble iframe{max-width:100%;height:auto}
    .asw-bubble pre{max-width:100%}
    .asw-bubble{padding:var(--sp-3) var(--sp-4);font-size:var(--asw-font-size,14px);line-height:1.85;
      word-break:break-word;white-space:pre-wrap;overflow-wrap:anywhere;position:relative;text-align:start;
      border:none;transition:transform var(--mm) var(--squish),box-shadow var(--mm) var(--ease)}
    .asw-row.bot .asw-bubble{background:var(--clay-body);color:var(--ink);
      border-radius:var(--r-md) var(--r-md) var(--sp-2) var(--r-md);
      box-shadow:var(--clay)}
    .asw-row.user .asw-bubble{background:var(--clay-lilac);color:var(--asw-user-text);
      border-radius:var(--r-md) var(--r-md) var(--r-md) var(--sp-2);
      box-shadow:var(--clay)}
    .asw-row:hover .asw-bubble{transform:translateY(-2px);box-shadow:var(--clay-up)}
    .asw[data-bubble="sharp"] .asw-bubble{border-radius:var(--r-sm)}
    .asw[data-bubble="pill"] .asw-bubble{border-radius:var(--r-pill);padding:var(--sp-3) var(--sp-5)}
    .asw-bubble.asw-error-bubble{background:var(--clay-rose);color:#7a2f4e}
    .asw.dark .asw-bubble.asw-error-bubble{color:#fff}

    /* rich text */
    .asw-bubble strong{font-weight:var(--w-bold)}
    .asw-bubble em{font-style:italic}
    .asw-bubble a{color:color-mix(in srgb,var(--accent) 70%,var(--ink));font-weight:var(--w-med);
      text-decoration:none;border-bottom:2px solid color-mix(in srgb,var(--clay-lilac) 60%,transparent)}
    .asw.dark .asw-bubble a{color:#c9bdff}
    .asw-row.user .asw-bubble a{color:inherit;border-bottom-color:rgba(255,255,255,.5)}
    .asw-bubble ul,.asw-bubble ol{margin:var(--sp-2) 0 var(--sp-1);padding-inline-start:var(--sp-5)}
    .asw-bubble li{margin:var(--sp-1) 0}
    .asw-bubble li::marker{color:color-mix(in srgb,var(--accent) 65%,var(--ink))}
    .asw-row.user .asw-bubble li::marker{color:currentColor}
    .asw-bubble p{margin:var(--sp-1) 0}
    .asw-bubble p:first-child{margin-top:0}
    .asw-bubble p:last-child{margin-bottom:0}
    .asw-bubble code:not(.asw-code-block code){padding:2px var(--sp-2);border-radius:var(--sp-2);
      background:var(--room-2);box-shadow:var(--clay-in);border:none;
      font-family:ui-monospace,'JetBrains Mono',Consolas,monospace;font-size:.86em;color:inherit;white-space:pre-wrap}
    .asw-row.user .asw-bubble code{background:rgba(255,255,255,.28);box-shadow:none}

    /* table — pressed into a tray */
    .asw-table-wrap{margin:var(--sp-3) 0;border:none;border-radius:var(--r-sm);overflow:hidden;overflow-x:auto;
      background:var(--room-2);box-shadow:var(--clay-in);direction:rtl}
    .asw-table-wrap table{border-collapse:collapse;width:100%;font-size:var(--t-sm);line-height:1.7}
    .asw-table-wrap th{background:transparent;font-weight:var(--w-bold);text-align:start;
      padding:var(--sp-2) var(--sp-3);white-space:nowrap;color:var(--ink)}
    .asw-table-wrap td{padding:var(--sp-2) var(--sp-3);color:var(--ink-2);
      border-top:2px solid color-mix(in srgb,var(--curve) 45%,transparent)}
    .asw-table-wrap th[style*="center"],.asw-table-wrap td[style*="center"]{text-align:center}

    /* code — a dark clay tray */
    .asw-code-wrap{position:relative;margin:var(--sp-3) 0;border-radius:var(--r-sm);overflow:hidden;
      background:#2f2a48;border:none;box-shadow:var(--clay-sm);direction:ltr;text-align:left}
    .asw-code-header{display:flex;align-items:center;gap:var(--sp-2);padding:var(--sp-2) var(--sp-3);
      background:rgba(255,255,255,.05);border:none}
    .asw-code-dots{display:flex;gap:5px;flex:none}
    .asw-code-dots span{width:9px;height:9px;border-radius:var(--r-pill);background:rgba(255,255,255,.18)}
    .asw-code-dots span:nth-child(1){background:var(--clay-rose)}
    .asw-code-dots span:nth-child(2){background:var(--clay-butter)}
    .asw-code-dots span:nth-child(3){background:var(--clay-mint)}
    .asw-code-lang{font-size:10px;color:rgba(255,255,255,.45);font-weight:var(--w-bold);letter-spacing:.1em;
      text-transform:uppercase;margin-left:var(--sp-1)}
    .asw-code-copy{margin-left:auto;display:inline-flex;align-items:center;gap:var(--sp-1);height:26px;
      padding:0 var(--sp-3);border:none;border-radius:var(--r-pill);
      background:rgba(255,255,255,.1);color:#e6e0ff;
      font-size:10px;font-weight:var(--w-med);cursor:pointer;font-family:inherit;
      transition:background var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-code-copy:hover{background:rgba(255,255,255,.18)}
    .asw-code-copy:active{transform:scale(.92)}
    .asw-code-copy.copied{color:var(--clay-mint)}
    .asw-code-copy svg{width:11px;height:11px}
    .asw-code-block{margin:0;padding:var(--sp-3) var(--sp-4);overflow-x:auto;
      font-family:ui-monospace,'JetBrains Mono',Consolas,monospace;font-size:var(--t-sm);line-height:1.75;
      color:#ddd6ff;white-space:pre;tab-size:2;background:none}
    .asw-code-block::-webkit-scrollbar{height:8px}
    .asw-code-block::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);border-radius:var(--r-pill)}
    .asw-code-block code{font-family:inherit}

    .asw-time{padding:var(--sp-1) var(--sp-2) 0;font-size:10px;color:var(--ink-3);font-weight:var(--w-med);
      font-variant-numeric:tabular-nums}
    .asw-row.user .asw-time{text-align:left}

    /* feedback — little pebbles */
    .asw-feedback{display:flex;align-items:center;gap:var(--sp-1);margin-top:var(--sp-2);opacity:0;
      transition:opacity var(--ms) var(--ease)}
    .asw-row:hover .asw-feedback,.asw-feedback:focus-within,.asw-feedback[data-sent],.asw-row.asw-last .asw-feedback{opacity:1}
    @media(hover:none){.asw-feedback{opacity:1}}
    .asw-feedback[hidden]{display:none}
    .asw-fb-btn{width:30px;height:30px;border:none;border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink-3);cursor:pointer;display:grid;place-items:center;
      box-shadow:var(--clay-sm);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),color var(--ms) var(--ease)}
    .asw-fb-btn:hover{color:var(--ink);transform:translateY(-2px)}
    .asw-fb-btn:active{transform:scale(.88);box-shadow:var(--clay-in)}
    .asw-fb-btn.active{box-shadow:var(--clay-in);color:var(--ink)}
    .asw-fb-btn.active.thumbs-up,.asw-fb-btn.copied{background:var(--clay-mint);color:#1f6b58}
    .asw-fb-btn.active.thumbs-down{background:var(--clay-rose);color:#7a2f4e}
    .asw.dark .asw-fb-btn.active.thumbs-up,.asw.dark .asw-fb-btn.copied,
    .asw.dark .asw-fb-btn.active.thumbs-down{color:#fff}
    .asw-fb-btn svg{width:14px;height:14px}

    .asw-retry{display:inline-flex;align-items:center;justify-content:center;gap:var(--sp-2);margin-top:var(--sp-3);
      height:34px;padding:0 var(--sp-4);border:none;border-radius:var(--r-pill);
      background:var(--clay-rose);color:#7a2f4e;box-shadow:var(--clay-sm);
      font-family:inherit;font-size:var(--t-xs);font-weight:var(--w-bold);cursor:pointer;
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw.dark .asw-retry{color:#fff}
    .asw-retry:hover{transform:translateY(-2px)}
    .asw-retry:active{transform:scale(.94);box-shadow:var(--clay-in)}
    .asw-retry svg{width:13px;height:13px}

    /* ═══════════════════════════════════════════════════════════════════
       TYPING
       ═══════════════════════════════════════════════════════════════════ */
    .asw-typing{position:relative;z-index:1;flex:none;display:flex;align-items:center;gap:var(--sp-3);
      padding:var(--sp-2) var(--sp-8) 0}
    .asw-typing[hidden]{display:none}
    .asw-typing-ava{width:32px;height:32px;flex:none;border-radius:var(--r-sm);
      background:var(--clay-mint);color:#1f6b58;display:grid;place-items:center;box-shadow:var(--clay-sm)}
    .asw.dark .asw-typing-ava{color:#eafff8}
    .asw-typing-ava svg{width:14px;height:14px}
    .asw-typing-bubble{display:flex;align-items:center;gap:6px;padding:var(--sp-3) var(--sp-4);
      background:var(--clay-body);border:none;border-radius:var(--r-md);box-shadow:var(--clay)}
    .asw-typing-dot{width:8px;height:8px;border-radius:var(--r-pill);background:var(--clay-lilac);
      box-shadow:var(--clay-sm);animation:cl-squish 1.3s var(--squish) infinite}
    .asw-typing-dot:nth-child(2){animation-delay:.17s}
    .asw-typing-dot:nth-child(3){animation-delay:.34s}
    .asw-typing-label{font-size:var(--t-xs);font-weight:var(--w-med);color:var(--ink-3);margin-inline-start:var(--sp-1)}

    .asw-bubble.streaming::after{content:"";display:inline-block;width:4px;height:15px;margin-inline-start:3px;
      border-radius:var(--r-pill);background:currentColor;vertical-align:-2px;opacity:.6;
      animation:cl-blink 1s steps(2) infinite}

    /* ═══════════════════════════════════════════════════════════════════
       HERO
       ═══════════════════════════════════════════════════════════════════ */
    .asw-hero{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;text-align:center;
      gap:var(--sp-5);padding:var(--sp-8) var(--sp-3) var(--sp-4);
      transition:opacity var(--mm) var(--ease),transform var(--mm) var(--ease)}
    .asw-hero>*{animation:cl-pop-in var(--ml) var(--squish) both}
    .asw-hero>*:nth-child(2){animation-delay:70ms}
    .asw-hero>*:nth-child(3){animation-delay:140ms}
    .asw-hero>*:nth-child(4){animation-delay:210ms}
    .asw-hero-out{opacity:0!important;transform:translateY(-12px) scale(.94)!important;pointer-events:none}
    .asw-hero-spot{position:absolute;top:0;left:50%;transform:translateX(-50%);width:280px;height:170px;
      pointer-events:none;filter:blur(40px);
      background:radial-gradient(ellipse at center,color-mix(in srgb,var(--clay-lilac) 45%,transparent),transparent 70%)}
    .asw-hero-orb-wrap{position:relative}
    /* a wobbling blob of clay */
    .asw-hero-orb{position:relative;width:90px;height:90px;display:grid;place-items:center;
      background:var(--clay-lilac);color:#fff;
      border-radius:58% 42% 47% 53% / 45% 50% 50% 55%;
      box-shadow:var(--clay-up);
      animation:cl-wobble 9s var(--ease) infinite}
    .asw-hero-orb::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;
      background:radial-gradient(52% 38% at 32% 24%,rgba(255,255,255,.34),transparent 66%)}
    .asw-hero-orb svg{width:36px;height:36px;position:relative;z-index:1}
    .asw-hero-orb img{width:100%;height:100%;border-radius:inherit;object-fit:cover}
    /* little clay beads floating around */
    .asw-hero-p{position:absolute;border-radius:var(--r-pill);box-shadow:var(--clay-sm)}
    .asw-hero-p.p1{width:14px;height:14px;top:-14px;inset-inline-start:-4px;background:var(--clay-mint);
      animation:cl-float 6s var(--ease) infinite}
    .asw-hero-p.p2{width:11px;height:11px;top:20px;inset-inline-end:-24px;background:var(--clay-peach);
      animation:cl-float 7.5s var(--ease) .7s infinite}
    .asw-hero-p.p3{width:9px;height:9px;bottom:-8px;inset-inline-start:-20px;background:var(--clay-butter);
      animation:cl-float 6.8s var(--ease) 1.4s infinite}
    .asw-hero-text{font-size:var(--t-lg);font-weight:var(--w-med);color:var(--ink);line-height:1.9;max-width:292px}
    .asw-hero-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-3);width:100%;max-width:340px}
    .asw-hero-grid .asw-suggestion{height:auto;justify-content:flex-start;text-align:start;white-space:normal;
      border-radius:var(--r-md);padding:var(--sp-3) var(--sp-4);line-height:1.6;font-size:var(--t-sm);gap:var(--sp-2)}
    /* each hero card gets its own pastel */
    .asw-hero-grid .asw-suggestion:nth-child(1){background:var(--clay-mint);color:#1f6b58}
    .asw-hero-grid .asw-suggestion:nth-child(2){background:var(--clay-peach);color:#8a4634}
    .asw-hero-grid .asw-suggestion:nth-child(3){background:var(--clay-butter);color:#7a5510}
    .asw-hero-grid .asw-suggestion:nth-child(4){background:var(--clay-rose);color:#7a2f4e}
    .asw.dark .asw-hero-grid .asw-suggestion{color:#fff}
    .asw-hero-grid .asw-suggestion span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .asw-card-arrow{margin-inline-start:auto;flex:none;opacity:0;transform:translateX(5px);
      transition:opacity var(--ms) var(--ease),transform var(--mm) var(--squish)}
    .asw-card-arrow svg{width:14px;height:14px;display:block}
    .asw-suggestion:hover .asw-card-arrow,.asw-suggestion:focus-visible .asw-card-arrow{opacity:1;transform:translateX(0)}
    @media(max-width:400px){.asw-hero-grid{grid-template-columns:1fr}}

    /* ═══════════════════════════════════════════════════════════════════
       SUGGESTIONS — a row of clay buttons
       ═══════════════════════════════════════════════════════════════════ */
    .asw-suggestions{position:relative;z-index:2;flex:none;display:flex;gap:var(--sp-3);align-items:center;
      overflow-x:auto;padding:var(--sp-4) var(--sp-5) var(--sp-2);background:transparent;
      scrollbar-width:none;-webkit-overflow-scrolling:touch}
    .asw-suggestions::-webkit-scrollbar{display:none}
    .asw-suggestions[hidden]{display:none}
    .asw-suggestion{display:inline-flex;align-items:center;gap:var(--sp-2);flex:0 0 auto;height:36px;
      padding:0 var(--sp-4);border:none;border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink);box-shadow:var(--clay-sm);
      font-family:inherit;font-size:var(--t-sm);font-weight:var(--w-med);cursor:pointer;
      white-space:nowrap;text-decoration:none;
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-suggestion:hover{transform:translateY(-3px);box-shadow:var(--clay-up)}
    .asw-suggestion:active{transform:scale(.94);box-shadow:var(--clay-in)}
    .asw-bubble .asw-suggestion{margin-top:var(--sp-2)}

    /* ═══════════════════════════════════════════════════════════════════
       COMPOSER
       ═══════════════════════════════════════════════════════════════════ */
    .asw-footer{position:relative;z-index:2;flex:none;
      padding:var(--sp-3) var(--sp-5) calc(var(--sp-5) + env(safe-area-inset-bottom,0px));
      background:transparent;border:none}
    /* the input is a groove pressed into the clay */
    .asw-input-wrap{position:relative;display:flex;align-items:flex-end;gap:var(--sp-2);padding:var(--sp-1);
      padding-inline:var(--sp-5) var(--sp-1);
      border:none;border-radius:var(--r-xl);
      background:var(--room-2);
      box-shadow:var(--clay-deep);
      transition:box-shadow var(--mm) var(--ease)}
    .asw-input-wrap:focus-within{box-shadow:var(--clay-deep),0 0 0 3px color-mix(in srgb,var(--clay-lilac) 55%,transparent)}
    .asw-input-wrap.asw-listening{box-shadow:var(--clay-deep),0 0 0 3px color-mix(in srgb,var(--err) 45%,transparent)}

    .asw-input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:var(--ink);
      font-family:inherit;font-size:var(--asw-font-size,14px);line-height:1.65;resize:none;
      padding:var(--sp-3) 0;max-height:132px;overflow-y:auto;scrollbar-width:none;font-weight:var(--w-reg)}
    .asw-input::-webkit-scrollbar{display:none}
    .asw-input::placeholder{color:var(--ink-3)}

    .asw-wave{display:flex;align-items:center;gap:3px;height:20px;flex:none;padding-inline-end:var(--sp-1)}
    .asw-wave[hidden]{display:none}
    .asw-wave span{width:4px;height:100%;border-radius:var(--r-pill);background:var(--err);
      transform-origin:center;animation:cl-wave .9s var(--ease) infinite}
    .asw-wave span:nth-child(1){animation-duration:.82s}
    .asw-wave span:nth-child(2){animation-duration:.66s;animation-delay:.09s}
    .asw-wave span:nth-child(3){animation-duration:1.05s;animation-delay:.05s}
    .asw-wave span:nth-child(4){animation-duration:.74s;animation-delay:.13s}
    .asw-wave span:nth-child(5){animation-duration:.95s;animation-delay:.03s}

    .asw-mic{width:38px;height:38px;flex:none;border:none;border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink-3);display:grid;place-items:center;cursor:pointer;
      box-shadow:var(--clay-sm);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),color var(--ms) var(--ease)}
    .asw-mic:hover{color:var(--ink);transform:translateY(-2px)}
    .asw-mic:active{transform:scale(.9);box-shadow:var(--clay-in)}
    .asw-mic[hidden]{display:none}
    .asw-mic svg{width:17px;height:17px}
    .asw-input-wrap.asw-listening .asw-mic{background:var(--clay-rose);color:#7a2f4e;box-shadow:var(--clay-in)}
    .asw.dark .asw-input-wrap.asw-listening .asw-mic{color:#fff}

    /* send — the biggest, friendliest blob */
    .asw-send{width:44px;height:44px;flex:none;border:none;border-radius:var(--r-sm);display:grid;place-items:center;
      background:var(--clay-lilac);color:#fff;cursor:pointer;
      box-shadow:var(--clay);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),
                 background var(--ms) var(--ease),border-radius var(--mm) var(--squish)}
    .asw-send:hover{transform:translateY(-3px);box-shadow:var(--clay-up);
      border-radius:46% 54% 50% 50% / 52% 48% 52% 48%}
    .asw-send:active{transform:scale(.9);box-shadow:var(--clay-in);border-radius:var(--r-sm)}
    .asw-send:disabled{cursor:default;background:var(--clay-body-3);color:var(--ink-3);
      box-shadow:var(--clay-in);transform:none}
    .asw-send svg{width:18px;height:18px}
    .asw-send.asw-stop{background:var(--clay-rose);color:#7a2f4e}
    .asw.dark .asw-send.asw-stop{color:#fff}

    .asw-scrollbtn{position:absolute;top:-50px;inset-inline-end:var(--sp-5);z-index:5;width:38px;height:38px;
      border-radius:var(--r-pill);border:none;background:var(--clay-body);color:var(--ink-2);
      display:grid;place-items:center;cursor:pointer;box-shadow:var(--clay);
      opacity:0;transform:translateY(8px) scale(.8);pointer-events:none;
      transition:opacity var(--ms) var(--ease),transform var(--mm) var(--squish),box-shadow var(--ms) var(--ease)}
    .asw-scrollbtn.show{opacity:1;transform:translateY(0) scale(1);pointer-events:auto}
    .asw-scrollbtn:hover{transform:translateY(-2px)}
    .asw-scrollbtn:active{transform:scale(.9);box-shadow:var(--clay-in)}
    .asw-scrollbtn svg{width:16px;height:16px}

    .asw-foot-meta{display:flex;flex-direction:column;align-items:center;gap:2px;padding-top:var(--sp-3)}
    .asw-disclaim{font-size:10px;color:var(--ink-3);text-align:center;line-height:1.6}
    .asw-powered{text-align:center;font-size:10px;color:var(--ink-3);font-weight:var(--w-reg)}
    .asw-powered[hidden]{display:none}
    .asw-powered a{color:color-mix(in srgb,var(--accent) 70%,var(--ink));text-decoration:none;font-weight:var(--w-med)}
    .asw-powered a:hover{text-decoration:underline}
    .asw-resource-links{display:inline-flex;gap:var(--sp-2);margin-inline-start:var(--sp-2)}

    /* ═══════════════════════════════════════════════════════════════════
       TOAST
       ═══════════════════════════════════════════════════════════════════ */
    .asw-toast{position:absolute;top:var(--sp-4);left:var(--sp-5);right:var(--sp-5);z-index:50;
      display:flex;align-items:center;justify-content:center;gap:var(--sp-2);
      padding:var(--sp-3) var(--sp-4);border:none;border-radius:var(--r-md);
      background:var(--clay-body);color:var(--ink);
      box-shadow:var(--clay-up);
      font-size:var(--t-sm);font-weight:var(--w-med);line-height:1.6;text-align:center;
      opacity:0;transform:translateY(-12px) scale(.92);
      transition:opacity var(--ms) var(--ease),transform var(--mm) var(--squish);pointer-events:none}
    .asw-toast.show{opacity:1;transform:translateY(0) scale(1)}
    .asw-toast svg{width:15px;height:15px;flex:none;color:var(--accent)}

    /* ═══════════════════════════════════════════════════════════════════
       CITATIONS
       ═══════════════════════════════════════════════════════════════════ */
    .asw-citations{display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2);margin-top:var(--sp-3);
      padding-top:var(--sp-3);border-top:2px solid color-mix(in srgb,var(--curve) 35%,transparent)}
    .asw-citations-label{font-size:10px;font-weight:var(--w-bold);color:var(--ink-3)}
    .asw-citation{display:inline-flex;align-items:center;gap:var(--sp-1);height:28px;font-size:var(--t-xs);
      font-weight:var(--w-med);color:var(--ink-2);border:none;
      background:var(--room-2);box-shadow:var(--clay-in);
      padding:0 var(--sp-3);border-radius:var(--r-pill);text-decoration:none;
      max-width:170px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      transition:color var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-citation:hover{color:var(--ink);transform:translateY(-1px)}
    .asw-citation svg{width:11px;height:11px;flex:none}

    /* ═══════════════════════════════════════════════════════════════════
       HANDOFF
       ═══════════════════════════════════════════════════════════════════ */
    .asw-handoff{flex:1 1 100%;display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2);margin-top:var(--sp-2);
      padding:var(--sp-4);border:none;border-radius:var(--r-md);
      background:var(--clay-body-2);box-shadow:var(--clay-sm);
      animation:cl-pop-in var(--mm) var(--squish) both}
    .asw-handoff-label{width:100%;font-size:var(--t-sm);line-height:1.75;color:var(--ink-2);font-weight:var(--w-reg)}
    .asw-handoff-btn{display:inline-flex;align-items:center;gap:var(--sp-1);height:32px;padding:0 var(--sp-4);
      border:none;border-radius:var(--r-pill);background:var(--clay-mint);color:#1f6b58;
      box-shadow:var(--clay-sm);
      font-family:inherit;font-size:var(--t-xs);font-weight:var(--w-bold);cursor:pointer;text-decoration:none;
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw.dark .asw-handoff-btn{color:#eafff8}
    .asw-handoff-btn:hover{transform:translateY(-2px)}
    .asw-handoff-btn:active{transform:scale(.94);box-shadow:var(--clay-in)}
    .asw-handoff-btn svg{width:13px;height:13px}
    .asw-messages:not(.asw-no-avatar) .asw-row > .asw-handoff,
    .asw-messages:not(.asw-no-avatar) .asw-row > .asw-leadform{margin-inline-start:40px}

    .asw-rule-hint{margin-top:var(--sp-2);padding:var(--sp-2) var(--sp-3);
      background:var(--room-2);border:none;border-radius:var(--r-sm);box-shadow:var(--clay-in);
      font-size:var(--t-sm);line-height:1.75;color:var(--ink-2)}
    .asw-messages > .asw-rule-hint{align-self:center;margin:0;padding:var(--sp-1) var(--sp-4);
      border-radius:var(--r-pill);font-size:10px;color:var(--ink-3);animation:cl-fade var(--mm) both}

    /* ═══════════════════════════════════════════════════════════════════
       SHEET
       ═══════════════════════════════════════════════════════════════════ */
    .asw-sheet{position:absolute;inset:0;z-index:40;display:flex;align-items:flex-end;opacity:0;pointer-events:none;
      transition:opacity var(--mm) var(--ease)}
    .asw-sheet::before{content:"";position:absolute;inset:0;background:color-mix(in srgb,var(--ink) 40%,transparent)}
    .asw-sheet.open{opacity:1;pointer-events:auto}
    .asw-sheet[hidden]{display:none}
    .asw-sheet-card{position:relative;width:100%;max-height:92%;overflow-y:auto;overscroll-behavior:contain;
      background:var(--room);border:none;
      border-radius:var(--r-xl) var(--r-xl) 0 0;
      box-shadow:var(--clay-up);
      padding:var(--sp-3) var(--sp-5) calc(var(--sp-5) + env(safe-area-inset-bottom,0px));
      transform:translateY(100%);transition:transform var(--ml) var(--squish);scrollbar-width:thin}
    .asw-sheet.open .asw-sheet-card{transform:translateY(0)}
    .asw-sheet-grip{width:48px;height:7px;border-radius:var(--r-pill);background:var(--room-2);
      box-shadow:var(--clay-in);margin:var(--sp-1) auto var(--sp-5)}
    .asw-sheet-close{position:absolute;top:var(--sp-4);inset-inline-end:var(--sp-5);width:34px;height:34px;
      border:none;border-radius:var(--r-pill);background:var(--clay-body);color:var(--ink-2);
      display:grid;place-items:center;cursor:pointer;box-shadow:var(--clay-sm);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),background var(--ms) var(--ease)}
    .asw-sheet-close:hover{background:var(--clay-rose);color:#7a2f4e}
    .asw.dark .asw-sheet-close:hover{color:#fff}
    .asw-sheet-close:active{transform:scale(.9);box-shadow:var(--clay-in)}
    .asw-sheet-close svg{width:14px;height:14px}
    .asw-sheet-title{font-size:var(--t-xl);font-weight:var(--w-bold);color:var(--ink);line-height:1.4}
    .asw-sheet-desc{font-size:var(--t-sm);color:var(--ink-2);line-height:1.8;margin:var(--sp-1) 0 var(--sp-5)}

    /* channel tiles — each a different clay colour */
    .asw-chans{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-3);margin-bottom:var(--sp-5)}
    @media(max-width:360px){.asw-chans{grid-template-columns:1fr}}
    .asw-chan{position:relative;display:flex;align-items:center;gap:var(--sp-3);padding:var(--sp-3) var(--sp-4);
      border:none;border-radius:var(--r-md);background:var(--clay-body);text-decoration:none;
      box-shadow:var(--clay-sm);
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-chan:hover{transform:translateY(-3px);box-shadow:var(--clay-up)}
    .asw-chan:active{transform:scale(.96);box-shadow:var(--clay-in)}
    .asw-chan-ic{width:38px;height:38px;flex:none;border-radius:var(--r-sm);display:grid;place-items:center;
      color:#fff;background:var(--chan,var(--clay-lilac));box-shadow:var(--clay-sm)}
    .asw-chan-ic svg{width:17px;height:17px}
    .asw-chan-tx{min-width:0;display:flex;flex-direction:column}
    .asw-chan-tx b{font-size:var(--t-sm);font-weight:var(--w-bold);color:var(--ink)}
    .asw-chan-tx i{font-style:normal;font-size:10px;color:var(--ink-3);white-space:nowrap;overflow:hidden;
      text-overflow:ellipsis;direction:ltr;text-align:end}
    .asw-chan-more{width:100%;justify-content:center;margin-top:2px}

    /* ═══════════════════════════════════════════════════════════════════
       FORM — fields pressed into the clay
       ═══════════════════════════════════════════════════════════════════ */
    .asw-form{text-align:start}
    .asw-field{margin-bottom:var(--sp-4)}
    .asw-field-row{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-3)}
    @media(max-width:340px){.asw-field-row{grid-template-columns:1fr}}
    .asw-flabel{display:flex;align-items:center;gap:var(--sp-1);font-size:var(--t-xs);font-weight:var(--w-bold);
      color:var(--ink-2);margin-bottom:var(--sp-2);padding-inline-start:var(--sp-3)}
    .asw-flabel b{color:var(--err);font-weight:var(--w-bold)}
    .asw-form input,.asw-form textarea{width:100%;font-family:inherit;font-size:var(--t-md);color:var(--ink);
      padding:var(--sp-3) var(--sp-4);border-radius:var(--r-sm);border:none;
      background:var(--room-2);box-shadow:var(--clay-deep);
      outline:none;font-weight:var(--w-reg);
      transition:box-shadow var(--ms) var(--ease)}
    .asw-form textarea{resize:vertical;min-height:72px;max-height:150px;line-height:1.7}
    .asw-form input::placeholder,.asw-form textarea::placeholder{color:var(--ink-3)}
    .asw-form input:focus,.asw-form textarea:focus{
      box-shadow:var(--clay-deep),0 0 0 3px color-mix(in srgb,var(--clay-lilac) 55%,transparent)}
    .asw-field.invalid input,.asw-field.invalid textarea{
      box-shadow:var(--clay-deep),0 0 0 3px color-mix(in srgb,var(--err) 45%,transparent)}
    .asw-field.ok input{box-shadow:var(--clay-deep),0 0 0 3px color-mix(in srgb,var(--ok) 45%,transparent)}
    .asw-ferr{display:none;font-size:10.5px;font-weight:var(--w-bold);color:var(--err);margin-top:var(--sp-2);
      padding-inline-start:var(--sp-3)}
    .asw-field.invalid .asw-ferr{display:block}

    .asw-form-submit{width:100%;display:inline-flex;align-items:center;justify-content:center;gap:var(--sp-2);
      margin-top:var(--sp-3);height:50px;padding:0 var(--sp-6);
      border:none;border-radius:var(--r-md);
      background:var(--clay-lilac);color:#fff;
      box-shadow:var(--clay);
      font-family:inherit;font-size:var(--t-md);font-weight:var(--w-bold);cursor:pointer;
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish),background var(--ms) var(--ease)}
    .asw-form-submit:hover{transform:translateY(-3px);box-shadow:var(--clay-up)}
    .asw-form-submit:active{transform:scale(.97);box-shadow:var(--clay-in)}
    .asw-form-submit:disabled{background:var(--clay-body-3);color:var(--ink-3);cursor:default;
      box-shadow:var(--clay-in);transform:none}
    .asw-form-submit svg{width:16px;height:16px}
    .asw-spinner{width:16px;height:16px;flex:none;border:3px solid color-mix(in srgb,currentColor 28%,transparent);
      border-top-color:currentColor;border-radius:var(--r-pill);animation:cl-spin .8s linear infinite}
    .asw-form-note{display:flex;align-items:center;justify-content:center;gap:var(--sp-1);font-size:10px;
      color:var(--ink-3);text-align:center;margin-top:var(--sp-4);line-height:1.7}
    .asw-form-note svg{width:12px;height:12px;flex:none}
    .asw-form-err{display:none;font-size:var(--t-xs);font-weight:var(--w-bold);color:var(--err);
      margin-top:var(--sp-3);text-align:center}
    .asw-form-err.show{display:block}

    .asw-form-success{display:flex;flex-direction:column;align-items:center;text-align:center;gap:var(--sp-3);
      padding:var(--sp-6) var(--sp-2) var(--sp-3);animation:cl-pop-in var(--mm) var(--squish) both}
    .asw-checkmark{width:64px;height:64px;stroke:var(--ok);stroke-width:4;fill:none;
      stroke-linecap:round;stroke-linejoin:round}
    .asw-checkmark circle{stroke:color-mix(in srgb,var(--clay-mint) 70%,transparent);
      stroke-dasharray:170;stroke-dashoffset:170;animation:cl-draw 700ms var(--squish) 60ms forwards}
    .asw-checkmark path{stroke-dasharray:44;stroke-dashoffset:44;animation:cl-draw 400ms var(--squish) 600ms forwards}
    .asw-fs-title{font-size:var(--t-lg);font-weight:var(--w-bold);color:var(--ink);margin-top:var(--sp-1)}
    .asw-fs-desc{font-size:var(--t-sm);color:var(--ink-2);line-height:1.85;max-width:266px}
    .asw-fs-close{margin-top:var(--sp-4);height:40px;padding:0 var(--sp-6);border:none;border-radius:var(--r-pill);
      background:var(--clay-body);color:var(--ink);box-shadow:var(--clay-sm);
      font-family:inherit;font-size:var(--t-sm);font-weight:var(--w-bold);cursor:pointer;
      transition:box-shadow var(--ms) var(--ease),transform var(--ms) var(--squish)}
    .asw-fs-close:hover{transform:translateY(-2px)}
    .asw-fs-close:active{transform:scale(.94);box-shadow:var(--clay-in)}
    .asw-leadform-wrap{animation:cl-pop-in var(--mm) var(--squish) both}
    .asw-leadform{position:relative;flex:1 1 100%;margin:var(--sp-2) 0;padding:var(--sp-4);
      border:none;border-radius:var(--r-md);background:var(--clay-body-2);box-shadow:var(--clay-sm);
      animation:cl-pop-in var(--mm) var(--squish) both}

    /* ═══════════════════════════════════════════════════════════════════
       MOTION — everything bounces a little
       ═══════════════════════════════════════════════════════════════════ */
    @keyframes cl-fade{from{opacity:0}to{opacity:1}}
    @keyframes cl-pop-in{from{opacity:0;transform:translateY(14px) scale(.9)}to{opacity:1;transform:translateY(0) scale(1)}}
    @keyframes cl-plop{0%{opacity:0;transform:scale(.3)}60%{opacity:1;transform:scale(1.08)}100%{transform:scale(1)}}
    @keyframes cl-spin{to{transform:rotate(360deg)}}
    @keyframes cl-ping{0%{transform:scale(.95);opacity:.7}70%,100%{transform:scale(1.3);opacity:0}}
    /* the dots squash and stretch like real clay */
    @keyframes cl-squish{
      0%,100%{transform:translateY(0) scale(1,1);opacity:.55}
      30%{transform:translateY(-7px) scale(.86,1.16);opacity:1}
      55%{transform:translateY(0) scale(1.18,.84);opacity:1}}
    @keyframes cl-blink{50%{opacity:0}}
    @keyframes cl-draw{to{stroke-dashoffset:0}}
    @keyframes cl-wave{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}
    @keyframes cl-float{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-9px) rotate(8deg)}}
    /* the hero blob slowly changes shape, like it is being kneaded */
    @keyframes cl-wobble{
      0%,100%{border-radius:58% 42% 47% 53% / 45% 50% 50% 55%;transform:translateY(0) rotate(0)}
      25%{border-radius:44% 56% 58% 42% / 52% 44% 56% 48%;transform:translateY(-6px) rotate(3deg)}
      50%{border-radius:52% 48% 40% 60% / 58% 52% 48% 42%;transform:translateY(0) rotate(0)}
      75%{border-radius:60% 40% 54% 46% / 42% 58% 42% 58%;transform:translateY(-4px) rotate(-3deg)}}

    /* ═══════════════════════════════════════════════════════════════════
       RESPONSIVE / PREFERENCES / A11Y
       ═══════════════════════════════════════════════════════════════════ */
    @media(max-width:480px){
      .asw-fab{width:60px;height:60px}
      .asw-panel{width:min(var(--asw-panel-w),calc(100vw - var(--sp-6)));height:min(var(--asw-panel-h),calc(100dvh - 88px))}
      .asw-root.mobile-fullscreen .asw-panel{position:fixed!important;inset:0!important;width:100vw!important;
        max-width:none!important;height:100vh!important;height:100dvh!important;max-height:none!important;
        border-radius:0!important;box-shadow:none!important;transform:translateY(16px) scale(1)!important}
      .asw-root.mobile-fullscreen .asw-panel.open{transform:translateY(0) scale(1)!important}
      .asw-root.mobile-fullscreen .asw-fab{display:none!important}
      .asw-root.mobile-fullscreen .asw-glow{display:none}
      .asw-root.mobile-fullscreen .asw-sheet-card{border-radius:0}
      .asw-messages{margin:0 var(--sp-3)}
      .asw-header,.asw-footer,.asw-suggestions{padding-inline:var(--sp-4)}
      .asw-row{max-width:92%}
    }
    @media(prefers-reduced-motion:reduce){
      .asw-panel,.asw-fab,.asw-suggestion,.asw-teaser,.asw-scrollbtn,.asw-toast,.asw-glow,.asw-fab-label,
      .asw-sheet,.asw-sheet-card,.asw-chan,.asw-send,.asw-input-wrap,.asw-bubble,.asw-header-btn,
      .asw-fb-btn,.asw-mic,.asw-retry,.asw-form-submit,.asw-fs-close,.asw-citation,.asw-handoff-btn{transition:none}
      .asw-typing-dot,.asw-fab-pulse,.asw-wave span,.asw-spinner,.asw-hero-p,.asw-hero-orb{animation:none}
      .asw-row,.asw-hero,.asw-hero>*,.asw-handoff,.asw-leadform,.asw-leadform-wrap,.asw-divider,
      .asw-form-success,.asw-fab{animation:none;opacity:1;transform:none}
      .asw-row:hover .asw-bubble,.asw-suggestion:hover,.asw-chan:hover,.asw-send:hover,
      .asw-header-btn:hover,.asw-fab:hover,.asw-teaser:hover{transform:none}
      .asw-checkmark circle,.asw-checkmark path{stroke-dashoffset:0;animation:none}
    }

    .asw[data-font="small"]{--asw-font-size:12.5px}
    .asw[data-font="large"]{--asw-font-size:16px}

    .asw[data-anim="off"] *,.asw[data-anim="off"] *::before,.asw[data-anim="off"] *::after{animation:none!important;transition:none!important}

    .asw :focus-visible{outline:none;box-shadow:var(--clay-sm),0 0 0 3px color-mix(in srgb,var(--clay-lilac) 65%,transparent)}
    .asw ::selection{background:color-mix(in srgb,var(--clay-lilac) 55%,transparent)}
    .asw-sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
      clip:rect(0,0,0,0);white-space:nowrap;border:0}
  `;

  /* ─────────────── HELPERS ─────────────── */
  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>\"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c];
    });
  }

  function formatTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function dayLabel(ts) {
    try {
      var d = new Date(ts);
      var now = new Date();
      var diff = new Date(now.getFullYear(), now.getMonth(), now.getDate()) -
                 new Date(d.getFullYear(), d.getMonth(), d.getDate());
      if (diff === 0) return "امروز";
      if (diff === 86400000) return "دیروز";
      return d.toLocaleDateString("fa-IR", { day: "numeric", month: "long" });
    } catch (_) { return ""; }
  }

  function getDefaultEndpoint() {
    if (scriptElement && scriptElement.src) return new URL("/api/chat/", scriptElement.src).toString();
    return new URL("/api/chat/", window.location.href).toString();
  }

  function getSiblingEndpoint(apiEndpoint, name) {
    return new URL(apiEndpoint.replace(/chat\/?$/, name + "/"), window.location.href).toString();
  }

  function isSafeUrl(value) {
    try {
      var url = new URL(String(value), window.location.href);
      return url.protocol === "https:" || url.protocol === "http:" || url.protocol === "mailto:" || url.protocol === "tel:";
    } catch (_) { return false; }
  }

  function detectDarkMode(mode) {
    if (mode === "dark") return true;
    if (mode === "light") return false;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function clamp(val, min, max) {
    var n = Number(val);
    if (!Number.isFinite(n)) return min;
    return Math.min(max, Math.max(min, n));
  }

  function generateSessionId() {
    return "asw-" + Math.random().toString(36).substr(2, 12) + "-" + Date.now().toString(36);
  }

  /* ─────────────── MARKDOWN RENDERER ─────────────── */
  var TABLE_ROW = /^\s*\|(.*)\|\s*$/;
  var TABLE_SEP = /^\s*\|[\s:\-|]+\|\s*$/;

  function renderMarkdown(text) {
    var src = String(text == null ? "" : text);
    var lines = src.split(/\r?\n/);
    var output = [];
    var inList = false;
    var inOl = false;
    var codeBlock = false;
    var codeLines = [];
    var codeLang = "";

    function closeLists() {
      if (inList) { output.push("</ul>"); inList = false; }
      if (inOl) { output.push("</ol>"); inOl = false; }
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];

      if (line.match(/^```/)) {
        if (codeBlock) {
          output.push(renderCodeBlock(codeLines.join("\n"), codeLang));
          codeLines = [];
          codeLang = "";
          codeBlock = false;
        } else {
          closeLists();
          codeBlock = true;
          codeLang = line.replace(/^```/, "").trim();
        }
        continue;
      }
      if (codeBlock) { codeLines.push(line); continue; }

      /* Tables — consecutive |rows| whose second line is a separator */
      if (TABLE_ROW.test(line)) {
        var rows = [];
        var j = i;
        while (j < lines.length && TABLE_ROW.test(lines[j])) { rows.push(lines[j]); j++; }
        if (rows.length >= 2 && TABLE_SEP.test(rows[1])) {
          closeLists();
          output.push(renderTable(rows));
          i = j - 1;
          continue;
        }
      }

      var isUl = line.match(/^\s*[-*•]\s+(.+)/);
      var isOl = line.match(/^\s*\d+\.\s+(.+)/);
      if (!isUl && inList) { output.push("</ul>"); inList = false; }
      if (!isOl && inOl) { output.push("</ol>"); inOl = false; }

      if (isUl) {
        if (!inList) { output.push("<ul>"); inList = true; }
        output.push("<li>" + renderInline(isUl[1]) + "</li>");
      } else if (isOl) {
        if (!inOl) { output.push("<ol>"); inOl = true; }
        output.push("<li>" + renderInline(isOl[1]) + "</li>");
      } else {
        output.push(renderInline(line));
      }
    }

    if (codeBlock) output.push(renderCodeBlock(codeLines.join("\n"), codeLang));
    if (inList) output.push("</ul>");
    if (inOl) output.push("</ol>");

    return output.join("<br>");
  }

  function renderTable(rows) {
    function cells(row) {
      return row.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(function (c) { return c.trim(); });
    }
    var aligns = cells(rows[1]).map(function (c) {
      return (c.length > 1 && c.indexOf(":") === 0 && c.lastIndexOf(":") === c.length - 1) ? ' style="text-align:center"' : "";
    });
    var html = '<div class="asw-table-wrap"><table><thead><tr>';
    cells(rows[0]).forEach(function (c, idx) {
      html += "<th" + (aligns[idx] || "") + ">" + renderInline(c) + "</th>";
    });
    html += "</tr></thead><tbody>";
    rows.slice(2).forEach(function (row) {
      html += "<tr>";
      cells(row).forEach(function (c, idx) {
        html += "<td" + (aligns[idx] || "") + ">" + renderInline(c) + "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  function renderInline(text) {
    var links = [];
    var s = String(text).replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, label, url) {
      if (!isSafeUrl(url)) return label;
      var token = "ASWL" + links.length;
      links.push({ token: token, html: '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(label) + "</a>" });
      return token;
    });
    var html = escapeHtml(s)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/__(.+?)__/g, "<strong>$1</strong>")
      .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>")
      .replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
    links.forEach(function (l) { html = html.replace(l.token, l.html); });
    return html;
  }

  function renderCodeBlock(code, lang) {
    var escapedCode = escapeHtml(code);
    var langLabel = lang || "code";
    var id = "asw-code-" + Math.random().toString(36).substr(2, 8);
    return '<div class="asw-code-wrap">' +
      '<div class="asw-code-header"><span class="asw-code-dots"><span></span><span></span><span></span></span>' +
      '<span class="asw-code-lang">' + escapeHtml(langLabel) + '</span>' +
      '<button class="asw-code-copy" data-code-id="' + id + '" type="button">' + ICONS.copy + '<span>کپی</span></button></div>' +
      '<pre class="asw-code-block"><code id="' + id + '">' + escapedCode + '</code></pre></div>';
  }

  /* ─────────────── WIDGET CLASS ─────────────── */
  class AISupportWidget {
    constructor(options) {
      this.options = Object.assign({}, DEFAULTS, options || {});
      this.explicitOptions = options || {};
      this.options.sessionId = this.options.sessionId || generateSessionId();
      if (!this.options.apiEndpoint || this.options.apiEndpoint === "/api/chat/") {
        this.options.apiEndpoint = getDefaultEndpoint();
      }
      this.options.configEndpoint = this.options.configEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "widget-config");
      this.options.eventsEndpoint = this.options.eventsEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "events");
      this.options.feedbackEndpoint = this.options.feedbackEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "feedback");
      this.options.historyEndpoint = this.options.historyEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "history");
      this.options.leadsEndpoint = this.options.leadsEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "leads");
      this.options.handoffEndpoint = this.options.handoffEndpoint || getSiblingEndpoint(this.options.apiEndpoint, "handoff");
      this.options.streamEndpoint = this.options.streamEndpoint || (this.options.apiEndpoint.replace(/\/$/, "") + "/stream/");
      this.conversationId = "";
      this.conversationToken = "";
      this.lastMessageId = null;
      this.abortStream = null;
      this.previewMode = this.options.previewMode === true || /asw-preview/.test(
        (window.location.search || "") + (window.location.hash || "")
      );
      this.isOpen = false;
      this.isLoading = false;
      this.sheetOpen = false;
      this.messageCount = 0;
      this._unread = 0;
      this._stick = true;
      this._chatStarted = false;
      this._suggestionItems = [];
      this._listening = false;
      this._uid = 0;
      this.mount();
      this.initialize();
    }

    /* ─── Mount ─── */
    mount() {
      if (document.getElementById("ai-support-widget-host")) return;

      this.host = document.createElement("div");
      this.host.id = "ai-support-widget-host";
      document.body.appendChild(this.host);
      this.shadow = this.host.attachShadow({ mode: "open" });

      var style = document.createElement("style");
      style.textContent = CSS;
      this.shadow.appendChild(style);

      var root = document.createElement("div");
      root.className = "asw asw-root";
      root.setAttribute("data-bubble", this.options.bubbleStyle);
      root.setAttribute("data-font", this.options.fontSize);
      this.applyThemeVars(root);

      var fabIconHtml = this.getFabIconHtml();

      root.innerHTML =
        /* Ambient glow */
        '<div class="asw-glow" id="asw-glow" aria-hidden="true"></div>' +
        /* Panel */
        '<section class="asw-panel" role="dialog" aria-label="' + escapeHtml(this.options.title) + '" aria-hidden="true">' +
          /* Header */
          '<header class="asw-header">' +
            '<div class="asw-heading">' +
              '<div class="asw-avatar-wrap">' +
                '<div class="asw-avatar" id="asw-avatar"></div>' +
                '<span class="asw-status" aria-hidden="true"></span>' +
              '</div>' +
              '<div class="asw-info">' +
                '<div class="asw-title-row"><span class="asw-title" id="asw-title"></span><span class="asw-ai-chip" aria-hidden="true">' + ICONS.sparkles + '<span>AI</span></span><span class="asw-badge" id="asw-badge"><span class="asw-badge-dot" aria-hidden="true"></span><span id="asw-badge-text"></span></span></div>' +
                '<div class="asw-subtitle" id="asw-subtitle"></div>' +
              '</div>' +
            '</div>' +
            '<div class="asw-actions">' +
              '<button class="asw-header-btn" id="asw-clear-history" type="button" aria-label="شروع گفتگوی جدید" title="گفتگوی جدید">' + ICONS.refresh + '</button>' +
              '<button class="asw-header-btn" id="asw-contact" type="button" aria-label="تماس با کارشناس" title="تماس با کارشناس">' + ICONS.phone + '</button>' +
              '<button class="asw-header-btn" id="asw-theme-toggle" type="button" aria-label="تغییر تم" title="تغییر تم"></button>' +
              '<button class="asw-header-btn asw-close" id="asw-close" type="button" aria-label="بستن چت" title="بستن">' + ICONS.close + '</button>' +
            '</div>' +
          '</header>' +
          /* Offline banner */
          '<div class="asw-netstatus" id="asw-netstatus" hidden role="status">' + ICONS.wifiOff + '<span>اتصال اینترنت قطع است — پاسخ‌ها ارسال نمی‌شوند</span></div>' +
          /* Messages */
          '<div class="asw-messages" id="asw-messages" role="log" aria-live="polite"></div>' +
          /* Typing */
          '<div class="asw-typing" id="asw-typing" hidden aria-label="در حال تایپ...">' +
            '<div class="asw-typing-ava" aria-hidden="true">' + ICONS.sparkles + '</div>' +
            '<div class="asw-typing-bubble" aria-hidden="true"><span class="asw-typing-dot"></span><span class="asw-typing-dot"></span><span class="asw-typing-dot"></span></div>' +
            '<span class="asw-typing-label" id="asw-typing-label">' + THINKING_STATUSES[0] + '</span>' +
          '</div>' +
          /* Suggestions */
          '<div class="asw-suggestions" id="asw-suggestions"></div>' +
          /* Footer */
          '<footer class="asw-footer">' +
            '<button class="asw-scrollbtn" id="asw-scrollbtn" type="button" aria-label="رفتن به آخرین پیام">' + ICONS.chevronDown + '</button>' +
            '<div class="asw-input-wrap" id="asw-input-wrap">' +
              '<textarea class="asw-input" id="asw-input" rows="1" autocomplete="off" enterkeyhint="send" placeholder="' + escapeHtml(this.options.inputPlaceholder) + '" aria-label="پیام" style="height:auto;min-height:24px;max-height:132px"></textarea>' +
              '<div class="asw-wave" id="asw-wave" hidden aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>' +
              '<button class="asw-mic" id="asw-mic" type="button" aria-label="ورودی صوتی" title="ورودی صوتی" hidden>' + ICONS.mic + '</button>' +
              '<button class="asw-send" id="asw-send" type="button" aria-label="ارسال پیام" disabled>' + ICONS.arrowUp + '</button>' +
            '</div>' +
            '<div class="asw-foot-meta">' +
              '<div class="asw-disclaim">پاسخ‌ها توسط هوش مصنوعی تولید می‌شوند و ممکن است اشتباه باشند.</div>' +
              '<div class="asw-powered" id="asw-powered">توسعه‌ی <a href="https://ai-support.ir" target="_blank" rel="noopener">AI Support</a><span class="asw-resource-links" id="asw-resources"></span></div>' +
            '</div>' +
          '</footer>' +
          /* Contact bottom-sheet */
          '<div class="asw-sheet" id="asw-sheet" hidden aria-hidden="true" role="dialog" aria-label="تماس با ما">' +
            '<div class="asw-sheet-card">' +
              '<div class="asw-sheet-grip" aria-hidden="true"></div>' +
              '<button class="asw-sheet-close" id="asw-sheet-close" type="button" aria-label="بستن">' + ICONS.close + '</button>' +
              '<div class="asw-sheet-title">' + escapeHtml(this.options.leadFormTitle) + '</div>' +
              '<div class="asw-sheet-desc">' + escapeHtml(this.options.leadFormDescription) + '</div>' +
              '<div class="asw-chans" id="asw-chans"></div>' +
              '<div id="asw-sheet-form"></div>' +
            '</div>' +
          '</div>' +
          /* Toast */
          '<div class="asw-toast" id="asw-toast" role="status"></div>' +
        '</section>' +
        /* FAB */
        '<button class="asw-fab" id="asw-fab" type="button" aria-label="باز کردن چت" aria-expanded="false">' +
          '<span class="asw-fab-label" aria-hidden="true">' + escapeHtml(this.options.fabLabel) + '</span>' +
          '<span class="asw-fab-pulse" aria-hidden="true"></span>' +
          '<span class="asw-fab-shine" aria-hidden="true"></span>' +
          '<span class="asw-fab-icon-main">' + fabIconHtml + '</span>' +
          '<span class="asw-fab-icon-close" aria-hidden="true">' + ICONS.close + '</span>' +
          '<span class="asw-fab-badge" id="asw-fab-badge" hidden aria-hidden="true"></span>' +
        '</button>' +
        /* Teaser */
        '<div class="asw-teaser" id="asw-teaser" role="button" tabindex="0" aria-label="گفتگو با پشتیبان" hidden>' +
          '<button class="asw-teaser-close" id="asw-teaser-close" type="button" aria-label="بستن">' + ICONS.close + '</button>' +
          '<div class="asw-teaser-orb" aria-hidden="true">' + ICONS.sparkles + '</div>' +
          '<div class="asw-teaser-body"><div class="asw-teaser-title">سوالی دارید؟</div><div class="asw-teaser-text">' + escapeHtml(this.options.teaserText) + '</div></div>' +
        '</div>';

      this.shadow.appendChild(root);
      this.root = root;
      this.panel = root.querySelector(".asw-panel");
      this.glow = root.querySelector("#asw-glow");
      this.fab = root.querySelector("#asw-fab");
      this.fabBadge = root.querySelector("#asw-fab-badge");
      this.teaser = root.querySelector("#asw-teaser");
      this.teaserClose = root.querySelector("#asw-teaser-close");
      this.closeBtn = root.querySelector("#asw-close");
      this.themeToggle = root.querySelector("#asw-theme-toggle");
      this.contactBtn = root.querySelector("#asw-contact");
      this.titleEl = root.querySelector("#asw-title");
      this.badgeText = root.querySelector("#asw-badge-text");
      this.subtitleEl = root.querySelector("#asw-subtitle");
      this.avatarEl = root.querySelector("#asw-avatar");
      this.netstatus = root.querySelector("#asw-netstatus");
      this.messages = root.querySelector("#asw-messages");
      this.typing = root.querySelector("#asw-typing");
      this.typingLabel = root.querySelector("#asw-typing-label");
      this.suggestions = root.querySelector("#asw-suggestions");
      this.input = root.querySelector("#asw-input");
      this.inputWrap = root.querySelector("#asw-input-wrap");
      this.wave = root.querySelector("#asw-wave");
      this.micBtn = root.querySelector("#asw-mic");
      this.sendBtn = root.querySelector("#asw-send");
      this.scrollBtn = root.querySelector("#asw-scrollbtn");
      this.powered = root.querySelector("#asw-powered");
      this.resources = root.querySelector("#asw-resources");
      this.toast = root.querySelector("#asw-toast");
      this.sheet = root.querySelector("#asw-sheet");
      this.sheetCard = root.querySelector(".asw-sheet-card");
      this.sheetClose = root.querySelector("#asw-sheet-close");
      this.chansEl = root.querySelector("#asw-chans");
      this.sheetFormEl = root.querySelector("#asw-sheet-form");

      this.applyVisuals();
      this.renderSuggestions();
      this.renderResources();
      this.renderChannels();
      this.bindEvents();
      this.updateSendState();
    }

    getFabIconHtml() {
      var o = this.options;
      if (o.iconType === "custom" && o.customIconUrl && isSafeUrl(o.customIconUrl)) {
        return '<img class="asw-fab-custom-icon" src="' + escapeHtml(o.customIconUrl) + '" alt="چت" referrerpolicy="no-referrer">';
      }
      return FAB_ICONS[o.defaultIconChoice] || FAB_ICONS["chat-bubble"];
    }

    /* ─── Initialize ─── */
    async initialize() {
      await this.loadConfig();
      this.sendEvent("widget_loaded");
      this.restoreConversation();
      var restored = this.restoreLocalHistory();
      if (!restored) await this.restoreHistory();
      // First-ever visit (no local/server history): render the hero greeting.
      if (this.messageCount === 0) {
        this.addMessage(this.options.greeting, "bot", true);
      }
      if (this.options.darkMode === "auto" && window.matchMedia) {
        var mq = window.matchMedia("(prefers-color-scheme: dark)");
        mq.addEventListener("change", () => this.applyTheme());
      }
      if (this.previewMode) {
        this.bindPreviewChannel();
      }
      this._maybeShowTeaser();
    }

    /* ─── Light conversation memory (localStorage, 7 days, no DB pressure) ─── */
    _localKey() { return "asw_history_" + (location.hostname || "local"); }
    restoreLocalHistory() {
      try {
        var raw = localStorage.getItem(this._localKey());
        if (!raw) return false;
        var data = JSON.parse(raw);
        if (!data || !Array.isArray(data.items) || !data.items.length) return false;
        if (data.ts && (Date.now() - data.ts) > 7 * 24 * 3600 * 1000) {
          localStorage.removeItem(this._localKey());
          return false;
        }
        this.messages.innerHTML = "";
        this.messageCount = 0;
        var self = this;
        var prevDay = null;
        data.items.slice(-22).forEach(function (m) {
          if (m.t) {
            var dk = new Date(m.t).toDateString();
            if (dk !== prevDay) {
              prevDay = dk;
              var div = document.createElement("div");
              div.className = "asw-divider";
              div.textContent = dayLabel(m.t);
              self.messages.appendChild(div);
            }
          }
          self.addMessage(m.content, m.role === "assistant" ? "bot" : "user", false, {
            citations: m.citations || [],
            skipFeedback: m.role !== "assistant",
            noAnim: false,
          });
        });
        var hint = document.createElement("div");
        hint.className = "asw-rule-hint";
        hint.textContent = "ادامه گفتگوی قبلی — این تاریخچه فقط روی همین مرورگر ذخیره شده است.";
        this.messages.prepend(hint);
        this.scrollToBottom();
        this._updateScrollBtn();
        return true;
      } catch (_) { return false; }
    }
    saveLocalHistory() {
      try {
        var items = [];
        this.messages.querySelectorAll(".asw-row").forEach(function (row) {
          var bubble = row.querySelector(".asw-bubble");
          if (!bubble) return;
          var isUser = row.classList.contains("user");
          items.push({
            role: isUser ? "user" : "assistant",
            content: bubble.textContent.slice(0, 800),
            citations: [],
            t: Date.now(),
          });
        });
        if (items.length > 22) items = items.slice(-22);
        localStorage.setItem(this._localKey(), JSON.stringify({ ts: Date.now(), items: items }));
      } catch (_) {}
    }
    clearLocalHistory() {
      try { localStorage.removeItem(this._localKey()); } catch (_) {}
    }

    /* ─── Conversation persistence (server token) ─── */
    restoreConversation() {
      try {
        this.conversationId = sessionStorage.getItem("asw_conversation_id") || "";
        this.conversationToken = sessionStorage.getItem("asw_conversation_token") || "";
      } catch (_) {}
    }

    saveConversation() {
      try {
        if (this.conversationId) sessionStorage.setItem("asw_conversation_id", this.conversationId);
        if (this.conversationToken) sessionStorage.setItem("asw_conversation_token", this.conversationToken);
      } catch (_) {}
    }

    async restoreHistory() {
      /* Restore server-side history when the conversation already exists. */
      if (!this.conversationId || !this.conversationToken) return;
      if (this.messageCount > 1) return;
      try {
        var url = this.options.historyEndpoint + "?conversation_id=" + encodeURIComponent(this.conversationId);
        var res = await fetch(url, { method: "GET", mode: "cors", credentials: "omit", headers: this.getHeaders() });
        if (!res.ok) return;
        var data = await res.json();
        var msgs = Array.isArray(data.messages) ? data.messages : [];
        if (!msgs.length) return;
        this.messages.innerHTML = "";
        this.messageCount = 0;
        this.addMessage(this.options.greeting, "bot", true);
        msgs.forEach((m) => {
          this.addMessage(m.content, m.role === "assistant" ? "bot" : "user", false, {
            citations: m.role === "assistant" ? (m.citations || []) : [],
            skipFeedback: true,
          });
        });
      } catch (_) {}
    }

    /* ─── Live preview channel (admin customizer) ─── */
    bindPreviewChannel() {
      window.addEventListener("message", (e) => {
        var data = e.data || {};
        if (data.type === "aiss:config" && data.config) {
          this.applyConfig(data.config);
        }
        if (data.type === "aiss:open") this.open();
        if (data.type === "aiss:close") this.close();
      });
      try { parent.postMessage({ type: "aiss:preview-ready" }, "*"); } catch (_) {}
    }

    applyConfig(cfg) {
      var self = this;
      var strKeys = ["title", "subtitle", "greeting", "primaryColor", "secondaryColor", "accentColor",
        "headerBadge", "botAvatarText", "inputPlaceholder", "themeMode", "darkMode", "fontFamily",
        "fontSize", "bubbleStyle", "position", "logoUrl", "leadFormTitle", "leadFormDescription", "handoffMessage",
        "teaserText", "fabLabel", "supportPhone"];
      strKeys.forEach(function (k) {
        if (cfg[k] !== undefined && cfg[k] !== null) self.options[k] = String(cfg[k]);
      });
      ["panelWidth", "panelHeight", "borderRadius", "positionVerticalOffset", "positionHorizontalOffset"].forEach(function (k) {
        var v = Number(cfg[k]);
        if (!isNaN(v)) self.options[k] = v;
      });
      ["mobileFullscreen", "showPoweredBy", "showTimestamp", "showAvatar", "showFeedback",
        "enableSounds", "enableAnimations", "showCitations", "enableLeadCapture", "enableHandoff",
        "showTeaser", "enableVoiceInput"].forEach(function (k) {
        if (cfg[k] !== undefined && cfg[k] !== null) self.options[k] = Boolean(cfg[k]);
      });
      if (Array.isArray(cfg.suggestions)) self.options.suggestions = cfg.suggestions;
      if (cfg.iconType) self.options.iconType = cfg.iconType;
      if (cfg.defaultIconChoice) self.options.defaultIconChoice = cfg.defaultIconChoice;
      if (cfg.customIconUrl !== undefined) self.options.customIconUrl = cfg.customIconUrl;
      this.applyVisuals();
      this.renderSuggestions();
      this.renderResources();
      this.renderChannels();
      if (this.sheet) {
        var st = this.sheet.querySelector(".asw-sheet-title");
        var sd = this.sheet.querySelector(".asw-sheet-desc");
        if (st) st.textContent = this.options.leadFormTitle;
        if (sd) sd.textContent = this.options.leadFormDescription;
      }
      if (this.teaser) {
        var t = this.teaser.querySelector(".asw-teaser-text");
        if (t) t.textContent = this.options.teaserText;
      }
      var label = this.fab.querySelector(".asw-fab-label");
      if (label) label.textContent = this.options.fabLabel;
      var fabMain = this.fab.querySelector(".asw-fab-icon-main");
      if (fabMain) fabMain.innerHTML = this.getFabIconHtml();
    }

    /* ─── Load Config from API ─── */
    async loadConfig() {
      if (!this.options.configEndpoint) return;
      try {
        var res = await fetch(this.options.configEndpoint, { method: "GET", mode: "cors", credentials: "omit", headers: this.getHeaders() });
        if (!res.ok) return;
        var raw = await res.json();
        var map = {
          title: "title", subtitle: "subtitle", greeting: "greeting",
          primaryColor: "primary_color", secondaryColor: "secondary_color",
          accentColor: "accent_color", headerBadge: "header_badge",
          botAvatarText: "bot_avatar_text", inputPlaceholder: "input_placeholder",
          themeMode: "theme_mode", darkMode: "dark_mode",
          panelWidth: "panel_width", panelHeight: "panel_height",
          borderRadius: "border_radius", mobileFullscreen: "mobile_fullscreen",
          logoUrl: "logo_url", fontFamily: "font_family", fontSize: "font_size",
          position: "position", showPoweredBy: "show_powered_by",
          showTimestamp: "show_timestamp", showAvatar: "show_avatar",
          showFeedback: "show_feedback",
          enableSounds: "enable_sounds", enableAnimations: "enable_animations",
          bubbleStyle: "bubble_style",
          positionVerticalOffset: "positionVerticalOffset",
          positionHorizontalOffset: "positionHorizontalOffset",
          iconType: "iconType",
          defaultIconChoice: "defaultIconChoice",
          customIconUrl: "customIconUrl",
          suggestions: "suggestions", faqUrl: "faq_url", privacyUrl: "privacy_url",
          supportEmail: "support_email",
          enableStreaming: "enable_streaming",
          showCitations: "show_citations",
          enableLeadCapture: "enable_lead_capture",
          leadFormTitle: "lead_form_title",
          leadFormDescription: "lead_form_description",
          enableHandoff: "enable_handoff",
          handoffTrigger: "handoff_trigger",
          handoffMessage: "handoff_message",
          handoffUrls: "handoff_urls",
          enableVoiceInput: "enable_voice_input",
          fabLabel: "fab_label",
          supportPhone: "support_phone",
        };
        var self = this;
        Object.keys(map).forEach(function (key) {
          var apiVal = raw[map[key]];
          if (apiVal !== undefined && apiVal !== null && !self.explicitOptions.hasOwnProperty(key)) {
            self.options[key] = apiVal;
          }
        });
        this.titleEl.textContent = this.options.title;
        this.badgeText.textContent = this.options.headerBadge;
        this.subtitleEl.textContent = this.options.subtitle;
        this.applyVisuals();
        this.renderSuggestions();
        this.renderResources();
        this.renderChannels();
        this.contactBtn.hidden = !this.options.enableLeadCapture;
        var sheetTitle = this.sheet.querySelector(".asw-sheet-title");
        var sheetDesc = this.sheet.querySelector(".asw-sheet-desc");
        if (sheetTitle) sheetTitle.textContent = this.options.leadFormTitle;
        if (sheetDesc) sheetDesc.textContent = this.options.leadFormDescription;
        var label = this.fab.querySelector(".asw-fab-label");
        if (label) label.textContent = this.options.fabLabel;
        var fabMain = this.fab.querySelector(".asw-fab-icon-main");
        if (fabMain) fabMain.innerHTML = this.getFabIconHtml();
      } catch (_) { /* defaults remain */ }
    }

    /* ─── Apply Theme Variables ─── */
    applyThemeVars(el) {
      var o = this.options;
      var s = el || this.root;
      s.style.setProperty("--asw-primary", o.primaryColor);
      s.style.setProperty("--asw-secondary", o.secondaryColor);
      s.style.setProperty("--asw-accent", o.accentColor || o.secondaryColor);
      s.style.setProperty("--asw-header-bg", this.getHeaderBg());
      s.style.setProperty("--asw-panel-w", clamp(o.panelWidth, 300, 520) + "px");
      s.style.setProperty("--asw-panel-h", clamp(o.panelHeight, 400, 800) + "px");
      s.style.setProperty("--asw-radius", clamp(o.borderRadius, 12, 36) + "px");
      s.style.setProperty("--asw-font", o.fontFamily);
      s.style.setProperty("--asw-font-size", o.fontSize === "small" ? "12px" : o.fontSize === "large" ? "16px" : "14px");
      s.setAttribute("data-bubble", o.bubbleStyle || "rounded");
      s.setAttribute("data-font", o.fontSize || "normal");
      s.setAttribute("data-anim", o.enableAnimations === false ? "off" : "on");
    }

    getHeaderBg() {
      var o = this.options;
      if (o.themeMode === "solid") return o.primaryColor;
      if (o.themeMode === "glass") return "linear-gradient(135deg, " + o.primaryColor + "dd, " + o.secondaryColor + "cc)";
      return "linear-gradient(135deg, " + o.primaryColor + ", " + o.secondaryColor + ")";
    }

    applyTheme() {
      var isDark = detectDarkMode(this.options.darkMode);
      this.root.classList.toggle("dark", isDark);
      if (this.themeToggle) {
        this.themeToggle.innerHTML = isDark
          ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
          : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
      }
    }

    applyVisuals() {
      this.applyThemeVars();
      this.applyTheme();
      var o = this.options;

      // Rigid 4-corner positioning: FAB anchored to extreme corner, panel adjacent
      var pos = o.position || "bottom-right";
      var cornerMap = { "bottom-right": "br", "bottom-left": "bl", "top-right": "tr", "top-left": "tl" };
      var vertPx = clamp(o.positionVerticalOffset, 8, 200);
      var horizPx = clamp(o.positionHorizontalOffset, 8, 200);
      var isBottom = pos.indexOf("bottom") !== -1;
      var isLeft = pos.indexOf("left") !== -1;
      var corner = cornerMap[pos] || "br";

      this.root.className = "asw asw-root corner-" + corner;
      this.root.style.top = isBottom ? "auto" : "0";
      this.root.style.bottom = isBottom ? "0" : "auto";
      this.root.style.left = isLeft ? "0" : "auto";
      this.root.style.right = isLeft ? "auto" : "0";

      // FAB: fixed at the extreme corner with exact offsets
      this.fab.style.position = "fixed";
      this.fab.style.top = isBottom ? "auto" : vertPx + "px";
      this.fab.style.bottom = isBottom ? vertPx + "px" : "auto";
      this.fab.style.left = isLeft ? horizPx + "px" : "auto";
      this.fab.style.right = isLeft ? "auto" : horizPx + "px";

      // Teaser: floats right next to the FAB
      if (this.teaser) {
        this.teaser.style.position = "fixed";
        this.teaser.style.top = isBottom ? "auto" : (vertPx + 72) + "px";
        this.teaser.style.bottom = isBottom ? (vertPx + 72) + "px" : "auto";
        this.teaser.style.left = isLeft ? horizPx + "px" : "auto";
        this.teaser.style.right = isLeft ? "auto" : horizPx + "px";
      }

      // Ambient glow: centered on the FAB corner
      if (this.glow) {
        this.glow.style.position = "fixed";
        var gs = 340;
        if (isBottom) {
          this.glow.style.top = "auto";
          this.glow.style.bottom = (vertPx - gs / 2 - 20) + "px";
        } else {
          this.glow.style.bottom = "auto";
          this.glow.style.top = (vertPx - gs / 2 - 20) + "px";
        }
        if (isLeft) {
          this.glow.style.right = "auto";
          this.glow.style.left = (horizPx - gs / 2 - 10) + "px";
        } else {
          this.glow.style.left = "auto";
          this.glow.style.right = (horizPx - gs / 2 - 10) + "px";
        }
      }

      // Panel: fixed, positioned directly adjacent to FAB
      this.panel.style.position = "fixed";
      var fabSize = 60;
      var panelGap = 12;
      if (isBottom) {
        this.panel.style.bottom = (vertPx + fabSize + panelGap) + "px";
        this.panel.style.top = "auto";
      } else {
        this.panel.style.top = (vertPx + fabSize + panelGap) + "px";
        this.panel.style.bottom = "auto";
      }
      if (isLeft) {
        this.panel.style.left = horizPx + "px";
        this.panel.style.right = "auto";
      } else {
        this.panel.style.right = horizPx + "px";
        this.panel.style.left = "auto";
      }

      this.root.classList.toggle("mobile-fullscreen", o.mobileFullscreen !== false);

      // Avatar
      if (o.logoUrl && isSafeUrl(o.logoUrl)) {
        this.avatarEl.innerHTML = "";
        var img = document.createElement("img");
        img.src = o.logoUrl;
        img.alt = "";
        img.referrerPolicy = "no-referrer";
        this.avatarEl.appendChild(img);
      } else {
        this.avatarEl.textContent = o.botAvatarText || "✦";
      }

      this.titleEl.textContent = o.title;
      this.badgeText.textContent = o.headerBadge;
      if (!this.isLoading) this.subtitleEl.textContent = o.subtitle;
      this.input.placeholder = o.inputPlaceholder;
      this.powered.hidden = o.showPoweredBy === false;
      this.messages.classList.toggle("asw-no-avatar", o.showAvatar === false);
    }

    /* ─── Suggestions (strip + hero cards) ─── */
    renderSuggestions() {
      var items = Array.isArray(this.options.suggestions) ? this.options.suggestions.filter(Boolean).slice(0, 6) : [];
      this._suggestionItems = items;
      this.suggestions.innerHTML = items.map(function (item) {
        return '<button class="asw-suggestion" type="button" data-msg="' + escapeHtml(item) + '"><span>' + escapeHtml(item) + "</span></button>";
      }).join("");
      this.syncSuggestions();
    }

    syncSuggestions() {
      var heroExists = !!(this.messages && this.messages.querySelector(".asw-hero"));
      this.suggestions.hidden = !this._suggestionItems.length || heroExists || this._chatStarted;
    }

    /* ─── Resource Links ─── */
    renderResources() {
      if (!this.resources) return;
      this.resources.textContent = "";
      var links = [];
      var o = this.options;
      if (o.faqUrl && isSafeUrl(o.faqUrl)) links.push({ label: "FAQ", url: o.faqUrl });
      if (o.privacyUrl && isSafeUrl(o.privacyUrl)) links.push({ label: "Privacy", url: o.privacyUrl });
      if (o.supportEmail) links.push({ label: "Support", url: "mailto:" + o.supportEmail });
      if (o.supportPhone) links.push({ label: "تماس", url: "tel:" + o.supportPhone });
      var sep = document.createTextNode(" · ");
      links.forEach(function (link, i) {
        if (i > 0) this.resources.appendChild(sep.cloneNode(true));
        var a = document.createElement("a");
        a.href = link.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = link.label;
        this.resources.appendChild(a);
      }, this);
    }

    /* ─── Contact channel cards (sheet) ─── */
    getContactChannels() {
      var o = this.options;
      var chans = [];
      if (o.supportPhone) {
        chans.push({ key: "phone", label: "تماس تلفنی", cap: o.supportPhone, url: "tel:" + o.supportPhone, tint: "#10b981", icon: ICONS.phone });
      }
      if (o.supportEmail) {
        chans.push({ key: "email", label: "ایمیل", cap: o.supportEmail, url: "mailto:" + o.supportEmail, tint: null, icon: ICONS.mail });
      }
      var urls = o.handoffUrls || {};
      if (urls.telegram && isSafeUrl(urls.telegram)) {
        chans.push({ key: "telegram", label: "تلگرام", cap: "پیام در تلگرام", url: urls.telegram, tint: "#229ED9", icon: ICONS.send });
      }
      if (urls.whatsapp && isSafeUrl(urls.whatsapp)) {
        chans.push({ key: "whatsapp", label: "واتساپ", cap: "چت در واتساپ", url: urls.whatsapp, tint: "#25D366", icon: ICONS.phone });
      }
      if (urls.contact_form && isSafeUrl(urls.contact_form)) {
        chans.push({ key: "contact_form", label: "فرم تماس", cap: "فرم کامل سایت", url: urls.contact_form, tint: null, icon: ICONS.user });
      }
      return chans;
    }

    renderChannels() {
      if (!this.chansEl) return;
      var self = this;
      var chans = this.getContactChannels();
      this.chansEl.textContent = "";
      chans.forEach(function (ch) {
        var a = document.createElement("a");
        a.className = "asw-chan";
        if (ch.tint) a.style.setProperty("--chan", ch.tint);
        a.href = ch.url;
        if (ch.url.indexOf("http") === 0) { a.target = "_blank"; a.rel = "noopener noreferrer"; }
        a.innerHTML = '<span class="asw-chan-ic" aria-hidden="true">' + ch.icon + '</span>' +
          '<span class="asw-chan-tx"><b>' + escapeHtml(ch.label) + '</b><i>' + escapeHtml(ch.cap) + '</i></span>';
        a.addEventListener("click", function () { self.logHandoff(ch.key, self._lastUserMessage || ""); });
        self.chansEl.appendChild(a);
      });
      this.chansEl.hidden = chans.length === 0;
    }

    /* ─── Bind Events ─── */
    bindEvents() {
      var self = this;

      this.fab.addEventListener("click", function () { self.toggle(); });
      this.closeBtn.addEventListener("click", function () { self.close(); });

      this.themeToggle.addEventListener("click", function () {
        var current = self.options.darkMode;
        if (current === "auto") {
          self.options.darkMode = detectDarkMode("auto") ? "light" : "dark";
        } else if (current === "dark") {
          self.options.darkMode = "light";
        } else {
          self.options.darkMode = "dark";
        }
        self.applyTheme();
      });

      this.input.addEventListener("input", function () {
        self.autoGrowInput();
        self.updateSendState();
      });

      this.input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          self.send();
        }
      });

      this.sendBtn.addEventListener("click", function () {
        // During streaming the send button acts as a stop control.
        if (self.isLoading && self.abortStream) {
          self.abortStream.abort();
          return;
        }
        self.send();
      });

      this.contactBtn.addEventListener("click", function () {
        if (self.options.enableLeadCapture === false) return;
        self.openSheet();
      });

      // Contact sheet
      if (this.sheetClose) {
        this.sheetClose.addEventListener("click", function () { self.closeSheet(); });
      }
      this.sheet.addEventListener("click", function (e) {
        if (e.target === self.sheet) self.closeSheet();
      });

      // Suggestion chips (strip + hero cards) — one delegated handler
      this.shadow.addEventListener("click", function (e) {
        var chip = e.target.closest("[data-msg]");
        if (!chip) return;
        self.sendText(chip.dataset.msg);
      });

      // New conversation (clears local history + session tokens)
      var clearBtn = this.shadow.querySelector("#asw-clear-history");
      if (clearBtn) {
        clearBtn.addEventListener("click", function (e) {
          e.preventDefault();
          self.clearLocalHistory();
          try { sessionStorage.removeItem("asw_conversation_id"); sessionStorage.removeItem("asw_conversation_token"); } catch(_){}
          self.conversationId = "";
          self.conversationToken = "";
          self.messages.innerHTML = "";
          self.messageCount = 0;
          self._chatStarted = false;
          self._handoffShown = false;
          self.addMessage(self.options.greeting, "bot", true);
          self.renderSuggestions();
          self.showToast("گفتگوی جدید شروع شد.", 2200);
        });
      }

      // Teaser
      if (this.teaser) {
        this.teaser.addEventListener("click", function () { self.open(); });
        this.teaser.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); self.open(); }
        });
      }
      if (this.teaserClose) {
        this.teaserClose.addEventListener("click", function (e) {
          e.stopPropagation();
          self._dismissTeaser(true);
        });
      }

      // Scroll-to-bottom pill + stick-to-bottom tracking
      this.messages.addEventListener("scroll", function () { self._updateScrollBtn(); }, { passive: true });
      if (this.scrollBtn) {
        this.scrollBtn.addEventListener("click", function () { self.scrollToBottom(true); });
      }

      // Offline / online awareness
      function updateNet() {
        if (!self.netstatus) return;
        self.netstatus.hidden = navigator.onLine !== false;
      }
      window.addEventListener("online", function () {
        updateNet();
        self.showToast("اتصال اینترنت برقرار شد.", 2200);
      });
      window.addEventListener("offline", updateNet);
      updateNet();

      // Tab-title flash while a reply arrives in a hidden tab
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) self._stopTitleFlash();
      });

      // Code copy buttons
      this.shadow.addEventListener("click", function (e) {
        var copyBtn = e.target.closest(".asw-code-copy");
        if (!copyBtn) return;
        var codeId = copyBtn.dataset.codeId;
        var codeEl = self.shadow.getElementById(codeId);
        if (!codeEl) return;
        navigator.clipboard.writeText(codeEl.textContent).then(function () {
          copyBtn.classList.add("copied");
          copyBtn.querySelector("span").textContent = "کپی شد ✓";
          setTimeout(function () {
            copyBtn.classList.remove("copied");
            copyBtn.querySelector("span").textContent = "کپی";
          }, 2000);
        }).catch(function () {});
      });

      // Feedback buttons
      this.shadow.addEventListener("click", function (e) {
        var fbBtn = e.target.closest(".asw-fb-btn");
        if (!fbBtn) return;
        self.handleFeedback(fbBtn);
      });

      document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") return;
        if (self.sheetOpen) { self.closeSheet(); return; }
        if (self.isOpen) self.close();
      });

      this.initVoice();
    }

    /* ─── Contact bottom-sheet ─── */
    openSheet() {
      if (!this.sheet) return;
      this._uid++;
      // Rebuild the form each time so the note is pre-filled with fresh context.
      this.sheetFormEl.innerHTML = "";
      var selfS = this;
      this.sheetFormEl.appendChild(this.buildContactForm("widget_form", {
        onDone: function () { selfS.closeSheet(); },
      }));
      this.sheet.hidden = false;
      this.sheet.setAttribute("aria-hidden", "false");
      var self = this;
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { self.sheet.classList.add("open"); });
      });
      this.sheetOpen = true;
    }

    closeSheet() {
      if (!this.sheet || !this.sheetOpen) return;
      this.sheet.classList.remove("open");
      this.sheet.setAttribute("aria-hidden", "true");
      var s = this.sheet;
      this.sheetOpen = false;
      setTimeout(function () { s.hidden = true; }, 380);
    }

    /* ─── Professional contact form (shared: sheet + inline handoff) ─── */
    buildContactForm(source, opts) {
      opts = opts || {};
      var self = this;
      var uid = "f" + (++this._uid) + source;
      var wrap = document.createElement("div");
      wrap.className = "asw-form" + (opts.compact ? " asw-leadform" : "");
      wrap.innerHTML =
        (opts.compact ? '<div class="asw-leadform-title">' + escapeHtml(this.options.leadFormTitle) + '</div>' +
          '<div class="asw-leadform-desc">' + escapeHtml(this.options.leadFormDescription) + '</div>' : "") +
        '<div class="asw-field" id="' + uid + '-nf">' +
          '<label class="asw-flabel" for="' + uid + '-name">نام و نام خانوادگی <b>*</b></label>' +
          '<input type="text" id="' + uid + '-name" name="name" placeholder="مثلاً: سارا محمدی" maxlength="200" autocomplete="name">' +
          '<div class="asw-ferr">لطفاً نام خود را وارد کنید (حداقل ۲ حرف).</div>' +
        '</div>' +
        '<div class="asw-field-row">' +
          '<div class="asw-field" id="' + uid + '-ef">' +
            '<label class="asw-flabel" for="' + uid + '-email">ایمیل</label>' +
            '<input type="email" id="' + uid + '-email" name="email" placeholder="you@mail.com" maxlength="254" autocomplete="email" dir="ltr" style="text-align:left">' +
            '<div class="asw-ferr">ایمیل واردشده معتبر نیست.</div>' +
          '</div>' +
          '<div class="asw-field" id="' + uid + '-pf">' +
            '<label class="asw-flabel" for="' + uid + '-phone">شماره تماس</label>' +
            '<input type="tel" id="' + uid + '-phone" name="phone" placeholder="0912···" maxlength="30" autocomplete="tel" dir="ltr" style="text-align:left">' +
            '<div class="asw-ferr">شماره تماس معتبر نیست.</div>' +
          '</div>' +
        '</div>' +
        '<div class="asw-field">' +
          '<label class="asw-flabel" for="' + uid + '-note">توضیحات (اختیاری)</label>' +
          '<textarea id="' + uid + '-note" name="note" rows="3" maxlength="2000" placeholder="خلاصه‌ی سؤال یا درخواست‌تان را بنویسید…"></textarea>' +
        '</div>' +
        '<input type="text" name="website" value="" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;height:0;width:0">' +
        '<button type="button" class="asw-form-submit">' +
          '<span class="asw-spinner" hidden></span>' + ICONS.send + '<span class="asw-btn-txt">ثبت درخواست تماس</span>' +
        '</button>' +
        '<div class="asw-form-err"></div>' +
        '<div class="asw-form-note">' + ICONS.info + '<span>اطلاعات شما فقط برای تماس کارشناس استفاده می‌شود و محرمانه می‌ماند.</span></div>';

      var nameField = wrap.querySelector("#" + uid + "-nf");
      var emailField = wrap.querySelector("#" + uid + "-ef");
      var phoneField = wrap.querySelector("#" + uid + "-pf");
      var nameInput = wrap.querySelector('[name="name"]');
      var emailInput = wrap.querySelector('[name="email"]');
      var phoneInput = wrap.querySelector('[name="phone"]');
      var noteInput = wrap.querySelector('[name="note"]');
      var honeypot = wrap.querySelector('[name="website"]');
      var submitBtn = wrap.querySelector(".asw-form-submit");
      var globalErr = wrap.querySelector(".asw-form-err");
      noteInput.value = (opts.question || this._lastUserMessage || "");

      function setFieldState(field, input, state) {
        field.classList.remove("invalid", "ok");
        if (state) field.classList.add(state);
      }

      function validate() {
        var ok = true;
        var name = nameInput.value.trim();
        var email = emailInput.value.trim();
        var phone = phoneInput.value.trim();
        setFieldState(nameField, nameInput, null);
        setFieldState(emailField, emailInput, null);
        setFieldState(phoneField, phoneInput, null);
        globalErr.classList.remove("show");

        if (name.length < 2) { setFieldState(nameField, nameInput, "invalid"); ok = false; }
        else { setFieldState(nameField, nameInput, "ok"); }
        if (!email && !phone) {
          setFieldState(emailField, emailInput, "invalid");
          setFieldState(phoneField, phoneInput, "invalid");
          globalErr.textContent = "برای تماس، حداقل ایمیل یا شماره تماس را وارد کنید.";
          globalErr.classList.add("show");
          ok = false;
        }
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setFieldState(emailField, emailInput, "invalid"); ok = false; }
        else if (email) { setFieldState(emailField, emailInput, "ok"); }
        if (phone && !/^[+0-9][0-9\s\-()]{6,24}$/.test(phone.replace(/\s/g, ""))) { setFieldState(phoneField, phoneInput, "invalid"); ok = false; }
        else if (phone) { setFieldState(phoneField, phoneInput, "ok"); }
        return ok;
      }

      [nameInput, emailInput, phoneInput].forEach(function (inp) {
        inp.addEventListener("input", function () {
          var f = inp.closest(".asw-field");
          if (f.classList.contains("invalid")) validate();
        });
      });

      submitBtn.addEventListener("click", function () {
        if (!validate()) return;

        var spinner = submitBtn.querySelector(".asw-spinner");
        var icon = submitBtn.querySelector("svg");
        var txt = submitBtn.querySelector(".asw-btn-txt");
        submitBtn.disabled = true;
        if (spinner) spinner.hidden = false;
        if (icon) icon.style.display = "none";
        txt.textContent = "در حال ارسال…";

        fetch(self.options.leadsEndpoint, {
          method: "POST",
          mode: "cors",
          credentials: "omit",
          headers: self.getHeaders(),
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim(),
            phone: phoneInput.value.trim(),
            note: (noteInput.value || "").substring(0, 2000),
            conversation_id: self.conversationId,
            conversation_token: self.conversationToken,
            website: honeypot ? honeypot.value : "",
          }),
        }).then(function (res) { return res.json().catch(function () { return {}; }); })
          .then(function (data) {
            if (data && data.ok !== false) {
              wrap.innerHTML =
                '<div class="asw-form-success">' +
                  '<svg class="asw-checkmark" viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="24"/><path d="M15 27l7.5 7.5L37 20"/></svg>' +
                  '<div class="asw-fs-title">درخواست شما با موفقیت ثبت شد</div>' +
                  '<div class="asw-fs-desc">کارشناسان ما در اسرع وقت با شما تماس می‌گیرند. زمان پاسخ‌گویی معمولاً کمتر از یک روز کاری است.</div>' +
                  (opts.onDone ? '<button type="button" class="asw-fs-close">متوجه شدم</button>' : '') +
                '</div>';
              self.showToast("درخواست تماس شما ثبت شد. ✓", 3000);
              if (opts.onDone) wrap.querySelector(".asw-fs-close").addEventListener("click", opts.onDone);
            } else {
              fail((data && data.message) || "ثبت اطلاعات ناموفق بود. لطفاً دوباره تلاش کنید.");
            }
          })
          .catch(function () {
            fail("خطای شبکه. لطفاً اتصال اینترنت را بررسی و دوباره تلاش کنید.");
          });

        function fail(message) {
          globalErr.textContent = message;
          globalErr.classList.add("show");
          submitBtn.disabled = false;
          if (spinner) spinner.hidden = true;
          if (icon) icon.style.display = "";
          txt.textContent = "ثبت درخواست تماس";
        }
      });
      return wrap;
    }

    /* ─── Voice input (Web Speech API — progressive enhancement) ─── */
    initVoice() {
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR || this.options.enableVoiceInput === false || !this.micBtn) return;
      var self = this;
      var rec;
      try { rec = new SR(); } catch (_) { return; }
      rec.lang = "fa-IR";
      rec.interimResults = true;
      rec.continuous = false;
      rec.maxAlternatives = 1;

      rec.onresult = function (e) {
        var txt = "";
        for (var i = 0; i < e.results.length; i++) txt += e.results[i][0].transcript;
        self.input.value = txt;
        self.autoGrowInput();
        self.updateSendState();
      };
      rec.onend = function () {
        self._listening = false;
        self.inputWrap.classList.remove("asw-listening");
        self.wave.hidden = true;
        if (!self.input.value) self.input.placeholder = self.options.inputPlaceholder;
      };
      rec.onerror = function (ev) {
        self._listening = false;
        self.inputWrap.classList.remove("asw-listening");
        self.wave.hidden = true;
        if (ev && ev.error === "not-allowed") self.showToast("دسترسی به میکروفون داده نشد.");
        else if (ev && ev.error === "network") self.showToast("سرویس تشخیص گفتار در دسترس نیست.");
      };

      this.micBtn.hidden = false;
      this.micBtn.addEventListener("click", function () {
        if (self._listening) { try { rec.stop(); } catch (_) {} return; }
        if (self.isLoading) return;
        try {
          rec.start();
          self._listening = true;
          self.inputWrap.classList.add("asw-listening");
          self.wave.hidden = false;
          self.input.placeholder = "در حال شنیدن…";
          self.input.focus();
        } catch (_) {}
      });
    }

    /* ─── Teaser ─── */
    _maybeShowTeaser() {
      if (this.options.showTeaser === false || this.previewMode) return;
      if (this.isOpen) return;
      try { if (sessionStorage.getItem("asw_teaser_dismissed")) return; } catch (_) {}
      if (window.innerWidth <= 520) return;
      var self = this;
      this._teaserTimer = setTimeout(function () {
        if (self.isOpen || !self.teaser) return;
        self.teaser.hidden = false;
        requestAnimationFrame(function () {
          requestAnimationFrame(function () { self.teaser.classList.add("show"); });
        });
      }, 3800);
    }

    _dismissTeaser(permanent) {
      if (this._teaserTimer) { clearTimeout(this._teaserTimer); this._teaserTimer = null; }
      if (!this.teaser) return;
      this.teaser.classList.remove("show");
      var t = this.teaser;
      setTimeout(function () { t.hidden = true; }, 320);
      if (permanent) { try { sessionStorage.setItem("asw_teaser_dismissed", "1"); } catch (_) {} }
    }

    /* ─── Unread badge + tab-title flash ─── */
    _markUnread() {
      this._unread = (this._unread || 0) + 1;
      if (this.fabBadge) {
        this.fabBadge.textContent = this._unread > 9 ? "9+" : String(this._unread);
        this.fabBadge.hidden = false;
        this.fabBadge.classList.remove("asw-pop");
        void this.fabBadge.offsetWidth;
        this.fabBadge.classList.add("asw-pop");
      }
      if (document.hidden) this._startTitleFlash();
    }

    _startTitleFlash() {
      if (this._titleTimer) return;
      var self = this;
      var original = document.title;
      this._origTitle = original;
      var flip = false;
      this._titleTimer = setInterval(function () {
        flip = !flip;
        document.title = flip ? "💬 پیام جدید — " + self.options.title : original;
      }, 1300);
    }

    _stopTitleFlash() {
      if (this._titleTimer) {
        clearInterval(this._titleTimer);
        this._titleTimer = null;
        if (this._origTitle) document.title = this._origTitle;
      }
    }

    /* ─── Auto-grow Textarea ─── */
    autoGrowInput() {
      var el = this.input;
      el.style.height = "auto";
      var newHeight = Math.min(el.scrollHeight, 132);
      el.style.height = newHeight + "px";
    }

    /* ─── Open / Close ─── */
    open() {
      this.isOpen = true;
      this._unread = 0;
      this._stopTitleFlash();
      if (this.fabBadge) this.fabBadge.hidden = true;
      this._dismissTeaser(true);
      if (this.glow) this.glow.classList.add("show");
      this.panel.classList.add("open");
      this.panel.setAttribute("aria-hidden", "false");
      this.fab.classList.add("active");
      this.fab.setAttribute("aria-expanded", "true");
      var self = this;
      setTimeout(function () { self.input.focus(); }, 300);
      this._updateScrollBtn();
    }

    close() {
      this.isOpen = false;
      this.panel.classList.remove("open");
      this.panel.setAttribute("aria-hidden", "true");
      this.fab.classList.remove("active");
      this.fab.setAttribute("aria-expanded", "false");
      if (this.glow) this.glow.classList.remove("show");
      this.fab.focus();
    }

    toggle() { this.isOpen ? this.close() : this.open(); }

    /* ─── Send State ─── */
    updateSendState() {
      this.sendBtn.disabled = this.isLoading || !this.input.value.trim();
    }

    scrollToBottom(force) {
      if (!force && this._stick === false) return;
      var m = this.messages;
      m.scrollTo({ top: m.scrollHeight, behavior: "smooth" });
    }

    _updateScrollBtn() {
      if (!this.scrollBtn) return;
      var m = this.messages;
      var dist = m.scrollHeight - m.scrollTop - m.clientHeight;
      this.scrollBtn.classList.toggle("show", dist > 160);
      this._stick = dist < 120;
    }

    /* ─── Toast ─── */
    showToast(msg, duration) {
      var t = this.toast;
      t.innerHTML = ICONS.info + "<span>" + escapeHtml(msg) + "</span>";
      t.classList.add("show");
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(function () { t.classList.remove("show"); }, duration || 4000);
    }

    /* ─── Hero (greeting) ─── */
    addHero(text) {
      var el = document.createElement("div");
      el.className = "asw-hero";
      var orbContent = (this.options.logoUrl && isSafeUrl(this.options.logoUrl))
        ? '<img src="' + escapeHtml(this.options.logoUrl) + '" alt="" referrerpolicy="no-referrer">'
        : ICONS.sparkles;
      var cards = "";
      var items = (this._suggestionItems || []).slice(0, 4);
      if (items.length) {
        cards = '<div class="asw-hero-grid">' + items.map(function (item) {
          return '<button class="asw-suggestion" type="button" data-msg="' + escapeHtml(item) + '">' +
            "<span>" + escapeHtml(item) + "</span>" +
            '<span class="asw-card-arrow" aria-hidden="true">' + ICONS.chevronLeft + "</span>" +
            "</button>";
        }).join("") + "</div>";
      }
      el.innerHTML =
        '<div class="asw-hero-spot" aria-hidden="true"></div>' +
        '<div class="asw-hero-orb-wrap" aria-hidden="true">' +
          '<span class="asw-hero-p p1"></span><span class="asw-hero-p p2"></span><span class="asw-hero-p p3"></span>' +
          '<div class="asw-hero-orb">' + orbContent + "</div>" +
        "</div>" +
        '<div class="asw-hero-text">' + escapeHtml(text) + "</div>" + cards;
      this.messages.appendChild(el);
      this.messageCount++;
      this.syncSuggestions();
      this._updateScrollBtn();
      this.scrollToBottom();
      return { row: el, col: el, bubble: el.querySelector(".asw-hero-text"), feedback: null, timeEl: null };
    }

    collapseHero() {
      var hero = this.messages.querySelector(".asw-hero");
      if (!hero) return;
      hero.classList.add("asw-hero-out");
      setTimeout(function () { if (hero.parentNode) hero.parentNode.removeChild(hero); }, 420);
    }

    /* ─── Add Message ─── */
    addMessage(text, sender, isGreeting, opts) {
      opts = opts || {};
      if (isGreeting && sender === "bot") return this.addHero(text);

      var prev = this.messages.lastElementChild;
      var isCont = !!(prev && prev.classList && prev.classList.contains("asw-row") && prev.classList.contains(sender));
      var row = document.createElement("div");
      row.className = "asw-row " + sender + (isCont ? " asw-cont" : "") + (opts.noAnim ? " no-anim" : "");

      // Only the newest answer shows its action toolbar by default.
      var oldLast = this.messages.querySelector(".asw-row.asw-last");
      if (oldLast) oldLast.classList.remove("asw-last");
      row.classList.add("asw-last");

      // Avatar
      if (this.options.showAvatar !== false) {
        var avatar = document.createElement("div");
        avatar.className = "asw-msg-avatar";
        if (sender === "bot") {
          if (this.options.logoUrl && isSafeUrl(this.options.logoUrl)) {
            var img = document.createElement("img");
            img.src = this.options.logoUrl;
            img.alt = "";
            img.referrerPolicy = "no-referrer";
            avatar.appendChild(img);
          } else {
            avatar.textContent = this.options.botAvatarText || "✦";
          }
        } else {
          avatar.textContent = "شما";
        }
        row.appendChild(avatar);
      }

      var col = document.createElement("div");
      col.className = "asw-col";

      var bubble = document.createElement("div");
      bubble.className = "asw-bubble" + (opts.streaming ? " streaming" : "") + (opts.isError ? " asw-error-bubble" : "");
      bubble.innerHTML = sender === "bot" ? renderMarkdown(text) : escapeHtml(text);

      col.appendChild(bubble);

      // Retry button on error bubbles
      if (opts.isError && opts.retry !== false && this._lastUserMessage) {
        var selfR = this;
        var retryMsg = this._lastUserMessage;
        var retry = document.createElement("button");
        retry.className = "asw-retry";
        retry.type = "button";
        retry.innerHTML = ICONS.refresh + "<span>تلاش دوباره</span>";
        retry.addEventListener("click", function () {
          if (row.parentNode) row.parentNode.removeChild(row);
          selfR.sendText(retryMsg);
        });
        col.appendChild(retry);
      }

      // Feedback: created for every bot answer; appended immediately unless
      // streaming (handleAnswerResultFromEl attaches it after the stream ends).
      var feedback = null;
      var wantFb = sender === "bot" && !isGreeting && this.options.showFeedback !== false;
      if (wantFb) {
        feedback = this.buildFeedbackEl(text);
        if (!opts.skipFeedback) col.appendChild(feedback);
      }

      var timeEl = null;
      if (this.options.showTimestamp !== false && !opts.streaming) {
        timeEl = document.createElement("div");
        timeEl.className = "asw-time";
        timeEl.textContent = formatTime();
        col.appendChild(timeEl);
      }

      // Citations
      if (sender === "bot" && this.options.showCitations && Array.isArray(opts.citations) && opts.citations.length) {
        col.appendChild(this.buildCitations(opts.citations));
      }

      row.appendChild(col);
      this.messages.appendChild(row);
      this.messageCount++;

      // Unread badge while panel is closed
      if (sender === "bot" && !isGreeting && !opts.streaming && !this.isOpen) this._markUnread();

      this.syncSuggestions();
      this._updateScrollBtn();
      this.scrollToBottom();
      if (!opts.streaming) this.saveLocalHistory();
      return { row: row, col: col, bubble: bubble, feedback: feedback, timeEl: timeEl };
    }

    buildFeedbackEl(answerPreview) {
      var el = document.createElement("div");
      el.className = "asw-feedback";
      el.innerHTML =
        '<button class="asw-fb-btn fb-copy" type="button" data-action="copy" aria-label="کپی پاسخ" title="کپی پاسخ">' + ICONS.copy + '</button>' +
        '<button class="asw-fb-btn thumbs-up" type="button" data-action="helpful" aria-label="مفيد بود" title="مفید بود">' + ICONS.thumbUp + '</button>' +
        '<button class="asw-fb-btn thumbs-down" type="button" data-action="not_helpful" aria-label="مفيد نبود" title="مفید نبود">' + ICONS.thumbDown + '</button>';
      el.setAttribute("data-question", (this._lastUserMessage || "").substring(0, 200));
      el.setAttribute("data-answer", answerPreview.substring(0, 300));
      return el;
    }

    buildCitations(citations) {
      var wrap = document.createElement("div");
      wrap.className = "asw-citations";
      var label = document.createElement("span");
      label.className = "asw-citations-label";
      label.textContent = "منابع:";
      wrap.appendChild(label);
      citations.slice(0, 4).forEach((c) => {
        var title = (c.title || "منبع").substring(0, 60);
        var chip = document.createElement(c.url && isSafeUrl(c.url) ? "a" : "span");
        chip.className = "asw-citation";
        chip.title = c.page_number ? title + " — صفحه " + c.page_number : title;
        chip.innerHTML = ICONS.link + '<span>' + escapeHtml(title) + (c.page_number ? " · ص" + escapeHtml(String(c.page_number)) : "") + '</span>';
        if (c.url && isSafeUrl(c.url)) {
          chip.href = c.url;
          chip.target = "_blank";
          chip.rel = "noopener noreferrer";
        }
        wrap.appendChild(chip);
      });
      return wrap;
    }

    /* ─── Feedback Handler ─── */
    handleFeedback(btn) {
      var feedbackDiv = btn.closest(".asw-feedback");
      if (!feedbackDiv) return;

      // Copy is a repeatable local action — never sent as feedback.
      if (btn.dataset.action === "copy") {
        var col = btn.closest(".asw-col");
        var bubble = col ? col.querySelector(".asw-bubble") : null;
        var text = bubble ? bubble.textContent.trim() : "";
        navigator.clipboard.writeText(text).then(function () {
          btn.classList.add("copied");
          btn.innerHTML = ICONS.check;
          setTimeout(function () {
            btn.classList.remove("copied");
            btn.innerHTML = ICONS.copy;
          }, 1600);
        }).catch(function () {});
        return;
      }

      if (feedbackDiv.dataset.sent) return;

      var action = btn.dataset.action;
      var isHelpful = action === "helpful";

      // Visual feedback
      feedbackDiv.querySelectorAll(".asw-fb-btn").forEach(function (b) {
        if (b.dataset.action === "copy") return;
        b.classList.remove("active");
        b.disabled = true;
      });
      btn.classList.add("active");

      if (isHelpful) {
        btn.innerHTML = ICONS.thumbUpFilled;
      } else {
        btn.innerHTML = ICONS.thumbDownFilled;
      }

      feedbackDiv.dataset.sent = "true";

      this.sendFeedback(isHelpful, feedbackDiv.dataset.question || "", feedbackDiv.dataset.answer || "", feedbackDiv.dataset.messageId || null);
    }

    sendFeedback(helpful, question, answerPreview, messageId) {
      if (!this.options.feedbackEndpoint) return;
      var body = {
        helpful: helpful,
        question: question,
        answer_preview: answerPreview,
        session_id: this.options.sessionId,
      };
      if (messageId) {
        body.message_id = Number(messageId);
        body.conversation_id = this.conversationId;
        body.conversation_token = this.conversationToken;
      }
      fetch(this.options.feedbackEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getHeaders(),
        body: JSON.stringify(body),
      }).catch(function () {});
    }

    /* ─── Events ─── */
    sendEvent(type, meta) {
      if (!this.options.eventsEndpoint) return;
      fetch(this.options.eventsEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getHeaders(),
        body: JSON.stringify({ event_type: type, metadata: meta || {} }),
      }).catch(function () {});
    }

    /* ─── Loading State — staged AI thinking statuses ─── */
    setLoading(loading) {
      var self = this;
      this.isLoading = loading;
      this.typing.hidden = !loading;
      this.input.disabled = loading;
      this.input.placeholder = loading ? "در حال پاسخ‌دهی..." : this.options.inputPlaceholder;
      if (this.subtitleEl) {
        this.subtitleEl.textContent = loading ? "در حال نوشتن…" : this.options.subtitle;
      }
      if (loading) {
        this._statusIdx = 0;
        if (this.typingLabel) this.typingLabel.textContent = THINKING_STATUSES[0];
        if (this._statusTimer) clearInterval(this._statusTimer);
        this._statusTimer = setInterval(function () {
          self._statusIdx = ((self._statusIdx || 0) + 1) % THINKING_STATUSES.length;
          if (self.typingLabel) self.typingLabel.textContent = THINKING_STATUSES[self._statusIdx];
        }, 1600);
        this.sendBtn.classList.add("asw-stop");
        this.sendBtn.innerHTML = ICONS.stop;
      } else {
        if (this._statusTimer) { clearInterval(this._statusTimer); this._statusTimer = null; }
        this.sendBtn.classList.remove("asw-stop");
        this.sendBtn.innerHTML = ICONS.arrowUp;
      }
      this.updateSendState();
      if (loading) this.scrollToBottom();
    }

    /* ─── Play Sound ─── */
    playSound(type) {
      if (!this.options.enableSounds) return;
      try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        gain.gain.value = 0.1;
        if (type === "send") { osc.frequency.value = 880; osc.type = "sine"; }
        else { osc.frequency.value = 660; osc.type = "sine"; }
        osc.start();
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
        osc.stop(ctx.currentTime + 0.15);
      } catch (_) {}
    }

    /* ─── Send Message ─── */
    send() {
      var msg = this.input.value.trim();
      if (!msg || this.isLoading) return;
      this.input.value = "";
      this.autoGrowInput();
      this.sendText(msg);
    }

    sendText(msg) {
      if (!msg || this.isLoading) return;

      var self = this;
      this._lastUserMessage = msg;
      this._chatStarted = true;
      this.addMessage(msg, "user");
      this.collapseHero();
      this.syncSuggestions();
      this.suggestions.hidden = true;
      this.setLoading(true);
      this.playSound("send");
      this.scrollToBottom(true);

      if (navigator.onLine === false) {
        var offMsg = "اتصال اینترنت قطع است. بعد از وصل شدن دوباره تلاش کنید.";
        this.addMessage(offMsg, "bot", false, { isError: true, skipFeedback: true });
        this.showToast(offMsg, 4000);
        this.setLoading(false);
        return;
      }

      var p = (function () {
        if (self.options.enableStreaming && !self.previewMode) {
          return self.streamChat(msg);
        }
        return self.callBackend(msg).then(function (result) {
          self.handleAnswerResult(result.answer, result);
          return null;
        });
      })();

      p.then(function () {
        self.playSound("receive");
      }).catch(function (err) {
        self.sendEvent("fallback_triggered", { message: err && err.message || "unknown" });
        var errMsg = err && err.userMessage ? err.userMessage : "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً دوباره تلاش کنید.";
        self.addMessage(errMsg, "bot", false, { isError: true, skipFeedback: true });
        self.showToast(errMsg, 5000);
      }).finally(function () {
        self.setLoading(false);
        self.input.focus();
      });
    }

    handleAnswerResult(answer, meta) {
      meta = meta || {};
      var els = this.addMessage(answer, "bot", false, {
        citations: meta.citations || [],
        skipFeedback: false,
      });
      if (els.feedback && meta.message_id) {
        els.feedback.setAttribute("data-message-id", String(meta.message_id));
      }
      if (Array.isArray(meta.rule_actions) && meta.rule_actions.length) {
        this.applyRuleActions(meta.rule_actions, answer);
      } else if (meta.fallback) {
        this.maybeShowHandoff(answer);
      }
      return els;
    }

    applyRuleActions(actions, answerText) {
      var self = this;
      var lastRow = this.messages.lastElementChild;
      if (!lastRow || !lastRow.classList.contains("asw-row")) return;
      actions.forEach(function (a) {
        var type = a.action_type || a.type || "";
        var payload = a.payload || a.url || "";
        var label = a.label || a.name || "مشاهده";
        if (type === "suggest_link" && payload) {
          var chip = document.createElement("a");
          chip.className = "asw-suggestion";
          chip.href = payload;
          chip.target = "_blank";
          chip.rel = "noopener noreferrer";
          chip.textContent = label;
          chip.style.display = "inline-flex";
          chip.style.marginTop = "8px";
          lastRow.querySelector(".asw-bubble").appendChild(chip);
        } else if (type === "suggest_text" && payload) {
          var hint = document.createElement("div");
          hint.className = "asw-rule-hint";
          hint.textContent = payload;
          lastRow.querySelector(".asw-bubble").appendChild(hint);
        } else if (type === "handoff") {
          self.maybeShowHandoff(answerText || payload);
        }
      });
      this.saveLocalHistory();
      this.scrollToBottom();
    }

    /* ─── Streaming (SSE) with smooth rAF typewriter ─── */
    async streamChat(message) {
      var self = this;
      this.abortStream = new AbortController();
      var timeout = setTimeout(function () { self.abortStream.abort(); }, Number(this.options.timeoutMs) || 60000);

      var els = null;
      var streamedText = "";
      var shownCount = 0;
      var streamClosed = false;
      var finished = false;
      var firstTokenSeen = false;
      var finishMeta = null;
      var rafId = 0;

      function paintStep() {
        rafId = 0;
        if (!els || finished) return;
        if (shownCount < streamedText.length) {
          var gap = streamedText.length - shownCount;
          shownCount = Math.min(streamedText.length, shownCount + Math.max(2, Math.ceil(gap / 12)));
          els.bubble.innerHTML = renderMarkdown(streamedText.slice(0, shownCount));
          self.scrollToBottom();
          rafId = requestAnimationFrame(paintStep);
        } else if (streamClosed) {
          finishUp();
        }
      }

      function ensurePaint() {
        if (!rafId && !finished) rafId = requestAnimationFrame(paintStep);
      }

      function finishUp() {
        if (finished) return;
        finished = true;
        if (rafId) { cancelAnimationFrame(rafId); rafId = 0; }
        if (els) {
          els.bubble.classList.remove("streaming");
          self.handleAnswerResultFromEl(els, streamedText, finishMeta || {});
        }
      }

      try {
        await new Promise(function (resolve, reject) {
          fetch(self.options.streamEndpoint, {
            method: "POST",
            mode: "cors",
            credentials: "omit",
            headers: self.getHeaders(),
            body: JSON.stringify({
              message: message,
              conversation_id: self.conversationId,
              page_url: (window.location && window.location.href || "").substring(0, 1000),
            }),
            signal: self.abortStream.signal,
          }).then(function (res) {
            if (!res.ok) {
              res.json().catch(function () { return {}; }).then(function (data) {
                var e = new Error(data.message || data.error || "Stream failed");
                e.userMessage = data.message || (res.status >= 500
                  ? "سرویس موقتاً در دسترس نیست. لطفاً لحظاتی بعد دوباره تلاش کنید."
                  : "لطفاً پیام خود را بررسی و دوباره ارسال کنید.");
                reject(e);
              });
              return;
            }
            if (!res.body || !res.body.getReader) {
              // No SSE support (older proxy) — fall back to JSON chat.
              resolve(null);
              return;
            }
            var reader = res.body.getReader();
            var decoder = new TextDecoder();
            var buffer = "";
            function pump() {
              reader.read().then(function (chunk) {
                if (chunk.done) { resolve(null); return; }
                buffer += decoder.decode(chunk.value, { stream: true });
                var events = buffer.split("\n\n");
                buffer = events.pop();
                events.forEach(function (raw) {
                  var name = "message";
                  var dataLines = [];
                  raw.split("\n").forEach(function (line) {
                    if (line.indexOf("event:") === 0) name = line.slice(6).trim();
                    else if (line.indexOf("data:") === 0) dataLines.push(line.slice(5).trim());
                  });
                  if (!dataLines.length) return;
                  var data;
                  try { data = JSON.parse(dataLines.join("\n")); } catch (_) { return; }
                  if (name === "meta") {
                    if (data.conversation_id) self.conversationId = data.conversation_id;
                    if (data.conversation_token) self.conversationToken = data.conversation_token;
                    self.saveConversation();
                  } else if (name === "token") {
                    streamedText += (data.t || "");
                    if (!firstTokenSeen) {
                      firstTokenSeen = true;
                      els = self.addMessage("", "bot", false, { streaming: true, skipFeedback: true });
                      self.typing.hidden = true;
                    }
                    ensurePaint();
                  } else if (name === "done") {
                    finishMeta = data;
                    streamClosed = true;
                    ensurePaint();
                  } else if (name === "error") {
                    var ee = new Error(data.message || "stream error");
                    ee.userMessage = data.message || "خطا در دریافت پاسخ.";
                    reject(ee);
                  }
                });
                pump();
              }).catch(function (e) { reject(e); });
            }
            pump();
          }).catch(reject);
        });

        if (els && streamedText) {
          // Let the typewriter finish, then finalize.
          streamClosed = true;
          ensurePaint();
        } else if (!streamedText) {
          // SSE stream empty/unsupported → classic JSON roundtrip.
          var result = await this.callBackend(message);
          this.handleAnswerResult(result.answer, result);
        }
      } catch (err) {
        if (rafId) { cancelAnimationFrame(rafId); rafId = 0; }
        if (err.name === "AbortError") {
          // User stop or timeout: keep partial text if meaningful.
          if (streamedText && els) {
            els.bubble.classList.remove("streaming");
            this.handleAnswerResultFromEl(els, streamedText + " …", finishMeta || {});
          } else {
            var te = new Error("Timeout");
            te.userMessage = "پاسخ‌دهی بیش از حد طول کشید. لطفاً دوباره تلاش کنید.";
            throw te;
          }
        } else {
          throw err;
        }
      } finally {
        clearTimeout(timeout);
        this.abortStream = null;
      }
    }

    handleAnswerResultFromEl(els, answer, meta) {
      els.bubble.innerHTML = renderMarkdown(answer);
      if (this.options.showCitations && Array.isArray(meta.citations) && meta.citations.length) {
        els.col.appendChild(this.buildCitations(meta.citations));
      }
      if (els.timeEl === null && this.options.showTimestamp !== false) {
        var t = document.createElement("div");
        t.className = "asw-time";
        t.textContent = formatTime();
        els.col.appendChild(t);
      }
      if (this.options.showFeedback !== false && els.feedback) {
        els.feedback.setAttribute("data-question", (this._lastUserMessage || "").substring(0, 200));
        els.feedback.setAttribute("data-answer", answer.substring(0, 300));
        if (meta.message_id) els.feedback.setAttribute("data-message-id", String(meta.message_id));
        els.col.appendChild(els.feedback);
      }
      if (Array.isArray(meta.rule_actions) && meta.rule_actions.length) {
        this.applyRuleActions(meta.rule_actions, answer);
      } else if (meta.fallback) this.maybeShowHandoff(answer);
      this.saveLocalHistory();
      this.scrollToBottom();
      this._updateScrollBtn();
    }

    /* ─── Human Handoff ─── */
    maybeShowHandoff(answerText) {
      var trigger = this.options.handoffTrigger || "low_confidence";
      if (!this.options.enableHandoff || trigger === "off" || this.previewMode) return;
      if (this._handoffShown) return;
      this._handoffShown = true;

      var self = this;
      var lastRow = this.messages.lastElementChild;
      if (!lastRow) return;
      var bar = document.createElement("div");
      bar.className = "asw-handoff";
      var label = document.createElement("span");
      label.className = "asw-handoff-label";
      label.textContent = this.options.handoffMessage;
      bar.appendChild(label);

      var urls = this.options.handoffUrls || {};
      var channels = [
        { key: "contact_form", url: urls.contact_form, label: "فرم تماس", icon: ICONS.user },
        { key: "telegram", url: urls.telegram, label: "تلگرام", icon: ICONS.link },
        { key: "whatsapp", url: urls.whatsapp, label: "واتساپ", icon: ICONS.phone },
      ];
      var anyChannel = false;
      channels.forEach(function (ch) {
        if (!ch.url || !isSafeUrl(ch.url)) return;
        anyChannel = true;
        var a = document.createElement("a");
        a.className = "asw-handoff-btn";
        a.href = ch.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.innerHTML = ch.icon + escapeHtml(ch.label);
        a.addEventListener("click", function () { self.logHandoff(ch.key, answerText); });
        bar.appendChild(a);
      });
      if (anyChannel) {
        lastRow.appendChild(bar);
        this.scrollToBottom();
      }
      // Always offer the contact form as the guaranteed channel.
      if (this.options.enableLeadCapture) {
        var formHolder = document.createElement("div");
        formHolder.className = "asw-leadform-wrap";
        formHolder.appendChild(this.buildContactForm("handoff_email", {
          compact: true,
          question: answerText,
        }));
        lastRow.appendChild(formHolder);
        this.scrollToBottom();
      }
    }

    logHandoff(channel, question) {
      if (!this.options.handoffEndpoint) return;
      fetch(this.options.handoffEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getHeaders(),
        body: JSON.stringify({
          channel: channel,
          message: (question || this._lastUserMessage || "").substring(0, 2000),
          conversation_id: this.conversationId,
          conversation_token: this.conversationToken,
        }),
      }).catch(function () {});
    }

    /* ─── API Call ─── */
    async callBackend(message) {
      var controller = new AbortController();
      var timeout = setTimeout(function () { controller.abort(); }, Number(this.options.timeoutMs) || 45000);
      try {
        var res = await fetch(this.options.apiEndpoint, {
          method: "POST", mode: "cors", credentials: "omit",
          headers: this.getHeaders(),
          body: JSON.stringify({
            message: message,
            conversation_id: this.conversationId,
            page_url: (window.location && window.location.href || "").substring(0, 1000),
          }),
          signal: controller.signal,
        });
        var data = {};
        try { data = await res.json(); } catch (_) { data = {}; }
        if (!res.ok) {
          var e = new Error(data.message || data.error || "Request failed");
          e.userMessage = res.status >= 500
            ? "سرویس موقتاً در دسترس نیست. لطفاً لحظاتی بعد دوباره تلاش کنید."
            : data.message || "لطفاً پیام خود را بررسی و دوباره ارسال کنید.";
          throw e;
        }
        var answer = data.answer || data.reply || data.response || data.message;
        if (typeof answer !== "string" || !answer.trim()) throw new Error("Empty answer");
        if (data.conversation_id) {
          this.conversationId = data.conversation_id;
          this.conversationToken = data.conversation_token || this.conversationToken;
          this.saveConversation();
        }
        return {
          answer: answer.trim(),
          citations: data.citations || [],
          message_id: data.message_id,
          fallback: data.fallback || false,
          rule_actions: data.rule_actions || [],
        };
      } catch (err) {
        if (err.name === "AbortError") {
          var te = new Error("Timeout");
          te.userMessage = "پاسخ‌دهی بیش از حد طول کشید. لطفاً دوباره تلاش کنید.";
          throw te;
        }
        throw err;
      } finally {
        clearTimeout(timeout);
      }
    }

    /* ─── Headers ─── */
    getHeaders() {
      var h = { "Content-Type": "application/json" };
      if (this.options.widgetPublicKey) h["X-Widget-Key"] = this.options.widgetPublicKey;
      return h;
    }
  }

  AISupportWidget.version = "6.0.0";

  /* ─────────────── BOOT ─────────────── */
  function boot() {
    var globalConfig = window.AI_WIDGET_CONFIG || {};
    var options = Object.assign({}, globalConfig);
    if (scriptConfig.api) options.apiEndpoint = scriptConfig.api;
    if (scriptConfig.widgetKey) options.widgetPublicKey = scriptConfig.widgetKey;
    if (scriptConfig.title) options.title = scriptConfig.title;
    if (scriptConfig.primaryColor) options.primaryColor = scriptConfig.primaryColor;
    if (scriptConfig.preview === "1" || scriptConfig.preview === "true") options.previewMode = true;
    window._aiWidget = new AISupportWidget(options);
  }

  window.AISupportWidget = AISupportWidget;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
