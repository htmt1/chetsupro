(() => {
  const DEFAULT_HINT = "色・顔などは「詳細」で追加";
  const LONG_PLACEHOLDER = "ゲームに表示されたアンテナ名";
  const tidy = () => {
    document.querySelectorAll('small[id^="obsInfo"]').forEach((el) => el.classList.toggle("ui-default-hint", el.textContent.trim() === DEFAULT_HINT));
    document.querySelectorAll(`input[placeholder="${LONG_PLACEHOLDER}"]`).forEach((el) => { el.placeholder = "アンテナ名"; });
    const rows = document.getElementById("resultRows");
    const section = rows && rows.closest("section");
    if (section) section.dataset.uiResults = rows.children.length ? "has" : "empty";
  };
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; tidy(); });
  };
  tidy();
  new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
