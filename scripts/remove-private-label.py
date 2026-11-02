"""Remove only the obsolete label from the public application shell."""
import sys
from pathlib import Path

page = Path(sys.argv[1]) / 'index.html'
text = page.read_text(encoding='utf-8')
page.write_text(text.replace('<span class="private-label">自分用</span>', ''), encoding='utf-8')
