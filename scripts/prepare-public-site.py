"""Add public search metadata after applying the checked application build."""
import html
import json
import re
import sys
from pathlib import Path

URL = 'https://htmt1.github.io/chetsupro/'
TITLE = 'chetsupro（けつぷろ）｜3DS版 電波人間のRPG FREE! 解析ツール'
DESCRIPTION = ('chetsupro（けつぷろ）は、3DS版「電波人間のRPG FREE!」の解析ツールです。'
               'シード検索、レアキャッチ・激レアキャッチの個体検索、出生候補の計算とルート作成、'
               '親候補の保存・絞り込みに対応しています。')


def prepare(root):
    page = root / 'index.html'
    text = page.read_text(encoding='utf-8')
    text, title_count = re.subn(r'<title>[^<]*</title>',
                               '<title>' + html.escape(TITLE) + '</title>', text, count=1)
    if title_count != 1 or text.count('</head>') != 1:
        raise ValueError('Expected the chetsupro HTML shell')
    # This is a public presentation label, not an access-control setting.
    text = re.sub(r'<span class="private-label">自分用</span>', '', text)
    text = re.sub(r'<!-- public-search:start -->.*?<!-- public-search:end -->',
                  '', text, flags=re.S)
    structured = {
        '@context': 'https://schema.org', '@type': 'WebSite',
        'name': 'chetsupro', 'alternateName': 'けつぷろ',
        'url': URL, 'description': DESCRIPTION, 'inLanguage': 'ja',
    }
    tags = [
        '<!-- public-search:start -->',
        '<meta name="description" content="' + html.escape(DESCRIPTION, quote=True) + '">',
        '<meta name="robots" content="index,follow">',
        '<link rel="canonical" href="' + URL + '">',
        '<link rel="sitemap" type="application/xml" href="' + URL + 'sitemap.xml">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="chetsupro">',
        '<meta property="og:locale" content="ja_JP">',
        '<meta property="og:title" content="' + html.escape(TITLE, quote=True) + '">',
        '<meta property="og:description" content="' + html.escape(DESCRIPTION, quote=True) + '">',
        '<meta property="og:url" content="' + URL + '">',
        '<script type="application/ld+json">' + json.dumps(structured, ensure_ascii=False).replace('<', '\\u003c') + '</script>',
        '<!-- public-search:end -->',
    ]
    text = text.replace('</head>', '\n'.join(tags) + '</head>')
    page.write_text(text, encoding='utf-8')
    (root / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>' + URL + '</loc></url>\n</urlset>\n', encoding='utf-8')
    print('Prepared public title, description, canonical URL, structured data and sitemap; removed private label.')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]))
