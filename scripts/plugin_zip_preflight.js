const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function readUInt16LE(buf, offset) { return buf.readUInt16LE(offset); }
function readUInt32LE(buf, offset) { return buf.readUInt32LE(offset); }

function entries(zipPath) {
  const buf = fs.readFileSync(zipPath);
  const result = [];
  let offset = 0;
  while (offset < buf.length - 30) {
    if (readUInt32LE(buf, offset) !== 0x04034b50) break;
    const method = readUInt16LE(buf, offset + 8);
    const compressedSize = readUInt32LE(buf, offset + 18);
    const fileNameLength = readUInt16LE(buf, offset + 26);
    const extraLength = readUInt16LE(buf, offset + 28);
    const name = buf.slice(offset + 30, offset + 30 + fileNameLength).toString("utf8");
    const dataStart = offset + 30 + fileNameLength + extraLength;
    const data = buf.slice(dataStart, dataStart + compressedSize);
    result.push({ name, method, data });
    offset = dataStart + compressedSize;
  }
  return result;
}

function inflate(entry) {
  if (entry.method === 0) return entry.data;
  if (entry.method === 8) return zlib.inflateRawSync(entry.data);
  throw new Error(`unsupported zip method ${entry.method}`);
}

const zipPath = process.argv[2];
const expected = process.argv[3] || process.env.ASTRBOT_EXPECT_PLUGIN || "astrbot_plugin_qq_voice_call";
if (!zipPath) throw new Error("usage: node plugin_zip_preflight.js <zip> [plugin]");
const list = entries(zipPath);
const names = list.map((item) => item.name);
const root = `${expected}/`;
if (names[0] !== root) throw new Error(`first entry must be ${root}`);
for (const name of names) {
  if (!name.startsWith(root)) throw new Error(`entry outside plugin root: ${name}`);
  if (name.includes("../") || name.includes("/.git/") || name.includes("__pycache__") || name.includes("/tests/") || name.includes("/scripts/")) {
    throw new Error(`unsafe or excluded entry: ${name}`);
  }
}
for (const required of ["metadata.yaml", "main.py", "call_session.py", "doubao_realtime_client.py", "napcat_call_adapter.py", "summary.py", "sylanne_bridge.py", "README.md", "_conf_schema.json"]) {
  if (!names.includes(root + required)) throw new Error(`missing ${required}`);
}
const metadata = list.find((item) => item.name === root + "metadata.yaml");
const metadataText = inflate(metadata).toString("utf8");
if (!metadataText.includes(`name: ${expected}`)) throw new Error("metadata name mismatch");
console.log(JSON.stringify({ ok: true, entries: names.length, size: fs.statSync(zipPath).size }));
