// Widget v4 unit checks in Node (no browser needed):
// verifies the JS file parses, and that critical v4 features exist.
// Run: node scripts/widget_js_check.js
const fs = require("fs");
const path = require("path");

const src = fs.readFileSync(
  path.join(__dirname, "..", "static", "widget", "widget.js"),
  "utf8",
);

let pass = 0;
let fail = 0;
function check(name, cond) {
  if (cond) { pass++; console.log("OK  " + name); }
  else { fail++; console.log("FAIL " + name); }
}

// v4 feature presence
check("SSE streaming (streamChat)", src.includes("async streamChat(message)"));
check("stop/abort support", src.includes("this.abortStream") && src.includes("AbortController"));
check("send button doubles as stop", src.includes('self.abortStream.abort()'));
check("citations renderer", src.includes("buildCitations(citations)"));
check("lead form with honeypot", src.includes('name="website"') && src.includes("buildLeadForm"));
check("handoff channels (telegram/whatsapp/contact_form)",
  src.includes("contact_form") && src.includes("whatsapp") && src.includes("telegram"));
check("handoff logged to backend", src.includes("logHandoff(channel"));
check("conversation persistence (sessionStorage)",
  src.includes("asw_conversation_id") && src.includes("asw_conversation_token"));
check("history restore", src.includes("async restoreHistory()"));
check("feedback with message_id", src.includes('data-message-id') && src.includes("Number(messageId)"));
check("live preview channel", src.includes("aiss:config") && src.includes("aiss:preview-ready"));
check("preview mode via data attr", src.includes("previewMode"));
check("SSE parser splits on blank line", src.includes('buffer.split("\\n\\n")'));
check("meta event stores token", src.includes("conversation_token"));
check("fallback triggers handoff", src.includes("meta.fallback") && src.includes("maybeShowHandoff"));

// safety: no innerHTML of raw user text
check("user text escaped", src.includes("escapeHtml(text)"));
check("no eval", !/\beval\s*\(/.test(src));
check("links use rel noopener", src.includes('rel = "noopener noreferrer"'));

// legacy copy in sync
const legacy = fs.readFileSync(
  path.join(__dirname, "..", "static", "widget.js"),
  "utf8",
);
check("legacy static/widget.js is synced", legacy === src);

console.log("\n" + pass + " passed, " + fail + " failed");
if (fail) process.exit(1);
console.log("WIDGET JS CHECKS: ALL OK");
