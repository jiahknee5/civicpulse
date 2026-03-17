#!/bin/bash
# Auto-save session log to DELL-31 every 5 minutes
LOG=~/hackathon/SESSION_LOG.md
REMOTE="nvidia@DELL-31.local:~/hackathon/"

while true; do
    # Sync entire hackathon folder to GB10
    rsync -az ~/hackathon/ $REMOTE 2>/dev/null
    echo "[$(date '+%H:%M:%S')] Synced to DELL-31" >> ~/hackathon/.sync.log
    sleep 300
done
