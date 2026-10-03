// Client-side PackedLootBag decoder and Starknet verification.
//
// Mirrors the wire layout documented in stark-loot's src/packed.cairo:
// two 29-bit item words per u64 quarter at bit offsets
// 0, 29, 64, 93, 128, 157, 192, 221.
// Item word fields: id (7 bits), greatness (5), suffix_id (5),
// name_prefix_id (7), name_suffix_id (5).

export const STARK_LOOT_CONTRACT =
  "0x05817c9625ad12198ebe04cc28e827e3b4d09465ddce16a6d7fc628afa3243ab";
export const GET_PACKED_BAG_SELECTOR =
  "0x02f9d6e8d1be0438609a3a5ea285b8aa1db8e0e7bce1b08ce9e1edf0e389293c";

const RPC_URL = "https://api.cartridge.gg/x/starknet/mainnet";
const SLOT_ORDER = ["weapon", "chest", "head", "waist", "foot", "hand", "neck", "ring"];

const MASK7 = 0x7fn;
const MASK5 = 0x1fn;
const ITEM = 29n;
const QUARTER = 64n;

const itemAt = (value, shift) => (value >> shift) & ((1n << ITEM) - 1n);

function decodeWord(word) {
  return {
    id: Number(word & MASK7),
    greatness: Number((word >> 7n) & MASK5),
    suffix_id: Number((word >> 12n) & MASK5),
    name_prefix_id: Number((word >> 17n) & MASK7),
    name_suffix_id: Number((word >> 24n) & MASK5),
  };
}

/** Decode a packed bag felt into eight items, in canonical slot order. */
export function decodePacked(value) {
  const packed = BigInt(value);
  const low = packed & ((1n << 128n) - 1n);
  const high = packed >> 128n;
  const words = [
    itemAt(low, 0n),
    itemAt(low, ITEM),
    itemAt(low, QUARTER),
    itemAt(low, QUARTER + ITEM),
    itemAt(high, 0n),
    itemAt(high, ITEM),
    itemAt(high, QUARTER),
    itemAt(high, QUARTER + ITEM),
  ];
  return words.map(decodeWord);
}

/** Call get_packed_bag on the deployed stateless stark_loot contract. */
export async function fetchPackedBag(bagId) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "starknet_call",
      params: [
        {
          contract_address: STARK_LOOT_CONTRACT,
          entry_point_selector: GET_PACKED_BAG_SELECTOR,
          calldata: ["0x" + BigInt(bagId).toString(16)],
        },
        "latest",
      ],
    }),
  });
  const payload = await response.json();
  if (payload.error) throw new Error(payload.error.message || "rpc error");
  if (!Array.isArray(payload.result) || payload.result.length < 1) {
    throw new Error("unexpected RPC response");
  }
  return BigInt(payload.result[0]);
}

/** Compare decoded on-chain items against the indexed bag. */
export function compareBag(bag, decoded) {
  return SLOT_ORDER.map((slot, index) => {
    const indexed = bag.items[slot];
    const chain = decoded[index];
    const fields = ["id", "greatness", "suffix_id", "name_prefix_id", "name_suffix_id"];
    return {
      slot,
      match: fields.every((field) => indexed[field] === chain[field]),
      indexed,
      chain,
    };
  });
}
