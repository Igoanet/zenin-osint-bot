#!/bin/bash
cd /root/zenin-bot
while true; do
    echo "[$(date)] Starting bot..."
    python3 bot.py >> bot.log 2>&1
    echo "[$(date)] Crashed. Restarting in 5s..."
    sleep 5
done
