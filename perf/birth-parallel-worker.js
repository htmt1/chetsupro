let parallelBirth = null;
self.onmessage = async (event) => {
  const data = event.data;
  if (data.type === "init") {
    try {
      const birthEngine = new BirthEngine(BIRTH_DATA), store = new BreedingStore(birthEngine, new RareEngine(RARE_DATA));
      const pool = await DenpaLargeData.decodeAsync(data.pool);
      DenpaLargeData.adopt(store.nodes, pool.nodes);
      await store.assertCurrentHeadsAsync([...data.config.ca.tips, ...data.config.cb.tips]);
      const pending = /* @__PURE__ */ new Map(), set = store.nodes.set;
      store.nodes.set = function(id, node) {
        if (!this.has(id)) pending.set(id, node);
        return set.call(this, id, node);
      };
      parallelBirth = { birthEngine, store, config: data.config, pending };
      self.postMessage({ type: "ready" });
    } catch (error) {
      self.postMessage({ type: "error", message: error.message || String(error) });
    }
    return;
  }
  if (data.type === "block") {
    try {
      const { birthEngine, store, config, pending } = parallelBirth, index = data.index, ids = [];
      const stats = { tested: 0, generation: 0, shared: 0, missing: 0, unresolved: 0, errors: {}, considered: 0 };
      const flush = async () => {
        if (!pending.size && !ids.length) {
          self.postMessage({ type: "progress", index, stats });
          await new Promise((r) => setTimeout(r, 0));
          return;
        }
        const ack = new Promise((resolve) => {
          acknowledge = resolve;
        });
        self.postMessage({ type: "chunk", index, nodes: [...pending.values()], ids: ids.splice(0), stats });
        pending.clear();
        await ack;
        acknowledge = null;
      };
      await computeBirthPairs(store, birthEngine, BIRTH_DATA, { ...config, stats, range: data.range, headsChecked: true }, { onChunk: flush, onResult: (id) => ids.push(id), isCancelled: () => false, batchSize: () => pending.size, budget: 32 });
      self.postMessage({ type: "block-done", index, stats });
    } catch (error) {
      self.postMessage({ type: "error", message: error.message || String(error) });
    }
    return;
  }
  return legacyBirthHandler(event);
};
