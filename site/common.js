// Shared helpers for The Loot Index.

export const SLOTS = ["weapon", "chest", "head", "waist", "foot", "hand", "neck", "ring"];

export const SLOT_LABEL = {
  weapon: "Weapon",
  chest: "Chest",
  head: "Head",
  waist: "Waist",
  foot: "Foot",
  hand: "Hand",
  neck: "Neck",
  ring: "Ring",
};

export const SITE = {
  name: "The Loot Index",
  lootContract: "0xFF9C1b15B16263C61d017ee9F65C50e4AE0113D7",
  starkLoot:
    "https://voyager.online/contract/0x05817c9625ad12198ebe04cc28e827e3b4d09465ddce16a6d7fc628afa3243ab",
  starkLootRepo: "https://github.com/Provable-Games/stark-loot",
};

export const MIN_BAG = 1;
export const MAX_BAG = 8000;

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined) continue;
    if (key === "class") node.className = value;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "dataset") Object.assign(node.dataset, value);
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

export const fmt = (value) => Number(value).toLocaleString("en-US");

export async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} for ${url}`);
  return response.json();
}

export function bagUrl(id) {
  return `bag.html?id=${id}`;
}

export function requestedBagId() {
  const params = new URLSearchParams(location.search);
  const id = Number(params.get("id"));
  return Number.isInteger(id) && id >= MIN_BAG && id <= MAX_BAG ? id : null;
}

export function openSeaUrl(id) {
  return `https://opensea.io/assets/ethereum/${SITE.lootContract}/${id}`;
}

export function initHeader() {
  const page = location.pathname.split("/").pop() || "index.html";
  for (const link of $$("nav.main a")) {
    const target = link.getAttribute("href");
    if (target === page) link.classList.add("active");
  }
}

export function initFooterYear() {
  const node = $("#year");
  if (node) node.textContent = String(new Date().getFullYear());
}

// Parse the compact index rows into objects using the fields array.
export function parseIndex(payload) {
  const fields = payload.fields;
  return payload.bags.map((row) => {
    const bag = {};
    fields.forEach((field, i) => (bag[field] = row[i]));
    return bag;
  });
}
