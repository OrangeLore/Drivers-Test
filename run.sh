#!/usr/bin/env bash
# Driver's Practice Test - portable launcher (macOS / Linux).
cd "$(dirname "$0")"
PORT="${AC7_PORT:-5600}"
echo "Starting Driver's Practice Test on http://localhost:$PORT"
python3 tools/app_server.py "$PORT" &
SRV=$!
sleep 2
( command -v xdg-open >/dev/null 2>&1 && xdg-open "http://localhost:$PORT" ) \
  || ( command -v open >/dev/null 2>&1 && open "http://localhost:$PORT" ) \
  || echo "Open http://localhost:$PORT in your browser."
wait $SRV
