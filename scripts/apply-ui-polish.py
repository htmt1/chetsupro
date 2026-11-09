import sys
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "ui"
MODULES = ("basic.html", "birth.html", "geki.html")
DEFAULT_PAGE_OLD = 'if (next === "home" || !PAGES[next]) next = "birth";'
DEFAULT_PAGE_NEW = 'if (next === "home" || !PAGES[next]) next = (() => { try { const last = localStorage.getItem("chetsupro.lastPage"); if (last && PAGES[last] && last !== "home") return last; } catch {} return "seed"; })();'


def inject(path, css, js):
    text = path.read_text(encoding="utf-8")
    if 'id="ui-polish-css"' in text:
        return text
    head = text.find("</head>")
    body = text.rfind("</body>")
    if head < 0 or body < 0:
        raise ValueError("Cannot find </head> or </body> in " + path.name)
    text = text[:head] + '<style id="ui-polish-css">' + css + "</style>" + text[head:]
    body = text.rfind("</body>")
    text = text[:body] + '<script id="ui-polish-js">' + js + "</script>" + text[body:]
    return text


def main(root):
    shell = root / "index.html"
    text = inject(shell, (UI / "shell.css").read_text(encoding="utf-8"), (UI / "shell.js").read_text(encoding="utf-8"))
    if DEFAULT_PAGE_OLD in text:
        text = text.replace(DEFAULT_PAGE_OLD, DEFAULT_PAGE_NEW, 1)
    elif DEFAULT_PAGE_NEW not in text:
        print("warning: default page logic not found; skipped")
    shell.write_text(text, encoding="utf-8")
    css = (UI / "module.css").read_text(encoding="utf-8")
    js = (UI / "module.js").read_text(encoding="utf-8")
    for name in MODULES:
        page = root / name
        page.write_text(inject(page, css, js), encoding="utf-8")
    print("Applied UI polish")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
