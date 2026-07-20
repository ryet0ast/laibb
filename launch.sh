#!/usr/bin/env bash
# launch.sh — GPT Builder Wizard (Mac / Linux)

cd "$(dirname "${BASH_SOURCE[0]}")"

echo ""
echo " ====================================================="
echo "  Custom GPT Builder — Search Strategy Assistant"
echo " ====================================================="
echo ""

PORT=8503

if ! command -v uv &>/dev/null; then
    echo "[setup] Installing uv — this only happens once..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

(sleep 2 && \
    if command -v open &>/dev/null; then open "http://localhost:${PORT}";
    elif command -v xdg-open &>/dev/null; then xdg-open "http://localhost:${PORT}"; fi) &

echo "Starting wizard..."
echo ""
echo " Opening http://localhost:${PORT} in your browser."
echo " To stop: press Ctrl+C"
echo ""
uv run streamlit run app.py --server.port "$PORT" --server.headless true --browser.gatherUsageStats false
