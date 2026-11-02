function filterAccounts(input) {
  const query = input.value.trim().toLowerCase();
  const select = input.closest("tr").querySelector('[name="account_id"]');
  for (const option of select.options) {
    if (!option.value) {
      option.hidden = false;
      continue;
    }
    const inactive = option.dataset.active !== "1" && !option.selected;
    const matches = !query || option.textContent.toLowerCase().includes(query) || option.selected;
    option.hidden = inactive || !matches;
  }
}

function syncAnalytics(row) {
  const account = row.querySelector('[name="account_id"]');
  const analytic = row.querySelector('[name="analytic_id"]');
  if (!account || !analytic) return;
  const selected = account.selectedOptions[0];
  const required = selected && selected.dataset.required === "1";
  let visible = 0;
  for (const option of analytic.options) {
    if (!option.value) {
      option.hidden = false;
      continue;
    }
    const inactive = option.dataset.active !== "1";
    const match = option.dataset.account === account.value && (!inactive || option.selected);
    option.hidden = !match;
    if (match) visible += 1;
  }
  const current = analytic.selectedOptions[0];
  if (current && current.hidden) analytic.value = "";
  analytic.classList.toggle("need", Boolean(required && visible > 0 && !analytic.value));
  const adder = row.querySelector(".add-analytic");
  if (adder) adder.hidden = !account.value;
  closeNewAnalytic(row);
}

function isSharedAmount() {
  const field = document.querySelector("label.shared-amount");
  return Boolean(field && !field.hidden);
}

function revealLineAmounts() {
  const shared = document.getElementById("entry-amount");
  document.querySelectorAll("#lines tr.line").forEach((row) => {
    const input = row.querySelector('[name="line_amount"]');
    if (input && !input.value.trim() && shared) input.value = shared.value;
  });
  if (shared) shared.value = "";
  document.querySelectorAll(".line-amt").forEach((el) => { el.hidden = false; });
  document.querySelectorAll(".shared-amount").forEach((el) => { el.hidden = true; });
}

function maybeCollapseAmounts() {
  const rows = [...document.querySelectorAll("#lines tr.line")];
  if (isSharedAmount() || rows.length > 2) return;
  const values = rows.map((row) => row.querySelector('[name="line_amount"]').value.trim());
  const filled = values.filter(Boolean);
  if (new Set(filled).size > 1) return;
  const shared = document.getElementById("entry-amount");
  if (shared) shared.value = filled[0] || "";
  rows.forEach((row) => { row.querySelector('[name="line_amount"]').value = ""; });
  document.querySelectorAll(".line-amt").forEach((el) => { el.hidden = true; });
  document.querySelectorAll(".shared-amount").forEach((el) => { el.hidden = false; });
}

function closeNewAnalytic(row) {
  const panel = row.querySelector(".new-analytic");
  if (!panel) return;
  panel.hidden = true;
  panel.querySelectorAll("input").forEach((input) => { input.value = ""; });
  const error = panel.querySelector(".na-error");
  if (error) {
    error.hidden = true;
    error.textContent = "";
  }
}

function showAnalyticError(panel, text) {
  const error = panel.querySelector(".na-error");
  error.textContent = text || "";
  error.hidden = !error.textContent;
}

async function saveAnalytic(row) {
  const panel = row.querySelector(".new-analytic");
  const save = panel.querySelector(".na-save");
  if (save.disabled) return;
  save.disabled = true;
  const account = row.querySelector('[name="account_id"]');
  const secInput = panel.querySelector(".na-sec");
  const body = new FormData();
  body.set("account_id", account.value);
  body.set("code", panel.querySelector(".na-code").value.trim());
  body.set("name_fr", panel.querySelector(".na-fr").value.trim());
  body.set("name_de", secInput && secInput.dataset.lang === "de" ? secInput.value.trim() : "");
  body.set("name_ru", secInput && secInput.dataset.lang === "ru" ? secInput.value.trim() : "");
  const form = document.getElementById("entry-form");
  try {
    const response = await fetch("/ecritures/analytique", { method: "POST", body });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      showAnalyticError(panel, (data.messages || []).join(" "));
      return;
    }
    document.querySelectorAll('[name="analytic_id"]').forEach((select) => {
      if ([...select.options].some((option) => option.value === String(data.id))) return;
      const option = document.createElement("option");
      option.value = String(data.id);
      option.dataset.account = String(data.account_id);
      option.dataset.active = "1";
      option.textContent = data.label;
      select.appendChild(option);
    });
    row.querySelector('[name="analytic_id"]').value = String(data.id);
    closeNewAnalytic(row);
    document.querySelectorAll("#lines tr.line").forEach((line) => syncAnalytics(line));
  } catch (err) {
    showAnalyticError(panel, form ? form.dataset.net : "");
  } finally {
    save.disabled = false;
  }
}

function bindEntryForm() {
  const tbody = document.querySelector("#lines tbody");
  if (!tbody) return;
  tbody.addEventListener("click", (event) => {
    const addAnalytic = event.target.closest(".add-analytic");
    if (addAnalytic) {
      const panel = addAnalytic.closest("tr.line").querySelector(".new-analytic");
      panel.hidden = false;
      panel.querySelector(".na-code").focus();
      return;
    }
    const save = event.target.closest(".na-save");
    if (save) {
      saveAnalytic(save.closest("tr.line"));
      return;
    }
    const button = event.target.closest(".remove-line");
    if (!button) return;
    if (tbody.querySelectorAll("tr.line").length <= 2) return;
    button.closest("tr.line").remove();
    maybeCollapseAmounts();
  });
  tbody.addEventListener("change", (event) => {
    if (event.target.name === "account_id") syncAnalytics(event.target.closest("tr.line"));
  });
  tbody.addEventListener("input", (event) => {
    if (event.target.classList.contains("acct-filter")) filterAccounts(event.target);
  });
  tbody.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    if (event.target.classList.contains("acct-filter") || event.target.closest(".new-analytic")) {
      event.preventDefault();
    }
    if (event.target.closest(".new-analytic")) saveAnalytic(event.target.closest("tr.line"));
  });
  document.getElementById("add-line").addEventListener("click", () => {
    if (isSharedAmount() && tbody.querySelectorAll("tr.line").length >= 2) revealLineAmounts();
    const copy = tbody.querySelector("tr.line").cloneNode(true);
    copy.querySelectorAll("input").forEach((input) => { input.value = ""; });
    copy.querySelectorAll("select").forEach((select) => { select.value = ""; });
    const side = copy.querySelector('[name="side"]');
    if (side) side.value = "credit";
    tbody.appendChild(copy);
    filterAccounts(copy.querySelector(".acct-filter"));
    syncAnalytics(copy);
  });
  tbody.querySelectorAll("tr.line").forEach((row) => {
    filterAccounts(row.querySelector(".acct-filter"));
    syncAnalytics(row);
  });
}

function bindChartFilter() {
  const input = document.getElementById("chart-filter");
  if (!input) return;
  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    document.querySelectorAll("tr.acct").forEach((row) => {
      const text = row.dataset.search || "";
      row.hidden = Boolean(query) && !text.includes(query);
    });
    document.querySelectorAll("tr.classhead").forEach((row) => {
      let sibling = row.nextElementSibling;
      let any = false;
      while (sibling && !sibling.classList.contains("classhead")) {
        if (sibling.classList.contains("acct") && !sibling.hidden) any = true;
        sibling = sibling.nextElementSibling;
      }
      row.hidden = !any;
    });
  });
}

function bindStatementGuess() {
  const codeInput = document.getElementById("account-code");
  const statement = document.getElementById("statement");
  if (!codeInput || !statement) return;
  let touched = statement.dataset.touched === "1";
  statement.addEventListener("change", () => { touched = true; });
  codeInput.addEventListener("input", () => {
    if (touched) return;
    const code = codeInput.value.trim();
    if (!/^[1-9]\d{2,7}$/.test(code)) return;
    const number = Number(code);
    const digit = Number(code[0]);
    let value = "asset";
    if (digit === 2) value = number >= 2800 ? "equity" : "liability";
    else if (digit === 9) value = "closing";
    else if (digit >= 3 && digit <= 8) value = "pl";
    statement.value = value;
  });
}

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const message = form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });
});

const yearSelect = document.getElementById("year-select");
if (yearSelect) {
  yearSelect.addEventListener("change", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("year", yearSelect.value);
    url.searchParams.delete("msg");
    window.location.href = url.toString();
  });
}

bindEntryForm();
bindChartFilter();
bindStatementGuess();
