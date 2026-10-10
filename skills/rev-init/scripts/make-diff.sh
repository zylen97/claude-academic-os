#!/bin/bash
# make-diff.sh — Generate color-coded diff PDF
# Compares baseline (from .revision-baseline) vs active manuscript (.revision-main or manuscript.tex)
# Output: manuscript-track-changes.pdf (blue=additions, red strikethrough=deletions)
#
# Known limitations of latexdiff:
#   - Custom environments (e.g., threeparttable) may produce spurious markup
#   - Multi-line math environments (\align, \equation) sometimes need --math-markup=off
#   - If manuscript uses \input{}, add --flatten flag to latexdiff command
#   - booktabs \toprule/\midrule/\bottomrule conflicts are handled by post-processing below

# Ensure TeX tools are in PATH (needed for manual/background runs)
export PATH="/Library/TeX/texbin:$PATH"

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_DIR"

# Read active manuscript from .revision-main (fallback: manuscript.tex / main.tex)
if [ -f ".revision-main" ]; then
    MODIFIED="$(cat .revision-main | tr -d '[:space:]')"
elif [ -f "manuscript.tex" ]; then
    MODIFIED="manuscript.tex"
elif [ -f "main.tex" ]; then
    MODIFIED="main.tex"
else
    echo "[diff] ERROR: No active manuscript found. Run /rev-init first."
    exit 1
fi

# Read baseline from .revision-baseline (multi-round support)
# Fallback chain: .revision-baseline → manuscript-original.tex (legacy)
if [ -f ".revision-baseline" ]; then
    ORIGINAL="$(cat .revision-baseline | tr -d '[:space:]')"
elif [ -f "manuscript-original.tex" ]; then
    ORIGINAL="manuscript-original.tex"
else
    echo "[diff] ERROR: No baseline found. Run /rev-init first."
    exit 1
fi
PREAMBLE="tools/latexdiff-preamble.tex"
DIFF_TEX="manuscript-track-changes.tex"

# Dependency checks
for f in "$ORIGINAL" "$MODIFIED" "$PREAMBLE"; do
    if [ ! -f "$f" ]; then
        echo "[diff] ERROR: $f not found"
        exit 1
    fi
done

echo "[diff] Running latexdiff..."
latexdiff \
    --preamble="$PREAMBLE" \
    --math-markup=coarse \
    "$ORIGINAL" "$MODIFIED" > "$DIFF_TEX" 2>latexdiff-stderr.log

if [ $? -ne 0 ]; then
    echo "[diff] ERROR: latexdiff failed. See latexdiff-stderr.log for details"
    exit 1
fi

# Post-process: fix latexdiff + booktabs incompatibility
# \DIFxxxFL markers before \toprule/\midrule/\bottomrule break \noalign context
echo "[diff] Post-processing diff for booktabs compatibility..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE=(sed -i '')
else
    SED_INPLACE=(sed -i)
fi
"${SED_INPLACE[@]}" 's/\\DIFaddendFL \\bottomrule/\\bottomrule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFdelendFL \\bottomrule/\\bottomrule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFaddendFL \\midrule/\\midrule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFdelendFL \\midrule/\\midrule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFaddendFL \\toprule/\\toprule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFdelendFL \\toprule/\\toprule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFaddbeginFL \\toprule/\\toprule/g' "$DIFF_TEX"
"${SED_INPLACE[@]}" 's/\\DIFdelbeginFL \\toprule/\\toprule/g' "$DIFF_TEX"

echo "[diff] Compiling diff PDF..."
latexmk -pvc- -pv- "$DIFF_TEX" 2>diff-compile-stderr.log

if [ $? -eq 0 ]; then
    echo "[diff] SUCCESS: manuscript-track-changes.pdf generated"
else
    echo "[diff] WARNING: Compilation had issues. See diff-compile-stderr.log for details"
    echo "[diff] Also check manuscript-track-changes.log"
    exit 1
fi
