import {
  SLOTS, SLOT_LABEL, el, $, getJSON, fmt, bagUrl, requestedBagId, openSeaUrl,
  initHeader, initFooterYear,
} from "./common.js";
import { renderCard, downloadCard, cardText } from "./card.js";
import { fetchPackedBag, decodePacked, compareBag } from "./packed.js";

initHeader();
initFooterYear();

const loading = $("#loading");
const content = $("#content");
const errorBox = $("#error");
const id = requestedBagId();

if (!id) {
  loading.classList.add("hidden");
  errorBox.textContent = "Bag IDs are 1–8,000.";
} else {
  init(id);
}

async function init(bagId) {
  try {
    const [bag, stats] = await Promise.all([
      getJSON(`data/bag/${bagId}.json`),
      getJSON("data/stats.json"),
    ]);
    render(bag, stats);
    loading.classList.add("hidden");
    content.classList.remove("hidden");
  } catch (error) {
    loading.classList.add("hidden");
    errorBox.textContent = `Could not load bag #${bagId}: ${error.message}`;
  }
}

function chip(text, extra = "") {
  return el("span", { class: `chip ${extra}`.trim() }, text);
}

function render(bag, stats) {
  document.title = `Bag #${bag.id} — The Loot Index`;

  $("#bag-id").textContent = `BAG #${fmt(bag.id)}`;
  $("#rank-line").textContent =
    `Rank #${fmt(bag.rank)} of 8,000 · ${bag.band} · top ${bag.top_pct}% · tied with ${fmt(bag.tied_count)}`;
  $("#greatness").textContent = String(bag.greatness_sum);

  $("#chips").append(
    chip(`${bag.plus_one_count}× +1`, bag.plus_one_count ? "gold" : ""),
    chip(`${bag.named_count} named`),
    chip(`${bag.revealed_count} revealed`),
    chip(`max ${bag.max_greatness}`),
    chip(`tier score ${bag.tier_score} · beta`),
  );

  if (bag.id > 1) $("#prev").href = bagUrl(bag.id - 1);
  else $("#prev").classList.add("hidden");
  if (bag.id < 8000) $("#next").href = bagUrl(bag.id + 1);
  else $("#next").classList.add("hidden");
  $("#opensea").href = openSeaUrl(bag.id);

  renderItems(bag);
  renderCard($("#card"), bag);
  $("#download").addEventListener("click", () => downloadCard($("#card"), bag));
  $("#copy").addEventListener("click", async () => {
    const status = $("#copy-status");
    try {
      await navigator.clipboard.writeText(cardText(bag));
      status.textContent = "Copied.";
    } catch {
      status.textContent = "Clipboard unavailable — select the card text manually.";
    }
  });

  drawHistogram($("#histogram"), stats.summary.histogram, bag.greatness_sum);

  $("#verify").addEventListener("click", () => verify(bag));
}

function renderItems(bag) {
  const container = $("#items");
  for (const slot of SLOTS) {
    const item = bag.items[slot];
    const rowClass =
      item.greatness === 20 ? "perfect" : item.greatness >= 19 ? "great" : "";
    const meta = `#${item.id} · Tier ${item.tier} · ${item.type ? item.type.replaceAll("_", " ") : "no combat type"}`;
    const hidden =
      `suffix #${item.suffix_id} “${item.suffix}” · prefix #${item.name_prefix_id} “${item.name_prefix}” · name suffix #${item.name_suffix_id} “${item.name_suffix}”`;

    container.append(
      el("div", { class: `item ${rowClass}`.trim() },
        el("div", { class: "slot" }, SLOT_LABEL[slot]),
        el("div", {},
          el("div", { class: "name", dataset: { name: slot }, title: item.item_name },
            item.current_name || item.item_name),
          el("div", { class: "meta" }, meta),
          el("div", { class: "meta" }, hidden),
        ),
        el("div", { class: "bar-cell" },
          el("div", { class: "bar" },
            el("span", { style: `width:${Math.round((item.greatness / 20) * 100)}%` }))),
        el("div", { class: "score" },
          el("b", {}, String(item.greatness)),
          el("div", { class: "tags" },
            item.greatness === 20 ? el("span", { class: "tag gold" }, "+1")
              : item.greatness >= 19 ? el("span", { class: "tag light" }, "named")
              : item.greatness > 14 ? el("span", { class: "tag" }, "revealed")
              : null),
        ),
      ),
    );
  }

  $("#latent").addEventListener("change", (event) => {
    for (const slot of SLOTS) {
      const node = document.querySelector(`[data-name="${slot}"]`);
      const item = bag.items[slot];
      node.textContent = event.target.checked
        ? item.final_name
        : item.current_name || item.item_name;
      node.classList.toggle("latent", event.target.checked);
    }
  });
}

function drawHistogram(canvas, histogram, bagSum) {
  const W = 900;
  const H = 240;
  const DPR = 2;
  canvas.width = W * DPR;
  canvas.height = H * DPR;
  const ctx = canvas.getContext("2d");
  ctx.scale(DPR, DPR);

  const entries = Object.entries(histogram)
    .map(([sum, count]) => [Number(sum), count])
    .sort((a, b) => a[0] - b[0]);
  const min = entries[0][0];
  const max = entries[entries.length - 1][0];
  const maxCount = Math.max(...entries.map(([, count]) => count));
  const pad = { left: 34, right: 10, top: 14, bottom: 26 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;
  const barW = plotW / (max - min + 1);

  ctx.fillStyle = "#5f5d55";
  ctx.font = "12px ui-monospace, Menlo, monospace";
  ctx.fillText(String(maxCount), 2, pad.top + 10);
  ctx.fillText("0", 2, pad.top + plotH);

  ctx.strokeStyle = "#242429";
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, pad.top + plotH);
  ctx.lineTo(pad.left + plotW, pad.top + plotH);
  ctx.stroke();

  for (const [sum, count] of entries) {
    const height = (count / maxCount) * plotH;
    const x = pad.left + (sum - min) * barW;
    ctx.fillStyle = sum === bagSum ? "#e6cf7a" : "#3a3a42";
    ctx.fillRect(x, pad.top + plotH - height, Math.max(1, barW - 1), height);
  }

  ctx.fillStyle = "#8d8a7c";
  ctx.fillText(String(min), pad.left, H - 8);
  const maxLabel = String(max);
  ctx.fillText(maxLabel, pad.left + plotW - ctx.measureText(maxLabel).width, H - 8);
  const marker = `your bag · ${bagSum}`;
  ctx.fillStyle = "#e6cf7a";
  ctx.fillText(marker, pad.left + plotW - ctx.measureText(marker).width, pad.top + 10);
}

async function verify(bag) {
  const button = $("#verify");
  const status = $("#verify-status");
  const list = $("#verify-list");
  button.disabled = true;
  list.replaceChildren();
  status.textContent = "Fetching packed bag from Starknet mainnet…";

  try {
    const packed = await fetchPackedBag(bag.id);
    const decoded = decodePacked(packed);
    const results = compareBag(bag, decoded);
    const allMatch = results.every((result) => result.match);

    for (const result of results) {
      list.append(
        el("div", { class: "verify-item" },
          el("div", { class: "muted" }, SLOT_LABEL[result.slot]),
          el("div", { class: result.match ? "ok" : "bad" }, result.match ? "MATCH" : "MISMATCH"),
        ),
      );
    }
    status.textContent = allMatch
      ? `All 40 fields match get_packed_bag(${bag.id}) on Starknet mainnet.`
      : "Mismatch found — the index and the chain disagree.";
    status.className = allMatch ? "ok" : "bad";
  } catch (error) {
    status.className = "muted";
    status.textContent = `Could not verify: ${error.message}. The RPC may be rate-limited; try again.`;
  } finally {
    button.disabled = false;
  }
}
