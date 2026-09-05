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
       AI Support Widget — SKEUOMORPHISM
       ───────────────────────────────────────────────────────────────────────
       Every element imitates a real, physical object (iOS 6 / Aqua era):

         · Panel      — a brushed-aluminium device with a stitched leather
                        header, an inset recessed screen and a felt tray.
         · Messages   — the assistant writes on lined notepaper; the user
                        speaks from a glossy blue lozenge with a real notch.
         · Buttons    — moulded plastic caps: top-light gradient, bevelled
                        edge, dark base rim, and they physically depress.
         · Input      — a recessed glass slot with an inner shadow.
         · Send       — a chrome-rimmed pushbutton with a specular highlight.
         · Type       — letterpress: 1px light shadow below, dark above.
         · Textures   — linen, paper grain, leather, felt, brushed metal,
                        all inline SVG data URIs (no external assets).

       Class names, IDs and state hooks are IDENTICAL to the original build,
       so the API, SSE streaming, memory, events and admin preview channel
       are completely untouched — only the presentation layer is new.
       ═══════════════════════════════════════════════════════════════════════ */
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    :host{all:initial;--asw-font:'Vazirmatn','Vazir','IRANSans','Lucida Grande','Helvetica Neue',ui-sans-serif,system-ui,sans-serif}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

    /* ───────────────────────────────────────────────────────────────────
       MATERIALS — the physical palette
       ─────────────────────────────────────────────────────────────────── */
    .asw{
      --asw-primary:#2c6fbb;--asw-secondary:#1c4f8f;--asw-accent:#5aa0e8;

      /* pigments */
      --metal-hi:#fdfdfd;
      --metal:#e4e6ea;
      --metal-lo:#b9bec7;
      --metal-edge:#8f959f;
      --paper:#fdfbf3;
      --paper-2:#f6f2e4;
      --paper-line:#cfe0ee;
      --paper-edge:#d9d2bd;
      --leather:#4a4a52;
      --leather-2:#2e2e35;
      --felt:#c9ccd4;
      --stitch:rgba(255,255,255,.34);

      /* inks */
      --ink:#2b2d33;
      --ink-2:#63676f;
      --ink-3:#9a9ea7;
      --ink-emboss:rgba(255,255,255,.85);
      --ink-deboss:rgba(0,0,0,.42);

      /* plastic key */
      --key-hi:#ffffff;
      --key:#eef0f3;
      --key-lo:#ccd1d9;
      --key-rim:#9aa1ac;

      /* glossy blue lozenge */
      --gel-hi:#7cb6f0;
      --gel:#3d84d4;
      --gel-lo:#1f5da8;
      --gel-rim:#164a7c;

      --asw-success:#3f8f4f;--asw-error:#b03028;--asw-warning:#b8862b;--online:#68c368;

      /* geometry */
      --rad:10px;--rad-sm:7px;--rad-lg:14px;--rad-pill:999px;

      /* spacing */
      --sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:20px;--sp-6:24px;--sp-8:32px;

      /* type */
      --t-xs:11px;--t-sm:12px;--t-md:13.5px;--t-lg:15px;--t-xl:18px;

      /* motion — physical, quick, with overshoot on release */
      --ms:90ms;--mm:180ms;--ml:320ms;
      --ease:cubic-bezier(.4,0,.2,1);
      --ease-out:cubic-bezier(.16,1,.3,1);
      --ease-press:cubic-bezier(.3,0,.6,1);

      /* recurring physical effects */
      --letterpress:0 1px 0 var(--ink-emboss);
      --letterpress-dark:0 -1px 0 rgba(0,0,0,.5);
      --bevel-out:inset 0 1px 0 rgba(255,255,255,.9),inset 0 -1px 0 rgba(0,0,0,.14);
      --bevel-in:inset 0 2px 4px rgba(0,0,0,.28),inset 0 -1px 0 rgba(255,255,255,.55);

      /* textures — inline SVG, %23 escapes the hash */
      --tex-linen:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='6' height='6'%3E%3Cpath d='M0 0h6v1H0zM0 3h6v1H0z' fill='%23000' opacity='.035'/%3E%3Cpath d='M0 0v6h1V0zM3 0v6h1V0z' fill='%23fff' opacity='.5'/%3E%3C/svg%3E");
      --tex-paper:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='40' height='40' filter='url(%23n)' opacity='.055'/%3E%3C/svg%3E");
      --tex-leather:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48'%3E%3Cfilter id='l'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.62' numOctaves='4'/%3E%3C/filter%3E%3Crect width='48' height='48' filter='url(%23l)' opacity='.32'/%3E%3C/svg%3E");
      --tex-brush:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='3' height='3'%3E%3Cpath d='M0 0h3v1H0z' fill='%23fff' opacity='.42'/%3E%3Cpath d='M0 1h3v1H0z' fill='%23000' opacity='.045'/%3E%3C/svg%3E");
      --tex-felt:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='30'%3E%3Cfilter id='f'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.1' numOctaves='2'/%3E%3C/filter%3E%3Crect width='30' height='30' filter='url(%23f)' opacity='.10'/%3E%3C/svg%3E");

      /* aliases consumed by the unchanged JS */
      --asw-bg:var(--paper);--asw-surface:var(--metal);--asw-surface-2:var(--metal-lo);
      --asw-text:var(--ink);--asw-text-secondary:var(--ink-2);--asw-text-muted:var(--ink-3);
      --asw-border:var(--metal-edge);--asw-border-strong:var(--metal-edge);
      --asw-bot-bg:var(--paper);--asw-bot-text:var(--ink);
      --asw-user-bg:var(--gel);--asw-user-bg-2:var(--gel-lo);--asw-user-text:#fff;
      --asw-input-bg:#fff;--asw-input-focus-bg:#fff;
      --asw-shadow:0 18px 40px -10px rgba(0,0,0,.55);
      --asw-header-bg:var(--leather);
      --asw-radius:var(--rad-lg);--asw-radius-sm:var(--rad);--asw-radius-xs:var(--rad-sm);
      --asw-panel-w:392px;--asw-panel-h:640px;
      --asw-spring:var(--ease-out);--asw-out:var(--ease-out);

      font-family:var(--asw-font);
      font-size:var(--asw-font-size,13.5px);
      direction:rtl;line-height:1.8;color:var(--ink);
      text-shadow:var(--letterpress);
      -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
    }

    /* night mode — the device under a desk lamp */
    .asw.dark{
      --metal-hi:#4c505a;--metal:#3a3e46;--metal-lo:#282b31;--metal-edge:#15171b;
      --paper:#3b3a36;--paper-2:#333230;--paper-line:#4c5a66;--paper-edge:#242320;
      --leather:#232329;--leather-2:#141418;
      --felt:#2a2d33;--stitch:rgba(255,255,255,.16);
      --ink:#f0ece1;--ink-2:#b3aea2;--ink-3:#807b72;
      --ink-emboss:rgba(255,255,255,.10);
      --key-hi:#5a5f69;--key:#454a53;--key-lo:#2f333a;--key-rim:#191c21;
      --letterpress:0 1px 0 rgba(0,0,0,.55);
      --bevel-out:inset 0 1px 0 rgba(255,255,255,.16),inset 0 -1px 0 rgba(0,0,0,.5);
      --bevel-in:inset 0 2px 5px rgba(0,0,0,.6),inset 0 -1px 0 rgba(255,255,255,.08);
      --asw-input-bg:#2b2a27;--asw-input-focus-bg:#2b2a27;
    }

    /* ───────────────────────────────────────────────────────────────────
       ROOT
       ─────────────────────────────────────────────────────────────────── */
    .asw-root{position:fixed;z-index:2147483647;width:0;height:0;pointer-events:none}
    .asw-root>*{pointer-events:auto}
    .asw-root *{box-sizing:border-box}

    /* warm lamp spill under the device */
    .asw-glow{position:fixed;z-index:0;width:300px;height:300px;border-radius:50%;pointer-events:none;background:radial-gradient(circle,rgba(255,214,140,.34),transparent 68%);filter:blur(52px);opacity:0;transform:scale(.6);transition:opacity var(--ml) var(--ease),transform var(--ml) var(--ease-out)}
    .asw-glow.show{opacity:.7;transform:scale(1)}

    /* ═══════════════════════════════════════════════════════════════════
       LAUNCHER — a moulded plastic button cap
       ═══════════════════════════════════════════════════════════════════ */
    .asw-fab{position:fixed;width:62px;height:62px;border:none;border-radius:50%;cursor:pointer;z-index:2;display:grid;place-items:center;
      background:
        linear-gradient(180deg,var(--gel-hi) 0%,var(--gel) 48%,var(--gel-lo) 100%);
      color:#fff;
      box-shadow:
        inset 0 1px 1px rgba(255,255,255,.95),
        inset 0 -3px 6px rgba(0,0,0,.34),
        0 1px 0 rgba(255,255,255,.5),
        0 3px 0 #16437c,
        0 5px 1px rgba(0,0,0,.28),
        0 9px 18px rgba(0,0,0,.42);
      text-shadow:0 -1px 0 rgba(0,0,0,.45);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press),background var(--mm) var(--ease);
      animation:sk-drop var(--ml) var(--ease-out) 100ms both}
    /* specular sheen across the top third */
    .asw-fab::before{content:"";position:absolute;top:3px;left:8%;right:8%;height:42%;border-radius:50% 50% 46% 46%/62% 62% 38% 38%;background:linear-gradient(180deg,rgba(255,255,255,.82),rgba(255,255,255,.06));pointer-events:none}
    .asw-fab:hover{background:linear-gradient(180deg,#8dc2f5 0%,#4a8fdd 48%,#2467b3 100%)}
    /* physically depress: sink 3px and lose the base rim */
    .asw-fab:active{transform:translateY(3px);
      box-shadow:
        inset 0 2px 5px rgba(0,0,0,.45),
        inset 0 -1px 0 rgba(255,255,255,.32),
        0 1px 2px rgba(0,0,0,.3)}
    .asw-fab.active{background:linear-gradient(180deg,var(--key-hi),var(--key) 50%,var(--key-lo));color:var(--ink-2);text-shadow:var(--letterpress);
      box-shadow:inset 0 1px 1px rgba(255,255,255,.95),inset 0 -3px 6px rgba(0,0,0,.16),0 3px 0 var(--key-rim),0 5px 1px rgba(0,0,0,.22),0 9px 16px rgba(0,0,0,.34)}
    .asw-fab svg{width:26px;height:26px;position:relative;filter:drop-shadow(0 -1px 0 rgba(0,0,0,.4)) drop-shadow(0 1px 0 rgba(255,255,255,.35))}
    .asw-fab-shine{display:none}
    .asw-fab-icon-main,.asw-fab-icon-close{position:absolute;inset:0;display:grid;place-items:center;transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out)}
    .asw-fab-icon-close{opacity:0;transform:rotate(-90deg) scale(.5)}
    .asw-fab.active .asw-fab-icon-main{opacity:0;transform:rotate(90deg) scale(.5)}
    .asw-fab.active .asw-fab-icon-close{opacity:1;transform:rotate(0) scale(1)}
    .asw-fab-custom-icon{width:28px;height:28px;border-radius:var(--rad-sm);object-fit:contain}
    .asw-fab-pulse{position:absolute;inset:-3px;border-radius:50%;border:2px solid rgba(255,255,255,.5);opacity:0;animation:sk-ping 2.8s var(--ease) 1.4s infinite;pointer-events:none}
    .asw-fab.active .asw-fab-pulse{display:none}

    /* embossed red enamel badge */
    .asw-fab-badge{position:absolute;top:-3px;inset-inline-end:-3px;min-width:22px;height:22px;padding:0 6px;border-radius:var(--rad-pill);
      background:linear-gradient(180deg,#ff8a80 0%,#e0342a 52%,#a81d16 100%);
      color:#fff;font-size:11px;font-weight:800;line-height:1;display:grid;place-items:center;
      border:1.5px solid rgba(255,255,255,.75);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.7),0 2px 3px rgba(0,0,0,.4);
      text-shadow:0 -1px 0 rgba(0,0,0,.4);pointer-events:none}
    .asw-fab-badge[hidden]{display:none}
    .asw-fab-badge.asw-pop{animation:sk-pop var(--mm) var(--ease-out)}

    /* engraved plaque tooltip */
    .asw-fab-label{position:absolute;inset-inline-end:calc(100% + var(--sp-3));top:50%;transform:translateY(-50%) translateX(6px);white-space:nowrap;padding:7px 13px;border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#5a5a62,#37373d);color:#f2f0ea;
      font-family:inherit;font-size:var(--t-sm);font-weight:700;
      border:1px solid rgba(0,0,0,.55);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 3px 7px rgba(0,0,0,.42);
      text-shadow:0 -1px 0 rgba(0,0,0,.6);
      opacity:0;pointer-events:none;transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out)}
    .corner-bl .asw-fab-label,.corner-tl .asw-fab-label{inset-inline-end:auto;inset-inline-start:calc(100% + var(--sp-3));transform:translateY(-50%) translateX(-6px)}
    .asw-fab:hover .asw-fab-label,.asw-fab:focus-visible .asw-fab-label{opacity:1;transform:translateY(-50%) translateX(0)}
    .asw-fab.active .asw-fab-label{display:none}

    /* ═══════════════════════════════════════════════════════════════════
       TEASER — a paper sticky note
       ═══════════════════════════════════════════════════════════════════ */
    .asw-teaser{position:fixed;z-index:1;max-width:262px;display:flex;align-items:flex-start;gap:var(--sp-3);padding:var(--sp-4);
      border-radius:2px 2px var(--rad) 2px;
      background:linear-gradient(170deg,#fffdf0,#fdf3cf 82%,#f3e6b4);
      background-image:var(--tex-paper),linear-gradient(170deg,#fffdf0,#fdf3cf 82%,#f3e6b4);
      border:none;
      box-shadow:0 1px 0 rgba(255,255,255,.7) inset,0 8px 16px -4px rgba(0,0,0,.34),0 2px 4px rgba(0,0,0,.18);
      cursor:pointer;opacity:0;transform:translateY(10px) rotate(-1.4deg);
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out);pointer-events:none}
    .asw-teaser.show{opacity:1;transform:translateY(0) rotate(-1.4deg);pointer-events:auto}
    .asw-teaser:hover{transform:translateY(-2px) rotate(-.6deg)}
    /* curled corner */
    .asw-teaser::after{content:"";position:absolute;bottom:0;inset-inline-start:0;width:20px;height:20px;background:linear-gradient(135deg,rgba(0,0,0,.16),transparent 52%);border-radius:0 0 0 var(--rad);pointer-events:none}
    .asw-teaser-orb{width:32px;height:32px;flex:none;border-radius:50%;background:linear-gradient(180deg,var(--gel-hi),var(--gel-lo));color:#fff;display:grid;place-items:center;box-shadow:inset 0 1px 0 rgba(255,255,255,.7),0 1px 2px rgba(0,0,0,.35)}
    .asw-teaser-orb svg{width:15px;height:15px}
    .asw-teaser-body{min-width:0;padding-inline-end:var(--sp-4)}
    .asw-teaser-title{font-size:var(--t-md);font-weight:800;color:#4a412a;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-teaser-text{font-size:var(--t-sm);color:#6b6047;line-height:1.7;margin-top:2px;text-shadow:0 1px 0 rgba(255,255,255,.7)}
    .asw-teaser-close{position:absolute;top:6px;inset-inline-start:6px;width:20px;height:20px;border:none;border-radius:50%;background:rgba(0,0,0,.07);color:#6b6047;display:grid;place-items:center;cursor:pointer;opacity:0;transition:opacity var(--ms) var(--ease),background var(--ms) var(--ease)}
    .asw-teaser:hover .asw-teaser-close,.asw-teaser-close:focus-visible{opacity:1}
    .asw-teaser-close:hover{background:rgba(0,0,0,.16)}
    .asw-teaser-close svg{width:10px;height:10px}
    @media(max-width:520px){.asw-teaser{display:none}}

    /* ═══════════════════════════════════════════════════════════════════
       PANEL — a brushed aluminium device
       ═══════════════════════════════════════════════════════════════════ */
    .asw-panel{position:fixed;z-index:3;width:var(--asw-panel-w);height:var(--asw-panel-h);
      max-width:calc(100vw - var(--sp-5));max-height:calc(100dvh - 96px);
      display:flex;flex-direction:column;overflow:hidden;
      padding:3px;
      background:var(--tex-brush),linear-gradient(180deg,var(--metal-hi),var(--metal) 12%,var(--metal-lo));
      border:1px solid var(--metal-edge);
      border-radius:var(--rad-lg);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.95),
        inset 0 -1px 0 rgba(0,0,0,.25),
        0 2px 3px rgba(0,0,0,.24),
        0 20px 44px -10px rgba(0,0,0,.56);
      opacity:0;transform:translateY(16px) scale(.97);transform-origin:bottom right;
      pointer-events:none;visibility:hidden;
      transition:opacity var(--mm) var(--ease),transform var(--mm) var(--ease),visibility 0s linear var(--mm)}
    .asw-panel.open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;visibility:visible;transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out),visibility 0s}
    .asw-panel.no-anim{transition:none}
    .asw-root.corner-br .asw-panel{transform-origin:bottom right}
    .asw-root.corner-bl .asw-panel{transform-origin:bottom left}
    .asw-root.corner-tr .asw-panel{transform-origin:top right}
    .asw-root.corner-tl .asw-panel{transform-origin:top left}
    .asw-root.corner-tr .asw-panel,.asw-root.corner-tl .asw-panel{transform:translateY(-16px) scale(.97)}
    .asw-root.corner-tr .asw-panel.open,.asw-root.corner-tl .asw-panel.open{transform:translateY(0) scale(1)}

    /* ═══════════════════════════════════════════════════════════════════
       HEADER — stitched leather strap
       ═══════════════════════════════════════════════════════════════════ */
    .asw-header{position:relative;z-index:4;flex:none;display:flex;align-items:center;gap:var(--sp-3);
      padding:var(--sp-4) var(--sp-4);
      background:var(--tex-leather),linear-gradient(180deg,var(--leather),var(--leather-2));
      border-radius:var(--rad) var(--rad) 0 0;
      border-bottom:1px solid rgba(0,0,0,.7);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.16),inset 0 -8px 14px rgba(0,0,0,.34),0 1px 0 rgba(255,255,255,.5);
      color:#f3f1ec}
    /* the stitching */
    .asw-header::after{content:"";position:absolute;left:8px;right:8px;bottom:5px;height:2px;
      background:repeating-linear-gradient(90deg,var(--stitch) 0 6px,transparent 6px 12px);
      border-radius:var(--rad-pill);pointer-events:none}
    .asw-heading{position:relative;display:flex;align-items:center;gap:var(--sp-3);min-width:0;flex:1}
    .asw-avatar-wrap{position:relative;flex:none}
    /* avatar — a chrome-rimmed portrait disc */
    .asw-avatar{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;overflow:hidden;
      background:linear-gradient(180deg,#fbfbfc,#c9ced7);
      color:var(--gel-lo);font-size:var(--t-lg);font-weight:800;
      border:1px solid rgba(0,0,0,.55);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),inset 0 -2px 4px rgba(0,0,0,.22),0 1px 0 rgba(255,255,255,.18);
      text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-avatar img{width:100%;height:100%;border-radius:inherit;object-fit:cover}
    /* status — a lit green LED */
    .asw-status{position:absolute;bottom:-1px;inset-inline-end:-1px;width:12px;height:12px;border-radius:50%;
      background:radial-gradient(circle at 34% 30%,#c4f5c4,var(--online) 52%,#2c7a2c);
      border:1.5px solid rgba(0,0,0,.5);
      box-shadow:0 0 5px rgba(104,195,104,.9),inset 0 1px 0 rgba(255,255,255,.6)}
    .asw-info{min-width:0;flex:1}
    .asw-title-row{display:flex;align-items:center;gap:var(--sp-2);min-width:0}
    /* engraved title */
    .asw-title{font-size:var(--t-lg);font-weight:800;letter-spacing:-.01em;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      color:#f6f4ef;text-shadow:0 -1px 0 rgba(0,0,0,.75),0 1px 0 rgba(255,255,255,.14)}
    .asw-subtitle{font-size:var(--t-xs);font-weight:500;color:#b5b1a8;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      text-shadow:0 -1px 0 rgba(0,0,0,.6)}
    /* brass nameplate chips */
    .asw-ai-chip,.asw-badge{display:inline-flex;align-items:center;gap:var(--sp-1);flex:none;height:19px;padding:0 var(--sp-2);border-radius:var(--rad-sm);
      font-size:9.5px;font-weight:800;letter-spacing:.05em;white-space:nowrap;
      background:linear-gradient(180deg,rgba(255,255,255,.20),rgba(0,0,0,.14));
      border:1px solid rgba(0,0,0,.5);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.24);
      color:#e8e5de;text-shadow:0 -1px 0 rgba(0,0,0,.6)}
    .asw-ai-chip svg{width:10px;height:10px}
    .asw-badge-dot{width:5px;height:5px;border-radius:50%;background:var(--online);box-shadow:0 0 4px var(--online);flex:none}

    /* header keys — small dark metal buttons */
    .asw-actions{position:relative;display:flex;gap:5px;flex:none}
    .asw-header-btn{width:29px;height:29px;border-radius:var(--rad-sm);display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,#66666e,#3c3c43);
      border:1px solid rgba(0,0,0,.62);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.28),inset 0 -2px 3px rgba(0,0,0,.34),0 1px 0 rgba(255,255,255,.12);
      color:#e2dfd8;
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press),background var(--mm) var(--ease)}
    .asw-header-btn:hover{background:linear-gradient(180deg,#75757e,#48484f)}
    .asw-header-btn:active{transform:translateY(1px);box-shadow:inset 0 2px 4px rgba(0,0,0,.55),inset 0 -1px 0 rgba(255,255,255,.14)}
    .asw-header-btn svg{width:15px;height:15px;filter:drop-shadow(0 -1px 0 rgba(0,0,0,.55));transition:transform var(--ml) var(--ease-out)}
    #asw-clear-history:hover svg{transform:rotate(-180deg)}

    /* ═══════════════════════════════════════════════════════════════════
       OFFLINE BANNER — a warning decal
       ═══════════════════════════════════════════════════════════════════ */
    .asw-netstatus{position:relative;z-index:3;flex:none;display:flex;align-items:center;justify-content:center;gap:var(--sp-2);
      padding:var(--sp-2) var(--sp-3);
      background:linear-gradient(180deg,#f6e5b0,#e4cd88);
      border-bottom:1px solid #b09650;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.75),inset 0 -2px 4px rgba(0,0,0,.10);
      color:#6b5416;font-size:var(--t-xs);font-weight:800;text-shadow:0 1px 0 rgba(255,255,255,.65)}
    .asw-netstatus[hidden]{display:none}
    .asw-netstatus svg{width:13px;height:13px;flex:none}

    /* ═══════════════════════════════════════════════════════════════════
       MESSAGES — recessed screen holding lined notepaper
       ═══════════════════════════════════════════════════════════════════ */
    .asw-messages{position:relative;z-index:1;flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;
      padding:var(--sp-5) var(--sp-4) var(--sp-3);
      display:flex;flex-direction:column;gap:var(--sp-4);scroll-behavior:smooth;
      background-color:var(--paper);
      background-image:
        var(--tex-paper),
        repeating-linear-gradient(180deg,transparent 0 27px,var(--paper-line) 27px 28px);
      box-shadow:inset 0 3px 7px rgba(0,0,0,.30),inset 0 -1px 0 rgba(255,255,255,.5);
      scrollbar-width:thin;scrollbar-color:var(--metal-edge) transparent}
    .asw-messages::-webkit-scrollbar{width:11px}
    .asw-messages::-webkit-scrollbar-track{background:linear-gradient(90deg,rgba(0,0,0,.12),rgba(0,0,0,.04));box-shadow:inset 1px 0 2px rgba(0,0,0,.2)}
    .asw-messages::-webkit-scrollbar-thumb{border-radius:var(--rad-pill);border:2px solid transparent;background-clip:padding-box;
      background-color:#a8adb6;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.8),inset 0 -1px 2px rgba(0,0,0,.3)}
    .asw-messages::-webkit-scrollbar-thumb:hover{background-color:#949aa4}

    .asw-row{position:relative;z-index:1;display:flex;flex-wrap:wrap;align-items:flex-end;gap:var(--sp-2);max-width:88%;animation:sk-rise var(--ml) var(--ease-out) both}
    .asw-row.user{align-self:flex-end;flex-direction:row-reverse}
    .asw-row.bot{align-self:flex-start}
    .asw-row.bot + .asw-row.bot,.asw-row.user + .asw-row.user{margin-top:calc(var(--sp-2) * -1)}
    .asw-row.asw-cont .asw-msg-avatar{visibility:hidden}
    .asw-row.no-anim{animation:none}

    .asw-msg-avatar{width:28px;height:28px;flex:0 0 28px;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:800;overflow:hidden;
      border:1px solid rgba(0,0,0,.4);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.8),0 1px 2px rgba(0,0,0,.25)}
    .asw-row.bot .asw-msg-avatar{background:linear-gradient(180deg,#fdfdfe,#cfd4dc);color:var(--gel-lo);text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-row.bot .asw-msg-avatar img{width:100%;height:100%;object-fit:cover}
    .asw-row.user .asw-msg-avatar{background:linear-gradient(180deg,var(--gel-hi),var(--gel-lo));color:#fff;text-shadow:0 -1px 0 rgba(0,0,0,.4)}
    .asw-no-avatar .asw-msg-avatar{display:none}

    /* day divider — an embossed rule on the paper */
    .asw-divider{position:relative;z-index:1;align-self:center;display:flex;align-items:center;gap:var(--sp-3);margin:var(--sp-1) 0;
      color:#8d8574;font-size:10.5px;font-weight:800;letter-spacing:.04em;
      text-shadow:0 1px 0 rgba(255,255,255,.85);animation:sk-fade var(--mm) var(--ease-out) both}
    .asw-divider::before,.asw-divider::after{content:"";width:36px;height:2px;border-radius:var(--rad-pill);
      background:linear-gradient(180deg,rgba(0,0,0,.16) 0 1px,rgba(255,255,255,.85) 1px 2px)}

    /* ── BUBBLES ──
       bot  : ink written straight onto the notepaper
       user : a glossy gel lozenge with a real tail notch */
    .asw-col{max-width:100%;min-width:0}
    .asw-bubble{max-width:100%}
    .asw-bubble img,.asw-bubble video,.asw-bubble iframe{max-width:100%;height:auto}
    .asw-bubble pre{max-width:100%}
    .asw-bubble{padding:var(--sp-3) var(--sp-4);font-size:var(--asw-font-size,13.5px);line-height:1.85;word-break:break-word;white-space:pre-wrap;overflow-wrap:anywhere;position:relative;text-align:start}
    .asw-row.bot .asw-bubble{
      background:linear-gradient(180deg,#fffefa,#f7f3e6);
      color:var(--ink);
      border:1px solid var(--paper-edge);
      border-radius:var(--rad);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 1px 2px rgba(0,0,0,.14),0 3px 6px -2px rgba(0,0,0,.10);
      text-shadow:0 1px 0 rgba(255,255,255,.75)}
    .asw-row.user .asw-bubble{
      background:linear-gradient(180deg,var(--gel-hi) 0%,var(--gel) 46%,var(--gel-lo) 100%);
      color:#fff;
      border:1px solid rgba(0,0,0,.34);
      border-radius:var(--rad);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.62),inset 0 -2px 5px rgba(0,0,0,.22),0 2px 4px rgba(0,0,0,.26);
      text-shadow:0 -1px 0 rgba(0,0,0,.32)}
    /* glass highlight sitting on the top half of the lozenge */
    .asw-row.user .asw-bubble::before{content:"";position:absolute;top:1px;left:2px;right:2px;height:46%;
      border-radius:var(--rad-sm) var(--rad-sm) 50% 50%/var(--rad-sm) var(--rad-sm) 14px 14px;
      background:linear-gradient(180deg,rgba(255,255,255,.44),rgba(255,255,255,.04));pointer-events:none}
    .asw[data-bubble="sharp"] .asw-bubble{border-radius:3px}
    .asw[data-bubble="pill"] .asw-bubble{border-radius:var(--rad-pill);padding:var(--sp-3) var(--sp-5)}
    .asw-bubble.asw-error-bubble{
      background:linear-gradient(180deg,#fdeae8,#f6d2ce);
      border-color:#c98b84;color:#8d2a22;
      text-shadow:0 1px 0 rgba(255,255,255,.6)}

    /* rich text */
    .asw-bubble strong{font-weight:800}
    .asw-bubble em{font-style:italic}
    .asw-bubble a{color:var(--gel-lo);font-weight:700;text-decoration:none;border-bottom:1px solid rgba(31,93,168,.4)}
    .asw-bubble a:hover{border-bottom-color:var(--gel-lo)}
    .asw-row.user .asw-bubble a{color:#fff;border-bottom-color:rgba(255,255,255,.6)}
    .asw-bubble ul,.asw-bubble ol{margin:var(--sp-2) 0 var(--sp-1);padding-inline-start:var(--sp-5)}
    .asw-bubble li{margin:var(--sp-1) 0}
    .asw-bubble li::marker{color:var(--gel)}
    .asw-bubble p{margin:var(--sp-1) 0}
    .asw-bubble p:first-child{margin-top:0}
    .asw-bubble p:last-child{margin-bottom:0}
    .asw-bubble code:not(.asw-code-block code){padding:1px 6px;border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#e9e5d6,#dcd7c4);border:1px solid #c6c0aa;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.7);
      font-family:ui-monospace,Monaco,'Courier New',monospace;font-size:.86em;color:#5c4a2a;white-space:pre-wrap;text-shadow:0 1px 0 rgba(255,255,255,.6)}
    .asw-row.user .asw-bubble code{background:rgba(0,0,0,.22);border-color:rgba(0,0,0,.3);color:#fff;text-shadow:none;box-shadow:none}

    /* tables — an engraved ledger */
    .asw-table-wrap{margin:var(--sp-3) 0;border:1px solid #bdb7a2;border-radius:var(--rad-sm);overflow:hidden;overflow-x:auto;
      background:#fffdf5;box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(0,0,0,.12);direction:rtl}
    .asw-table-wrap table{border-collapse:collapse;width:100%;font-size:var(--t-sm);line-height:1.75}
    .asw-table-wrap th{background:linear-gradient(180deg,#efeadb,#ddd7c3);font-weight:800;text-align:start;padding:var(--sp-2) var(--sp-3);white-space:nowrap;
      color:#4a4536;border-bottom:1px solid #bdb7a2;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-table-wrap td{padding:var(--sp-2) var(--sp-3);border-top:1px solid #e3ddc9;color:var(--ink-2)}
    .asw-table-wrap tbody tr:nth-child(even){background:rgba(0,0,0,.022)}
    .asw-table-wrap th[style*="center"],.asw-table-wrap td[style*="center"]{text-align:center}

    /* code — a CRT terminal inset into the page */
    .asw-code-wrap{position:relative;margin:var(--sp-3) 0;border-radius:var(--rad-sm);overflow:hidden;
      background:#12141a;border:1px solid #05060a;
      box-shadow:inset 0 2px 6px rgba(0,0,0,.85),0 1px 0 rgba(255,255,255,.6);direction:ltr;text-align:left}
    .asw-code-header{display:flex;align-items:center;gap:var(--sp-2);padding:6px var(--sp-3);
      background:linear-gradient(180deg,#42454e,#26282e);border-bottom:1px solid #05060a;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.2)}
    .asw-code-dots{display:flex;gap:5px;flex:none}
    .asw-code-dots span{width:10px;height:10px;border-radius:50%;border:1px solid rgba(0,0,0,.5);box-shadow:inset 0 1px 0 rgba(255,255,255,.55)}
    .asw-code-dots span:nth-child(1){background:radial-gradient(circle at 34% 30%,#ff9a92,#d0463c)}
    .asw-code-dots span:nth-child(2){background:radial-gradient(circle at 34% 30%,#ffe08a,#d9a520)}
    .asw-code-dots span:nth-child(3){background:radial-gradient(circle at 34% 30%,#a8e88e,#3f9c34)}
    .asw-code-lang{font-size:10px;color:#a9b0bd;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-left:var(--sp-1);text-shadow:0 -1px 0 rgba(0,0,0,.6)}
    .asw-code-copy{margin-left:auto;display:inline-flex;align-items:center;gap:5px;height:21px;padding:0 var(--sp-2);
      border-radius:var(--rad-sm);border:1px solid rgba(0,0,0,.6);
      background:linear-gradient(180deg,#5b5f69,#3a3d45);color:#d5d9e2;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.24);
      font-size:10px;font-weight:700;cursor:pointer;font-family:inherit;text-shadow:0 -1px 0 rgba(0,0,0,.55);
      transition:transform var(--ms) var(--ease-press)}
    .asw-code-copy:active{transform:translateY(1px);box-shadow:inset 0 2px 4px rgba(0,0,0,.6)}
    .asw-code-copy.copied{color:#8ce68c}
    .asw-code-copy svg{width:11px;height:11px}
    .asw-code-block{margin:0;padding:var(--sp-3) var(--sp-4);overflow-x:auto;
      font-family:ui-monospace,Monaco,'Courier New',monospace;font-size:var(--t-sm);line-height:1.75;
      color:#9fe89f;text-shadow:0 0 6px rgba(120,240,120,.45);white-space:pre;tab-size:2;background:none}
    .asw-code-block::-webkit-scrollbar{height:8px}
    .asw-code-block::-webkit-scrollbar-thumb{background:#3a3d45;border-radius:var(--rad-pill)}
    .asw-code-block code{font-family:inherit}

    /* timestamp — pencil annotation */
    .asw-time{padding:var(--sp-1) var(--sp-1) 0;font-size:10px;color:#9a9285;font-weight:600;letter-spacing:.02em;
      font-variant-numeric:tabular-nums;text-shadow:0 1px 0 rgba(255,255,255,.7)}
    .asw-row.user .asw-time{text-align:left}

    /* feedback — tiny metal keys */
    .asw-feedback{display:flex;align-items:center;gap:3px;margin-top:var(--sp-2);opacity:0;transition:opacity var(--mm) var(--ease)}
    .asw-row:hover .asw-feedback,.asw-feedback:focus-within,.asw-feedback[data-sent],.asw-row.asw-last .asw-feedback{opacity:1}
    @media(hover:none){.asw-feedback{opacity:.95}}
    .asw-feedback[hidden]{display:none}
    .asw-fb-btn{width:25px;height:25px;border-radius:var(--rad-sm);display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,#fdfdfe,#dfe3ea);
      border:1px solid #a9afb9;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 1px 1px rgba(0,0,0,.16);
      color:#6d727b;
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-fb-btn:hover{background:linear-gradient(180deg,#ffffff,#e8ecf2)}
    .asw-fb-btn:active{transform:translateY(1px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-fb-btn.active{color:var(--gel-lo);box-shadow:inset 0 2px 3px rgba(0,0,0,.26)}
    .asw-fb-btn.active.thumbs-up,.asw-fb-btn.copied{color:var(--asw-success)}
    .asw-fb-btn.active.thumbs-down{color:var(--asw-error)}
    .asw-fb-btn svg{width:13px;height:13px;filter:drop-shadow(0 1px 0 rgba(255,255,255,.7))}

    /* retry — a small red plastic key */
    .asw-retry{display:inline-flex;align-items:center;gap:var(--sp-2);margin-top:var(--sp-3);height:29px;padding:0 var(--sp-4);
      border-radius:var(--rad-sm);border:1px solid #8e2a22;
      background:linear-gradient(180deg,#e2635a,#b03028 52%,#8d221b);
      color:#fff;font-family:inherit;font-size:var(--t-xs);font-weight:800;cursor:pointer;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 2px 0 #6f1a14,0 3px 4px rgba(0,0,0,.3);
      text-shadow:0 -1px 0 rgba(0,0,0,.45);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-retry:active{transform:translateY(2px);box-shadow:inset 0 2px 4px rgba(0,0,0,.5)}
    .asw-retry svg{width:12px;height:12px}

    /* ═══════════════════════════════════════════════════════════════════
       TYPING — a pencil scratching
       ═══════════════════════════════════════════════════════════════════ */
    .asw-typing{position:relative;z-index:1;flex:none;display:flex;align-items:center;gap:var(--sp-2);
      padding:var(--sp-2) var(--sp-4) var(--sp-3);background:var(--paper);
      box-shadow:inset 0 2px 5px rgba(0,0,0,.16)}
    .asw-typing[hidden]{display:none}
    .asw-typing-ava{width:24px;height:24px;flex:none;border-radius:50%;
      background:linear-gradient(180deg,var(--gel-hi),var(--gel-lo));color:#fff;display:grid;place-items:center;
      border:1px solid rgba(0,0,0,.4);box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 1px 2px rgba(0,0,0,.25)}
    .asw-typing-ava svg{width:11px;height:11px}
    .asw-typing-bubble{display:flex;align-items:center;gap:5px;padding:9px var(--sp-3);
      background:linear-gradient(180deg,#fffefa,#f4f0e2);
      border:1px solid var(--paper-edge);border-radius:var(--rad);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(0,0,0,.12)}
    .asw-typing-dot{width:7px;height:7px;border-radius:50%;
      background:radial-gradient(circle at 34% 30%,#b9c2cf,#78818f);
      box-shadow:inset 0 -1px 1px rgba(0,0,0,.3),0 1px 0 rgba(255,255,255,.8);
      animation:sk-bounce 1.1s var(--ease) infinite}
    .asw-typing-dot:nth-child(2){animation-delay:.14s}
    .asw-typing-dot:nth-child(3){animation-delay:.28s}
    .asw-typing-label{font-size:var(--t-xs);font-weight:700;color:#8a8274;margin-inline-start:var(--sp-1);text-shadow:0 1px 0 rgba(255,255,255,.75)}

    /* streaming caret — a blinking ink cursor */
    .asw-bubble.streaming::after{content:"";display:inline-block;width:8px;height:15px;margin-inline-start:2px;
      background:linear-gradient(180deg,#5c636e,#2f343c);border-radius:1px;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.4);vertical-align:-3px;animation:sk-blink 1s steps(2) infinite}

    /* ═══════════════════════════════════════════════════════════════════
       HERO — a title page
       ═══════════════════════════════════════════════════════════════════ */
    .asw-hero{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;text-align:center;gap:var(--sp-4);
      padding:var(--sp-8) var(--sp-4) var(--sp-4);transition:opacity var(--mm) var(--ease),transform var(--mm) var(--ease)}
    .asw-hero>*{animation:sk-rise var(--ml) var(--ease-out) both}
    .asw-hero>*:nth-child(2){animation-delay:60ms}
    .asw-hero>*:nth-child(3){animation-delay:120ms}
    .asw-hero>*:nth-child(4){animation-delay:180ms}
    .asw-hero-out{opacity:0!important;transform:translateY(-10px)!important;pointer-events:none}
    .asw-hero-spot{position:absolute;top:0;left:50%;transform:translateX(-50%);width:250px;height:150px;
      background:radial-gradient(ellipse at center,rgba(255,246,214,.85),transparent 70%);pointer-events:none}
    .asw-hero-orb-wrap{position:relative}
    /* a domed glass medallion */
    .asw-hero-orb{position:relative;width:74px;height:74px;border-radius:50%;
      background:linear-gradient(180deg,var(--gel-hi) 0%,var(--gel) 48%,var(--gel-lo) 100%);
      color:#fff;display:grid;place-items:center;
      border:1px solid rgba(0,0,0,.4);
      box-shadow:inset 0 2px 1px rgba(255,255,255,.85),inset 0 -6px 12px rgba(0,0,0,.3),0 3px 0 #16437c,0 6px 12px rgba(0,0,0,.36);
      text-shadow:0 -1px 0 rgba(0,0,0,.4)}
    .asw-hero-orb::before{content:"";position:absolute;top:4px;left:12%;right:12%;height:40%;
      border-radius:50% 50% 46% 46%/64% 64% 36% 36%;
      background:linear-gradient(180deg,rgba(255,255,255,.8),rgba(255,255,255,.05));pointer-events:none}
    .asw-hero-orb svg{width:31px;height:31px;position:relative;filter:drop-shadow(0 -1px 0 rgba(0,0,0,.35))}
    .asw-hero-orb img{width:100%;height:100%;border-radius:inherit;object-fit:cover}
    .asw-hero-p{position:absolute;border-radius:50%;
      background:radial-gradient(circle at 34% 30%,#fff,var(--gel));
      box-shadow:0 1px 2px rgba(0,0,0,.3)}
    .asw-hero-p.p1{width:9px;height:9px;top:-8px;inset-inline-start:2px;opacity:.7}
    .asw-hero-p.p2{width:6px;height:6px;top:12px;inset-inline-end:-16px;opacity:.5}
    .asw-hero-p.p3{width:5px;height:5px;bottom:-4px;inset-inline-start:-14px;opacity:.55}
    .asw-hero-text{font-size:var(--t-lg);font-weight:700;color:#4c473a;line-height:1.9;max-width:290px;
      text-shadow:0 1px 0 rgba(255,255,255,.9)}

    /* hero prompts — embossed index cards */
    .asw-hero-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-2);width:100%;max-width:344px}
    .asw-hero-grid .asw-suggestion{height:auto;justify-content:flex-start;text-align:start;white-space:normal;
      border-radius:var(--rad-sm);padding:var(--sp-3);line-height:1.6;font-size:var(--t-sm);gap:var(--sp-2)}
    .asw-hero-grid .asw-suggestion span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .asw-card-arrow{margin-inline-start:auto;flex:none;color:var(--gel);opacity:0;transform:translateX(4px);
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out)}
    .asw-card-arrow svg{width:13px;height:13px;display:block}
    .asw-suggestion:hover .asw-card-arrow,.asw-suggestion:focus-visible .asw-card-arrow{opacity:1;transform:translateX(0)}
    @media(max-width:400px){.asw-hero-grid{grid-template-columns:1fr}}

    /* ═══════════════════════════════════════════════════════════════════
       SUGGESTIONS — a felt tray of plastic keys
       ═══════════════════════════════════════════════════════════════════ */
    .asw-suggestions{position:relative;z-index:2;flex:none;display:flex;gap:var(--sp-2);align-items:center;overflow-x:auto;
      padding:var(--sp-3) var(--sp-4);
      background:var(--tex-felt),linear-gradient(180deg,#b9bec7,#a9aeb8);
      border-top:1px solid rgba(255,255,255,.5);
      box-shadow:inset 0 2px 5px rgba(0,0,0,.26);
      scrollbar-width:none;-webkit-overflow-scrolling:touch}
    .asw-suggestions::-webkit-scrollbar{display:none}
    .asw-suggestions[hidden]{display:none}
    .asw-suggestion{display:inline-flex;align-items:center;gap:var(--sp-2);flex:0 0 auto;height:30px;padding:0 var(--sp-3);
      border-radius:var(--rad-sm);
      background:linear-gradient(180deg,var(--key-hi) 0%,var(--key) 52%,var(--key-lo) 100%);
      border:1px solid var(--key-rim);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 3px rgba(0,0,0,.12),0 2px 0 rgba(0,0,0,.24),0 3px 4px rgba(0,0,0,.22);
      color:#41454d;font-family:inherit;font-size:var(--t-sm);font-weight:700;cursor:pointer;white-space:nowrap;text-decoration:none;
      text-shadow:0 1px 0 rgba(255,255,255,.9);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press),background var(--mm) var(--ease)}
    .asw-suggestion:hover{background:linear-gradient(180deg,#fff 0%,#f4f6f9 52%,#d6dbe3 100%)}
    .asw-suggestion:active{transform:translateY(2px);box-shadow:inset 0 2px 4px rgba(0,0,0,.34),inset 0 -1px 0 rgba(255,255,255,.5)}
    .asw-bubble .asw-suggestion{margin-top:var(--sp-2)}

    /* ═══════════════════════════════════════════════════════════════════
       COMPOSER — brushed metal tray with a recessed glass slot
       ═══════════════════════════════════════════════════════════════════ */
    .asw-footer{position:relative;z-index:2;flex:none;
      padding:var(--sp-3) var(--sp-3) calc(var(--sp-3) + env(safe-area-inset-bottom,0px));
      background:var(--tex-brush),linear-gradient(180deg,var(--metal-hi),var(--metal) 40%,var(--metal-lo));
      border-top:1px solid rgba(0,0,0,.34);
      border-radius:0 0 var(--rad) var(--rad);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95)}
    .asw-input-wrap{display:flex;align-items:flex-end;gap:var(--sp-2);padding:5px;padding-inline:var(--sp-4) 5px;
      border:1px solid #8f959f;border-radius:var(--rad-pill);
      background:linear-gradient(180deg,#ececef,#ffffff 22%);
      box-shadow:inset 0 2px 4px rgba(0,0,0,.26),inset 0 -1px 0 rgba(255,255,255,.9),0 1px 0 rgba(255,255,255,.85);
      transition:box-shadow var(--mm) var(--ease)}
    .asw-input-wrap:focus-within{box-shadow:inset 0 2px 4px rgba(0,0,0,.26),0 0 0 3px rgba(61,132,212,.36),0 1px 0 rgba(255,255,255,.85)}
    .asw-input-wrap.asw-listening{box-shadow:inset 0 2px 4px rgba(0,0,0,.26),0 0 0 3px rgba(176,48,40,.34)}
    .asw-input{min-width:0;flex:1;border:0;outline:0;background:none;color:var(--ink);font-family:inherit;
      font-size:var(--asw-font-size,13.5px);line-height:1.65;resize:none;padding:6px 0;max-height:132px;overflow-y:auto;
      scrollbar-width:none;text-shadow:none}
    .asw-input::-webkit-scrollbar{display:none}
    .asw-input::placeholder{color:#a4a8b0}

    .asw-wave{display:flex;align-items:center;gap:2.5px;height:18px;flex:none;padding-inline-end:var(--sp-1)}
    .asw-wave[hidden]{display:none}
    .asw-wave span{width:3px;height:100%;border-radius:var(--rad-pill);
      background:linear-gradient(180deg,#e2635a,#8d221b);box-shadow:inset 0 1px 0 rgba(255,255,255,.4);
      transform-origin:center;animation:sk-wave .9s var(--ease) infinite}
    .asw-wave span:nth-child(1){animation-duration:.82s}
    .asw-wave span:nth-child(2){animation-duration:.66s;animation-delay:.09s}
    .asw-wave span:nth-child(3){animation-duration:1.05s;animation-delay:.05s}
    .asw-wave span:nth-child(4){animation-duration:.74s;animation-delay:.13s}
    .asw-wave span:nth-child(5){animation-duration:.95s;animation-delay:.03s}

    .asw-mic{width:32px;height:32px;flex:none;border-radius:50%;display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,#fdfdfe,#dfe3ea);border:1px solid #a9afb9;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 1px 1px rgba(0,0,0,.16);
      color:#6d727b;transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-mic:active{transform:translateY(1px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-mic[hidden]{display:none}
    .asw-mic svg{width:16px;height:16px;filter:drop-shadow(0 1px 0 rgba(255,255,255,.7))}
    .asw-input-wrap.asw-listening .asw-mic{color:var(--asw-error);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}

    /* send — chrome-rimmed pushbutton */
    .asw-send{width:36px;height:36px;flex:none;border-radius:50%;display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,var(--gel-hi) 0%,var(--gel) 48%,var(--gel-lo) 100%);
      color:#fff;border:1px solid rgba(0,0,0,.38);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.85),inset 0 -3px 5px rgba(0,0,0,.26),0 2px 0 #16437c,0 3px 5px rgba(0,0,0,.3);
      text-shadow:0 -1px 0 rgba(0,0,0,.4);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press),background var(--mm) var(--ease),filter var(--mm) var(--ease)}
    .asw-send::before{content:"";position:absolute;top:2px;left:5px;right:5px;height:40%;
      border-radius:50% 50% 46% 46%/64% 64% 36% 36%;
      background:linear-gradient(180deg,rgba(255,255,255,.7),rgba(255,255,255,.04));pointer-events:none}
    .asw-send:active{transform:translateY(2px);box-shadow:inset 0 2px 5px rgba(0,0,0,.5)}
    .asw-send:disabled{cursor:default;filter:grayscale(1);opacity:.55;transform:none;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 1px 0 rgba(0,0,0,.2)}
    .asw-send svg{width:16px;height:16px;position:relative;filter:drop-shadow(0 -1px 0 rgba(0,0,0,.35))}
    .asw-send.asw-stop{background:linear-gradient(180deg,#e2635a,#b03028 50%,#8d221b);box-shadow:inset 0 1px 0 rgba(255,255,255,.5),inset 0 -3px 5px rgba(0,0,0,.26),0 2px 0 #6f1a14,0 3px 5px rgba(0,0,0,.3)}

    .asw-scrollbtn{position:absolute;top:-44px;inset-inline-end:var(--sp-4);z-index:5;width:32px;height:32px;border-radius:50%;
      display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,#fdfdfe,#d5dae2);border:1px solid #949aa4;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 2px 4px rgba(0,0,0,.3);
      color:#5b616b;opacity:0;transform:translateY(5px);pointer-events:none;
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out)}
    .asw-scrollbtn.show{opacity:1;transform:translateY(0);pointer-events:auto}
    .asw-scrollbtn:active{transform:translateY(1px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-scrollbtn svg{width:14px;height:14px;filter:drop-shadow(0 1px 0 rgba(255,255,255,.7))}

    .asw-foot-meta{display:flex;flex-direction:column;align-items:center;gap:1px;padding-top:var(--sp-2)}
    .asw-disclaim{font-size:9.5px;color:#6f747d;text-align:center;line-height:1.6;text-shadow:0 1px 0 rgba(255,255,255,.85)}
    .asw-powered{text-align:center;font-size:10px;color:#6f747d;font-weight:600;text-shadow:0 1px 0 rgba(255,255,255,.85)}
    .asw-powered[hidden]{display:none}
    .asw-powered a{color:var(--gel-lo);text-decoration:none;font-weight:800}
    .asw-powered a:hover{text-decoration:underline}
    .asw-resource-links{display:inline-flex;gap:var(--sp-2);margin-inline-start:var(--sp-2)}

    /* ═══════════════════════════════════════════════════════════════════
       TOAST — an engraved plaque
       ═══════════════════════════════════════════════════════════════════ */
    .asw-toast{position:absolute;top:var(--sp-3);left:var(--sp-4);right:var(--sp-4);z-index:50;
      display:flex;align-items:center;justify-content:center;gap:var(--sp-2);
      padding:var(--sp-3) var(--sp-4);border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#55555d,#2f2f36);color:#f2f0ea;
      font-size:var(--t-sm);font-weight:700;line-height:1.6;text-align:center;
      border:1px solid rgba(0,0,0,.6);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 5px 12px rgba(0,0,0,.45);
      text-shadow:0 -1px 0 rgba(0,0,0,.6);
      opacity:0;transform:translateY(-8px);
      transition:opacity var(--mm) var(--ease),transform var(--ml) var(--ease-out);pointer-events:none}
    .asw-toast.show{opacity:1;transform:translateY(0)}
    .asw-toast svg{width:14px;height:14px;flex:none;color:#ffd479}

    /* ═══════════════════════════════════════════════════════════════════
       CITATIONS — paper tabs
       ═══════════════════════════════════════════════════════════════════ */
    .asw-citations{display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2);margin-top:var(--sp-3);padding-top:var(--sp-3);
      border-top:1px dashed #c9c2ac}
    .asw-citations-label{font-size:10px;font-weight:800;color:#8d8574;letter-spacing:.02em;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-citation{display:inline-flex;align-items:center;gap:5px;height:23px;font-size:var(--t-xs);font-weight:700;
      color:#5c5340;background:linear-gradient(180deg,#f7f2df,#e9e2c9);
      border:1px solid #cbc3aa;padding:0 var(--sp-2);border-radius:var(--rad-sm);text-decoration:none;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 1px 1px rgba(0,0,0,.12);
      text-shadow:0 1px 0 rgba(255,255,255,.7);
      max-width:170px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      transition:transform var(--ms) var(--ease-press)}
    .asw-citation:hover{transform:translateY(-1px)}
    .asw-citation svg{width:10px;height:10px;flex:none}

    /* ═══════════════════════════════════════════════════════════════════
       HANDOFF — a taped notice
       ═══════════════════════════════════════════════════════════════════ */
    .asw-handoff{flex:1 1 100%;display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2);margin-top:var(--sp-1);
      padding:var(--sp-3);border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#fdfbef,#f2ecd8);
      border:1px solid #d3cbb2;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(0,0,0,.12);
      animation:sk-fade var(--mm) var(--ease-out) both}
    .asw-handoff-label{width:100%;font-size:var(--t-sm);line-height:1.75;color:#5f5847;font-weight:600;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-handoff-btn{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 var(--sp-3);
      border-radius:var(--rad-sm);
      background:linear-gradient(180deg,var(--key-hi),var(--key) 52%,var(--key-lo));
      border:1px solid var(--key-rim);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 2px 0 rgba(0,0,0,.2),0 2px 3px rgba(0,0,0,.18);
      color:#41454d;font-family:inherit;font-size:var(--t-xs);font-weight:800;cursor:pointer;text-decoration:none;
      text-shadow:0 1px 0 rgba(255,255,255,.9);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-handoff-btn:active{transform:translateY(2px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-handoff-btn svg{width:12px;height:12px}
    .asw-messages:not(.asw-no-avatar) .asw-row > .asw-handoff,
    .asw-messages:not(.asw-no-avatar) .asw-row > .asw-leadform{margin-inline-start:36px}

    .asw-rule-hint{margin-top:var(--sp-2);padding:var(--sp-2) var(--sp-3);
      background:linear-gradient(180deg,#f4efdd,#e9e2ca);border:1px solid #d3cbb2;border-radius:var(--rad-sm);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.85);
      font-size:var(--t-sm);line-height:1.75;color:#5f5847;text-shadow:0 1px 0 rgba(255,255,255,.75)}
    .asw-messages > .asw-rule-hint{align-self:center;margin:0;padding:5px var(--sp-3);border-radius:var(--rad-pill);
      font-size:var(--t-xs);color:#8d8574;animation:sk-fade var(--mm) both}

    /* ═══════════════════════════════════════════════════════════════════
       SHEET — a drawer sliding out of the device
       ═══════════════════════════════════════════════════════════════════ */
    .asw-sheet{position:absolute;inset:0;z-index:40;display:flex;align-items:flex-end;opacity:0;pointer-events:none;
      transition:opacity var(--mm) var(--ease)}
    .asw-sheet::before{content:"";position:absolute;inset:0;background:rgba(10,10,14,.55)}
    .asw-sheet.open{opacity:1;pointer-events:auto}
    .asw-sheet[hidden]{display:none}
    .asw-sheet-card{position:relative;width:100%;max-height:92%;overflow-y:auto;overscroll-behavior:contain;
      background:var(--tex-brush),linear-gradient(180deg,var(--metal-hi),var(--metal) 14%,var(--metal-lo));
      border-radius:var(--rad-lg) var(--rad-lg) 0 0;
      border-top:1px solid rgba(255,255,255,.95);
      box-shadow:0 -6px 18px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.95);
      padding:var(--sp-3) var(--sp-5) calc(var(--sp-5) + env(safe-area-inset-bottom,0px));
      transform:translateY(100%);transition:transform var(--ml) var(--ease-out);scrollbar-width:thin}
    .asw-sheet.open .asw-sheet-card{transform:translateY(0)}
    /* a real machined grab handle */
    .asw-sheet-grip{width:44px;height:6px;border-radius:var(--rad-pill);margin:2px auto var(--sp-4);
      background:linear-gradient(180deg,#9aa0aa,#c8cdd5);
      box-shadow:inset 0 1px 1px rgba(0,0,0,.4),0 1px 0 rgba(255,255,255,.9)}
    .asw-sheet-close{position:absolute;top:var(--sp-3);inset-inline-end:var(--sp-4);width:28px;height:28px;border-radius:50%;
      display:grid;place-items:center;cursor:pointer;
      background:linear-gradient(180deg,#fdfdfe,#d5dae2);border:1px solid #949aa4;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 1px 2px rgba(0,0,0,.22);color:#5b616b;
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-sheet-close:active{transform:translateY(1px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-sheet-close svg{width:13px;height:13px}
    .asw-sheet-title{font-size:var(--t-xl);font-weight:800;color:#3a3e46;letter-spacing:-.01em;line-height:1.4;
      text-shadow:0 1px 0 rgba(255,255,255,.95)}
    .asw-sheet-desc{font-size:var(--t-sm);color:#5f646d;line-height:1.8;margin:var(--sp-1) 0 var(--sp-4);
      text-shadow:0 1px 0 rgba(255,255,255,.85)}

    /* channel cards — embossed plates */
    .asw-chans{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-2);margin-bottom:var(--sp-4)}
    @media(max-width:360px){.asw-chans{grid-template-columns:1fr}}
    .asw-chan{position:relative;display:flex;align-items:center;gap:var(--sp-3);padding:var(--sp-3);
      border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#fdfdfe,#e2e6ec);
      border:1px solid #a5abb5;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.98),0 2px 0 rgba(0,0,0,.16),0 3px 5px rgba(0,0,0,.18);
      text-decoration:none;
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-chan:active{transform:translateY(2px);box-shadow:inset 0 2px 4px rgba(0,0,0,.28)}
    .asw-chan-ic{width:34px;height:34px;flex:none;border-radius:var(--rad-sm);display:grid;place-items:center;
      color:#fff;background:linear-gradient(180deg,color-mix(in srgb,var(--chan,var(--gel)) 72%,#fff),var(--chan,var(--gel)));
      border:1px solid rgba(0,0,0,.34);
      box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 1px 2px rgba(0,0,0,.25)}
    .asw-chan-ic svg{width:16px;height:16px;filter:drop-shadow(0 -1px 0 rgba(0,0,0,.3))}
    .asw-chan-tx{min-width:0;display:flex;flex-direction:column}
    .asw-chan-tx b{font-size:var(--t-sm);font-weight:800;color:#3f434b;text-shadow:0 1px 0 rgba(255,255,255,.9)}
    .asw-chan-tx i{font-style:normal;font-size:10px;color:#787d86;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      direction:ltr;text-align:end;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-chan-more{width:100%;justify-content:center;margin-top:2px}

    /* ═══════════════════════════════════════════════════════════════════
       FORM — recessed glass fields on the metal drawer
       ═══════════════════════════════════════════════════════════════════ */
    .asw-form{text-align:start}
    .asw-field{margin-bottom:var(--sp-3)}
    .asw-field-row{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-3)}
    @media(max-width:340px){.asw-field-row{grid-template-columns:1fr}}
    .asw-flabel{display:flex;align-items:center;gap:var(--sp-1);font-size:var(--t-xs);font-weight:800;color:#4e535b;
      margin-bottom:5px;text-shadow:0 1px 0 rgba(255,255,255,.9)}
    .asw-flabel b{color:var(--asw-error);font-weight:900}
    .asw-form input,.asw-form textarea{width:100%;font-family:inherit;font-size:var(--t-md);color:var(--ink);
      padding:10px var(--sp-3);border-radius:var(--rad-sm);
      border:1px solid #8f959f;background:linear-gradient(180deg,#ececef,#fff 20%);
      box-shadow:inset 0 2px 4px rgba(0,0,0,.24),inset 0 -1px 0 rgba(255,255,255,.9),0 1px 0 rgba(255,255,255,.85);
      outline:none;text-shadow:none;transition:box-shadow var(--mm) var(--ease)}
    .asw-form textarea{resize:vertical;min-height:64px;max-height:150px;line-height:1.7}
    .asw-form input::placeholder,.asw-form textarea::placeholder{color:#a4a8b0}
    .asw-form input:focus,.asw-form textarea:focus{box-shadow:inset 0 2px 4px rgba(0,0,0,.24),0 0 0 3px rgba(61,132,212,.34)}
    .asw-field.invalid input,.asw-field.invalid textarea{border-color:#a8392f;box-shadow:inset 0 2px 4px rgba(0,0,0,.24),0 0 0 3px rgba(176,48,40,.3)}
    .asw-field.ok input{border-color:#5c9a68}
    .asw-ferr{display:none;font-size:10.5px;font-weight:800;color:var(--asw-error);margin-top:4px;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-field.invalid .asw-ferr{display:block}

    /* submit — a big glossy pill button */
    .asw-form-submit{width:100%;display:inline-flex;align-items:center;justify-content:center;gap:var(--sp-2);
      margin-top:var(--sp-2);height:44px;padding:0 var(--sp-6);
      border-radius:var(--rad-pill);border:1px solid rgba(0,0,0,.38);
      background:linear-gradient(180deg,var(--gel-hi) 0%,var(--gel) 48%,var(--gel-lo) 100%);
      color:#fff;font-family:inherit;font-size:var(--t-md);font-weight:800;cursor:pointer;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.8),inset 0 -3px 6px rgba(0,0,0,.24),0 3px 0 #16437c,0 5px 8px rgba(0,0,0,.3);
      text-shadow:0 -1px 0 rgba(0,0,0,.42);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press),filter var(--mm) var(--ease)}
    .asw-form-submit::before{content:"";position:absolute;top:2px;left:6px;right:6px;height:42%;border-radius:var(--rad-pill);
      background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.03));pointer-events:none}
    .asw-form-submit:active{transform:translateY(3px);box-shadow:inset 0 2px 6px rgba(0,0,0,.5)}
    .asw-form-submit:disabled{filter:grayscale(.85);opacity:.6;cursor:default;transform:none;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.5),0 2px 0 rgba(0,0,0,.2)}
    .asw-form-submit svg{width:15px;height:15px;position:relative}
    .asw-form-submit span{position:relative}
    .asw-spinner{width:15px;height:15px;flex:none;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;
      border-radius:50%;animation:sk-spin .7s linear infinite;position:relative}
    .asw-form-note{display:flex;align-items:center;justify-content:center;gap:5px;font-size:10px;color:#6f747d;
      text-align:center;margin-top:var(--sp-3);line-height:1.7;text-shadow:0 1px 0 rgba(255,255,255,.85)}
    .asw-form-note svg{width:11px;height:11px;flex:none}
    .asw-form-err{display:none;font-size:var(--t-xs);font-weight:800;color:var(--asw-error);margin-top:var(--sp-2);text-align:center}
    .asw-form-err.show{display:block}

    .asw-form-success{display:flex;flex-direction:column;align-items:center;text-align:center;gap:var(--sp-2);
      padding:var(--sp-5) var(--sp-2) var(--sp-3);animation:sk-fade var(--mm) var(--ease-out) both}
    .asw-checkmark{width:58px;height:58px;stroke:var(--asw-success);stroke-width:3;fill:none;stroke-linecap:round;stroke-linejoin:round;
      filter:drop-shadow(0 2px 2px rgba(0,0,0,.28))}
    .asw-checkmark circle{stroke-dasharray:170;stroke-dashoffset:170;animation:sk-draw 700ms var(--ease-out) 80ms forwards}
    .asw-checkmark path{stroke-dasharray:44;stroke-dashoffset:44;animation:sk-draw 400ms var(--ease-out) 640ms forwards}
    .asw-fs-title{font-size:var(--t-lg);font-weight:800;color:#3a3e46;margin-top:var(--sp-1);text-shadow:0 1px 0 rgba(255,255,255,.9)}
    .asw-fs-desc{font-size:var(--t-sm);color:#5f646d;line-height:1.85;max-width:262px;text-shadow:0 1px 0 rgba(255,255,255,.8)}
    .asw-fs-close{margin-top:var(--sp-3);height:34px;padding:0 var(--sp-6);border-radius:var(--rad-sm);
      background:linear-gradient(180deg,var(--key-hi),var(--key) 52%,var(--key-lo));
      border:1px solid var(--key-rim);color:#41454d;font-family:inherit;font-size:var(--t-sm);font-weight:800;cursor:pointer;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 2px 0 rgba(0,0,0,.2),0 3px 4px rgba(0,0,0,.18);
      text-shadow:0 1px 0 rgba(255,255,255,.9);
      transition:transform var(--ms) var(--ease-press),box-shadow var(--ms) var(--ease-press)}
    .asw-fs-close:active{transform:translateY(2px);box-shadow:inset 0 2px 3px rgba(0,0,0,.3)}
    .asw-leadform-wrap{animation:sk-fade var(--mm) var(--ease-out) both}
    .asw-leadform{position:relative;flex:1 1 100%;margin:var(--sp-1) 0;padding:var(--sp-4);border-radius:var(--rad-sm);
      background:linear-gradient(180deg,#fdfbef,#f0ead6);border:1px solid #d3cbb2;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(0,0,0,.12);
      animation:sk-fade var(--mm) var(--ease-out) both}

    /* ═══════════════════════════════════════════════════════════════════
       MOTION
       ═══════════════════════════════════════════════════════════════════ */
    @keyframes sk-fade{from{opacity:0}to{opacity:1}}
    @keyframes sk-rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
    @keyframes sk-drop{0%{opacity:0;transform:translateY(-18px) scale(.9)}60%{transform:translateY(2px) scale(1.02)}100%{opacity:1;transform:translateY(0) scale(1)}}
    @keyframes sk-spin{to{transform:rotate(360deg)}}
    @keyframes sk-pop{from{transform:scale(.4)}to{transform:scale(1)}}
    @keyframes sk-ping{0%{transform:scale(1);opacity:.55}70%,100%{transform:scale(1.3);opacity:0}}
    @keyframes sk-bounce{0%,100%{transform:translateY(0);opacity:.45}50%{transform:translateY(-4px);opacity:1}}
    @keyframes sk-blink{50%{opacity:0}}
    @keyframes sk-draw{to{stroke-dashoffset:0}}
    @keyframes sk-wave{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}

    /* ═══════════════════════════════════════════════════════════════════
       RESPONSIVE / PREFERENCES / A11Y
       ═══════════════════════════════════════════════════════════════════ */
    @media(max-width:480px){
      .asw-fab{width:56px;height:56px}
      .asw-panel{width:min(var(--asw-panel-w),calc(100vw - var(--sp-6)));height:min(var(--asw-panel-h),calc(100dvh - 84px))}
      .asw-root.mobile-fullscreen .asw-panel{position:fixed!important;inset:0!important;width:100vw!important;max-width:none!important;
        height:100vh!important;height:100dvh!important;max-height:none!important;border-radius:0!important;padding:0!important;
        border:none!important;transform:translateY(20px)!important}
      .asw-root.mobile-fullscreen .asw-panel.open{transform:translateY(0)!important}
      .asw-root.mobile-fullscreen .asw-header{border-radius:0}
      .asw-root.mobile-fullscreen .asw-footer{border-radius:0}
      .asw-root.mobile-fullscreen .asw-fab{display:none!important}
      .asw-root.mobile-fullscreen .asw-glow{display:none}
      .asw-root.mobile-fullscreen .asw-sheet-card{border-radius:0}
      .asw-row{max-width:93%}
    }
    @media(prefers-reduced-motion:reduce){
      .asw-panel,.asw-fab,.asw-suggestion,.asw-teaser,.asw-scrollbtn,.asw-toast,.asw-glow,.asw-fab-label,.asw-sheet,.asw-sheet-card,.asw-chan,.asw-send{transition:none}
      .asw-typing-dot,.asw-fab-pulse,.asw-wave span,.asw-spinner{animation:none}
      .asw-row,.asw-hero,.asw-hero>*,.asw-handoff,.asw-leadform,.asw-leadform-wrap,.asw-divider,.asw-form-success,.asw-fab{animation:none;opacity:1;transform:none}
      .asw-checkmark circle,.asw-checkmark path{stroke-dashoffset:0;animation:none}
    }

    .asw[data-font="small"]{--asw-font-size:12px}
    .asw[data-font="large"]{--asw-font-size:15.5px}

    .asw[data-anim="off"] *,.asw[data-anim="off"] *::before,.asw[data-anim="off"] *::after{animation:none!important;transition:none!important}

    .asw :focus-visible{outline:2px solid var(--gel);outline-offset:2px}
    .asw ::selection{background:rgba(61,132,212,.3)}
    .asw-sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
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
