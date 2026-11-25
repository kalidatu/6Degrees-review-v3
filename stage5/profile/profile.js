const parentOrigin = new URL(document.referrer).origin;
const el = id => document.getElementById(id);
let revision = -1;
let pending = false;
function send(type, fields = {}) {
  parent.postMessage({isStreamlitMessage:true, type, ...fields}, parentOrigin);
}
function selectMember(id) {
  if (pending) return;
  pending = true;
  send("streamlit:setComponentValue", {dataType:"json", value:{
    view:revision, person:id, event:crypto.randomUUID()
  }});
}
function render(p) {
  el("initials").textContent = p.name.trim().split(/\s+/).map(word => word[0]).slice(0,2).join("");
  const photo = el("photo");
  photo.hidden = true;
  photo.removeAttribute("src");
  if (p.photo && /^https:\/\//i.test(p.photo)) {
    photo.onload = () => { photo.hidden = false; };
    photo.onerror = () => { photo.hidden = true; };
    photo.src = p.photo;
  }
  el("name").textContent = p.name;
  el("memberId").textContent = "Member ID " + p.id;
  el("location").textContent = p.location;
  el("location").hidden = !p.location;
  el("distance").textContent = p.distance ?? "No known connection";
  el("distance").classList.toggle("long", p.distance === null);
  el("count").textContent = p.contacts.length;
  el("bio").textContent = p.bio || "No biography added yet";
  el("bio").classList.toggle("muted", !p.bio);
  el("comingSoon").hidden = p.is_self;
  el("message").hidden = p.is_self;
  el("connect").hidden = p.is_self || p.connected;
  el("connected").hidden = !p.connected;
  const chips = el("chips");
  chips.replaceChildren();
  chips.scrollTop = 0;
  for (const member of p.contacts.slice(0, 10)) {
    const chip = document.createElement("button");
    chip.textContent = member.name;
    chip.title = "Explore " + member.name + " · ID " + member.id;
    chip.setAttribute("aria-label",chip.title);
    chip.onclick = () => selectMember(member.id);
    chips.append(chip);
  }
  if (!p.contacts.length) chips.textContent = "No direct connections";
}
addEventListener("message", event => {
  if (event.source !== parent || event.origin !== parentOrigin || event.data.type !== "streamlit:render") return;
  const p = event.data.args;
  if (p.view <= revision) return;
  revision = p.view;
  pending = false;
  render(p);
  showConnections(p);
});
new ResizeObserver(() => send("streamlit:setFrameHeight", {height:document.body.offsetHeight})).observe(document.body);
send("streamlit:componentReady", {apiVersion:1});
