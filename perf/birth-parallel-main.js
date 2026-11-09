function birthBlocks(config, size) {
  const na = config.ca.tips.length, nb = config.cb.tips.length, same = config.same, out = [];
  let start = null, filled = 0;
  for (let i = 0; i < na; i++) {
    let j = same ? i + 1 : 0;
    while (j < nb) {
      if (!start) {
        start = { i0: i, j0: j };
        filled = 0;
      }
      const take = Math.min(nb - j, size - filled);
      j += take;
      filled += take;
      if (filled >= size) {
        out.push(j < nb ? { ...start, i1: i, j1: j } : { ...start, i1: i + 1, j1: same ? i + 2 : 0 });
        start = null;
      }
    }
  }
  if (start) out.push({ ...start, i1: na, j1: 0 });
  return out;
}
function birthStatsTotal(parts) {
  const total = { tested: 0, generation: 0, shared: 0, missing: 0, unresolved: 0, errors: {}, considered: 0 };
  for (const part of parts) {
    if (!part) continue;
    for (const [key, value] of Object.entries(part)) {
      if (key === "errors") for (const [message, count] of Object.entries(value || {})) total.errors[message] = (total.errors[message] || 0) + count;
      else if (typeof value === "number") total[key] = (total[key] || 0) + value;
    }
  }
  return total;
}
async function runBirthWorker(config, hooks) {
  const cores = Math.max(1, Math.min(32, navigator.hardwareConcurrency || 2)), count = Math.min(cores, Math.floor(config.total / 4e3));
  if (count < 2 || typeof DenpaLargeData === "undefined") return runBirthWorkerSingle(config, hooks);
  const { onChunk, onPhase, isCancelled } = hooks;
  const snapshot = await store.snapshotAsync([.../* @__PURE__ */ new Set([...config.ca.tips, ...config.cb.tips])], { isCancelled });
  if (isCancelled()) return;
  const packed = await DenpaLargeData.encodeAsync(snapshot, { isCancelled });
  if (isCancelled()) return;
  const blocks = birthBlocks(config, Math.max(256, Math.ceil(config.total / (count * 12))));
  if (!blocks.length) return;
  const message = { ...config, ca: { id: config.ca.id, label: config.ca.label, tips: config.ca.tips }, cb: { id: config.cb.id, label: config.cb.label, tips: config.cb.tips } };
  await new Promise((resolve, reject) => {
    const url = URL.createObjectURL(new Blob([$("birthWorkerSource").textContent], { type: "text/javascript" }));
    const workers = [], buffers = blocks.map(() => ({ chunks: [], done: false })), parts = [];
    let nextBlock = 0, nextRelease = 0, finished = false, stopping = false, chain = Promise.resolve(), lastProgress = 0;
    const finish = (error) => {
      if (finished) return;
      finished = true;
      for (const w of workers) w.terminate();
      URL.revokeObjectURL(url);
      if (activeBirthWorker?.stop === stop) activeBirthWorker = null;
      error ? reject(error) : resolve();
    };
    const totals = () => birthStatsTotal(parts);
    const stop = () => {
      if (finished || stopping) return;
      stopping = true;
      for (const w of workers) w.terminate();
      chain = chain.then(async () => {
        for (let k = nextRelease; k < blocks.length; k++) {
          const buffer = buffers[k];
          while (buffer.chunks.length) {
            const chunk = buffer.chunks.shift();
            await onChunk({ nodes: chunk.nodes, ids: chunk.ids, stats: totals() });
          }
        }
        Object.assign(config.stats, totals());
      }).catch(() => {}).then(() => finish());
    };
    const release = async () => {
      while (!finished && !stopping && nextRelease < blocks.length) {
        const buffer = buffers[nextRelease];
        while (buffer.chunks.length && !finished) {
          const chunk = buffer.chunks.shift();
          await onChunk({ nodes: chunk.nodes, ids: chunk.ids, stats: totals() });
        }
        if (!buffer.done) break;
        nextRelease++;
      }
      if (!finished && !stopping && nextRelease >= blocks.length) {
        Object.assign(config.stats, totals());
        finish();
      }
    };
    const queueRelease = () => chain = chain.then(release).catch(finish);
    const assign = (worker) => {
      if (finished) return;
      if (nextBlock >= blocks.length) return;
      const index = nextBlock++;
      worker.postMessage({ type: "block", index, range: blocks[index] });
    };
    activeBirthWorker = { stop };
    onPhase("親候補を確認しています…");
    try {
      for (let k = 0; k < count; k++) {
        const worker = new Worker(url);
        workers.push(worker);
        worker.onerror = (event) => finish(Error("出生計算を続けられませんでした。" + (event.message || "計算用の処理を起動できません。")));
        worker.onmessage = async ({ data }) => {
          if (finished || stopping) return;
          try {
            if (isCancelled()) {
              stop();
              return;
            }
            if (data.type === "ready") assign(worker);
            else if (data.type === "progress") {
              parts[data.index] = data.stats;
              const now = performance.now();
              if (now - lastProgress > 150) {
                lastProgress = now;
                Object.assign(config.stats, totals());
                onPhase("検索中");
              }
            } else if (data.type === "chunk") {
              parts[data.index] = data.stats;
              buffers[data.index].chunks.push({ nodes: data.nodes, ids: data.ids });
              await queueRelease();
              if (!finished) worker.postMessage({ type: "ack" });
            } else if (data.type === "block-done") {
              parts[data.index] = data.stats;
              buffers[data.index].done = true;
              assign(worker);
              await queueRelease();
            } else if (data.type === "error") finish(Error(data.message));
          } catch (error) {
            finish(error);
          }
        };
        worker.postMessage({ type: "init", pool: packed, config: message });
      }
    } catch (error) {
      finish(error);
    }
  });
}
