#!/bin/bash
cd "$(dirname "$0")"

python main.py --no-browser &
sleep 2

if command -v xdg-open &>/dev/null; then
    xdg-open http://127.0.0.1:9599
elif command -v open &>/dev/null; then
    open http://127.0.0.1:9599
fi
