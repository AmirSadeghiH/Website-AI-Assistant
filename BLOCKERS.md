# BLOCKERS — prodcheck release gate (Django/any)

Kept 325 of 388 release-gate items (stack filter: any + django). Each item needs: file:line + quote, or UNKNOWN.

## Pre-Release Gates — Findings That Should Block Release  [security]

- [ ] (security.core.17-release-gates.60ad8ae7) Any unauthenticated access to sensitive data.
- [ ] (security.core.17-release-gates.dfda281c) Any cross-user data access.
- [ ] (security.core.17-release-gates.9528231b) Any cross-tenant data access.
- [ ] (security.core.17-release-gates.bad33a16) Any privilege escalation.
- [ ] (security.core.17-release-gates.dbadd4e5) Any production database credential in source/build artifacts.
- [ ] (security.core.17-release-gates.7232530a) Any ability to bypass RLS through ordinary client access.
- [ ] (security.core.17-release-gates.c8b7a0a8) Any exposed private storage object without intentional public access.
- [ ] (security.core.17-release-gates.bd756ce4) Any unauthenticated privileged API.
- [ ] (security.core.17-release-gates.791371b7) Any SSRF to cloud/internal infrastructure.
- [ ] (security.core.17-release-gates.f3b4dbce) Any unauthenticated feature that fetches a URL on the caller's behalf — an open proxy.
- [ ] (security.core.17-release-gates.02d2259f) Any way to send email, SMS or push to a recipient chosen by the request body.
- [ ] (security.core.17-release-gates.ca4fa8b4) Any paid third-party action reachable without a per-user quota.
- [ ] (security.core.17-release-gates.8ab22911) Any arbitrary command execution.
- [ ] (security.core.17-release-gates.9365a2e5) Any arbitrary file read/write with sensitive impact.
- [ ] (security.core.17-release-gates.2455385a) Any account-takeover path.
- [ ] (security.core.17-release-gates.bb032804) Any production GitHub workflow that lets untrusted PR code obtain production credentials.
- [ ] (security.core.17-release-gates.f4ff2b63) Any CI workflow that permits arbitrary branch/PR input to become privileged shell execution.
- [ ] (security.core.17-release-gates.e21760be) Any Apple app private signing credential leaked.
- [ ] (security.core.17-release-gates.c28cce2d) Any production deployment path that can be modified without appropriate review/approval.
- [ ] (security.core.17-release-gates.7409f91f) Any origin bypass that defeats the intended security controls.

## Pre-Release Gates — High-Risk “Must Not Exist” Search  [security]

> Reviewed 2026-09-05 — full-repo scan (py/js/html/json/yml/md/cfg/ini) with evidence.
> 🔴 **ACTION REQUIRED:** the LLM API key (`sk-sOYZ…`) sat inside a tracked `ai-support-platform.zip` that was pushed to GitHub history (commits `af996d7`, `49abad9`). Zip now untracked+deleted, but **rotate the key and set a distinct `SECRET_KEY` before production.**

- [x] (security.core.17-release-gates.a9100f3e) database password — none in source; DB creds only via env (`config/settings.py:123-135`), `.env` gitignored and never committed (`git log --all -- .env` empty)
- [x] (security.core.17-release-gates.ad701190) database connection string with credentials — regex scan across repo: 0 matches
- [x] (security.core.17-release-gates.04914dc2) JWT signing secret — no JWT anywhere; conversation tokens are HMAC over `SECRET_KEY` (`chat/conversation_tokens.py:15-26`)
- [x] (security.core.17-release-gates.ceaba9bb) Google service-account private key — none (0 regex matches; no JSON key files)
- [x] (security.core.17-release-gates.da35d3b7) GitHub PAT — none (0 regex matches)
- [x] (security.core.17-release-gates.540fb8ee) GitHub runner token — N/A — no CI workflows exist (`.github/` absent)
- [x] (security.core.17-release-gates.88a07be0) Apple private signing key — N/A — no mobile app
- [x] (security.core.17-release-gates.7f359c38) OAuth client secret — N/A — no OAuth integration
- [x] (security.core.17-release-gates.be06a860) webhook signing secret — N/A — no webhook receivers
- [x] (security.core.17-release-gates.8289bd14) encryption key — `FIELD_ENCRYPTION_KEY` only read from env (`chat/encrypted_fields.py:24-30`), never hardcoded; fallback derives from `SECRET_KEY`
- [x] (security.core.17-release-gates.b90c4147) private certificate key — no `.pem`/`.key`/`id_rsa` files on disk (now enforced by `chat/tests_secretscan.py::test_no_private_key_files_on_disk`)
- [x] (security.core.17-release-gates.a2f4245a) SSH private key — none (same scan)
- [x] (security.core.17-release-gates.59eb0fcd) production `.env` — `.env` is local-only, gitignored (`.gitignore:12`), never committed; **but a copy leaked inside the tracked zip (fixed this pass — rotate keys)**
- [x] (security.core.17-release-gates.a9cda3c0) `.npmrc` credentials — file does not exist
- [x] (security.core.17-release-gates.ab632e50) package-manager authentication tokens — none (0 regex matches)
- [x] (security.core.17-release-gates.b40c5562) hard-coded admin passwords — source clean; only test fixtures (`chat/tests.py:458,870`, `chat/tests_security.py:572`) with clearly-fake values
- [x] (security.core.17-release-gates.dd7a3abc) test credentials that work against production — fixtures live only in test files; nothing wired to any real account
- [x] (security.core.17-release-gates.138ef7d5) debugging backdoors — no magic GET params / hidden superuser flags (grep clean); DEBUG loopback bypass is documented and DEBUG-gated (`chat/api_permissions.py:187-188`)
- [x] (security.core.17-release-gates.f8595cec) hidden master/admin parameters — none (grep clean)
- [x] (security.core.17-release-gates.536e67e6) undocumented administrative endpoints — all 19 panel routes are `@staff_member_required` (`chat/panel_urls.py:10-28`); `business_rules_preview` (`chat/views.py:1047`) is unrouted dead code with an in-code staff check

## Pre-Release Gates — Production Configuration Review  [security]

- [ ] (security.core.17-release-gates.d3c4cbe7) Review production environment variables.
- [ ] (security.core.17-release-gates.c5add758) Review staging environment variables.
- [ ] (security.core.17-release-gates.ff684e09) Compare production vs staging security configuration.
- [ ] (security.core.17-release-gates.67a326e3) Verify no development debug flags.
- [ ] (security.core.17-release-gates.efa4ad70) Verify no test accounts with production privileges.
- [ ] (security.core.17-release-gates.9a34a08f) Verify no default passwords.
- [ ] (security.core.17-release-gates.2fd5b478) Verify no development endpoints.
- [ ] (security.core.17-release-gates.9f2a5f1a) Verify no localhost fallback.
- [ ] (security.core.17-release-gates.a279d351) Verify production logging is safe.
- [ ] (security.core.17-release-gates.08e7cf6b) Verify production CORS.
- [ ] (security.core.17-release-gates.b19a1034) Verify production CSP.
- [ ] (security.core.17-release-gates.bb14d1c5) Verify production cookies.
- [ ] (security.core.17-release-gates.3359f794) Verify production TLS.
- [ ] (security.core.17-release-gates.cb208502) Verify production DNS.
- [ ] (security.core.17-release-gates.b242ae14) Verify production IAM.
- [ ] (security.core.17-release-gates.99944078) Verify production bucket settings.
- [ ] (security.core.17-release-gates.e331f6c2) Verify production OAuth redirect URIs.
- [ ] (security.core.17-release-gates.a759d320) Verify production Apple configuration.
- [ ] (security.core.17-release-gates.bc584e16) Verify production app bundle identifiers.

## Pre-Release Gates — Development / Staging Isolation  [security]

- [ ] (security.core.17-release-gates.689d4203) Production credentials cannot be used from development.
- [ ] (security.core.17-release-gates.d25e19e7) Development credentials cannot access production.
- [ ] (security.core.17-release-gates.97a34962) Staging users cannot access production.
- [ ] (security.core.17-release-gates.5978f59a) Staging APIs do not share sensitive secrets with production.
- [ ] (security.core.17-release-gates.9a2155f0) Staging DNS cannot overwrite production DNS.
- [ ] (security.core.17-release-gates.10d94004) Staging CI cannot deploy to production.
- [ ] (security.core.17-release-gates.f7a0de80) Production GitHub environments require correct branch/tag.
- [ ] (security.core.17-release-gates.332f9a49) Development databases cannot contain unnecessary production PII.
- [ ] (security.core.17-release-gates.5897d05a) Production data copied to staging is sanitized.
- [ ] (security.core.17-release-gates.b6f5a577) Developer local machines do not receive production credentials unnecessarily.

## Pre-Release Gates — Security Testing Automation  [security]

- [ ] (security.core.17-release-gates.272d04e5) Run SAST.
- [ ] (security.core.17-release-gates.7bfbb725) Run SCA.
- [ ] (security.core.17-release-gates.e38ca8da) Run secret scanning.
- [ ] (security.core.17-release-gates.d820fd94) Run IaC scanning.
- [ ] (security.core.17-release-gates.f458ad1f) Run container scanning.
- [ ] (security.core.17-release-gates.c914885d) Run DAST.
- [ ] (security.core.17-release-gates.f72d374e) Run API fuzzing.
- [ ] (security.core.17-release-gates.ff82d165) Run authorization regression tests.
- [ ] (security.core.17-release-gates.54674757) Run RLS regression tests.
- [ ] (security.core.17-release-gates.2b2688be) Run storage authorization tests.
- [ ] (security.core.17-release-gates.1d0a9262) Run SSRF regression tests.
- [ ] (security.core.17-release-gates.7848e55e) Run XSS regression tests.
- [ ] (security.core.17-release-gates.c17f9918) Run CSRF regression tests.
- [ ] (security.core.17-release-gates.deda3a9b) Run dependency update checks.
- [ ] (security.core.17-release-gates.a4387857) Run mobile static analysis.
- [ ] (security.core.17-release-gates.64ec700a) Run binary security checks.
- [ ] (security.core.17-release-gates.1f6b00de) Run code-signing verification.
- [ ] (security.core.17-release-gates.ae75a8a6) Run infrastructure drift detection.

## Pre-Release Gates — Manual Penetration-Test Scenarios  [security]

- [ ] (security.core.17-release-gates.4cb12617) Account enumeration.
- [ ] (security.core.17-release-gates.35b236fd) Credential stuffing.
- [ ] (security.core.17-release-gates.fe569f46) Password reset takeover.
- [ ] (security.core.17-release-gates.70e6d9ba) Email change takeover.
- [ ] (security.core.17-release-gates.77c20973) MFA enrollment takeover.
- [ ] (security.core.17-release-gates.638432b0) MFA removal bypass.
- [ ] (security.core.17-release-gates.38cf5891) Session fixation.
- [ ] (security.core.17-release-gates.a745d98c) Session replay.
- [ ] (security.core.17-release-gates.e2a952aa) JWT tampering.
- [ ] (security.core.17-release-gates.be018d89) Token substitution.
- [ ] (security.core.17-release-gates.03788e0e) OAuth account-linking takeover.
- [ ] (security.core.17-release-gates.6a08cf52) Horizontal privilege escalation.
- [ ] (security.core.17-release-gates.ce710550) Vertical privilege escalation.
- [ ] (security.core.17-release-gates.522f5ed8) Cross-tenant access.
- [ ] (security.core.17-release-gates.00d8163e) BOLA/IDOR.
- [ ] (security.core.17-release-gates.2edca622) Mass assignment.
- [ ] (security.core.17-release-gates.042defb5) Hidden admin endpoint access.
- [ ] (security.core.17-release-gates.2fed190d) Property-level authorization bypass.
- [ ] (security.core.17-release-gates.183c1b6d) Function-level authorization bypass.
- [ ] (security.core.17-release-gates.ed66cb08) SQL injection.
- [ ] (security.core.17-release-gates.6ccf207d) NoSQL/JSON injection if applicable.
- [ ] (security.core.17-release-gates.b4b2e718) Command injection.
- [ ] (security.core.17-release-gates.6bfdd5ce) Template injection.
- [ ] (security.core.17-release-gates.f43722df) XSS.
- [ ] (security.core.17-release-gates.b1638992) SSRF.
- [ ] (security.core.17-release-gates.6c178d08) XXE if applicable.
- [ ] (security.core.17-release-gates.80ee4118) Path traversal.
- [ ] (security.core.17-release-gates.c9c0fd03) Header injection.
- [ ] (security.core.17-release-gates.887f24cb) Host-header attacks.
- [ ] (security.core.17-release-gates.aa4d70c8) CRLF injection.
- [ ] (security.core.17-release-gates.2f75a2e4) ReDoS.
- [ ] (security.core.17-release-gates.ed065733) Prototype pollution.
- [ ] (security.core.17-release-gates.192049c0) Deserialization abuse.
- [ ] (security.core.17-release-gates.ec48a151) Huge JSON.
- [ ] (security.core.17-release-gates.6a689837) Deep JSON nesting.
- [ ] (security.core.17-release-gates.6cf1dc13) Huge arrays.
- [ ] (security.core.17-release-gates.5f12408f) Huge strings.
- [ ] (security.core.17-release-gates.d20f9de8) Huge multipart uploads.
- [ ] (security.core.17-release-gates.7fd19151) Archive bombs.
- [ ] (security.core.17-release-gates.ad883649) Expensive search.
- [ ] (security.core.17-release-gates.e30462c4) Expensive regex.
- [ ] (security.core.17-release-gates.5f7d1b38) Excessive pagination.
- [ ] (security.core.17-release-gates.a393c3a8) Concurrent expensive requests.
- [ ] (security.core.17-release-gates.59e89c37) Webhook flooding.
- [ ] (security.core.17-release-gates.f0202567) Account creation flooding.
- [ ] (security.core.17-release-gates.55f9db02) OTP flooding.

## Pre-Release Gates — Final Security Sign-Off  [security]

- [ ] (security.core.17-release-gates.0cf71683) Threat model reviewed.
- [ ] (security.core.17-release-gates.516c8490) Asset inventory complete.
- [ ] (security.core.17-release-gates.b3752793) Endpoint inventory complete.
- [ ] (security.core.17-release-gates.4963343c) Authorization matrix complete.
- [ ] (security.core.17-release-gates.ac7edc52) Secrets audit complete.
- [ ] (security.core.17-release-gates.6ee54d83) Dependency/supply-chain audit complete.
- [ ] (security.core.17-release-gates.af50a7d0) DAST completed.
- [ ] (security.core.17-release-gates.88a89be2) API authorization testing completed.
- [ ] (security.core.17-release-gates.5b6818e4) Mobile security testing completed.
- [ ] (security.core.17-release-gates.0fab71db) Production configuration reviewed.
- [ ] (security.core.17-release-gates.92ca6ef0) Incident-response test completed.
- [ ] (security.core.17-release-gates.08c74511) All critical findings remediated.
- [ ] (security.core.17-release-gates.87a207cd) All high findings remediated or formally accepted.
- [ ] (security.core.17-release-gates.9a48a54e) Regression tests added for every security finding.
- [ ] (security.core.17-release-gates.ac218ce6) Security evidence archived.
- [ ] (security.core.17-release-gates.719696bc) Final security reviewer approval recorded.

## AI Release Gate — The "Do Not Trust" List  [security]

- [ ] (security.ai.11-release-gate.c5b9ffe1) user prompts
- [ ] (security.ai.11-release-gate.9e7eb1bd) uploaded files
- [ ] (security.ai.11-release-gate.53f29d7d) webpages
- [ ] (security.ai.11-release-gate.68941ae5) emails
- [ ] (security.ai.11-release-gate.ec96667a) documents
- [ ] (security.ai.11-release-gate.8102586b) database text
- [ ] (security.ai.11-release-gate.36ad8b8d) Storage metadata
- [ ] (security.ai.11-release-gate.a85392aa) search results
- [ ] (security.ai.11-release-gate.ab01bf61) vector results
- [ ] (security.ai.11-release-gate.fba7dc78) retrieved documents
- [ ] (security.ai.11-release-gate.de1304d0) model output
- [ ] (security.ai.11-release-gate.c0c72e29) tool output
- [ ] (security.ai.11-release-gate.3edb2f64) agent output
- [ ] (security.ai.11-release-gate.5c2bd86b) MCP output
- [ ] (security.ai.11-release-gate.dd14fc83) A2A messages
- [ ] (security.ai.11-release-gate.8bddb40f) generated SQL
- [ ] (security.ai.11-release-gate.3870c0e6) generated code
- [ ] (security.ai.11-release-gate.f45b61ae) generated URLs
- [ ] (security.ai.11-release-gate.e7765261) generated shell commands
- [ ] (security.ai.11-release-gate.0b60e984) generated API parameters
- [ ] (security.ai.11-release-gate.d8c12af5) generated authorization claims
- [ ] (security.ai.11-release-gate.2799f21e) generated role names
- [ ] (security.ai.11-release-gate.850549d7) model-generated policy decisions

## AI Release Gate — Production Release Gate  [security]

- [ ] (security.ai.11-release-gate.639a2820) Agent threat model is complete.
- [ ] (security.ai.11-release-gate.42ead2e5) Tool inventory is complete.
- [ ] (security.ai.11-release-gate.7fc1dd61) Agent identity model is complete.
- [ ] (security.ai.11-release-gate.19e9a48e) Tool authorization matrix is complete.
- [ ] (security.ai.11-release-gate.e1d5f59f) Prompt injection testing is complete.
- [ ] (security.ai.11-release-gate.edd21707) Indirect prompt injection testing is complete.
- [ ] (security.ai.11-release-gate.86d29d63) RAG security testing is complete.
- [ ] (security.ai.11-release-gate.6a77558d) Memory security testing is complete.
- [ ] (security.ai.11-release-gate.f796dc50) Cross-tenant testing is complete.
- [ ] (security.ai.11-release-gate.b7d9423e) Tool authorization tests pass.
- [ ] (security.ai.11-release-gate.5ebc4376) Output-validation tests pass.
- [ ] (security.ai.11-release-gate.1531d9ad) SSRF tests pass.
- [ ] (security.ai.11-release-gate.9ecb7b25) Code-execution sandbox is verified where applicable.
- [ ] (security.ai.11-release-gate.837fb1aa) Cost/rate controls are verified.
- [ ] (security.ai.11-release-gate.ae94cf87) Human approval controls are verified.
- [ ] (security.ai.11-release-gate.be76ac7c) Audit logging is verified.
- [ ] (security.ai.11-release-gate.3d9e0ed7) Incident kill switch is verified.
- [ ] (security.ai.11-release-gate.89e0b3b9) Production credentials are least privilege.
- [ ] (security.ai.11-release-gate.27931d0c) Agent cannot disable its own security controls.
- [ ] (security.ai.11-release-gate.ebda02ae) Agent cannot obtain unrestricted production credentials.
- [ ] (security.ai.11-release-gate.5fe17778) Agent cannot silently expand its tool permissions.
- [ ] (security.ai.11-release-gate.1fd3f9d4) Agent cannot approve its own privileged actions.
- [ ] (security.ai.11-release-gate.6fb336dd) Adversarial regression suite passes.
- [ ] (security.ai.11-release-gate.d6fc8eb4) Security reviewer approves the release.

## Vibe-Coding Release Gate — Release Gate  [security]

- [ ] (security.ai-generated-code.09-release-gate.f9d62cee) Human reviewed the security architecture.
- [ ] (security.ai-generated-code.09-release-gate.007b6c7c) Human reviewed authentication.
- [ ] (security.ai-generated-code.09-release-gate.0fd7ba37) Human reviewed authorization.
- [ ] (security.ai-generated-code.09-release-gate.635bed83) Human reviewed tenant isolation.
- [ ] (security.ai-generated-code.09-release-gate.80caf19c) Human reviewed database/RLS changes.
- [ ] (security.ai-generated-code.09-release-gate.d4be5db2) Human reviewed Storage changes.
- [ ] (security.ai-generated-code.09-release-gate.4e2935c3) Human reviewed secrets.
- [ ] (security.ai-generated-code.09-release-gate.fd635834) Human reviewed dependencies.
- [ ] (security.ai-generated-code.09-release-gate.18fdce76) Human reviewed CI/CD changes.
- [ ] (security.ai-generated-code.09-release-gate.40364775) Human reviewed infrastructure changes.
- [ ] (security.ai-generated-code.09-release-gate.fa9b57f4) Human reviewed mobile security changes where applicable.
- [ ] (security.ai-generated-code.09-release-gate.27a26d3d) Automated security scanning passes.
- [ ] (security.ai-generated-code.09-release-gate.eb492734) Authorization regression tests pass.
- [ ] (security.ai-generated-code.09-release-gate.d54503ef) Negative security tests pass.
- [ ] (security.ai-generated-code.09-release-gate.da956da1) No production secret was introduced.
- [ ] (security.ai-generated-code.09-release-gate.062c4460) No permission was unintentionally widened.
- [ ] (security.ai-generated-code.09-release-gate.26f456c6) No security control was silently removed.
- [ ] (security.ai-generated-code.09-release-gate.fd0d64d3) No new public endpoint was unintentionally exposed.
- [ ] (security.ai-generated-code.09-release-gate.13e5fd4e) AI-generated tool/agent permissions remain least privilege.
- [ ] (security.ai-generated-code.09-release-gate.9ec4102c) Security-sensitive generated code has a human owner.

## Vibe-Coding Release Gate — Red Flags  [security]

- [ ] (security.ai-generated-code.09-release-gate.0f56f52f) AI added an authentication library.
- [ ] (security.ai-generated-code.09-release-gate.bb0b36c5) AI changed authentication/session code.
- [ ] (security.ai-generated-code.09-release-gate.e5954657) AI changed authorization/roles.
- [ ] (security.ai-generated-code.09-release-gate.fb58c9bf) AI introduced a new admin endpoint.
- [ ] (security.ai-generated-code.09-release-gate.2a3867f9) AI introduced a "temporary" bypass.
- [ ] (security.ai-generated-code.09-release-gate.510967f3) AI disabled a failing security test.
- [ ] (security.ai-generated-code.09-release-gate.9570f284) AI changed CORS.
- [ ] (security.ai-generated-code.09-release-gate.7c4b31dc) AI changed CSP.
- [ ] (security.ai-generated-code.09-release-gate.2211f544) AI changed cookies.
- [ ] (security.ai-generated-code.09-release-gate.6382e2fb) AI changed TLS.
- [ ] (security.ai-generated-code.09-release-gate.b4538810) AI added external dependencies.
- [ ] (security.ai-generated-code.09-release-gate.1e72975b) AI added shell execution.
- [ ] (security.ai-generated-code.09-release-gate.cbd2fcdc) AI added file processing.
- [ ] (security.ai-generated-code.09-release-gate.b8fb9ce6) AI added URL fetching.
- [ ] (security.ai-generated-code.09-release-gate.6fe32a8a) AI added SQL.
- [ ] (security.ai-generated-code.09-release-gate.f3aeab2e) AI added a WebView.
- [ ] (security.ai-generated-code.09-release-gate.46e151a8) AI added native entitlements.
- [ ] (security.ai-generated-code.09-release-gate.844dc89f) AI changed IAM.
- [ ] (security.ai-generated-code.09-release-gate.3de3234e) AI changed DNS.
- [ ] (security.ai-generated-code.09-release-gate.0b22ef9c) AI changed production deployment.
- [ ] (security.ai-generated-code.09-release-gate.02934fd8) AI added an AI agent/tool.
- [ ] (security.ai-generated-code.09-release-gate.c25faed1) AI added RAG/memory.
- [ ] (security.ai-generated-code.09-release-gate.b40aba72) AI gave another AI agent additional privileges.

## Load Testing & Scale Gates — Make the test mean something  [scale]

- [ ] (scale.08-load-testing-and-gates.a9529993) Verify the test reproduces the real traffic mix — the ratio of reads to writes, the distribution across endpoints, the size of payloads.
- [ ] (scale.08-load-testing-and-gates.0fbaf320) Verify the test runs against production-sized data; an empty table is fast in a way production never is.
- [ ] (scale.08-load-testing-and-gates.1983a318) Verify the data has realistic distribution, including the one tenant with far more rows than the rest.
- [ ] (scale.08-load-testing-and-gates.89a3e3be) Verify caches are in a realistic state — an all-hit cache proves nothing, and a fully cold one may be unrealistically harsh.
- [ ] (scale.08-load-testing-and-gates.fd698849) Verify the test exercises authenticated journeys, not only the public homepage.
- [ ] (scale.08-load-testing-and-gates.fe99344e) Verify it runs from outside your own network, so it includes the edge, the load balancer and TLS.
- [ ] (scale.08-load-testing-and-gates.ed6d5ade) Verify third-party dependencies are either included or stubbed with realistic latency, not with an instant mock.

## Load Testing & Scale Gates — Run it properly  [scale]

- [ ] (scale.08-load-testing-and-gates.31bab130) Ramp load gradually to find the knee of the curve, rather than running one fixed level and declaring pass or fail.
- [ ] (scale.08-load-testing-and-gates.9a440525) Record what broke first, and at what load; that is the actual result of the test.
- [ ] (scale.08-load-testing-and-gates.93d1b87d) Fix it, then run again — the second bottleneck is never the same as the first.
- [ ] (scale.08-load-testing-and-gates.e5342418) Run a soak test long enough to expose leaks, connection exhaustion and disk growth.
- [ ] (scale.08-load-testing-and-gates.9bff74ad) Run a spike test, because a launch or a newsletter is a spike, not a ramp.
- [ ] (scale.08-load-testing-and-gates.ba70b637) Measure at p95 and p99; an average latency stays fine long after a quarter of users have given up.
- [ ] (scale.08-load-testing-and-gates.d808b602) Watch the system's own metrics during the test, not just the load tool's output — the tool tells you it hurt, the metrics tell you where.
- [ ] (scale.08-load-testing-and-gates.2e2a3a19) Verify testing against production, if you do it, has a stated blast radius, a kill switch and someone watching.

## Load Testing & Scale Gates — The gate  [scale]

- [ ] (scale.08-load-testing-and-gates.5a046a4f) Verify the system handles the peak you expect at launch, with a stated multiple of headroom.
- [ ] (scale.08-load-testing-and-gates.a2186c3e) Verify the load at which it degrades is written down, along with how it degrades.
- [ ] (scale.08-load-testing-and-gates.38bd3bce) Verify degradation is graceful — shedding load with a 429 or 503 rather than timing out or corrupting state.
- [ ] (scale.08-load-testing-and-gates.bc76a3e7) Verify database connection count at peak stays under its limit with margin.
- [ ] (scale.08-load-testing-and-gates.b30326e7) Verify queue backlog at peak drains within an acceptable time once the spike passes.
- [ ] (scale.08-load-testing-and-gates.b3b888dd) Verify error rate under peak load stays within the target, and that errors are the kind you intended.
- [ ] (scale.08-load-testing-and-gates.504e6c70) Verify there is a documented plan for the load you have not tested: what gets turned off, what gets scaled, who decides.
- [ ] (scale.08-load-testing-and-gates.3637b8a1) Verify the numbers from this test are recorded with the release, so the next test has something to compare against.

## Performance Release Gate — Thresholds  [performance]

- [ ] (performance.09-release-gate.eb10ba6e) Verify the p75 field LCP is under 2.5 seconds on mobile, or that the exception is written down with an owner and a date.
- [ ] (performance.09-release-gate.4ebda75c) Verify the p75 field INP is under 200 milliseconds.
- [ ] (performance.09-release-gate.f77233ee) Verify the p75 field CLS is under 0.1.
- [ ] (performance.09-release-gate.4bfeb34d) Verify the lab Lighthouse performance score on mobile meets the target agreed for this project, measured as a median of several runs.
- [ ] (performance.09-release-gate.15c17a87) Verify the Lighthouse accessibility score is 100, or that every remaining item is a known false positive with a note.
- [ ] (performance.09-release-gate.a32e2c1d) Verify the Lighthouse best-practices and SEO scores are at target.
- [ ] (performance.09-release-gate.8adb011e) Verify these numbers were measured on the templates that carry traffic, not only the homepage.

## Performance Release Gate — No regressions  [performance]

- [ ] (performance.09-release-gate.8195c507) Verify the performance budget is not exceeded by this release.
- [ ] (performance.09-release-gate.2b96dfda) Verify no new render-blocking resource was added to the critical path.
- [ ] (performance.09-release-gate.de4e1224) Verify no new third-party script was added without an owner and a measured cost.
- [ ] (performance.09-release-gate.e278a863) Verify bundle size did not increase without a deliberate decision recorded in the pull request.
- [ ] (performance.09-release-gate.4650c770) Verify the LCP element on each key template is still what it was, and still discoverable in the HTML.
- [ ] (performance.09-release-gate.6556e795) Verify no image above the fold gained `loading="lazy"`.
- [ ] (performance.09-release-gate.2ea04ebc) Verify the CI performance check ran on this commit and passed.

## Performance Release Gate — When something is out of your hands  [performance]

- [ ] (performance.09-release-gate.43de42f7) Verify a third party degrading the score has been quantified, so the conversation with the vendor has a number in it.
- [ ] (performance.09-release-gate.f38a5311) Verify a facade, a delayed load or a self-hosted copy has been considered before accepting the cost.
- [ ] (performance.09-release-gate.400f5dd3) Verify the decision to ship despite a failing metric is recorded with who made it and when it is revisited.
- [ ] (performance.09-release-gate.a37141a2) Verify field metrics are watched for the week after release, tied to this deploy.

## Performance Release Gate — Coverage  [performance]

- [ ] (performance.09-release-gate.365c7cc1) Verify the gate ran against mobile emulation with throttling, not desktop on a fast connection.
- [ ] (performance.09-release-gate.e012f0d6) Verify the logged-in experience was measured if it is where users spend their time.
- [ ] (performance.09-release-gate.4b474b02) Verify the numbers in this gate are stored with the release, so the next regression has something to compare against.

## Can You Act At All — Who and how  [post-launch]

- [ ] (post-launch.01-readiness.96cb143c) Verify it is written down who responds to a production incident, including out of hours, and that the person knows.
- [ ] (post-launch.01-readiness.75402dbd) For a solo founder: verify you have decided which alerts are allowed to wake you and which can wait until morning, rather than treating all of them as either.
- [ ] (post-launch.01-readiness.6b2ffb7f) Verify there is a second person who can act if the first is unreachable, or a written acceptance that there is not.
- [ ] (post-launch.01-readiness.ca90f2dc) Verify the alerting channel has been tested by firing a real alert, not assumed to work.
- [ ] (post-launch.01-readiness.8f07c3e0) Verify alerts reach a device that is on at night if the service matters at night.
- [ ] (post-launch.01-readiness.02189970) Verify the person who responds knows where the runbooks are without searching.

## Can You Act At All — Access when you need it  [post-launch]

- [ ] (post-launch.01-readiness.0fee829f) Verify you can reach the production console, the database and the deploy pipeline from a phone or a borrowed laptop.
- [ ] (post-launch.01-readiness.aeeea424) Verify two-factor recovery codes for every critical account are stored somewhere you can reach when your laptop is the thing that is broken.
- [ ] (post-launch.01-readiness.48ae1906) Verify the password manager is not the single point of failure for its own recovery.
- [ ] (post-launch.01-readiness.7b46fa42) Verify credentials are not held only by one person, and that a break-glass path exists and has been tested.
- [ ] (post-launch.01-readiness.c83d044c) Verify the break-glass path is auditable — using it should be loud, not silent.
- [ ] (post-launch.01-readiness.fda2fa70) Verify you can still authenticate if the identity provider is the thing that is down.
- [ ] (post-launch.01-readiness.f1fbff41) Verify domain registrar and DNS provider access is not tied to an email address hosted on the domain itself.

## Can You Act At All — Can you actually change anything  [post-launch]

- [ ] (post-launch.01-readiness.2d5e6151) Verify you can deploy right now — not in principle, but by having deployed recently.
- [ ] (post-launch.01-readiness.1c759f4c) Verify a deploy does not require a person who is on holiday, a machine that is off, or a token that expired.
- [ ] (post-launch.01-readiness.80fdc7b1) Verify CI is green on `main`, so an emergency fix is not blocked behind an unrelated failure.
- [ ] (post-launch.01-readiness.cff0b12e) Verify you can deploy a one-line change end to end in under fifteen minutes, and know what that number actually is.
- [ ] (post-launch.01-readiness.5bb5bfdd) Verify you can roll back without a rebuild — see [`06-rollback-and-kill-switches.md`](06-rollback-and-kill-switches.md).
- [ ] (post-launch.01-readiness.972718cb) Verify you can scale up or shed load without a code change.

## Can You Act At All — Know what you have  [post-launch]

- [ ] (post-launch.01-readiness.fdeb68bd) Verify there is a current list of what runs in production: services, databases, queues, cron jobs, third parties, domains.
- [ ] (post-launch.01-readiness.11cfcaf1) Verify each one has an owner, even if every owner is you.
- [ ] (post-launch.01-readiness.3eedf656) Verify you know which provider hosts what, and which account it is billed to.
- [ ] (post-launch.01-readiness.aac33eeb) Verify a diagram or written description of the request path exists that a new person could follow.
- [ ] (post-launch.01-readiness.3e03326a) Verify you know which single failure would take everything down, and whether that is acceptable.

## Can You Act At All — Will you notice before a customer does  [post-launch]

- [ ] (post-launch.01-readiness.1c8a331d) Verify something exercises the critical paths on a schedule after deploy — signup, login, checkout, the one action the product exists for — and not only in CI before merge.
- [ ] (post-launch.01-readiness.767e1199) Verify a failed run reaches a person, rather than a dashboard nobody opens.
- [ ] (post-launch.01-readiness.94e593c1) Verify you know how long a silent regression could last before anyone noticed: an hour, a day, or until a customer wrote in.
- [ ] (post-launch.01-readiness.7e85f566) Verify the checks run against production or a production-like environment, since the ones that only ever ran against a local stub have never tested your real configuration.
- [ ] (post-launch.01-readiness.ae3dc8f1) Verify someone is accountable for a failing scheduled check, or it becomes noise that everyone learns to skip.
- [ ] (post-launch.01-readiness.c199a7f2) Verify a check that has been failing for a week is treated as an outage in the monitoring, not as a known issue.
- [ ] (post-launch.01-readiness.78edf3f8) Verify something outside the check itself asserts that it produced a pass or a fail recently — a clock asking "has this reported in the last N hours", not the check reporting its own health.
- [ ] (post-launch.01-readiness.3faa72cc) Verify a run that is killed rather than failed still alerts: a runner timeout is usually recorded as cancelled, not as a failure, so alerting keyed on failure fires nothing at all.
- [ ] (post-launch.01-readiness.ebcbf428) Verify the alerting path itself fails loudly when its credential is missing or expired, rather than skipping the step and leaving the job green.
- [ ] (post-launch.01-readiness.48d12ec1) Verify a step conditioned on a secret being present cannot pass by being skipped — an unset key should turn the build red, not quietly remove the notification.
- [ ] (post-launch.01-readiness.e97d14cf) Verify every HTTP call in a check fails on an error status, since a plain `curl` exits zero on 401 or 404 and a check reading its empty output concludes nothing is wrong.
- [ ] (post-launch.01-readiness.a8d9a87f) Verify you have looked at the run history, not the last run: consecutive cancellations and a silent inbox look identical to a system finding nothing wrong.
- [ ] (post-launch.01-readiness.e531309f) Verify every notification reads its sender and recipient from configuration rather than carrying a hardcoded address, since a check that asserts an alert was sent asserts nothing about whether it arrived somewhere a person can read.
- [ ] (post-launch.01-readiness.a60f971a) Verify at least one real alert from each notification path has been received by a human, not merely observed leaving: a path that has never delivered since the day it was written looks exactly like a path with nothing to report.
- [ ] (post-launch.01-readiness.4ea86ff2) Verify automated issue or ticket creation deduplicates against what is already open and holds a concurrency guard, because one persistently failing check otherwise files the same issue on every run until the volume is indistinguishable from having no alerting at all.

## Can You Act At All — The gate  [post-launch]

- [ ] (post-launch.01-readiness.a80cb89b) Verify a runbook exists for the three most likely failures before launch, not after the first one.
- [ ] (post-launch.01-readiness.ec8d58c2) Verify at least one recovery procedure has been rehearsed end to end.
- [ ] (post-launch.01-readiness.d1ffa3e8) Verify launching without a prepared response is a recorded decision with a date to revisit, rather than an oversight.
