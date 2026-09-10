#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-auth",
#     "google-auth-httplib2",
#     "google-api-python-client",
# ]
# ///
"""One-off cleanup: remove the automation guest emails from canceled events.

Calendly cancels bookings by renaming the GCal event to "Canceled: <title>"
while leaving status=confirmed, which calendar_automation.py treated as a live
booking and stamped the Moderna + Nonlinear Labs emails onto. This script
removes those two emails from every event in the look-ahead window whose
title starts with "Canceled:"/"Cancelled:", without touching anything else.
"""

import os
import pickle
import re
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TERTIARY = os.getenv("TERTIARY_EMAIL", "eric.ma@modernatx.com")
SECONDARY = os.getenv("SECONDARY_EMAIL", "eric.ma@nonlinearlabs.ai")
PRIMARY = os.getenv("PRIMARY_EMAIL", "ericmajinglong@gmail.com")
AUTOMATION_EMAILS = {TERTIARY.lower(), SECONDARY.lower()}
CANCEL_PATTERN = re.compile(r"^\s*cancell?ed\s*:", re.IGNORECASE)

with open("token.pickle", "rb") as f:
    creds = pickle.load(f)
if not creds.valid and creds.expired and creds.refresh_token:
    creds.refresh(Request())

service = build("calendar", "v3", credentials=creds)

now = datetime.now(timezone.utc)
time_min = (now - timedelta(days=7)).isoformat()
time_max = (now + timedelta(days=180)).isoformat()

events = (
    service.events()
    .list(
        calendarId=PRIMARY,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    )
    .execute()
    .get("items", [])
)

cleaned = 0
for ev in events:
    if not CANCEL_PATTERN.match(ev.get("summary", "")):
        continue
    attendees = ev.get("attendees", [])
    keep = [a for a in attendees if a.get("email", "").lower() not in AUTOMATION_EMAILS]
    removed = len(attendees) - len(keep)
    if removed == 0:
        print(f"⏭️  Nothing to remove: {ev.get('summary')!r}")
        continue
    print(f"🧹 {ev.get('summary')!r}: removing {removed} automation guest(s)")
    service.events().patch(
        calendarId=PRIMARY,
        eventId=ev["id"],
        body={"attendees": keep},
        sendUpdates="none",
    ).execute()
    cleaned += 1

print(f"\n✅ Cleaned {cleaned} canceled event(s)")
