(() => {
  const KEY = "chetsupro.lastPage";
  const root = document.documentElement;
  const nav = document.getElementById("nav");
  const remember = () => {
    const page = root.dataset.page;
    if (page) try { localStorage.setItem(KEY, page); } catch {}
  };
  const reveal = () => {
    const active = nav && nav.querySelector("button.active");
    if (!active || nav.scrollWidth <= nav.clientWidth) return;
    const navBox = nav.getBoundingClientRect(), box = active.getBoundingClientRect();
    const left = nav.scrollLeft + box.left - navBox.left - (navBox.width - box.width) / 2;
    nav.scrollTo({ left: Math.max(0, left), behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  };
  const moveCatalogMode = () => {
    const field = document.querySelector(".catalog-controls .search-field");
    const mode = field && field.querySelector(".filter-mode");
    if (mode) field.after(mode);
  };
  new MutationObserver(() => { remember(); reveal(); }).observe(root, { attributes: true, attributeFilter: ["data-page"] });
  remember();
  reveal();
  moveCatalogMode();
  addEventListener("load", () => { moveCatalogMode(); reveal(); });
})();
