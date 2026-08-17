(function () {
  "use strict";

  if (window.AISupportWidget) {
    return;
  }

  var scriptElement = document.currentScript;
  var scriptConfig = scriptElement && scriptElement.dataset
    ? scriptElement.dataset
    : {};

  var DEFAULTS = {
    apiEndpoint: "/api/chat/",
    configEndpoint: "",
    historyEndpoint: "",
    eventsEndpoint: "",
    feedbackEndpoint: "",
    widgetPublicKey: "",
    title: "دستیار هوش مصنوعی کارسنج",
    subtitle: "Online • پاسخ های فوری به سوالات شما",
    greeting: "سلام! 👋 چطور می‌توانم کمکتان کنم؟",
    timeoutMs: 45000,
    primaryColor: "#5048E5",
    secondaryColor: "#7C3AED",
    headerBadge: "ONLINE",
    botAvatarText: "AI",
    inputPlaceholder: "سؤال خود را بنویسید...",
    themeMode: "gradient",
    panelWidth: 380,
    panelHeight: 600,
    borderRadius: 22,
    mobileFullscreen: true,
    logoUrl: "",
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
    showHistory: true,
    allowFeedback: true,
    showPoweredBy: true,
    suggestions: [],
  };

  var ICONS = {
    chat:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z"/><path d="M8 12h8M8 8h5"/></svg>',
    close:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12"/></svg>',
    send:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m22 2-11 11M22 2l-7 20-4-9-9-4 20-7Z"/></svg>',
    history:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 7v5l3 2"/></svg>',
  };

  var CSS = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:var(--asw-font,Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif)}",
    ".asw-root{position:fixed;right:20px;bottom:20px;z-index:2147483647;display:flex;flex-direction:column;align-items:flex-end;gap:12px}",
    ".asw-fab{width:58px;height:58px;border:0;border-radius:50%;background:var(--asw-header-background);color:#fff;display:grid;place-items:center;cursor:pointer;box-shadow:0 12px 30px #5048e561;transition:transform .2s,box-shadow .2s}",
    ".asw-fab:hover{transform:translateY(-2px);box-shadow:0 16px 36px #5048e56b}",
    ".asw-fab svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}",
    ".asw-panel{width:var(--asw-panel-width);height:var(--asw-panel-height);max-width:calc(100vw - 24px);max-height:calc(100dvh - 90px);display:flex;flex-direction:column;overflow:hidden;background:var(--asw-surface);border:1px solid #e2e8f0;border-radius:var(--asw-radius);box-shadow:0 24px 60px #0f172e2e;opacity:0;pointer-events:none;transform:translateY(12px) scale(.98);transform-origin:bottom right;transition:opacity .2s,transform .3s cubic-bezier(.16,1,.3,1)}",
    ".asw-panel.open{opacity:1;pointer-events:auto;transform:none}",
    ".asw-header{display:flex;align-items:center;justify-content:space-between;padding:15px;background:var(--asw-header-background);color:#fff}",
    ".asw-heading{display:flex;align-items:center;gap:10px;min-width:0}.asw-avatar{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:#fff;color:var(--asw-primary);font-size:12px;font-weight:800}.asw-avatar img{width:100%;height:100%;border-radius:inherit;object-fit:cover}",
    ".asw-title-row{display:flex;align-items:center;gap:6px;min-width:0}.asw-title{font-size:14px;font-weight:750;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.asw-badge{padding:3px 6px;border:1px solid #ffffff45;border-radius:999px;background:#ffffff22;font-size:9px;letter-spacing:.08em;white-space:nowrap}.asw-subtitle{margin-top:3px;font-size:11px;opacity:.9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".asw-actions{display:flex;gap:5px}.asw-close,.asw-history-toggle{width:30px;height:30px;border:1px solid #ffffff3d;border-radius:50%;background:#ffffff24;color:#fff;display:grid;place-items:center;cursor:pointer}.asw-close svg,.asw-history-toggle svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}",
    ".asw-messages{flex:1;min-height:0;display:flex;flex-direction:column;gap:10px;overflow:auto;padding:16px 12px 10px}.asw-messages.hidden{display:none}",
    ".asw-row{display:flex;align-items:flex-end;gap:7px;max-width:88%}.asw-row.user{align-self:flex-end;flex-direction:row-reverse}.asw-row.bot{align-self:flex-start}",
    ".asw-msg-avatar{width:26px;height:26px;flex:0 0 26px;display:grid;place-items:center;border-radius:50%;font-size:9px;font-weight:800}.asw-row.bot .asw-msg-avatar{background:#fff;border:1px solid #e2e8f0;color:var(--asw-primary)}.asw-row.user .asw-msg-avatar{background:var(--asw-primary);color:#fff}",
    ".asw-col{max-width:100%}.asw-bubble{padding:10px 12px;border-radius:16px;font-size:13px;line-height:1.55;word-break:break-word;white-space:pre-wrap;box-shadow:0 2px 10px #0f172e0f}.asw-row.bot .asw-bubble{background:#fff;border:1px solid #e2e8f0;color:#0f172a;border-bottom-left-radius:6px;white-space:normal}.asw-row.user .asw-bubble{background:var(--asw-primary);color:#fff;border-bottom-right-radius:6px}.asw-bubble strong{font-weight:800}.asw-bubble em{font-style:italic}.asw-bubble a{color:var(--asw-primary);font-weight:650;text-decoration:underline;text-underline-offset:2px}.asw-bubble ul{margin:6px 0 2px;padding-inline-start:20px}.asw-bubble li{margin:3px 0}.asw-time{padding:3px 2px 0;color:#94a3b8;font-size:10px}.asw-row.user .asw-time{text-align:right}.asw-feedback{display:flex;gap:4px;margin-top:4px}.asw-feedback button{border:1px solid #e2e8f0;border-radius:999px;background:#fff;color:#64748b;font-size:11px;line-height:1;padding:4px 7px;cursor:pointer}.asw-feedback button:hover,.asw-feedback button.selected{border-color:var(--asw-primary);color:var(--asw-primary)}",
    ".asw-typing{padding:0 12px 8px;color:#94a3b8;font-size:12px}.asw-typing[hidden]{display:none}.asw-typing span{display:inline-block;margin-right:3px;animation:asw-pulse 1.1s infinite}.asw-typing span:nth-child(2){animation-delay:.15s}.asw-typing span:nth-child(3){animation-delay:.3s}@keyframes asw-pulse{50%{opacity:.3}}",
    ".asw-suggestions{display:flex;gap:6px;overflow:auto;padding:6px 12px 8px;scrollbar-width:none}.asw-suggestions[hidden]{display:none}.asw-suggestions::-webkit-scrollbar{display:none}.asw-suggestions button{flex:0 0 auto;padding:7px 10px;border:1px solid #e2e8f0;border-radius:999px;background:#fff;color:#334155;font-size:12px;cursor:pointer}.asw-suggestions button:hover{border-color:var(--asw-primary);color:var(--asw-primary)}",
    ".asw-footer{padding:10px;background:#fff;border-top:1px solid #e2e8f0}.asw-input-row{display:flex;gap:6px;align-items:center;padding:5px 5px 5px 12px;border:1px solid #e2e8f0;border-radius:999px;background:#f1f5f9}.asw-input-row:focus-within{background:#fff;border-color:#a5b4fc;box-shadow:0 0 0 3px #5048e51a}.asw-input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:#0f172a;font-size:13px}.asw-send{width:34px;height:34px;border:0;border-radius:50%;display:grid;place-items:center;background:var(--asw-primary);color:#fff;cursor:pointer}.asw-send:disabled{cursor:not-allowed;opacity:.45}.asw-send svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.asw-powered{text-align:center;margin-top:6px;color:#94a3b8;font-size:10px}.asw-powered a{color:inherit;text-decoration:underline;text-underline-offset:2px}.asw-powered[hidden]{display:none}",
    "@media(max-width:600px){.asw-root{right:10px;bottom:10px}.asw-panel{width:min(var(--asw-panel-width),calc(100vw - 20px));height:min(var(--asw-panel-height),calc(100dvh - 80px))}.asw-root.mobile-fullscreen .asw-panel{position:fixed;right:0;bottom:0;width:100vw;max-width:none;height:100dvh;max-height:none;border-radius:0}.asw-root.mobile-fullscreen .asw-panel.open~.asw-fab{display:none}}",
    "@media(prefers-reduced-motion:reduce){.asw-panel,.asw-fab{transition:none}.asw-typing span{animation:none}}",
  ].join("");

  function escapeText(value) {
    return String(value == null ? "" : value);
  }

  function escapeHtml(value) {
    return escapeText(value).replace(/[&<>"']/g, function (character) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      }[character];
    });
  }

  function formatTime() {
    return new Date().toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function getConversationId() {
    try {
      var key = "ai-support-conversation";
      var current = window.sessionStorage.getItem(key);
      if (current) return current;
      current = "conv_" + Math.random().toString(36).slice(2) + Date.now();
      window.sessionStorage.setItem(key, current);
      return current;
    } catch (_error) {
      return "conv_" + Math.random().toString(36).slice(2) + Date.now();
    }
  }

  function getConversationToken() {
    try {
      return window.sessionStorage.getItem("ai-support-conversation-token") || "";
    } catch (_error) {
      return "";
    }
  }

  function saveConversationToken(token) {
    if (!token) return;
    try {
      window.sessionStorage.setItem("ai-support-conversation-token", token);
    } catch (_error) {}
  }

  function getDefaultEndpoint() {
    if (scriptElement && scriptElement.src) {
      return new URL("/api/chat/", scriptElement.src).toString();
    }
    return new URL("/api/chat/", window.location.href).toString();
  }

  function getSiblingEndpoint(apiEndpoint, name) {
    return new URL(
      apiEndpoint.replace(/chat\/?$/, name + "/"),
      window.location.href
    ).toString();
  }

  function escapeAttribute(value) {
    return escapeHtml(value);
  }

  function isSafeUrl(value) {
    try {
      var url = new URL(String(value), window.location.href);
      return (
        url.protocol === "https:" ||
        url.protocol === "http:" ||
        url.protocol === "mailto:"
      );
    } catch (_error) {
      return false;
    }
  }

  function renderInlineMarkdown(value) {
    var links = [];
    var source = String(value == null ? "" : value).replace(
      /\[([^\]]+)\]\(([^)\s]+(?:\s+[^)\s]+)?)\)/g,
      function (_match, label, url) {
        if (!isSafeUrl(url)) return label;
        var token = "ASWLINKTOKEN" + links.length + "X";
        links.push({
          token: token,
          html:
            '<a href="' +
            escapeAttribute(url) +
            '" target="_blank" rel="noopener noreferrer">' +
            escapeHtml(label) +
            "</a>",
        });
        return token;
      }
    );
    var html = escapeHtml(source)
      .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_\n]+)__/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>")
      .replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");
    links.forEach(function (link) {
      html = html.replace(link.token, link.html);
    });
    return html;
  }

  function renderMarkdown(value) {
    var lines = String(value == null ? "" : value).split(/\r?\n/);
    var output = [];
    var inList = false;
    lines.forEach(function (line) {
      var match = line.match(/^\s*[-*\u2022]\s+(.+)$/);
      if (match) {
        if (!inList) {
          output.push("<ul>");
          inList = true;
        }
        output.push("<li>" + renderInlineMarkdown(match[1]) + "</li>");
        return;
      }
      if (inList) {
        output.push("</ul>");
        inList = false;
      }
      output.push(renderInlineMarkdown(line));
    });
    if (inList) output.push("</ul>");
    return output.join("<br>");
  }

  class AISupportWidget {
    constructor(options) {
      this.options = Object.assign({}, DEFAULTS, options || {});
      this.explicitOptions = options || {};
      if (!this.options.apiEndpoint || this.options.apiEndpoint === "/api/chat/") {
        this.options.apiEndpoint = getDefaultEndpoint();
      }
      this.options.configEndpoint =
        this.options.configEndpoint ||
        getSiblingEndpoint(this.options.apiEndpoint, "widget-config");
      this.options.historyEndpoint =
        this.options.historyEndpoint ||
        getSiblingEndpoint(this.options.apiEndpoint, "history");
      this.options.eventsEndpoint =
        this.options.eventsEndpoint ||
        getSiblingEndpoint(this.options.apiEndpoint, "events");
      this.options.feedbackEndpoint =
        this.options.feedbackEndpoint ||
        getSiblingEndpoint(this.options.apiEndpoint, "feedback");
      this.conversationId = getConversationId();
      this.conversationToken = getConversationToken();
      this.history = [];
      this.historyHidden = false;
      this.isOpen = false;
      this.isLoading = false;
      this.mount();
      this.initialize();
    }

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
      root.className = "asw-root";
      root.style.setProperty("--asw-primary", this.options.primaryColor);
      root.style.setProperty("--asw-secondary", this.options.secondaryColor);
      root.style.setProperty(
        "--asw-header-background",
        this.getHeaderBackground()
      );
      root.style.setProperty(
        "--asw-panel-width",
        this.clampNumber(this.options.panelWidth, 280, 520) + "px"
      );
      root.style.setProperty(
        "--asw-panel-height",
        this.clampNumber(this.options.panelHeight, 360, 760) + "px"
      );
      root.style.setProperty(
        "--asw-radius",
        this.clampNumber(this.options.borderRadius, 10, 36) + "px"
      );
      root.style.setProperty(
        "--asw-surface",
        this.options.themeMode === "glass" ? "#ffffffed" : "#f8fafc"
      );
      root.classList.toggle(
        "mobile-fullscreen",
        this.options.mobileFullscreen !== false
      );
      root.innerHTML =
        '<section class="asw-panel" role="dialog" aria-label="' +
        escapeHtml(this.options.title) +
        '" aria-hidden="true">' +
        '<header class="asw-header"><div class="asw-heading"><div class="asw-avatar"></div><div><div class="asw-title-row"><div class="asw-title"></div><span class="asw-badge"></span></div><div class="asw-subtitle"></div></div></div><div class="asw-actions"><button class="asw-history-toggle" type="button" aria-label="Hide history">' +
        ICONS.history +
        '</button><button class="asw-close" type="button" aria-label="Close chat">' +
        ICONS.close +
        '</button></header>' +
        '<div class="asw-messages" role="log" aria-live="polite"></div>' +
        '<div class="asw-typing" hidden>AI is typing<span>.</span><span>.</span><span>.</span></div>' +
        '<div class="asw-suggestions"></div>' +
        '<footer class="asw-footer"><div class="asw-input-row"><input class="asw-input" type="text" autocomplete="off" placeholder="Ask anything..." aria-label="Message"><button class="asw-send" type="button" aria-label="Send message">' +
        ICONS.send +
        '</button></div><div class="asw-powered">Powered by AI Support <span class="asw-resource-links"></span></div></footer></section>' +
        '<button class="asw-fab" type="button" aria-label="Open chat" aria-expanded="false">' +
        ICONS.chat +
        "</button>";
      this.shadow.appendChild(root);

      this.root = root;
      this.panel = root.querySelector(".asw-panel");
      this.fab = root.querySelector(".asw-fab");
      this.closeButton = root.querySelector(".asw-close");
      this.historyToggle = root.querySelector(".asw-history-toggle");
      this.title = root.querySelector(".asw-title");
      this.headerBadge = root.querySelector(".asw-badge");
      this.subtitle = root.querySelector(".asw-subtitle");
      this.messages = root.querySelector(".asw-messages");
      this.typing = root.querySelector(".asw-typing");
      this.suggestions = root.querySelector(".asw-suggestions");
      this.input = root.querySelector(".asw-input");
      this.sendButton = root.querySelector(".asw-send");
      this.powered = root.querySelector(".asw-powered");
      this.resourceLinks = root.querySelector(".asw-resource-links");

      this.title.textContent = this.options.title;
      this.subtitle.textContent = this.options.subtitle;
      this.root.querySelector(".asw-avatar").textContent = this.options.botAvatarText;
      this.headerBadge.textContent = this.options.headerBadge || "";
      this.renderSuggestions();
      this.renderResourceLinks();
      this.applyVisualOptions();
      this.bindEvents();
      this.addMessage(this.options.greeting, "bot");
      this.updateSendState();
    }

    async initialize() {
      await this.loadConfig();
      await this.loadHistory();
      this.sendEvent("widget_loaded");
    }

    async loadConfig() {
      if (!this.options.configEndpoint) return;
      try {
        var response = await fetch(
          this.options.configEndpoint,
          {
            method: "GET",
            mode: "cors",
            credentials: "omit",
            headers: this.getApiHeaders(),
          }
        );
        if (!response.ok) return;
        var rawConfig = await response.json();
        var config = {
          title: rawConfig.title,
          subtitle: rawConfig.subtitle,
          greeting: rawConfig.greeting,
          primaryColor: rawConfig.primary_color,
          secondaryColor: rawConfig.secondary_color,
          headerBadge: rawConfig.header_badge,
          botAvatarText: rawConfig.bot_avatar_text,
          inputPlaceholder: rawConfig.input_placeholder,
          themeMode: rawConfig.theme_mode,
          panelWidth: rawConfig.panel_width,
          panelHeight: rawConfig.panel_height,
          borderRadius: rawConfig.border_radius,
          mobileFullscreen: rawConfig.mobile_fullscreen,
          logoUrl: rawConfig.logo_url,
          fontFamily: rawConfig.font_family,
          position: rawConfig.position,
          showHistory: rawConfig.show_history,
          allowFeedback: rawConfig.allow_feedback,
          showPoweredBy: rawConfig.show_powered_by,
          suggestions: rawConfig.suggestions,
          faqUrl: rawConfig.faq_url,
          privacyUrl: rawConfig.privacy_url,
          supportEmail: rawConfig.support_email,
        };
        Object.keys(config).forEach((key) => {
          if (config[key] === undefined || config[key] === null) return;
          if (!Object.prototype.hasOwnProperty.call(this.explicitOptions, key)) {
            this.options[key] = config[key];
          }
        });
        this.title.textContent = this.options.title;
        this.subtitle.textContent = this.options.subtitle;
        this.applyVisualOptions();
        this.renderSuggestions();
        this.renderResourceLinks();
      } catch (_error) {
        // Local defaults remain usable when configuration is unavailable.
      }
    }

    async loadHistory() {
      if (this.options.showHistory === false || !this.options.historyEndpoint) {
        return;
      }
      try {
        var response = await fetch(
          this.options.historyEndpoint +
            "?conversation_id=" +
            encodeURIComponent(this.conversationId),
          {
            method: "GET",
            mode: "cors",
            credentials: "omit",
            headers: this.getApiHeaders(),
          }
        );
        if (!response.ok) return;
        var data = await response.json();
        var messages = Array.isArray(data.messages) ? data.messages : [];
        if (!messages.length) return;
        this.messages.innerHTML = "";
        this.history = [];
        messages.forEach((item) => {
          if (item.role !== "user" && item.role !== "assistant") return;
          this.addMessage(
            item.content,
            item.role === "user" ? "user" : "bot",
            item.role === "assistant" ? item.id : null
          );
          this.history.push({
            role: item.role,
            content: item.content,
          });
        });
      } catch (_error) {
        // A failed history request must not block a new conversation.
      }
    }

    applyVisualOptions() {
      this.root.style.setProperty("--asw-primary", this.options.primaryColor);
      this.root.style.setProperty("--asw-secondary", this.options.secondaryColor);
      this.root.style.setProperty(
        "--asw-header-background",
        this.getHeaderBackground()
      );
      this.root.style.setProperty(
        "--asw-panel-width",
        this.clampNumber(this.options.panelWidth, 280, 520) + "px"
      );
      this.root.style.setProperty(
        "--asw-panel-height",
        this.clampNumber(this.options.panelHeight, 360, 760) + "px"
      );
      this.root.style.setProperty(
        "--asw-radius",
        this.clampNumber(this.options.borderRadius, 10, 36) + "px"
      );
      this.root.classList.toggle(
        "mobile-fullscreen",
        this.options.mobileFullscreen !== false
      );
      this.root.style.setProperty("--asw-font", this.options.fontFamily);
      this.panel.style.fontFamily = this.options.fontFamily;
      this.input.placeholder = this.options.inputPlaceholder || "Ask anything...";
      this.root.querySelector(".asw-avatar").textContent =
        this.options.botAvatarText || "AI";
      this.headerBadge.textContent = this.options.headerBadge || "";
      var avatar = this.root.querySelector(".asw-avatar");
      if (this.options.logoUrl && isSafeUrl(this.options.logoUrl)) {
        avatar.textContent = "";
        avatar.style.backgroundImage = "";
        var logo = document.createElement("img");
        logo.src = this.options.logoUrl;
        logo.alt = "";
        logo.referrerPolicy = "no-referrer";
        avatar.appendChild(logo);
      } else {
        avatar.style.backgroundImage = "";
        avatar.textContent = this.options.botAvatarText || "AI";
      }
      this.historyToggle.hidden = this.options.showHistory === false;
      this.powered.hidden = this.options.showPoweredBy === false;
      if (this.options.position === "bottom-left") {
        this.root.style.right = "auto";
        this.root.style.left = "20px";
        this.root.style.alignItems = "flex-start";
      } else {
        this.root.style.right = "20px";
        this.root.style.left = "auto";
        this.root.style.alignItems = "flex-end";
      }
    }

    clampNumber(value, min, max) {
      var number = Number(value);
      if (!Number.isFinite(number)) return min;
      return Math.min(max, Math.max(min, number));
    }

    getHeaderBackground() {
      if (this.options.themeMode === "solid") {
        return this.options.primaryColor;
      }
      if (this.options.themeMode === "glass") {
        return "linear-gradient(135deg, " +
          this.options.primaryColor +
          "dd, " +
          this.options.secondaryColor +
          "cc)";
      }
      return "linear-gradient(135deg, " +
        this.options.primaryColor +
        ", " +
        this.options.secondaryColor +
        ")";
    }

    renderSuggestions() {
      var items = Array.isArray(this.options.suggestions)
        ? this.options.suggestions.filter(Boolean).slice(0, 8)
        : [];
      this.suggestions.innerHTML = items
        .map(function (item) {
          return (
            '<button type="button" data-message="' +
            escapeAttribute(item) +
            '">' +
            escapeHtml(item) +
            "</button>"
          );
        })
        .join("");
      this.suggestions.hidden = items.length === 0;
    }

    renderResourceLinks() {
      if (!this.resourceLinks) return;
      this.resourceLinks.textContent = "";
      var resources = [
        { label: "FAQ", url: this.options.faqUrl },
        { label: "Privacy", url: this.options.privacyUrl },
        {
          label: "Support",
          url: this.options.supportEmail
            ? "mailto:" + this.options.supportEmail
            : "",
        },
      ];
      resources.forEach(function (resource) {
        if (!resource.url || !isSafeUrl(resource.url)) return;
        var link = document.createElement("a");
        link.href = resource.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = resource.label;
        this.resourceLinks.appendChild(document.createTextNode(" · "));
        this.resourceLinks.appendChild(link);
      }, this);
    }

    bindEvents() {
      var self = this;
      this.fab.addEventListener("click", function () {
        self.toggle();
      });
      this.closeButton.addEventListener("click", function () {
        self.close();
      });
      this.historyToggle.addEventListener("click", function () {
        self.historyHidden = !self.historyHidden;
        self.messages.classList.toggle("hidden", self.historyHidden);
        self.historyToggle.setAttribute(
          "aria-label",
          self.historyHidden ? "Show history" : "Hide history"
        );
      });
      this.sendButton.addEventListener("click", function () {
        self.send();
      });
      this.input.addEventListener("input", function () {
        self.updateSendState();
      });
      this.input.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          self.send();
        }
      });
      this.suggestions.addEventListener("click", function (event) {
        var button = event.target.closest("[data-message]");
        if (!button) return;
        self.input.value = button.dataset.message;
        self.send();
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && self.isOpen) self.close();
      });
    }

    open() {
      this.isOpen = true;
      this.panel.classList.add("open");
      this.panel.setAttribute("aria-hidden", "false");
      this.fab.setAttribute("aria-expanded", "true");
      window.setTimeout(() => this.input.focus(), 200);
    }

    close() {
      this.isOpen = false;
      this.panel.classList.remove("open");
      this.panel.setAttribute("aria-hidden", "true");
      this.fab.setAttribute("aria-expanded", "false");
      this.fab.focus();
    }

    toggle() {
      this.isOpen ? this.close() : this.open();
    }

    updateSendState() {
      this.sendButton.disabled = this.isLoading || !this.input.value.trim();
    }

    scrollToBottom() {
      this.messages.scrollTop = this.messages.scrollHeight;
    }

    addMessage(text, sender, messageId) {
      var row = document.createElement("div");
      row.className = "asw-row " + sender;
      var avatar = document.createElement("div");
      avatar.className = "asw-msg-avatar";
      avatar.textContent = sender === "user" ? "You" : "AI";
      var column = document.createElement("div");
      column.className = "asw-col";
      var bubble = document.createElement("div");
      bubble.className = "asw-bubble";
      if (sender === "bot") {
        bubble.innerHTML = renderMarkdown(text);
      } else {
        bubble.textContent = escapeText(text);
      }
      var time = document.createElement("div");
      time.className = "asw-time";
      time.textContent = formatTime();
      column.appendChild(bubble);
      column.appendChild(time);
      if (sender === "bot" && messageId && this.options.allowFeedback) {
        var feedback = document.createElement("div");
        feedback.className = "asw-feedback";
        feedback.innerHTML =
          '<button type="button" data-feedback="helpful" aria-label="Helpful">👍</button>' +
          '<button type="button" data-feedback="not_helpful" aria-label="Not helpful">👎</button>';
        feedback.addEventListener("click", (event) => {
          var button = event.target.closest("[data-feedback]");
          if (!button) return;
          feedback.querySelectorAll("button").forEach((item) => {
            item.classList.toggle("selected", item === button);
          });
          this.sendFeedback(messageId, button.dataset.feedback);
        });
        column.appendChild(feedback);
      }
      row.appendChild(avatar);
      row.appendChild(column);
      this.messages.appendChild(row);
      this.scrollToBottom();
    }

    sendEvent(eventType, metadata) {
      if (!this.options.eventsEndpoint) return;
      fetch(this.options.eventsEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getApiHeaders(),
        body: JSON.stringify({
          conversation_id: this.conversationId,
          conversation_token: this.conversationToken,
          event_type: eventType,
          metadata: metadata || {},
        }),
      })
        .then(function (response) {
          return response.ok ? response.json() : null;
        })
        .then((data) => {
          if (data && data.conversation_token) {
            this.conversationToken = data.conversation_token;
            saveConversationToken(data.conversation_token);
          }
        })
        .catch(function () {});
    }

    sendFeedback(messageId, feedback) {
      if (
        !this.options.allowFeedback ||
        !messageId ||
        !this.options.feedbackEndpoint
      ) {
        return;
      }
      fetch(this.options.feedbackEndpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: this.getApiHeaders(),
        body: JSON.stringify({
          conversation_id: this.conversationId,
          conversation_token: this.conversationToken,
          message_id: messageId,
          feedback: feedback,
        }),
      }).catch(function () {});
    }

    setLoading(loading) {
      this.isLoading = loading;
      this.typing.hidden = !loading;
      this.input.disabled = loading;
      this.input.placeholder = loading ? "AI is typing..." : "Ask anything...";
      this.updateSendState();
      this.scrollToBottom();
    }

    async send() {
      var message = this.input.value.trim();
      if (!message || this.isLoading) return;

      this.addMessage(message, "user");
      this.input.value = "";
      this.suggestions.hidden = true;
      this.setLoading(true);

      try {
        var result = await this.callBackend(message, this.history.slice(-8));
        if (result.conversationToken) {
          this.conversationToken = result.conversationToken;
          saveConversationToken(result.conversationToken);
        }
        this.addMessage(result.answer, "bot", result.messageId);
        this.history.push({ role: "user", content: message });
        this.history.push({ role: "assistant", content: result.answer });
      } catch (error) {
        this.sendEvent("fallback_triggered", {
          message: error && error.message ? error.message : "unknown_error",
        });
        this.addMessage(
          error && error.userMessage
            ? error.userMessage
            : "Sorry, the assistant is temporarily unavailable. Please try again.",
          "bot"
        );
      } finally {
        this.setLoading(false);
        this.input.focus();
      }
    }

    async callBackend(message, history) {
      var controller = new AbortController();
      var timeout = window.setTimeout(
        () => controller.abort(),
        Number(this.options.timeoutMs) || DEFAULTS.timeoutMs
      );
      var payload = {
        message: message,
        conversation_id: this.conversationId,
        history: history || [],
      };

      try {
        var response = await fetch(this.options.apiEndpoint, {
          method: "POST",
          mode: "cors",
          credentials: "omit",
          headers: this.getApiHeaders(),
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        var data = {};
        try {
          data = await response.json();
        } catch (_parseError) {
          data = {};
        }
        if (!response.ok) {
          var backendError = new Error(data.message || data.error || "Request failed");
          backendError.userMessage =
            response.status >= 500
              ? "The assistant is temporarily unavailable. Please try again."
              : data.message || "Please check your message and try again.";
          throw backendError;
        }
        var answer = data.answer || data.reply || data.response || data.message;
        if (typeof answer !== "string" || !answer.trim()) {
          throw new Error("Backend returned an empty answer");
        }
        return {
          answer: answer.trim(),
          messageId: data.message_id || null,
          conversationToken: data.conversation_token || "",
        };
      } catch (error) {
        if (error.name === "AbortError") {
          var timeoutError = new Error("Request timed out");
          timeoutError.userMessage = "The response took too long. Please try again.";
          throw timeoutError;
        }
        throw error;
      } finally {
        window.clearTimeout(timeout);
      }
    }

    getApiHeaders() {
      var headers = { "Content-Type": "application/json" };
      if (this.options.widgetPublicKey) {
        headers["X-Widget-Key"] = this.options.widgetPublicKey;
      }
      if (this.conversationToken) {
        headers["X-Conversation-Token"] = this.conversationToken;
      }
      return headers;
    }
  }

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
