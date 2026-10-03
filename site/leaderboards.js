import { el, $, getJSON, fmt, bagUrl, parseIndex, initHeader, initFooterYear } from "./common.js";

initHeader();
initFooterYear();

const payload = await getJSON("data/index.json");
const bags = parseIndex(payload);

const TABS = [
  {
    id: "greatness",
    label: "Greatest",
    sort: (a, b) => a.rank - b.rank,
  },
  {
    id: "plusones",
    label: "Most +1s",
    sort: (a, b) =>
      b.plus_one_count - a.plus_one_count ||
      b.greatness_sum - a.greatness_sum ||
      a.id - b.id,
  },
  {
    id: "named",
    label: "Most named",
    sort: (a, b) =>
      b.named_count - a.named_count ||
      b.greatness_sum - a.greatness_sum ||
      a.id - b.id,
  },
  {
    id: "tier",
    label: "Tier score · beta",
    sort: (a, b) =>
      b.tier_score - a.tier_score ||
      b.greatness_sum - a.greatness_sum ||
      a.id - b.id,
  },
  {
    id: "deepest",
    label: "Deepest (lowest)",
    sort: (a, b) => a.greatness_sum - b.greatness_sum || a.id - b.id,
  },
];

const tabs = $("#tabs");
const rows = $("#rows");

function render(tab) {
  for (const button of tabs.children) {
    button.classList.toggle("active", button.dataset.id === tab.id);
  }
  location.hash = tab.id;

  const sorted = [...bags].sort(tab.sort).slice(0, 100);
  rows.replaceChildren(
    ...sorted.map((bag, index) =>
      el("tr", {},
        el("td", { class: "num muted" }, String(index + 1)),
        el("td", {}, el("a", { href: bagUrl(bag.id) }, `#${fmt(bag.id)}`)),
        el("td", { class: "num" }, String(bag.greatness_sum)),
        el("td", { class: "num gold" }, bag.plus_one_count ? String(bag.plus_one_count) : "–"),
        el("td", { class: "num" }, String(bag.named_count)),
        el("td", { class: "num" }, String(bag.tier_score)),
        el("td", { class: "num muted" }, `${bag.top_pct}%`),
      ),
    ),
  );
}

for (const tab of TABS) {
  tabs.append(
    el("button", {
      class: "tab",
      dataset: { id: tab.id },
      onclick: () => render(tab),
    }, tab.label),
  );
}

const initial = TABS.find((tab) => tab.id === location.hash.slice(1)) ?? TABS[0];
render(initial);
