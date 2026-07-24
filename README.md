# Zenin OSINT Bot

Telegram OSINT Bot - Phone, Aadhaar, IP, IFSC, PAN, GST, Vehicle RC lookups.

## Setup

```bash
pip install -r requirements.txt
python3 bot.py
```

## Run with auto-restart (tmux)

```bash
tmux new-session -d -s zenin "bash start.sh"
```

## Features
- Phone number lookup
- Aadhaar OSINT
- IP geolocation
- IFSC bank lookup
- PAN card lookup
- GST lookup
- Vehicle RC lookup
- Admin panel
- MongoDB backed
