const API_BASE = "http://127.0.0.1:5000/api";

const CATEGORIES = ["Electronics","Documents","Accessories","Bags","Clothing","Keys","Books","ID Cards","Other"];
const LOCATIONS = ["Library","Cafeteria","Hostel","Sports Complex","Main Building","Parking Lot","Auditorium","Computer Lab","Other"];

let currentPage = 1;

/* ---------- Tab Navigation ---------- */
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

/* ---------- Populate dropdowns ---------- */
function fillSelect(el, options, placeholder) {
  el.innerHTML = placeholder ? `<option value="">${placeholder}</option>` : "";
  options.forEach(o => {
    const opt = document.createElement("option");
    opt.value = o; opt.textContent = o;
    el.appendChild(opt);
  });
}
fillSelect(document.getElementById("filterCategory"), CATEGORIES, "All Categories");
fillSelect(document.getElementById("filterLocation"), LOCATIONS, "All Locations");
fillSelect(document.getElementById("reportCategory"), CATEGORIES);
fillSelect(document.getElementById("reportLocation"), LOCATIONS);

/* ---------- API helper ---------- */
async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || "Something went wrong.");
  }
  return body;
}

/* ---------- Browse Items ---------- */
async function loadItems(page = 1) {
  currentPage = page;
  const search = document.getElementById("searchInput").value.trim();
  const type = document.getElementById("filterType").value;
  const category = document.getElementById("filterCategory").value;
  const location = document.getElementById("filterLocation").value;

  const params = new URLSearchParams({ page, per_page: 9 });
  if (search) params.append("search", search);
  if (type) params.append("item_type", type);
  if (category) params.append("category", category);
  if (location) params.append("location", location);

  const grid = document.getElementById("itemsGrid");
  grid.innerHTML = `<p style="color:var(--text-dim)">Loading...</p>`;

  try {
    const { data, meta } = await api(`/items?${params.toString()}`);
    renderItems(data);
    renderPagination(meta);
  } catch (err) {
    grid.innerHTML = `<p class="result err">${err.message}</p>`;
  }
}

function renderItems(items) {
  const grid = document.getElementById("itemsGrid");
  if (!items.length) {
    grid.innerHTML = `<p style="color:var(--text-dim)">No items found.</p>`;
    return;
  }
  grid.innerHTML = items.map(item => `
    <div class="card item-card" onclick="openItemDetail(${item.id})">
      <div class="item-top">
        <span class="badge ${item.item_type}">${item.item_type}</span>
        <span class="badge ${item.status}">${item.status}</span>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description).slice(0, 90)}${item.description.length > 90 ? "..." : ""}</p>
      <div class="item-meta">
        <span>${item.category}</span>
        <span>•</span>
        <span>${item.location}</span>
      </div>
    </div>
  `).join("");
}

function renderPagination(meta) {
  const el = document.getElementById("pagination");
  if (!meta || meta.total_pages <= 1) { el.innerHTML = ""; return; }
  let html = "";
  for (let i = 1; i <= meta.total_pages; i++) {
    html += `<button class="${i === meta.page ? "active" : ""}" onclick="loadItems(${i})">${i}</button>`;
  }
  el.innerHTML = html;
}

document.getElementById("applyFilters").addEventListener("click", () => loadItems(1));
document.getElementById("searchInput").addEventListener("keydown", e => { if (e.key === "Enter") loadItems(1); });

/* ---------- Item Detail Modal ---------- */
async function openItemDetail(id) {
  try {
    const { data: item } = await api(`/items/${id}`);
    const modalContent = document.getElementById("modalContent");
    modalContent.innerHTML = `
      <h2>${escapeHtml(item.title)}</h2>
      <div class="detail-row"><span>Type</span><span>${item.item_type}</span></div>
      <div class="detail-row"><span>Status</span><span>${item.status}</span></div>
      <div class="detail-row"><span>Category</span><span>${item.category}</span></div>
      <div class="detail-row"><span>Location</span><span>${item.location}</span></div>
      <div class="detail-row"><span>Description</span><span>${escapeHtml(item.description)}</span></div>
      <div class="detail-row"><span>Reported By</span><span>${escapeHtml(item.reporter_name)}</span></div>
      <div class="detail-row"><span>Reported On</span><span>${new Date(item.created_at).toLocaleDateString()}</span></div>
      ${item.item_type === "found" && item.status === "active" ? claimFormHtml(item.id) : ""}
      <div id="claimSubmitResult" class="result"></div>
    `;
    document.getElementById("modal").classList.add("active");

    if (item.item_type === "found" && item.status === "active") {
      document.getElementById("claimForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        await submitClaim(item.id, e.target);
      });
    }
  } catch (err) {
    alert(err.message);
  }
}

function claimFormHtml(itemId) {
  return `
    <hr style="border-color: var(--border); margin: 16px 0;" />
    <h3 style="font-size:14px;">Submit a Claim</h3>
    <form id="claimForm" class="form">
      <input type="text" name="claimant_name" placeholder="Your Name" required />
      <input type="email" name="claimant_email" placeholder="Your Email" required />
      <input type="text" name="claimant_phone" placeholder="Phone (10 digits)" required />
      <textarea name="proof_description" rows="3" placeholder="Describe proof of ownership (min 15 chars)" required></textarea>
      <button type="submit" class="btn primary full">Submit Claim</button>
    </form>
  `;
}

async function submitClaim(itemId, form) {
  const payload = Object.fromEntries(new FormData(form).entries());
  const resultEl = document.getElementById("claimSubmitResult");
  try {
    const { data } = await api(`/items/${itemId}/claims`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    resultEl.className = "result ok";
    resultEl.textContent = `Claim submitted! Your claim ID is ${data.id}. Track it in the "Track Claim" tab.`;
    form.reset();
  } catch (err) {
    resultEl.className = "result err";
    resultEl.textContent = err.message;
  }
}

document.getElementById("modalClose").addEventListener("click", () => {
  document.getElementById("modal").classList.remove("active");
});

/* ---------- Report Item ---------- */
document.getElementById("reportForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = Object.fromEntries(new FormData(e.target).entries());
  const resultEl = document.getElementById("reportResult");
  try {
    const { data } = await api("/items", { method: "POST", body: JSON.stringify(payload) });
    resultEl.className = "result ok";
    resultEl.textContent = `Report submitted successfully! Item ID: ${data.id}`;
    e.target.reset();
  } catch (err) {
    resultEl.className = "result err";
    resultEl.textContent = err.message;
  }
});

/* ---------- Track Claim ---------- */
document.getElementById("trackBtn").addEventListener("click", async () => {
  const id = document.getElementById("claimIdInput").value;
  const resultEl = document.getElementById("trackResult");
  if (!id) { resultEl.className = "result err"; resultEl.textContent = "Enter a claim ID."; return; }
  try {
    const { data } = await api(`/claims/${id}`);
    resultEl.className = "result ok";
    resultEl.innerHTML = `Status: <strong>${data.status.toUpperCase()}</strong> — submitted on ${new Date(data.created_at).toLocaleString()}`;
  } catch (err) {
    resultEl.className = "result err";
    resultEl.textContent = err.message;
  }
});

/* ---------- Admin ---------- */
function adminHeaders() {
  const key = document.getElementById("adminKey").value.trim();
  return { "X-Admin-Key": key };
}

document.getElementById("loadStatsBtn").addEventListener("click", async () => {
  const grid = document.getElementById("statsGrid");
  try {
    const { data } = await api("/admin/stats", { headers: adminHeaders() });
    grid.innerHTML = `
      ${statCard(data.items.total, "Total Items")}
      ${statCard(data.items.active, "Active")}
      ${statCard(data.items.claimed, "Claimed")}
      ${statCard(data.items.returned, "Returned")}
      ${statCard(data.claims.pending, "Pending Claims")}
      ${statCard(data.resolution_rate_percent + "%", "Resolution Rate")}
    `;
  } catch (err) {
    grid.innerHTML = `<p class="result err">${err.message}</p>`;
  }
});

function statCard(num, label) {
  return `<div class="card"><div class="num">${num}</div><div class="lbl">${label}</div></div>`;
}

document.getElementById("approveBtn").addEventListener("click", () => handleClaimAction("approve"));
document.getElementById("rejectBtn").addEventListener("click", () => handleClaimAction("reject"));

async function handleClaimAction(action) {
  const id = document.getElementById("adminClaimId").value;
  const resultEl = document.getElementById("adminClaimResult");
  if (!id) { resultEl.className = "result err"; resultEl.textContent = "Enter a claim ID."; return; }
  try {
    const { data } = await api(`/claims/${id}/${action}`, { method: "PATCH", headers: adminHeaders() });
    resultEl.className = "result ok";
    resultEl.textContent = `Claim ${id} is now ${data.status}.`;
  } catch (err) {
    resultEl.className = "result err";
    resultEl.textContent = err.message;
  }
}

document.getElementById("markReturnedBtn").addEventListener("click", () => handleItemAction("return"));
document.getElementById("deleteItemBtn").addEventListener("click", () => handleItemAction("delete"));

async function handleItemAction(action) {
  const id = document.getElementById("adminItemId").value;
  const resultEl = document.getElementById("adminItemResult");
  if (!id) { resultEl.className = "result err"; resultEl.textContent = "Enter an item ID."; return; }
  try {
    if (action === "return") {
      const { data } = await api(`/items/${id}/return`, { method: "PATCH", headers: adminHeaders() });
      resultEl.className = "result ok";
      resultEl.textContent = `Item ${id} marked as ${data.status}.`;
    } else {
      await api(`/items/${id}`, { method: "DELETE", headers: adminHeaders() });
      resultEl.className = "result ok";
      resultEl.textContent = `Item ${id} deleted.`;
    }
  } catch (err) {
    resultEl.className = "result err";
    resultEl.textContent = err.message;
  }
}

/* ---------- Utility ---------- */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ---------- Init ---------- */
loadItems(); 