#!/usr/bin/env bash
# Install the expeditions-specialist skill. Usage: ./install.sh [claude|codex|both]
set -eu
src="$(cd "$(dirname "$0")" && pwd)"; name="$(basename "$src")"; agent="${1:-claude}"
install_to () { mkdir -p "$1/$name"
  ( cd "$src" && tar -cf - --exclude=install.sh --exclude=install.ps1 . ) | ( cd "$1/$name" && tar -xf - )
  echo "  installed -> $1/$name"; }
case "$agent" in
  claude) install_to "$HOME/.claude/skills" ;;
  codex)  install_to "$HOME/.codex/skills" ;;
  both)   install_to "$HOME/.claude/skills"; install_to "$HOME/.codex/skills" ;;
  *) echo "usage: $0 [claude|codex|both]" >&2; exit 2 ;;
esac
missing=""
for pair in "PIL:pillow" "numpy:numpy" "cv2:opencv-python"; do
  python -c "import ${pair%%:*}" 2>/dev/null || missing="$missing ${pair##*:}"
done
echo
[ -n "$missing" ] && echo "  missing:$missing" && echo "  install: python -m pip install$missing" || echo "  python dependencies present"
python -c "import rembg" 2>/dev/null || echo "  rembg not installed (only needed to cut an opaque portrait)"
echo
echo "  Verify with:  python scripts/specialist_doctor.py"
