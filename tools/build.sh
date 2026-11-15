#!/usr/bin/env bash
# Rebuild ../install.sh from install.sh.in (expands @@XXXX@@ Nerd Font glyph tokens).
set -euo pipefail
cd "$(dirname "$0")"
python3 -I - <<'PY'
import re
s = open('install.sh.in', encoding='utf-8').read()
s = re.sub(r'@@([0-9A-F]{4,5})@@', lambda m: chr(int(m.group(1), 16)), s)
open('../install.sh', 'w', encoding='utf-8').write(s)
PY
chmod +x ../install.sh
sha256sum ../install.sh
