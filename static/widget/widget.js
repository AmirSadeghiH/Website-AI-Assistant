/**
 * AI Support Widget v3.0 — Professional Chat Widget
 * Features: Shadow DOM, auto-grow textarea, dark/light themes,
 *           spring animations, code blocks, dynamic icons,
 *           rigid 4-corner positioning with custom offsets,
 *           inline feedback (thumbs up/down) on bot messages,
 *           full CSS variable system.
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
    copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    thumbUp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>',
    thumbDown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>',
    thumbUpFilled: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>',
    thumbDownFilled: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>',
  };

  /* ─────────────── CSS (BEM) ─────────────── */
  var CSS = `
    :host{all:initial;--asw-font:'Vazirmatn','Inter',ui-sans-serif,system-ui,sans-serif}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    .asw{font-family:var(--asw-font);font-size:var(--asw-font-size,14px);direction:rtl;line-height:1.6;color:var(--asw-text);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}

    /* ─── CSS Variable System ─── */
    .asw{--asw-primary:#6366f1;--asw-secondary:#8b5cf6;--asw-accent:#a78bfa;--asw-bg:#ffffff;--asw-surface:#f8fafc;--asw-surface-2:#f1f5f9;--asw-text:#0f172a;--asw-text-secondary:#64748b;--asw-text-muted:#94a3b8;--asw-border:#e2e8f0;--asw-border-focus:#6366f1;--asw-shadow:0 25px 60px rgba(15,23,42,.12);--asw-radius:24px;--asw-radius-sm:12px;--asw-radius-xs:8px;--asw-panel-w:400px;--asw-panel-h:640px;--asw-header-bg:linear-gradient(135deg,var(--asw-primary),var(--asw-secondary));--asw-user-bg:var(--asw-primary);--asw-user-text:#fff;--asw-bot-bg:#fff;--asw-bot-text:#0f172a;--asw-input-bg:#f1f5f9;--asw-input-focus-bg:#fff;--asw-typing-dot:var(--asw-text-muted);--asw-suggestion-bg:#fff;--asw-suggestion-border:var(--asw-border);--asw-suggestion-text:var(--asw-text);--asw-suggestion-active:var(--asw-primary);--asw-success:#10b981;--asw-error:#ef4444;--asw-warning:#f59e0b}

    /* Dark mode */
    .asw.dark{--asw-bg:#0f172a;--asw-surface:#1e293b;--asw-surface-2:#334155;--asw-text:#f1f5f9;--asw-text-secondary:#94a3b8;--asw-text-muted:#64748b;--asw-border:#334155;--asw-border-focus:#818cf8;--asw-shadow:0 25px 60px rgba(0,0,0,.4);--asw-bot-bg:#1e293b;--asw-bot-text:#f1f5f9;--asw-input-bg:#1e293b;--asw-input-focus-bg:#0f172a;--asw-typing-dot:#64748b;--asw-suggestion-bg:#1e293b;--asw-suggestion-border:#334155;--asw-suggestion-text:#f1f5f9}

    /* ─── Root Container ─── */
    .asw-root{position:fixed;z-index:2147483647;width:0;height:0;pointer-events:none}
    .asw-root>*{pointer-events:auto}
    .asw-root *{box-sizing:border-box}

    /* ─── FAB (Floating Action Button) — anchored to extreme corner ─── */
    .asw-fab{width:60px;height:60px;border:none;border-radius:50%;background:var(--asw-header-bg);color:#fff;display:grid;place-items:center;cursor:pointer;box-shadow:0 8px 32px rgba(99,102,241,.4);transition:transform .3s cubic-bezier(.34,1.56,.64,1),box-shadow .3s ease;position:fixed;overflow:hidden}
    .asw-fab::before{content:'';position:absolute;inset:0;background:rgba(255,255,255,.15);border-radius:inherit;opacity:0;transition:opacity .3s}
    .asw-fab:hover{transform:scale(1.08);box-shadow:0 12px 40px rgba(99,102,241,.5)}
    .asw-fab:hover::before{opacity:1}
    .asw-fab:active{transform:scale(.95)}
    .asw-fab svg{width:26px;height:26px;transition:transform .3s cubic-bezier(.34,1.56,.64,1)}
    .asw-fab .asw-fab-icon-main{display:block}
    .asw-fab .asw-fab-icon-close{display:none}
    .asw-fab.active .asw-fab-icon-main{display:none}
    .asw-fab.active .asw-fab-icon-close{display:block}
    .asw-fab.active svg{transform:rotate(90deg)}
    .asw-fab-custom-icon{width:28px;height:28px;border-radius:6px;object-fit:contain}
    .asw-fab-pulse{position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--asw-primary);opacity:0;animation:asw-pulse-ring 2s ease-out infinite}
    @keyframes asw-pulse-ring{0%{transform:scale(.8);opacity:.6}100%{transform:scale(1.4);opacity:0}}

    /* ─── Panel — fixed, positioned adjacent to FAB ─── */
    .asw-panel{width:var(--asw-panel-w);height:var(--asw-panel-h);max-width:calc(100vw - 24px);max-height:calc(100dvh - 100px);display:flex;flex-direction:column;overflow:hidden;background:var(--asw-bg);border-radius:var(--asw-radius);box-shadow:var(--asw-shadow);border:1px solid var(--asw-border);opacity:0;pointer-events:none;position:fixed;transition:opacity .35s cubic-bezier(.16,1,.3,1),transform .4s cubic-bezier(.16,1,.3,1)}
    .asw-panel.open{opacity:1;pointer-events:auto;transform:translateY(0) scale(1)}
    .asw-panel.no-anim{transition:none}
    /* Panel transform origins per corner */
    .asw-root.corner-br .asw-panel{transform-origin:bottom right}
    .asw-root.corner-bl .asw-panel{transform-origin:bottom left}
    .asw-root.corner-tr .asw-panel{transform-origin:top right}
    .asw-root.corner-tl .asw-panel{transform-origin:top left}
    /* Top corners: panel opens downward */
    .asw-root.corner-tr .asw-panel,.asw-root.corner-tl .asw-panel{transform:translateY(-20px) scale(.95)}
    .asw-root.corner-tr .asw-panel.open,.asw-root.corner-tl .asw-panel.open{transform:translateY(0) scale(1)}

    /* ─── Header ─── */
    .asw-header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;background:var(--asw-header-bg);color:#fff;position:relative;overflow:hidden;flex-shrink:0}
    .asw-header::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.2),transparent)}
    .asw-heading{display:flex;align-items:center;gap:12px;min-width:0;flex:1}
    .asw-avatar{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:rgba(255,255,255,.2);backdrop-filter:blur(10px);color:#fff;font-size:18px;font-weight:700;flex-shrink:0;border:2px solid rgba(255,255,255,.25);transition:transform .3s}
    .asw-avatar img{width:100%;height:100%;border-radius:inherit;object-fit:cover}
    .asw-info{min-width:0;flex:1}
    .asw-title-row{display:flex;align-items:center;gap:8px}
    .asw-title{font-size:15px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#fff}
    .asw-badge{padding:3px 8px;border-radius:999px;background:rgba(255,255,255,.2);backdrop-filter:blur(8px);font-size:10px;font-weight:600;letter-spacing:.05em;color:#fff;white-space:nowrap;display:flex;align-items:center;gap:4px}
    .asw-badge-dot{width:6px;height:6px;border-radius:50%;background:#34d399;animation:asw-dot-pulse 2s ease-in-out infinite}
    @keyframes asw-dot-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
    .asw-subtitle{font-size:12px;color:rgba(255,255,255,.85);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

    /* Header Actions */
    .asw-actions{display:flex;gap:6px}
    .asw-header-btn{width:32px;height:32px;border:1px solid rgba(255,255,255,.2);border-radius:10px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:#fff;display:grid;place-items:center;cursor:pointer;transition:all .2s}
    .asw-header-btn:hover{background:rgba(255,255,255,.25);transform:scale(1.05)}
    .asw-header-btn:active{transform:scale(.95)}
    .asw-header-btn svg{width:16px;height:16px}

    /* ─── Messages ─── */
    .asw-messages{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:20px 16px 12px;display:flex;flex-direction:column;gap:16px;scroll-behavior:smooth;scrollbar-width:thin;scrollbar-color:var(--asw-border) transparent}
    .asw-messages::-webkit-scrollbar{width:5px}
    .asw-messages::-webkit-scrollbar-track{background:transparent}
    .asw-messages::-webkit-scrollbar-thumb{background:var(--asw-border);border-radius:10px}

    /* Message Row */
    .asw-row{display:flex;align-items:flex-end;gap:10px;max-width:90%;opacity:0;transform:translateY(12px);animation:asw-msg-in .4s cubic-bezier(.16,1,.3,1) forwards}
    .asw-row.user{align-self:flex-end;flex-direction:row-reverse}
    .asw-row.bot{align-self:flex-start}
    @keyframes asw-msg-in{to{opacity:1;transform:translateY(0)}}
    .asw-row.no-anim{animation:none;opacity:1;transform:none}

    /* Message Avatar */
    .asw-msg-avatar{width:30px;height:30px;flex:0 0 30px;border-radius:10px;display:grid;place-items:center;font-size:11px;font-weight:700;transition:transform .2s}
    .asw-row.bot .asw-msg-avatar{background:var(--asw-surface);border:1px solid var(--asw-border);color:var(--asw-primary)}
    .asw-row.user .asw-msg-avatar{background:var(--asw-primary);color:#fff}
    .asw-row .asw-msg-avatar:hover{transform:scale(1.1)}
    .asw-no-avatar .asw-msg-avatar{display:none}

    /* Message Bubble */
    .asw-col{max-width:100%;min-width:0}
    .asw-bubble{padding:12px 16px;font-size:var(--asw-font-size,14px);line-height:1.7;word-break:break-word;white-space:pre-wrap;max-width:100%;overflow-wrap:break-word;position:relative}
    .asw-row.bot .asw-bubble{background:var(--asw-bot-bg);color:var(--asw-bot-text);border:1px solid var(--asw-border);box-shadow:0 2px 12px rgba(0,0,0,.04)}
    .asw-row.user .asw-bubble{background:var(--asw-user-bg);color:var(--asw-user-text);box-shadow:0 4px 16px rgba(99,102,241,.25)}

    /* Bubble Styles */
    .asw[data-bubble="rounded"] .asw-bubble{border-radius:18px 18px 18px 6px}
    .asw[data-bubble="rounded"] .asw-row.user .asw-bubble{border-radius:18px 18px 6px 18px}
    .asw[data-bubble="sharp"] .asw-bubble{border-radius:4px}
    .asw[data-bubble="pill"] .asw-bubble{border-radius:24px;padding:10px 18px}

    /* Bubble Content */
    .asw-bubble strong{font-weight:700}
    .asw-bubble em{font-style:italic}
    .asw-bubble a{color:var(--asw-primary);font-weight:600;text-decoration:none;border-bottom:1px solid transparent;transition:border-color .2s}
    .asw-row.bot .asw-bubble a:hover{border-bottom-color:var(--asw-primary)}
    .asw-bubble ul,.asw-bubble ol{margin:8px 0 4px;padding-inline-start:20px}
    .asw-bubble li{margin:4px 0}
    .asw-bubble p{margin:4px 0}
    .asw-bubble p:first-child{margin-top:0}
    .asw-bubble p:last-child{margin-bottom:0}

    /* Code Blocks */
    .asw-code-wrap{position:relative;margin:8px 0;border-radius:var(--asw-radius-xs);overflow:hidden;background:#1e293b;border:1px solid #334155}
    .asw-code-header{display:flex;align-items:center;justify-content:space-between;padding:6px 12px;background:#0f172a;border-bottom:1px solid #334155}
    .asw-code-lang{font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
    .asw-code-copy{display:flex;align-items:center;gap:4px;padding:3px 8px;border:none;border-radius:6px;background:rgba(255,255,255,.08);color:#94a3b8;font-size:11px;cursor:pointer;transition:all .2s;font-family:inherit}
    .asw-code-copy:hover{background:rgba(255,255,255,.15);color:#e2e8f0}
    .asw-code-copy.copied{color:var(--asw-success)}
    .asw-code-copy svg{width:12px;height:12px}
    .asw-code-block{padding:14px 16px;overflow-x:auto;font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:12.5px;line-height:1.6;color:#e2e8f0;white-space:pre;tab-size:2}
    .asw-code-block code{font-family:inherit}

    /* Inline Code */
    .asw-bubble code:not(.asw-code-block code){padding:2px 6px;border-radius:4px;background:var(--asw-surface-2);font-family:'JetBrains Mono','Fira Code',monospace;font-size:.88em;color:var(--asw-primary);border:1px solid var(--asw-border)}

    /* Timestamp */
    .asw-time{padding:4px 4px 0;font-size:10.5px;color:var(--asw-text-muted);font-weight:500;letter-spacing:.02em}
    .asw-row.user .asw-time{text-align:right}

    /* ─── Feedback (thumbs up/down) ─── */
    .asw-feedback{display:flex;gap:2px;margin-top:6px;opacity:0;transition:opacity .2s}
    .asw-row:hover .asw-feedback{opacity:1}
    .asw-feedback[hidden]{display:none}
    .asw-fb-btn{width:28px;height:28px;border:none;border-radius:6px;background:transparent;color:var(--asw-text-muted);cursor:pointer;display:grid;place-items:center;transition:all .2s}
    .asw-fb-btn:hover{background:var(--asw-surface-2);color:var(--asw-primary)}
    .asw-fb-btn.active{color:var(--asw-primary)}
    .asw-fb-btn.active.thumbs-up{color:var(--asw-success)}
    .asw-fb-btn.active.thumbs-down{color:var(--asw-error)}
    .asw-fb-btn svg{width:14px;height:14px}

    /* ─── Typing Indicator ─── */
    .asw-typing{padding:4px 16px 12px;display:flex;align-items:center;gap:8px}
    .asw-typing[hidden]{display:none}
    .asw-typing-label{font-size:12px;color:var(--asw-text-muted);font-weight:500}
    .asw-typing-dots{display:flex;gap:4px;align-items:center}
    .asw-typing-dot{width:7px;height:7px;border-radius:50%;background:var(--asw-primary);animation:asw-bounce .6s ease-in-out infinite}
    .asw-typing-dot:nth-child(2){animation-delay:.15s}
    .asw-typing-dot:nth-child(3){animation-delay:.3s}
    @keyframes asw-bounce{0%,100%{transform:translateY(0);opacity:.4}50%{transform:translateY(-6px);opacity:1}}

    /* ─── Suggestions ─── */
    .asw-suggestions{display:flex;gap:8px;overflow-x:auto;padding:4px 16px 12px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
    .asw-suggestions::-webkit-scrollbar{display:none}
    .asw-suggestions[hidden]{display:none}
    .asw-suggestion{flex:0 0 auto;padding:8px 16px;border:1px solid var(--asw-suggestion-border);border-radius:999px;background:var(--asw-suggestion-bg);color:var(--asw-suggestion-text);font-size:12.5px;font-weight:500;cursor:pointer;transition:all .25s cubic-bezier(.16,1,.3,1);white-space:nowrap;font-family:inherit}
    .asw-suggestion:hover{border-color:var(--asw-suggestion-active);color:var(--asw-suggestion-active);transform:translateY(-1px);box-shadow:0 4px 12px rgba(99,102,241,.15)}
    .asw-suggestion:active{transform:translateY(0)}

    /* ─── Footer / Input ─── */
    .asw-footer{padding:12px 14px 14px;background:var(--asw-bg);border-top:1px solid var(--asw-border);flex-shrink:0}
    .asw-input-wrap{display:flex;align-items:flex-end;gap:8px;padding:8px 10px 8px 16px;border:2px solid var(--asw-border);border-radius:20px;background:var(--asw-input-bg);transition:all .3s cubic-bezier(.16,1,.3,1)}
    .asw-input-wrap:focus-within{background:var(--asw-input-focus-bg);border-color:var(--asw-border-focus);box-shadow:0 0 0 4px rgba(99,102,241,.1)}

    /* Auto-grow Textarea */
    .asw-input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:var(--asw-text);font-size:var(--asw-font-size,14px);font-family:inherit;line-height:1.6;resize:none;max-height:120px;padding:4px 0;overflow-y:auto;scrollbar-width:none}
    .asw-input::-webkit-scrollbar{display:none}
    .asw-input::placeholder{color:var(--asw-text-muted)}

    /* Send Button */
    .asw-send{width:40px;height:40px;border:none;border-radius:50%;display:grid;place-items:center;background:var(--asw-primary);color:#fff;cursor:pointer;transition:all .25s cubic-bezier(.16,1,.3,1);flex-shrink:0}
    .asw-send:hover{transform:scale(1.08);box-shadow:0 4px 16px rgba(99,102,241,.35)}
    .asw-send:active{transform:scale(.92)}
    .asw-send:disabled{cursor:not-allowed;opacity:.35;transform:none;box-shadow:none}
    .asw-send svg{width:18px;height:18px}

    /* Powered By */
    .asw-powered{text-align:center;padding:6px 0 0;font-size:10.5px;color:var(--asw-text-muted);font-weight:500}
    .asw-powered[hidden]{display:none}
    .asw-powered a{color:var(--asw-primary);text-decoration:none;font-weight:600}
    .asw-powered a:hover{text-decoration:underline}
    .asw-resource-links{display:inline-flex;gap:6px;margin-inline-start:6px}

    /* ─── Empty State ─── */
    .asw-empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:40px 24px;gap:16px}
    .asw-empty-icon{width:64px;height:64px;border-radius:20px;background:linear-gradient(135deg,var(--asw-primary),var(--asw-secondary));display:grid;place-items:center;color:#fff;box-shadow:0 8px 24px rgba(99,102,241,.3);animation:asw-float 3s ease-in-out infinite}
    .asw-empty-icon svg{width:32px;height:32px}
    @keyframes asw-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
    .asw-empty-title{font-size:16px;font-weight:700;color:var(--asw-text)}
    .asw-empty-text{font-size:13px;color:var(--asw-text-secondary);max-width:260px;line-height:1.6}

    /* ─── Error Toast ─── */
    .asw-toast{position:absolute;bottom:80px;left:16px;right:16px;padding:12px 16px;border-radius:var(--asw-radius-sm);background:var(--asw-error);color:#fff;font-size:13px;font-weight:500;text-align:center;box-shadow:0 8px 24px rgba(239,68,68,.3);opacity:0;transform:translateY(8px);transition:all .3s;pointer-events:none;z-index:10}
    .asw-toast.show{opacity:1;transform:translateY(0);pointer-events:auto}

    /* ─── Responsive ─── */
    @media(max-width:480px){
      .asw-fab{width:54px;height:54px}
      .asw-panel{width:min(var(--asw-panel-w),calc(100vw - 24px));height:min(var(--asw-panel-h),calc(100dvh - 80px))}
      .asw-root.mobile-fullscreen .asw-panel{position:fixed!important;inset:0!important;width:100vw!important;max-width:none!important;height:100dvh!important;max-height:none!important;border-radius:0!important}
      .asw-root.mobile-fullscreen .asw-fab{display:none!important}
      .asw-row{max-width:92%}
    }
    @media(prefers-reduced-motion:reduce){
      .asw-panel,.asw-fab,.asw-suggestion{transition:none}
      .asw-typing-dot{animation:none}
      .asw-row{animation:none;opacity:1;transform:none}
      .asw-empty-icon{animation:none}
    }

    /* ─── Font Size Variants ─── */
    .asw[data-font="small"]{--asw-font-size:12px}
    .asw[data-font="large"]{--asw-font-size:16px}

    /* ─── Accessibility ─── */
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
      return url.protocol === "https:" || url.protocol === "http:" || url.protocol === "mailto:";
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
  function renderMarkdown(text) {
    var src = String(text == null ? "" : text);
    var lines = src.split(/\r?\n/);
    var output = [];
    var inList = false;
    var inOl = false;
    var codeBlock = false;
    var codeLines = [];
    var codeLang = "";

    lines.forEach(function (line) {
      if (line.match(/^```/)) {
        if (codeBlock) {
          output.push(renderCodeBlock(codeLines.join("\n"), codeLang));
          codeLines = [];
          codeLang = "";
          codeBlock = false;
        } else {
          if (inList) { output.push("</ul>"); inList = false; }
          if (inOl) { output.push("</ol>"); inOl = false; }
          codeBlock = true;
          codeLang = line.replace(/^```/, "").trim();
        }
        return;
      }
      if (codeBlock) { codeLines.push(line); return; }

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
    });

    if (codeBlock) output.push(renderCodeBlock(codeLines.join("\n"), codeLang));
    if (inList) output.push("</ul>");
    if (inOl) output.push("</ol>");

    return output.join("<br>");
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
      '<div class="asw-code-header"><span class="asw-code-lang">' + escapeHtml(langLabel) + '</span>' +
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
      this.isOpen = false;
      this.isLoading = false;
      this.messageCount = 0;
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

      // Build the FAB icon based on configuration
      var fabIconHtml = this.getFabIconHtml();

      root.innerHTML =
        /* Panel */
        '<section class="asw-panel" role="dialog" aria-label="' + escapeHtml(this.options.title) + '" aria-hidden="true">' +
          /* Header */
          '<header class="asw-header">' +
            '<div class="asw-heading">' +
              '<div class="asw-avatar" id="asw-avatar"></div>' +
              '<div class="asw-info">' +
                '<div class="asw-title-row"><span class="asw-title" id="asw-title"></span><span class="asw-badge" id="asw-badge"><span class="asw-badge-dot"></span><span id="asw-badge-text"></span></span></div>' +
                '<div class="asw-subtitle" id="asw-subtitle"></div>' +
              '</div>' +
            '</div>' +
            '<div class="asw-actions">' +
              '<button class="asw-header-btn" id="asw-theme-toggle" type="button" aria-label="Toggle theme" title="تغییر تم">' +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>' +
              '</button>' +
              '<button class="asw-header-btn asw-close" id="asw-close" type="button" aria-label="بستن چت">' + ICONS.close + '</button>' +
            '</div>' +
          '</header>' +
          /* Messages */
          '<div class="asw-messages" id="asw-messages" role="log" aria-live="polite"></div>' +
          /* Typing */
          '<div class="asw-typing" id="asw-typing" hidden aria-label="در حال تایپ...">' +
            '<div class="asw-typing-dots"><span class="asw-typing-dot"></span><span class="asw-typing-dot"></span><span class="asw-typing-dot"></span></div>' +
            '<span class="asw-typing-label">در حال نوشتن...</span>' +
          '</div>' +
          /* Suggestions */
          '<div class="asw-suggestions" id="asw-suggestions"></div>' +
          /* Footer */
          '<footer class="asw-footer">' +
            '<div class="asw-input-wrap" id="asw-input-wrap">' +
              '<textarea class="asw-input" id="asw-input" rows="1" autocomplete="off" placeholder="' + escapeHtml(this.options.inputPlaceholder) + '" aria-label="پیام" style="height:auto;min-height:24px;max-height:120px"></textarea>' +
              '<button class="asw-send" id="asw-send" type="button" aria-label="ارسال" disabled>' + ICONS.send + '</button>' +
            '</div>' +
            '<div class="asw-powered" id="asw-powered">Powered by <a href="https://ai-support.ir" target="_blank" rel="noopener">AI Support</a><span class="asw-resource-links" id="asw-resources"></span></div>' +
          '</footer>' +
          /* Toast */
          '<div class="asw-toast" id="asw-toast"></div>' +
        '</section>' +
        /* FAB */
        '<button class="asw-fab" id="asw-fab" type="button" aria-label="باز کردن چت" aria-expanded="false">' +
          '<span class="asw-fab-pulse"></span>' +
          '<span class="asw-fab-icon-main">' + fabIconHtml + '</span>' +
          '<span class="asw-fab-icon-close">' + ICONS.close + '</span>' +
        '</button>';

      this.shadow.appendChild(root);
      this.root = root;
      this.panel = root.querySelector(".asw-panel");
      this.fab = root.querySelector("#asw-fab");
      this.closeBtn = root.querySelector("#asw-close");
      this.themeToggle = root.querySelector("#asw-theme-toggle");
      this.titleEl = root.querySelector("#asw-title");
      this.badgeText = root.querySelector("#asw-badge-text");
      this.subtitleEl = root.querySelector("#asw-subtitle");
      this.avatarEl = root.querySelector("#asw-avatar");
      this.messages = root.querySelector("#asw-messages");
      this.typing = root.querySelector("#asw-typing");
      this.suggestions = root.querySelector("#asw-suggestions");
      this.input = root.querySelector("#asw-input");
      this.sendBtn = root.querySelector("#asw-send");
      this.powered = root.querySelector("#asw-powered");
      this.resources = root.querySelector("#asw-resources");
      this.toast = root.querySelector("#asw-toast");

      this.applyVisuals();
      this.renderSuggestions();
      this.renderResources();
      this.bindEvents();
      this.addMessage(this.options.greeting, "bot", true);
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
      if (this.options.darkMode === "auto" && window.matchMedia) {
        var mq = window.matchMedia("(prefers-color-scheme: dark)");
        mq.addEventListener("change", () => this.applyTheme());
      }
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
        // Update FAB icon after config loads
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

      // Root: invisible container at the corner
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

      // Panel: fixed, positioned directly adjacent to FAB
      this.panel.style.position = "fixed";
      var fabSize = 60;
      var panelGap = 12;
      if (isBottom) {
        // Panel above FAB: bottom = fab_bottom + fab_size + gap
        this.panel.style.bottom = (vertPx + fabSize + panelGap) + "px";
        this.panel.style.top = "auto";
      } else {
        // Panel below FAB: top = fab_top + fab_size + gap
        this.panel.style.top = (vertPx + fabSize + panelGap) + "px";
        this.panel.style.bottom = "auto";
      }
      if (isLeft) {
        // Panel extends right from FAB left edge
        this.panel.style.left = horizPx + "px";
        this.panel.style.right = "auto";
      } else {
        // Panel extends left from FAB right edge        
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
      this.subtitleEl.textContent = o.subtitle;
      this.input.placeholder = o.inputPlaceholder;
      this.powered.hidden = o.showPoweredBy === false;
      this.messages.classList.toggle("asw-no-avatar", o.showAvatar === false);
    }

    /* ─── Render Suggestions ─── */
    renderSuggestions() {
      var items = Array.isArray(this.options.suggestions) ? this.options.suggestions.filter(Boolean).slice(0, 6) : [];
      this.suggestions.innerHTML = items.map(function (item) {
        return '<button class="asw-suggestion" type="button" data-msg="' + escapeHtml(item) + '">' + escapeHtml(item) + "</button>";
      }).join("");
      this.suggestions.hidden = items.length === 0;
    }

    /* ─── Render Resource Links ─── */
    renderResources() {
      if (!this.resources) return;
      this.resources.textContent = "";
      var links = [];
      var o = this.options;
      if (o.faqUrl && isSafeUrl(o.faqUrl)) links.push({ label: "FAQ", url: o.faqUrl });
      if (o.privacyUrl && isSafeUrl(o.privacyUrl)) links.push({ label: "Privacy", url: o.privacyUrl });
      if (o.supportEmail) links.push({ label: "Support", url: "mailto:" + o.supportEmail });
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

      this.sendBtn.addEventListener("click", function () { self.send(); });

      this.suggestions.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-msg]");
        if (!btn) return;
        self.input.value = btn.dataset.msg;
        self.autoGrowInput();
        self.send();
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
        if (e.key === "Escape" && self.isOpen) self.close();
      });
    }

    /* ─── Auto-grow Textarea ─── */
    autoGrowInput() {
      var el = this.input;
      el.style.height = "auto";
      var newHeight = Math.min(el.scrollHeight, 120);
      el.style.height = newHeight + "px";
    }

    /* ─── Open / Close ─── */
    open() {
      this.isOpen = true;
      this.panel.classList.add("open");
      this.panel.setAttribute("aria-hidden", "false");
      this.fab.classList.add("active");
      this.fab.setAttribute("aria-expanded", "true");
      var self = this;
      setTimeout(function () { self.input.focus(); }, 300);
    }

    close() {
      this.isOpen = false;
      this.panel.classList.remove("open");
      this.panel.setAttribute("aria-hidden", "true");
      this.fab.classList.remove("active");
      this.fab.setAttribute("aria-expanded", "false");
      this.fab.focus();
    }

    toggle() { this.isOpen ? this.close() : this.open(); }

    /* ─── Send State ─── */
    updateSendState() {
      this.sendBtn.disabled = this.isLoading || !this.input.value.trim();
    }

    scrollToBottom() {
      var m = this.messages;
      m.scrollTo({ top: m.scrollHeight, behavior: "smooth" });
    }

    /* ─── Toast ─── */
    showToast(msg, duration) {
      var t = this.toast;
      t.textContent = msg;
      t.classList.add("show");
      setTimeout(function () { t.classList.remove("show"); }, duration || 4000);
    }

    /* ─── Add Message ─── */
    addMessage(text, sender, isGreeting) {
      var row = document.createElement("div");
      row.className = "asw-row " + sender + (isGreeting ? " no-anim" : "");

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
      bubble.className = "asw-bubble";
      bubble.innerHTML = sender === "bot" ? renderMarkdown(text) : escapeHtml(text);

      col.appendChild(bubble);

      if (this.options.showTimestamp !== false) {
        var time = document.createElement("div");
        time.className = "asw-time";
        time.textContent = formatTime();
        col.appendChild(time);
      }

      // Feedback buttons (only on bot messages, not greeting, when enabled)
      if (sender === "bot" && !isGreeting && this.options.showFeedback !== false) {
        var feedback = document.createElement("div");
        feedback.className = "asw-feedback";
        feedback.innerHTML =
          '<button class="asw-fb-btn thumbs-up" type="button" data-action="helpful" aria-label="مفيد بود">' + ICONS.thumbUp + '</button>' +
          '<button class="asw-fb-btn thumbs-down" type="button" data-action="not_helpful" aria-label="مفيد نبود">' + ICONS.thumbDown + '</button>';
        feedback.setAttribute("data-question", (this._lastUserMessage || "").substring(0, 200));
        feedback.setAttribute("data-answer", text.substring(0, 300));
        col.appendChild(feedback);
      }

      row.appendChild(col);
      this.messages.appendChild(row);
      this.messageCount++;
      this.scrollToBottom();
    }

    /* ─── Feedback Handler ─── */
    handleFeedback(btn) {
      var feedbackDiv = btn.closest(".asw-feedback");
      if (!feedbackDiv || feedbackDiv.dataset.sent) return;

      var action = btn.dataset.action;
      var isHelpful = action === "helpful";

      // Visual feedback
      feedbackDiv.querySelectorAll(".asw-fb-btn").forEach(function (b) {
        b.classList.remove("active");
        b.disabled = true;
      });
      btn.classList.add("active");

      // Replace icon with filled version
      if (isHelpful) {
        btn.innerHTML = ICONS.thumbUpFilled;
      } else {
        btn.innerHTML = ICONS.thumbDownFilled;
      }

      feedbackDiv.dataset.sent = "true";

      // Send to backend
      this.sendFeedback(isHelpful, feedbackDiv.dataset.question || "", feedbackDiv.dataset.answer || "");
    }

    sendFeedback(helpful, question, answerPreview) {
      if (!this.options.feedbackEndpoint) return;
      fetch(this.options.feedbackEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getHeaders(),
        body: JSON.stringify({
          helpful: helpful,
          question: question,
          answer_preview: answerPreview,
          session_id: this.options.sessionId,
        }),
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

    /* ─── Loading State ─── */
    setLoading(loading) {
      this.isLoading = loading;
      this.typing.hidden = !loading;
      this.input.disabled = loading;
      this.input.placeholder = loading ? "در حال پاسخ‌دهی..." : this.options.inputPlaceholder;
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
    async send() {
      var msg = this.input.value.trim();
      if (!msg || this.isLoading) return;

      this._lastUserMessage = msg;
      this.addMessage(msg, "user");
      this.input.value = "";
      this.autoGrowInput();
      this.suggestions.hidden = true;
      this.setLoading(true);
      this.playSound("send");

      try {
        var result = await this.callBackend(msg);
        this.addMessage(result.answer, "bot");
        this.playSound("receive");
      } catch (err) {
        this.sendEvent("fallback_triggered", { message: err && err.message || "unknown" });
        var errMsg = err && err.userMessage ? err.userMessage : "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً دوباره تلاش کنید.";
        this.addMessage(errMsg, "bot");
        this.showToast(errMsg, 5000);
      } finally {
        this.setLoading(false);
        this.input.focus();
      }
    }

    /* ─── API Call ─── */
    async callBackend(message) {
      var controller = new AbortController();
      var timeout = setTimeout(function () { controller.abort(); }, Number(this.options.timeoutMs) || 45000);
      try {
        var res = await fetch(this.options.apiEndpoint, {
          method: "POST", mode: "cors", credentials: "omit",
          headers: this.getHeaders(),
          body: JSON.stringify({ message: message }),
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
        return { answer: answer.trim() };
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

  /* ─────────────── BOOT ─────────────── */
  function boot() {
    var globalConfig = window.AI_WIDGET_CONFIG || {};
    var options = Object.assign({}, globalConfig);
    if (scriptConfig.api) options.apiEndpoint = scriptConfig.api;
    if (scriptConfig.widgetKey) options.widgetPublicKey = scriptConfig.widgetKey;
    if (scriptConfig.title) options.title = scriptConfig.title;
    if (scriptConfig.primaryColor) options.primaryColor = scriptConfig.primaryColor;
    window._aiWidget = new AISupportWidget(options);
  }

  window.AISupportWidget = AISupportWidget;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
