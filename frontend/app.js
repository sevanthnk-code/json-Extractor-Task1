"use strict";

const icons = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  receipt: '<path d="M5 3h14v18l-3-2-4 2-4-2-3 2z"/><path d="M8 8h8M8 12h8M8 16h4"/>',
  "file-user": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><circle cx="12" cy="13" r="2"/><path d="M8.5 19a3.5 3.5 0 0 1 7 0"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a7.8 7.8 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a7.8 7.8 0 0 1-1.5-.9l-1.7.7-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.7a7.8 7.8 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a7.8 7.8 0 0 1 1.5.9l1.7-.7 1.4 2.4-1.4 1.1a7 7 0 0 1 0 1.8z"/>',
  shield: '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11z"/><path d="m9 12 2 2 4-4"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  upload: '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M20 16.5v3A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5v-3"/>',
  arrow: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  sparkle: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3z"/><path d="m19 14 1 2.5 2.5 1-2.5 1L19 21l-1-2.5-2.5-1 2.5-1L19 14z"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeoff: '<path d="m3 3 18 18"/><path d="M10.6 10.6a2 2 0 0 0 2.8 2.8"/><path d="M9.9 5.2A10.7 10.7 0 0 1 12 5c6.5 0 10 7 10 7a14.8 14.8 0 0 1-3.2 4.1"/><path d="M6.2 6.2C3.5 8 2 12 2 12s3.5 7 10 7a10.7 10.7 0 0 0 2.1-.2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  close: '<path d="m18 6-12 12M6 6l12 12"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
  code: '<path d="m8 17-5-5 5-5M16 7l5 5-5 5M14 4l-4 16"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M5 21a7 7 0 0 1 14 0"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  refresh: '<path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M5.5 9A7 7 0 0 1 17 6.5L20 12M4 12l3 5.5A7 7 0 0 0 18.5 15"/>',
};

const state = {
  user: null,
  page: "dashboard",
  history: null,
  authMode: "login",
  authError: "",
  modalRecord: null,
  extractions: {
    invoice: { file: null, text: "", result: null, tab: "fields", busy: false, error: "" },
    resume: { file: null, text: "", result: null, tab: "fields", busy: false, error: "" },
  },
};

const authRoot = document.querySelector("#auth-root");
const appRoot = document.querySelector("#app-root");
const pageContent = document.querySelector("#page-content");
const toast = document.querySelector("#toast");
let toastTimer;

function icon(name, className = "") {
  const contents = icons[name] || icons.file;
  return `<svg class="${escapeHtml(className)}" viewBox="0 0 24 24" aria-hidden="true">${contents}</svg>`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function initials(name) {
  return String(name || "SmartExtract")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

function prettyDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function titleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 3600);
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Could not reach SmartExtract. Check that the FastAPI server is running.");
    }
    throw error;
  }

  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  let body;
  try {
    body = contentType.includes("application/json")
      ? await response.json()
      : contentType.includes("text/html")
        ? { detail: "The FastAPI API is not available at this address. Start the SmartExtract backend and refresh." }
        : { detail: await response.text() };
  } catch {
    body = { detail: `The server returned an unreadable response (${response.status}).` };
  }
  if (!response.ok) {
    const detail = body && typeof body === "object" ? body.detail : null;
    const message = Array.isArray(detail)
      ? detail.map((entry) => entry.msg).filter(Boolean).join(" ")
      : typeof detail === "string"
        ? detail
        : `The request failed (${response.status}).`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return body;
}

function renderAuth() {
  const isRegister = state.authMode === "register";
  authRoot.innerHTML = `
    <div class="auth-screen">
      <section class="auth-art" aria-label="SmartExtract introduction">
        <a class="auth-brand" href="/" aria-label="SmartExtract">
          <span class="brand-mark">S</span>
          <span><strong>SmartExtract</strong><small>Structured AI workspace</small></span>
        </a>
        <div class="auth-promo">
          <p class="eyebrow">Turn information into momentum</p>
          <h1>Less manual work.<br />More meaningful data.</h1>
          <p>Extract structured, validated information from invoices and resumes with a workspace designed for clarity.</p>
          <div class="auth-features">
            <div class="auth-feature"><span>${icon("check")}</span> Structured by your Pydantic schemas</div>
            <div class="auth-feature"><span>${icon("lock")}</span> Protected account and session</div>
            <div class="auth-feature"><span>${icon("sparkle")}</span> Powered by your Gemini integration</div>
          </div>
        </div>
        <div class="auth-footer">SmartExtract · AI structured data workspace</div>
      </section>
      <section class="auth-panel">
        <div class="auth-form-wrap">
          <div class="auth-mobile-brand"><span class="brand-mark">S</span><span><strong>SmartExtract</strong><small>Structured AI workspace</small></span></div>
          <p class="eyebrow">${isRegister ? "Create your workspace" : "Welcome back"}</p>
          <h2>${isRegister ? "Create your account" : "Sign in to SmartExtract"}</h2>
          <p class="auth-intro">${isRegister ? "Set up your account to start organizing document extractions." : "Enter your account details to continue to your workspace."}</p>
          ${state.authError ? `<div class="inline-error auth-error" role="alert">${escapeHtml(state.authError)}</div>` : ""}
          <form id="${isRegister ? "register-form" : "login-form"}" novalidate>
            ${isRegister ? `
              <div class="form-field">
                <label for="auth-name">Full name</label>
                <div class="input-wrap"><input class="form-input" id="auth-name" name="full_name" autocomplete="name" maxlength="120" placeholder="Your name" required /></div>
              </div>` : ""}
            <div class="form-field">
              <label for="auth-email">Email address</label>
              <div class="input-wrap"><input class="form-input" id="auth-email" name="email" type="email" autocomplete="email" maxlength="254" placeholder="you@company.com" required /></div>
            </div>
            <div class="form-field">
              <label for="auth-password">Password</label>
              <div class="input-wrap">
                <input class="form-input password-input" id="auth-password" name="password" type="password" autocomplete="${isRegister ? "new-password" : "current-password"}" minlength="${isRegister ? "12" : "1"}" maxlength="256" placeholder="${isRegister ? "At least 12 characters" : "Enter your password"}" required />
                <button class="password-toggle" type="button" data-action="toggle-password" aria-label="Show password" aria-pressed="false">${icon("eye")}</button>
              </div>
              ${isRegister ? '<div class="form-hint"><span>Use at least 12 characters.</span></div>' : ""}
            </div>
            ${isRegister ? `
              <div class="form-field">
                <label for="auth-confirm">Confirm password</label>
                <div class="input-wrap">
                  <input class="form-input password-input" id="auth-confirm" name="confirm_password" type="password" autocomplete="new-password" minlength="12" maxlength="256" placeholder="Re-enter your password" required />
                  <button class="password-toggle" type="button" data-action="toggle-password" aria-label="Show password" aria-pressed="false">${icon("eye")}</button>
                </div>
              </div>` : ""}
            <button class="button button-primary auth-submit" type="submit">${isRegister ? "Create account" : "Sign in"} <span>${icon("arrow")}</span></button>
          </form>
          <p class="auth-switch">${isRegister ? "Already have an account?" : "New to SmartExtract?"}
            <button type="button" data-action="${isRegister ? "show-login" : "show-register"}">${isRegister ? "Sign in" : "Create an account"}</button>
          </p>
          <p class="auth-legal">Your documents are sent to the configured Gemini service for extraction. Use only documents you are authorized to process.</p>
        </div>
      </section>
    </div>`;
}

function showAuth(message = "") {
  state.user = null;
  state.authError = message;
  appRoot.hidden = true;
  renderAuth();
}

function showApp(user) {
  state.user = user;
  state.authError = "";
  authRoot.innerHTML = "";
  appRoot.hidden = false;
  const sidebar = document.querySelector("#sidebar-user");
  sidebar.innerHTML = `
    <span class="user-avatar">${escapeHtml(initials(user.full_name))}</span>
    <span class="user-meta"><strong>${escapeHtml(user.full_name)}</strong><span>${escapeHtml(user.email)}</span></span>`;
  const avatar = document.querySelector("#topbar-avatar");
  avatar.textContent = initials(user.full_name);
  avatar.setAttribute("aria-label", `Settings for ${user.full_name}`);
  renderPage();
}

function pageHeading(eyebrow, title, description, extra = "") {
  return `<div class="page-heading">
    <div><p class="eyebrow">${escapeHtml(eyebrow)}</p><h1>${title}</h1><p>${description}</p></div>
    ${extra}
  </div>`;
}

function renderPage() {
  const titles = {
    dashboard: "Overview",
    invoice: "Invoice extraction",
    resume: "Resume extraction",
    history: "Extraction history",
    settings: "Settings",
  };
  document.querySelector("#page-title").textContent = titles[state.page] || "Overview";
  document.querySelectorAll(".nav-link[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === state.page);
  });
  if (state.page === "dashboard") renderDashboard();
  else if (state.page === "invoice" || state.page === "resume") renderExtraction(state.page);
  else if (state.page === "history") renderHistory();
  else renderSettings();
  if (state.modalRecord) renderRecordModal();
}

function recordSymbol(type) {
  const name = type === "resume" ? "file-user" : "receipt";
  return `<span class="activity-symbol ${type === "resume" ? "resume" : ""}">${icon(name)}</span>`;
}

function renderActivity(records) {
  if (!records || records.length === 0) {
    return `<div class="empty-state"><span class="placeholder-icon">${icon("clock")}</span><strong>No activity yet</strong><p>Your completed and failed extractions will appear here.</p></div>`;
  }
  return `<div class="activity-list">${records.slice(0, 5).map((record) => `
    <div class="activity-row">
      ${recordSymbol(record.document_type)}
      <div class="activity-copy"><strong>${escapeHtml(titleCase(record.document_type))} extraction</strong><span>${escapeHtml(prettyDate(record.processed_at))}</span></div>
      <span class="status-badge ${record.status === "success" ? "success" : "failed"}">${escapeHtml(record.status)}</span>
    </div>`).join("")}</div>`;
}

function renderDashboard() {
  const firstName = escapeHtml((state.user?.full_name || "there").trim().split(/\s+/)[0]);
  const stats = state.history?.stats;
  const metrics = stats
    ? [
      ["Documents processed", stats.total_documents, "file", ""],
      ["Successful extractions", stats.successful_extractions, "check", "green"],
      ["Failed extractions", stats.failed_extractions, "close", "red"],
    ]
    : null;
  const metricCards = metrics
    ? metrics.map(([label, value, symbol, color]) => `
      <article class="metric-card">
        <div class="metric-top"><span>${escapeHtml(label)}</span><span class="metric-icon ${color}">${icon(symbol)}</span></div>
        <p class="metric-value">${Number(value) || 0}</p><p class="metric-caption">From your extraction history</p>
      </article>`).join("")
    : `<article class="metric-card"><div class="loading-inline"><span class="spinner"></span> Loading your workspace stats…</div></article>`.repeat(3);

  pageContent.innerHTML = `
    ${pageHeading("Workspace overview", `Welcome back, ${firstName}`, "Your document extraction workspace is ready. Choose a workflow or pick up where you left off.", `<span class="date-chip">${icon("calendar")}${escapeHtml(new Date().toLocaleDateString(undefined, { dateStyle: "long" }))}</span>`)}
    <section class="metrics-grid" aria-label="Extraction statistics">${metricCards}</section>
    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-heading"><div><h2>Recent activity</h2><p>Your latest extraction attempts</p></div><button class="text-button" data-page="history">View history</button></div>
        ${state.history ? renderActivity(state.history.records) : '<div class="empty-state"><span class="loading-inline"><span class="spinner"></span> Loading activity…</span></div>'}
      </section>
      <section class="panel">
        <div class="panel-heading"><div><h2>Start extracting</h2><p>Choose a document workflow</p></div></div>
        <div class="quick-list">
          <button class="quick-card" data-page="invoice"><span class="quick-icon">${icon("receipt")}</span><span class="quick-copy"><strong>Extract an invoice</strong><span>Amounts, dates and billing details</span></span><span class="quick-arrow">${icon("chevron")}</span></button>
          <button class="quick-card" data-page="resume"><span class="quick-icon green">${icon("file-user")}</span><span class="quick-copy"><strong>Extract a resume</strong><span>Candidate, skills and experience</span></span><span class="quick-arrow">${icon("chevron")}</span></button>
        </div>
      </section>
    </div>`;
}

function renderExtraction(type) {
  const item = state.extractions[type];
  const isInvoice = type === "invoice";
  const title = isInvoice ? "Invoice extraction" : "Resume extraction";
  const description = isInvoice
    ? "Upload a plain-text invoice to extract validated billing details."
    : "Upload a plain-text resume to structure candidate information.";
  const symbol = isInvoice ? "receipt" : "file-user";
  const result = item.result?.data;
  const fileHtml = item.file ? `
    <div class="file-meta">
      <div class="file-meta-main"><span class="quick-icon">${icon("file")}</span><span><strong>${escapeHtml(item.file.name)}</strong><small>${formatBytes(item.file.size)} · text file ready</small></span></div>
      <button class="remove-file" data-action="remove-file" data-type="${type}" aria-label="Remove file">${icon("close")}</button>
    </div>
    <div class="preview-block"><div class="preview-heading"><span>Document preview</span><span>${item.text.length.toLocaleString()} characters</span></div><pre class="preview-text">${escapeHtml(item.text)}</pre></div>` : "";

  pageContent.innerHTML = `
    ${pageHeading(isInvoice ? "Document workflow" : "Candidate workflow", title, description)}
    <div class="extract-layout">
      <section class="extract-card">
        <div class="card-title"><span class="card-title-icon ${isInvoice ? "" : "green"}">${icon(symbol)}</span><span><h2>Upload your document</h2><p>Select a UTF-8 .txt file up to 2 MB. The document is sent to Gemini only when you start extraction.</p></span></div>
        <div class="upload-zone" data-dropzone="${type}">
          <span><span class="upload-icon">${icon("upload")}</span><strong>Drop your text file here</strong><p>or browse from your device · .txt only</p><button class="button button-secondary" type="button" data-action="choose-file" data-type="${type}">Browse files</button></span>
        </div>
        <input class="file-input" id="document-file" type="file" accept=".txt,text/plain" aria-label="Choose a plain text document" />
        ${fileHtml}
        ${item.error ? `<p class="inline-error" role="alert">${escapeHtml(item.error)}</p>` : ""}
        <div class="extract-actions"><p class="helper-copy">Results are validated against the existing Pydantic schema.</p><button class="button button-primary" data-action="extract" data-type="${type}" ${!item.text || item.busy ? "disabled" : ""}>${item.busy ? '<span class="spinner"></span> Extracting…' : `${icon("sparkle")} Extract ${isInvoice ? "invoice" : "resume"}`}</button></div>
      </section>
      <section class="result-card" aria-live="polite">
        ${result ? renderResult(type, item) : `
          <div class="result-header"><div><h2>Extraction result</h2><p>Validated data from your document</p></div></div>
          ${item.busy ? `<div class="result-placeholder"><span class="spinner"></span><strong style="margin-top:12px">Gemini is processing your document</strong><p>This can take a few moments. The validated response will appear here.</p></div>` : `<div class="result-placeholder"><span class="placeholder-icon">${icon("code")}</span><strong>Your structured result will appear here</strong><p>Upload a text document and start extraction to see actual validated JSON.</p></div>`}`}
      </section>
    </div>`;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function prettyJson(data) {
  return JSON.stringify(data, null, 2);
}

function invoiceFields(data) {
  const keys = [
    "invoice_number", "invoice_date", "due_date", "vendor_name", "customer_name",
    "customer_email", "subtotal_amount", "tax_amount", "total_amount", "currency",
    "payment_status",
  ];
  return `<div class="result-fields">${keys.map((key) => {
    const value = data[key];
    const rendered = value === null || value === undefined || value === "" ? "—" : String(value);
    return `<div class="field-tile"><label>${escapeHtml(titleCase(key))}</label><strong>${escapeHtml(rendered)}</strong></div>`;
  }).join("")}</div>`;
}

function resumeFields(data) {
  const scalarKeys = ["full_name", "email", "phone", "location", "professional_summary"];
  const scalars = scalarKeys.map((key) => {
    const value = data[key] || "—";
    return `<div class="field-tile ${key === "professional_summary" ? "wide" : ""}"><label>${escapeHtml(titleCase(key))}</label><strong>${escapeHtml(value)}</strong></div>`;
  }).join("");
  const skills = Array.isArray(data.skills) && data.skills.length
    ? data.skills.map((skill) => `<span class="skill-chip">${escapeHtml(skill)}</span>`).join("")
    : '<span class="muted-copy">No skills returned.</span>';
  const education = Array.isArray(data.education) && data.education.length
    ? data.education.map((entry) => `<article class="resume-entry"><strong>${escapeHtml(entry.degree || "Education")}${entry.field_of_study ? ` · ${escapeHtml(entry.field_of_study)}` : ""}</strong><span>${escapeHtml(entry.institution || "Institution not provided")}</span><small>${escapeHtml([entry.start_date, entry.end_date].filter(Boolean).join(" – ") || "Dates not provided")}</small></article>`).join("")
    : '<span class="muted-copy">No education entries returned.</span>';
  const experience = Array.isArray(data.experience) && data.experience.length
    ? data.experience.map((entry) => `<article class="resume-entry"><strong>${escapeHtml(entry.job_title || "Role not provided")}</strong><span>${escapeHtml(entry.employer || "Employer not provided")}${entry.location ? ` · ${escapeHtml(entry.location)}` : ""}</span><small>${escapeHtml([entry.start_date, entry.end_date].filter(Boolean).join(" – ") || "Dates not provided")}</small>${Array.isArray(entry.responsibilities) && entry.responsibilities.length ? `<ul>${entry.responsibilities.map((part) => `<li>${escapeHtml(part)}</li>`).join("")}</ul>` : ""}${Array.isArray(entry.achievements) && entry.achievements.length ? `<ul>${entry.achievements.map((part) => `<li>${escapeHtml(part)}</li>`).join("")}</ul>` : ""}</article>`).join("")
    : '<span class="muted-copy">No experience entries returned.</span>';
  const listSection = (label, values) => `<div class="resume-subsection"><label>${escapeHtml(label)}</label><div class="resume-list">${Array.isArray(values) && values.length ? values.map((value) => `<span class="resume-entry">${escapeHtml(value)}</span>`).join("") : '<span class="muted-copy">None returned.</span>'}</div></div>`;
  return `<div class="resume-result">
    <div class="result-fields">${scalars}</div>
    <div class="resume-subsection"><label>Technical skills</label><div class="skill-list">${skills}</div></div>
    <div class="resume-subsection"><label>Education</label><div class="resume-list">${education}</div></div>
    <div class="resume-subsection"><label>Experience</label><div class="resume-list">${experience}</div></div>
    ${listSection("Projects", data.projects)}
    ${listSection("Certifications", data.certifications)}
  </div>`;
}

function renderResult(type, item) {
  const data = item.result.data;
  const isJson = item.tab === "json";
  return `
    <div class="result-header"><div><h2>Extraction result</h2><p>Validated ${escapeHtml(titleCase(type))} · ${escapeHtml(prettyDate(item.result.processed_at))}</p></div><span class="status-badge success">validated</span></div>
    <div class="result-tabs" role="tablist" aria-label="Extraction result view">
      <button class="result-tab ${isJson ? "" : "active"}" data-action="result-tab" data-type="${type}" data-tab="fields" role="tab" aria-selected="${!isJson}">Fields</button>
      <button class="result-tab ${isJson ? "active" : ""}" data-action="result-tab" data-type="${type}" data-tab="json" role="tab" aria-selected="${isJson}">Validated JSON</button>
    </div>
    ${isJson ? `<pre class="json-view">${escapeHtml(prettyJson(data))}</pre>` : (type === "invoice" ? invoiceFields(data) : resumeFields(data))}
    <div class="result-actions"><button class="button button-secondary" data-action="download-result" data-type="${type}">${icon("download")} Download JSON</button></div>`;
}

function renderHistory() {
  const records = state.history?.records;
  const content = records?.length
    ? `<div class="table-wrap"><table class="data-table">
        <thead><tr><th>Document type</th><th>Processed</th><th>Status</th><th>Result</th></tr></thead>
        <tbody>${records.map((record) => `
          <tr>
            <td><span class="table-doc">${recordSymbol(record.document_type)}${escapeHtml(titleCase(record.document_type))}</span></td>
            <td>${escapeHtml(prettyDate(record.processed_at))}</td>
            <td><span class="status-badge ${record.status === "success" ? "success" : "failed"}">${escapeHtml(record.status)}</span></td>
            <td><button class="text-button" data-action="view-record" data-record-id="${record.id}">${record.data ? "View JSON" : "View details"}</button></td>
          </tr>`).join("")}</tbody>
      </table></div>`
    : state.history
      ? `<div class="empty-state"><span class="placeholder-icon">${icon("clock")}</span><strong>No extraction records yet</strong><p>Successful and failed attempts will appear here after processing.</p></div>`
      : `<div class="empty-state"><span class="loading-inline"><span class="spinner"></span> Loading your history…</span></div>`;
  pageContent.innerHTML = `
    ${pageHeading("Workspace records", "Extraction history", "Review your recent invoice and resume extraction attempts.")}
    <section class="panel"><div class="panel-heading"><div><h2>Recent documents</h2><p>Showing up to 100 most recent records</p></div><button class="icon-button" data-action="refresh-history" aria-label="Refresh history">${icon("refresh")}</button></div>${content}</section>
    ${state.modalRecord ? renderRecordModal() : ""}`;
}

function renderSettings() {
  const user = state.user || {};
  pageContent.innerHTML = `
    ${pageHeading("Your account", "Settings", "Manage your profile and sign out of your SmartExtract workspace.")}
    <div class="settings-grid">
      <section class="profile-card">
        <div class="profile-top"><span class="profile-avatar">${escapeHtml(initials(user.full_name))}</span><div><h2>${escapeHtml(user.full_name || "SmartExtract user")}</h2><p>SmartExtract account</p></div></div>
        <div class="profile-fields">
          <div class="profile-field"><label>Full name</label><strong>${escapeHtml(user.full_name || "—")}</strong></div>
          <div class="profile-field"><label>Email address</label><strong>${escapeHtml(user.email || "—")}</strong></div>
          <div class="profile-field"><label>Member since</label><strong>${escapeHtml(user.created_at ? new Date(user.created_at).toLocaleDateString() : "—")}</strong></div>
          <div class="profile-field"><label>Session security</label><strong>HttpOnly signed session</strong></div>
        </div>
        <div class="settings-help"><span class="note-icon">${icon("shield")}</span><div><strong>Account profile</strong><p>Profile editing and password reset are not available yet. Your account information is read from the authenticated backend.</p></div></div>
        <div class="danger-zone"><h3>Sign out</h3><p>This ends your current authenticated session on this device.</p><button class="button button-danger" data-action="logout">${icon("lock")} Log out</button></div>
      </section>
      <aside class="settings-help"><span class="note-icon">${icon("lock")}</span><div><strong>Private by default</strong><p>Session cookies are HttpOnly and SameSite. Documents are processed by your configured Gemini API and are not saved to extraction history; validated results and statuses are saved to your local SQLite database.</p></div></aside>
    </div>`;
}

function renderRecordModal() {
  const record = state.modalRecord;
  if (!record) return "";
  return `<div class="modal-backdrop" data-action="close-modal">
    <section class="record-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-heading"><div><p class="eyebrow">Extraction record</p><h2 id="modal-title">${escapeHtml(titleCase(record.document_type))} · ${escapeHtml(record.status)}</h2><p>${escapeHtml(prettyDate(record.processed_at))}</p></div><button class="icon-button" data-action="close-modal" aria-label="Close">${icon("close")}</button></div>
      ${record.data ? `<pre class="json-view">${escapeHtml(prettyJson(record.data))}</pre><div class="result-actions"><button class="button button-secondary" data-action="download-history" data-record-id="${record.id}">${icon("download")} Download JSON</button></div>` : `<p class="inline-error">${escapeHtml(record.error || "No validated JSON was produced for this attempt.")}</p>`}
    </section>
  </div>`;
}

function openPage(page) {
  if (!["dashboard", "invoice", "resume", "history", "settings"].includes(page)) return;
  state.page = page;
  state.modalRecord = null;
  closeNav();
  renderPage();
  if (!state.history && page !== "settings") refreshHistory();
}

function closeNav() {
  document.querySelector("#sidebar").classList.remove("open");
  document.querySelector(".mobile-scrim").classList.remove("visible");
}

async function refreshHistory() {
  try {
    state.history = await api("/api/extractions/history");
    renderPage();
  } catch (error) {
    if (error.status === 401) showAuth("Your session expired. Please sign in again.");
    else showToast(error.message || "Could not load extraction history.", true);
  }
}

async function loadDocument(file, type) {
  if (!file) return;
  const item = state.extractions[type];
  item.error = "";
  if (!file.name.toLowerCase().endsWith(".txt")) {
    item.file = null;
    item.text = "";
    item.result = null;
    item.error = "Choose a .txt file. Other document formats are not supported.";
    renderExtraction(type);
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    item.file = null;
    item.text = "";
    item.result = null;
    item.error = "The file is larger than 2 MB. Choose a smaller text file.";
    renderExtraction(type);
    return;
  }
  try {
    const bytes = await file.arrayBuffer();
    const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    if (!text.trim()) throw new Error("The selected text file is empty.");
    item.file = file;
    item.text = text;
    item.result = null;
    item.tab = "fields";
    item.error = "";
  } catch (error) {
    item.file = null;
    item.text = "";
    item.result = null;
    item.error = error instanceof TypeError
      ? "The selected file could not be decoded as UTF-8 text."
      : error.message || "Could not read the selected text file.";
  }
  renderExtraction(type);
}

async function startExtraction(type) {
  const item = state.extractions[type];
  if (!item.text || item.busy) return;
  item.busy = true;
  item.error = "";
  item.result = null;
  renderExtraction(type);
  try {
    const response = await api(`/api/extract/${type}`, {
      method: "POST",
      body: JSON.stringify({ document_text: item.text }),
    });
    item.result = response;
    item.tab = "fields";
    showToast(`${titleCase(type)} extraction validated successfully.`);
  } catch (error) {
    item.error = error.message || "Extraction failed. Please try again.";
    showToast(item.error, true);
  } finally {
    item.busy = false;
    renderExtraction(type);
    try {
      state.history = await api("/api/extractions/history");
    } catch (error) {
      if (error.status === 401) showAuth("Your session expired. Please sign in again.");
    }
  }
}

function downloadJson(data, filename) {
  const blob = new Blob([`${prettyJson(data)}\n`], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function validateForm(form) {
  if (!form.reportValidity()) return false;
  return true;
}

async function submitAuthForm(form) {
  const isRegister = form.id === "register-form";
  if (!validateForm(form)) return;
  const fields = new FormData(form);
  const payload = {
    email: String(fields.get("email") || "").trim(),
    password: String(fields.get("password") || ""),
  };
  if (isRegister) {
    payload.full_name = String(fields.get("full_name") || "").trim();
    if (payload.password !== String(fields.get("confirm_password") || "")) {
      state.authError = "The passwords do not match.";
      renderAuth();
      return;
    }
  }
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span> Please wait…';
  state.authError = "";
  try {
    const response = await api(isRegister ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showApp(response.user);
    state.history = null;
    await refreshHistory();
    showToast(isRegister ? "Your account is ready." : "Welcome back.");
  } catch (error) {
    state.authError = error.message || "Authentication failed. Please try again.";
    renderAuth();
  }
}

async function logout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
    state.history = null;
    state.modalRecord = null;
    showAuth("You have been signed out.");
  } catch (error) {
    showToast(error.message || "Could not sign out. Please try again.", true);
  }
}

document.addEventListener("click", async (event) => {
  const pageButton = event.target.closest("[data-page]");
  if (pageButton) {
    event.preventDefault();
    openPage(pageButton.dataset.page);
    return;
  }

  const control = event.target.closest("[data-action]");
  if (!control) return;
  const action = control.dataset.action;

  if (action === "show-register" || action === "show-login") {
    state.authMode = action === "show-register" ? "register" : "login";
    state.authError = "";
    renderAuth();
  } else if (action === "toggle-password") {
    const input = control.parentElement.querySelector("input");
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    control.innerHTML = icon(visible ? "eyeoff" : "eye");
    control.setAttribute("aria-label", visible ? "Hide password" : "Show password");
    control.setAttribute("aria-pressed", String(visible));
  } else if (action === "toggle-nav") {
    document.querySelector("#sidebar").classList.toggle("open");
    document.querySelector(".mobile-scrim").classList.toggle("visible");
  } else if (action === "close-nav") {
    closeNav();
  } else if (action === "choose-file") {
    document.querySelector("#document-file").click();
  } else if (action === "remove-file") {
    const item = state.extractions[control.dataset.type];
    item.file = null;
    item.text = "";
    item.result = null;
    item.error = "";
    renderExtraction(control.dataset.type);
  } else if (action === "extract") {
    await startExtraction(control.dataset.type);
  } else if (action === "result-tab") {
    state.extractions[control.dataset.type].tab = control.dataset.tab;
    renderExtraction(control.dataset.type);
  } else if (action === "download-result") {
    const item = state.extractions[control.dataset.type];
    if (item.result?.data) downloadJson(item.result.data, `smartextract-${control.dataset.type}.json`);
  } else if (action === "refresh-history") {
    await refreshHistory();
  } else if (action === "view-record") {
    const record = state.history?.records.find((entry) => String(entry.id) === control.dataset.recordId);
    if (record) {
      state.modalRecord = record;
      renderPage();
    }
  } else if (action === "close-modal") {
    if (event.target === control || control.classList.contains("icon-button")) {
      state.modalRecord = null;
      renderPage();
    }
  } else if (action === "download-history") {
    const record = state.history?.records.find((entry) => String(entry.id) === control.dataset.recordId);
    if (record?.data) downloadJson(record.data, `smartextract-${record.document_type}-${record.id}.json`);
  } else if (action === "logout") {
    await logout();
  }
});

document.addEventListener("submit", async (event) => {
  if (event.target.id === "login-form" || event.target.id === "register-form") {
    event.preventDefault();
    await submitAuthForm(event.target);
  }
});

document.addEventListener("change", async (event) => {
  if (event.target.id === "document-file" && event.target.files?.[0]) {
    await loadDocument(event.target.files[0], state.page);
    event.target.value = "";
  }
});

document.addEventListener("dragover", (event) => {
  const zone = event.target.closest("[data-dropzone]");
  if (!zone) return;
  event.preventDefault();
  zone.classList.add("dragover");
});

document.addEventListener("dragleave", (event) => {
  const zone = event.target.closest("[data-dropzone]");
  if (zone && !zone.contains(event.relatedTarget)) zone.classList.remove("dragover");
});

document.addEventListener("drop", async (event) => {
  const zone = event.target.closest("[data-dropzone]");
  if (!zone) return;
  event.preventDefault();
  zone.classList.remove("dragover");
  await loadDocument(event.dataTransfer.files?.[0], zone.dataset.dropzone);
});

async function start() {
  try {
    const response = await api("/api/auth/me");
    showApp(response.user);
    await refreshHistory();
  } catch (error) {
    showAuth(error.status === 401 ? "" : error.message);
  }
}

start();
