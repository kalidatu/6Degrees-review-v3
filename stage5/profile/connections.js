// List presentation only. Python owns navigation and sends the history depth.
const pageSize = 25;
const panelHistory = [];
let panel;
let listPage = 0;
let selectedId = null;
let matches = [];
function showConnections(p) {
  const rows = el("rows");
  if (panel) panelHistory[panel.depth] = {
    query:el("localSearch").value, scope:el("scope").value, page:listPage, scroll:rows.scrollTop, selectedId
  };
  if (p.reset) panelHistory.length = 0;
  if (panel && p.depth > panel.depth && !p.revisit) panelHistory.length = p.depth;
  const saved = panelHistory[p.depth];
  selectedId = saved?.selectedId ?? null;
  panel = p;
  el("panelTitle").textContent = p.name + "'s Network (" + p.contacts.length.toLocaleString() + ")";
  el("localSearch").value = saved?.query ?? "";
  el("scope").value = saved?.scope ?? "All";
  filterConnections(saved?.page ?? 0);
  rows.scrollTop = saved?.scroll ?? 0;
}
function filterConnections(page) {
  const term = el("localSearch").value.trim().toLowerCase();
  const scope = el("scope").value;
  const unavailable = scope === "Route Relevant" && !panel.map_mode;
  matches = panel.contacts.filter(m =>
    (scope !== "Mutual" || m.mutual) &&
    (scope !== "Route Relevant" || m.relevant) &&
    (m.name.toLowerCase().includes(term) || String(m.id) === term.replace(/^#/, "")));
  const total = panel.contacts.length;
  const noun = total === 1 ? "connection" : "connections";
  el("matchCount").textContent = term || scope !== "All"
    ? matches.length.toLocaleString() + " of " + total.toLocaleString() + " " + noun + (matches.length === 1 ? " matches" : " match")
    : "Showing all " + total.toLocaleString() + " " + noun;
  listPage = Math.min(page, Math.max(0, Math.ceil(matches.length / pageSize)-1));
  el("hint").textContent = unavailable ? "Open a Connection Map to filter by route." :
    !matches.length ? "No matching connections." : "";
  drawPage();
}
function drawPage() {
  const start = listPage * pageSize;
  const rows = el("rows");
  rows.classList.toggle("large-list", matches.length > 15);
  rows.replaceChildren();
  rows.scrollTop = 0;
  for (const member of matches.slice(start, start + pageSize)) {
    const button = document.createElement("button");
    const id = document.createElement("small");
    id.textContent = "ID " + member.id;
    button.append(member.name, id);
    if (member.id === selectedId) button.setAttribute("aria-current", "true");
    button.onclick = () => {
      selectedId = member.id;
      selectMember(member.id);
    };
    rows.append(button);
  }
  el("pages").hidden = matches.length === 0;
  el("prev").hidden = el("next").hidden = matches.length <= pageSize;
  const end = Math.min(start + pageSize, matches.length);
  el("range").textContent = "Showing " + (start + 1).toLocaleString() + "–" + end.toLocaleString()
    + " of " + matches.length.toLocaleString() + (matches.length === 1 ? " match" : " matches");
  el("prev").disabled = listPage === 0;
  el("next").disabled = start + pageSize >= matches.length;
}
document.getElementById("localSearch").oninput = () => filterConnections(0);
document.getElementById("scope").onchange = () => filterConnections(0);
document.getElementById("prev").onclick = () => { listPage--; drawPage(); };
document.getElementById("next").onclick = () => { listPage++; drawPage(); };
