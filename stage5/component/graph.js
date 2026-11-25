// Streamlit Components v1 iframe protocol. The frame and app share an origin.
const parentOrigin = new URL(document.referrer || window.location.href).origin;
function send(type, fields = {}) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...fields }, parentOrigin);
}

let network;
let view = -1;
let focus;
let mapMode = false;
let gesture;
let pending = false;
const graph = document.getElementById("graph");

function personAt(event) {
  const canvas = graph.querySelector("canvas");
  if (!canvas || event.target !== canvas) return undefined;
  const bounds = canvas.getBoundingClientRect();
  return network.getNodeAt({ x: event.clientX - bounds.left, y: event.clientY - bounds.top });
}

// Register one listener pair for the lifetime of the frame. A redraw or a
// vis-network selection notification cannot initiate navigation.
graph.addEventListener("pointerdown", event => {
  if (!event.isTrusted || !event.isPrimary || event.button !== 0 || pending || moving) return;
  const person = personAt(event);
  if (person === undefined || (person === focus && !mapMode)) return;
  gesture = { id: event.pointerId, person, view, x: event.clientX, y: event.clientY };
});
graph.addEventListener("pointercancel", () => { gesture = undefined; });
graph.addEventListener("pointerleave", () => { gesture = undefined; });
graph.addEventListener("pointerup", event => {
  const start = gesture;
  gesture = undefined;
  if (!event.isTrusted || !start || pending || start.id !== event.pointerId ||
      start.view !== view || start.person !== personAt(event) ||
      Math.hypot(event.clientX - start.x, event.clientY - start.y) > 8) return;
  pending = true;
  send("streamlit:setComponentValue", {
    dataType: "json", value: { person: start.person, view, event: crypto.randomUUID() }
  });
});
// Coordinates are expressed in the current view's frame. Interpolate from
// the actual on-screen geometry, including when Home interrupts a transition.
let animation = 0;
let moving = false;
let depth = 0;
let data;
const cameras = [];
function framing(nodes) {
  const xs = nodes.map(n => n.x), ys = nodes.map(n => n.y);
  const left = Math.min(...xs), right = Math.max(...xs);
  const top = Math.min(...ys), bottom = Math.max(...ys);
  return { position: {x: (left + right) / 2, y: (top + bottom) / 2 + 10},
           scale: Math.max(0.75, Math.min(1.15, graph.clientWidth / (right-left+116),
                                         graph.clientHeight / (bottom-top+115))) };
}
function camera() {
  return {position: network.getViewPosition(), scale: network.getScale()};
}
function transition(data, selected, target) {
  cancelAnimationFrame(animation);
  const from = camera();
  const previous = network.getPositions();
  const origin = previous[selected] || {x: 0, y: 0};
  const start = data.nodes.map(node => previous[node.id] || origin);
  const nodes = data.nodes.map((node, i) => ({...node, ...start[i]}));
  network.setData({nodes, edges: data.edges});
  const duration = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 460;
  const begin = performance.now();
  moving = true;
  function draw(now) {
    const t = duration ? Math.min(1, Math.max(0, (now - begin) / duration)) : 1;
    const blend = t * t * (3 - 2 * t);
    data.nodes.forEach((node, i) => {
      const point = start[i];
      network.moveNode(node.id, point.x + blend * (node.x - point.x),
                                point.y + blend * (node.y - point.y));
    });
    network.moveTo({position: {
      x: from.position.x + blend * (target.position.x - from.position.x),
      y: from.position.y + blend * (target.position.y - from.position.y)
    }, scale: from.scale + blend * (target.scale - from.scale)});
    network.redraw();
    moving = t < 1;
    if (moving) animation = requestAnimationFrame(draw);
  }
  draw(begin);
}
window.addEventListener("message", (event) => {
  if (event.source !== window.parent || event.origin !== parentOrigin ||
      event.data.type !== "streamlit:render") return;
  const args = event.data.args;
  if (args.view <= view) return;
  gesture = undefined;
  pending = false;
  focus = args.focus;
  mapMode = args.mapMode;
  view = args.view;
  data = args.graph;
  let target = framing(data.nodes);
  if (network) {
    if (args.reset) {
      cameras.length = 0;
    } else if (args.depth !== depth) {
      cameras[depth] = camera();
      if (args.revisit && cameras[args.depth]) target = cameras[args.depth];
      if (!args.revisit) cameras.length = args.depth;
    }
    transition(data, focus, target);
  } else {
    network = new vis.Network(graph, args.graph, {
      physics: false,
      nodes: { shape: "dot", size: 19, borderWidth: 2, font: { size: 16, color: "#172f36", strokeWidth: 3, strokeColor: "#eff6f5" } },
      edges: { width: 1.8, color: "#738b90", smooth: false },
      interaction: { dragNodes: false, dragView: true, zoomView: true, selectable: false }
    });
    network.moveTo(target);
  }
  depth = args.depth;
  send("streamlit:setFrameHeight", { height: 528 });
});
let lastWidth = 0;
new ResizeObserver(() => {
  if (network && graph.clientWidth !== lastWidth && !moving) network.moveTo(framing(data.nodes));
  lastWidth = graph.clientWidth;
}).observe(graph);
send("streamlit:componentReady", { apiVersion: 1 });
