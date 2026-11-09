import base64
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_SCANNER_SHA256 = "370dd77f6916c080336021dc864577e1b14d302ca30e88b28c296ae7f4ee30e3"
PAGES = ("basic.html", "geki.html")
THREADS_OLD = '$("threads").value = String(Math.min(4, (navigator.hardwareConcurrency || 4) >= 4 ? 4 : 2));'
THREADS_NEW = '(() => { const select = $("threads"), cores = Math.max(1, Math.min(64, navigator.hardwareConcurrency || 4)), counts = [...new Set([1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, cores].filter((n) => n <= cores))].sort((a, b) => a - b); select.replaceChildren(...counts.map((n) => { const o = document.createElement("option"); o.textContent = String(n); return o; })); select.value = String(cores); })();'
CHUNK_OLD = "Math.min(5e5, Math.round(m.done / Math.max(1, m.milliseconds) * 180))"
CHUNK_NEW = "Math.min(16777216, Math.round(m.done / Math.max(1, m.milliseconds) * 180))"
DEFAULT_CHUNK_OLD = "state.chunkSize || 2e5"
DEFAULT_CHUNK_NEW = "state.chunkSize || 1048576"


def replace_once(text, old, new, label, name):
    if new in text:
        return text
    if old not in text:
        print(f"warning: {label} not found in {name}; skipped")
        return text
    return text.replace(old, new, 1)


LOOP_OLD = "outer: for (let i = 0; i < ca.tips.length; i++) for (let j = same ? i + 1 : 0; j < cb.tips.length; j++) {\n    if (isCancelled()) break outer;"
LOOP_NEW = "const range = config.range;\n  outer: for (let i = range ? range.i0 : 0; i < ca.tips.length; i++) for (let j = range && i === range.i0 ? range.j0 : same ? i + 1 : 0; j < cb.tips.length; j++) {\n    if (range && (i > range.i1 || i === range.i1 && j >= range.j1)) break outer;\n    if (isCancelled()) break outer;"
HEADS_OLD = "await store.assertCurrentHeadsAsync([...ca.tips, ...cb.tips]);\n  if (isCancelled()) return;"
HEADS_NEW = "if (!config.headsChecked) await store.assertCurrentHeadsAsync([...ca.tips, ...cb.tips]);\n  if (isCancelled()) return;"
HANDLER_OLD = 'self.onmessage = async ({ data }) => {\n  if (data.type === "ack") {'
HANDLER_NEW = 'const legacyBirthHandler = async ({ data }) => {\n  if (data.type === "ack") {'
RUNNER_OLD = "async function runBirthWorker(config, { onChunk, onPhase, isCancelled }) {"
RUNNER_NEW = "async function runBirthWorkerSingle(config, { onChunk, onPhase, isCancelled }) {"


def patch_birth(site):
    path = site / "birth.html"
    text = path.read_text(encoding="utf-8")
    if "runBirthWorkerSingle" in text:
        return
    match = re.search(r'<script id="birthWorkerSource" type="text/plain">', text)
    if not match:
        print("warning: birth worker not found; skipped")
        return
    start = match.end()
    end = text.find("</script>", start)
    worker = text[start:end]
    anchors = [(worker, LOOP_OLD), (worker, HEADS_OLD), (worker, HANDLER_OLD), (text[:start], RUNNER_OLD)]
    if any(source.count(anchor) != 1 for source, anchor in anchors):
        print("warning: birth search code changed; parallel birth search skipped")
        return
    worker = worker.replace(LOOP_OLD, LOOP_NEW).replace(HEADS_OLD, HEADS_NEW).replace(HANDLER_OLD, HANDLER_NEW)
    worker += (ROOT / "perf" / "birth-parallel-worker.js").read_text(encoding="utf-8")
    head = text[:start].replace(RUNNER_OLD, (ROOT / "perf" / "birth-parallel-main.js").read_text(encoding="utf-8") + RUNNER_NEW)
    path.write_text(head + worker + text[end:], encoding="utf-8")


SHRINE_OLD = "count = Math.min(4, Math.max(1, (navigator.hardwareConcurrency || 2) - 1));"
SHRINE_NEW = "count = Math.min(32, Math.max(1, navigator.hardwareConcurrency || 2));"


def main(site):
    scanner = (ROOT / "perf" / "scanner.wasm").read_bytes()
    encoded = base64.b64encode(scanner).decode()
    for name in PAGES:
        path = site / name
        text = path.read_text(encoding="utf-8")
        match = re.search(r'(<script id="wasmData" type="text/plain">)(.*?)(</script>)', text, re.S)
        if not match:
            print(f"warning: scanner not found in {name}; skipped")
        else:
            current = base64.b64decode(match.group(2).strip())
            digest = hashlib.sha256(current).hexdigest()
            if current == scanner:
                pass
            elif digest == OLD_SCANNER_SHA256:
                text = text[:match.start(2)] + encoded + text[match.end(2):]
            else:
                print(f"warning: scanner in {name} differs from the verified version; kept as is")
        text = replace_once(text, THREADS_OLD, THREADS_NEW, "thread setting", name)
        text = replace_once(text, CHUNK_OLD, CHUNK_NEW, "chunk sizing", name)
        text = replace_once(text, DEFAULT_CHUNK_OLD, DEFAULT_CHUNK_NEW, "default chunk", name)
        path.write_text(text, encoding="utf-8")
    geki = site / "geki.html"
    geki.write_text(replace_once(geki.read_text(encoding="utf-8"), SHRINE_OLD, SHRINE_NEW, "boot seed workers", "geki.html"), encoding="utf-8")
    patch_birth(site)
    print("Applied speedups")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
