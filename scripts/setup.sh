#!/usr/bin/env bash
# Create (or repair) the shared Chatterbox venv. Idempotent: exits fast if it works.
#   CHATTERBOX_HOME  default ~/.local/share/chatterbox-tts
set -euo pipefail
HOME_DIR="${CHATTERBOX_HOME:-$HOME/.local/share/chatterbox-tts}"
VENV="$HOME_DIR/venv"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -x "$VENV/bin/python" ]] && "$VENV/bin/python" -c "from chatterbox.tts_turbo import ChatterboxTurboTTS" 2>/dev/null; then
  echo "chatterbox venv OK: $VENV"; exit 0
fi

# Python 3.11 (what upstream tests on). Prefer pyenv's, else any python3.11.
PY="${CHATTERBOX_PYTHON:-}"
if [[ -z "$PY" ]]; then
  for c in "$HOME"/.pyenv/versions/3.11*/bin/python python3.11; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
[[ -n "$PY" ]] || { echo "need Python 3.11 (pyenv install 3.11 or set CHATTERBOX_PYTHON)" >&2; exit 1; }

mkdir -p "$HOME_DIR"
"$PY" -m venv "$VENV"
# pip 24.0, not latest: savvas-scfw parses `pip install --dry-run --report -` and
# fails on pip 26's output ("Expecting value: line 1 column 1").
"$VENV/bin/python" -m pip install -q "pip==24.0"

# Go through the savvas-scfw supply-chain firewall when it is installed.
# scfw resolves "pip" from PATH, hence the activate.
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pipi() { if command -v savvas-scfw >/dev/null; then savvas-scfw run pip install "$@"; else pip install "$@"; fi; }
pipi --no-deps chatterbox-tts
pipi -r "$SKILL_DIR/requirements.txt"

python -c "from chatterbox.tts_turbo import ChatterboxTurboTTS; import torch; print('chatterbox venv ready:', '$VENV', '| torch', torch.__version__, '| mps', torch.backends.mps.is_available())"
