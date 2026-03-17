#!/usr/bin/env bash
# CivicPulse Demo Launcher
# Usage:  ./demo/launch.sh [--skip-pipeline]
# Starts: Command Center (port 7860) + Behind the Scenes (port 7861)

set -e
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$DEMO_DIR/data"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CivicPulse Demo Launcher — NVIDIA DGX Spark (GB10)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Data pipeline ────────────────────────────────────────────────────────────
if [[ "$1" != "--skip-pipeline" ]]; then
    if [[ ! -f "$DATA_DIR/top_risk_zips.json" ]] || [[ ! -f "$DATA_DIR/zip_risk.json" ]]; then
        echo "▶  Building risk profiles (first run — takes ~60s)..."
        python3 "$DEMO_DIR/data_pipeline.py"
        echo "✓  Data pipeline complete"
    else
        echo "✓  Data already built (use --skip-pipeline to skip check)"
    fi
else
    echo "⏭  Skipping data pipeline"
fi

# ── Verify required files ────────────────────────────────────────────────────
for f in zip_risk.json top_risk_zips.json county_summary.json cdc_averages.json; do
    if [[ ! -f "$DATA_DIR/$f" ]]; then
        echo "✗  Missing: $DATA_DIR/$f"
        echo "   Run: python3 $DEMO_DIR/data_pipeline.py"
        exit 1
    fi
done
echo "✓  All data files present"
echo ""

# ── Kill any existing demo processes ────────────────────────────────────────
echo "▶  Checking for processes on ports 7860 and 7861..."
lsof -ti:7860 | xargs kill -9 2>/dev/null && echo "  Killed existing process on 7860" || true
lsof -ti:7861 | xargs kill -9 2>/dev/null && echo "  Killed existing process on 7861" || true
sleep 1

# ── Launch apps ──────────────────────────────────────────────────────────────
echo "▶  Starting Command Center on http://0.0.0.0:7860 ..."
python3 "$DEMO_DIR/command_center.py" > "$DEMO_DIR/command_center.log" 2>&1 &
CC_PID=$!

echo "▶  Starting Behind the Scenes on http://0.0.0.0:7861 ..."
python3 "$DEMO_DIR/behind_the_scenes.py" > "$DEMO_DIR/behind_the_scenes.log" 2>&1 &
BTS_PID=$!

sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓  Command Center     →  http://localhost:7860"
echo "  ✓  Behind the Scenes  →  http://localhost:7861"
echo ""
echo "  Logs:"
echo "    tail -f $DEMO_DIR/command_center.log"
echo "    tail -f $DEMO_DIR/behind_the_scenes.log"
echo ""
echo "  Stop: kill $CC_PID $BTS_PID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Keep running until Ctrl+C ────────────────────────────────────────────────
trap "echo ''; echo 'Stopping...'; kill $CC_PID $BTS_PID 2>/dev/null; exit 0" INT TERM
wait $CC_PID $BTS_PID
