import {
  el, $, getJSON, fmt, bagUrl, parseIndex, initHeader, initFooterYear, MIN_BAG, MAX_BAG,
} from "./common.js";

initHeader();
initFooterYear();

const input = $("#bag-input");
const error = $("#search-error");

$("#search").addEventListener("submit", (event) => {
  event.preventDefault();
  const id = Number(input.value);
  if (!Number.isInteger(id) || id < MIN_BAG || id > MAX_BAG) {
    error.textContent = `Enter a bag ID between ${fmt(MIN_BAG)} and ${fmt(MAX_BAG)}.`;
    error.classList.remove("hidden");
    return;
  }
  location.href = bagUrl(id);
});

$("#random").addEventListener("click", () => {
  location.href = bagUrl(MIN_BAG + Math.floor(Math.random() * MAX_BAG));
});

const [indexPayload, statsPayload] = await Promise.all([
  getJSON("data/index.json"),
  getJSON("data/stats.json"),
]);

const bags = parseIndex(indexPayload);
const summary = statsPayload.summary;

function stat(label, value, sub) {
  return el("div", { class: "stat" },
    el("div", { class: "label" }, label),
    el("div", { class: "value" }, value),
    el("div", { class: "sub" }, sub),
  );
}

$("#stats").append(
  stat("Bags", fmt(bags.length), "IDs 1–8,000"),
  stat("Median greatness", String(summary.greatness_sum.median), `mean ${summary.greatness_sum.mean}`),
  stat("Range", `${summary.greatness_sum.min}–${summary.greatness_sum.max}`, "sum of 8 items"),
  stat("Top bag", `#${summary.top_greatness[0].id}`, `${summary.top_greatness[0].greatness_sum} greatness`),
);

const top10 = [...bags].sort((a, b) => a.rank - b.rank).slice(0, 10);
const tbody = $("#top10");
for (const bag of top10) {
  tbody.append(el("tr", {},
    el("td", { class: "num" }, String(bag.rank)),
    el("td", {}, el("a", { href: bagUrl(bag.id) }, `#${bag.id}`)),
    el("td", { class: "num" }, String(bag.greatness_sum)),
    el("td", { class: "num gold" }, bag.plus_one_count ? String(bag.plus_one_count) : "–"),
    el("td", { class: "num" }, String(bag.named_count)),
    el("td", { class: "num muted" }, `${bag.top_pct}%`),
  ));
}
