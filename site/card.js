// Share-card renderer: draws a 1200x630 bag card to a canvas.

import { SLOTS, SLOT_LABEL, fmt } from "./common.js";

const W = 1200;
const H = 630;
const DPR = 2;

const INK = "#f2f0e6";
const MUTED = "#8d8a7c";
const LINE = "#26262c";
const GOLD = "#e6cf7a";
const BG = "#09090a";

const font = (size, weight = 400) =>
  `${weight} ${size}px ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace`;

export function renderCard(canvas, bag) {
  canvas.width = W * DPR;
  canvas.height = H * DPR;
  canvas.style.aspectRatio = `${W} / ${H}`;
  const ctx = canvas.getContext("2d");
  ctx.scale(DPR, DPR);

  ctx.fillStyle = BG;
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = INK;
  ctx.lineWidth = 3;
  ctx.strokeRect(22, 22, W - 44, H - 44);

  // Header
  ctx.fillStyle = MUTED;
  ctx.font = font(17, 700);
  ctx.fillText("T H E   L O O T   I N D E X", 56, 76);

  ctx.textAlign = "right";
  ctx.fillStyle = INK;
  ctx.font = font(17, 700);
  ctx.fillText(`RANK #${fmt(bag.rank)} / 8,000`, W - 56, 76);

  // Bag number and rank line
  ctx.textAlign = "left";
  ctx.fillStyle = INK;
  ctx.font = font(62, 700);
  ctx.fillText(`BAG #${fmt(bag.id)}`, 56, 176);

  ctx.fillStyle = MUTED;
  ctx.font = font(19);
  ctx.fillText(
    `${bag.band} · top ${bag.top_pct}% · tied with ${fmt(bag.tied_count)} · tier score ${bag.tier_score}`,
    56,
    208
  );

  // Greatness block
  ctx.textAlign = "right";
  ctx.fillStyle = INK;
  ctx.font = font(132, 700);
  ctx.fillText(String(bag.greatness_sum), W - 56, 186);
  ctx.fillStyle = MUTED;
  ctx.font = font(16, 400);
  ctx.fillText("G R E A T N E S S", W - 56, 216);

  // Items: two columns of four
  const colW = (W - 112) / 2;
  SLOTS.forEach((slot, index) => {
    const item = bag.items[slot];
    const x = 56 + (index % 2) * colW;
    const y = 292 + Math.floor(index / 2) * 66;

    ctx.textAlign = "left";
    ctx.fillStyle = MUTED;
    ctx.font = font(12, 400);
    ctx.fillText(SLOT_LABEL[slot].toUpperCase(), x, y);

    ctx.fillStyle = item.greatness === 20 ? GOLD : INK;
    ctx.font = font(21, item.greatness >= 19 ? 700 : 400);
    ctx.fillText(item.item_name, x, y + 26);

    if (item.greatness === 20) {
      const nameWidth = ctx.measureText(item.item_name).width;
      ctx.fillStyle = GOLD;
      ctx.font = font(12, 700);
      ctx.fillText("+1", x + nameWidth + 8, y + 26);
    } else if (item.greatness >= 19) {
      const nameWidth = ctx.measureText(item.item_name).width;
      ctx.fillStyle = MUTED;
      ctx.font = font(12, 400);
      ctx.fillText("NAMED", x + nameWidth + 8, y + 26);
    }

    ctx.textAlign = "right";
    ctx.fillStyle = item.greatness >= 19 ? INK : MUTED;
    ctx.font = font(21, item.greatness >= 19 ? 700 : 400);
    ctx.fillText(String(item.greatness), x + colW - 12, y + 26);
  });

  // Footer
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(56, 570);
  ctx.lineTo(W - 56, 570);
  ctx.stroke();

  ctx.textAlign = "left";
  ctx.fillStyle = MUTED;
  ctx.font = font(16);
  ctx.fillText("greatness is the only stat the contract rolls", 56, 602);

  ctx.textAlign = "right";
  ctx.fillText(location.host || "the loot index", W - 56, 602);
}

export function downloadCard(canvas, bag) {
  canvas.toBlob((blob) => {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `loot-bag-${bag.id}.png`;
    link.click();
    URL.revokeObjectURL(link.href);
  }, "image/png");
}

export function cardText(bag) {
  const lines = [
    `Bag #${bag.id} — rank #${bag.rank} of 8,000 (${bag.band}, top ${bag.top_pct}%)`,
    `Greatness ${bag.greatness_sum} · ${bag.plus_one_count}x +1 · ${bag.named_count} named`,
  ];
  for (const slot of SLOTS) {
    const item = bag.items[slot];
    const tag = item.greatness === 20 ? " +1" : item.greatness >= 19 ? " (named)" : "";
    lines.push(`${SLOT_LABEL[slot]}: ${item.item_name} (${item.greatness})${tag}`);
  }
  return lines.join("\n");
}
