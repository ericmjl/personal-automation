#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-auth",
#     "google-auth-httplib2",
#     "google-api-python-client",
# ]
# ///
"""READ-ONLY diagnostic: find canceled Calendly events that got the Moderna
email added. Makes no writes to the calendar."""

import os
import pickle
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TERTIARY = os.getenv("TERTIARY_EMAIL", "eric.ma@modernatx.com")
PRIMARY = os.getenv("PRIMARY_EMAIL", "ericmajinglong@gmail.com")

with open("token.pickle", "rb") as f:
    creds = pickle.load(f)
if not creds.valid and creds.expired and creds.refresh_token:
    creds.refresh(Request())

service = build("calendar", "v3", credentials=creds)

now = datetime.now(timezone.utc)
time_min = (now - timedelta(days=7)).isoformat()
time_max = (now + timedelta(days=180)).isoformat()

events_result = (
    service.events()
    .list(
        calendarId=PRIMARY,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    )
    .execute()
)
events = events_result.get("items", [])
print(f"Total events in window: {len(events)}")

flagged = 0
for ev in events:
    summary = ev.get("summary", "(no title)")
    status = ev.get("status", "?")
    is_cancel_word = "cancel" in summary.lower()
    is_cancel_status = status == "cancelled"
    has_tertiary = any(
        a.get("email", "").lower() == TERTIARY.lower()
        for a in ev.get("attendees", [])
    )
    if is_cancel_word or is_cancel_status or has_tertiary:
        flagged += 1
        start = ev.get("start", {}).get(
            "dateTime", ev.get("start", {}).get("date", "?")
        )
        attendees = ", ".join(
            f"{a.get('email')}({a.get('responseStatus')})"
            for a in ev.get("attendees", [])
        )
        organizer = ev.get("organizer", {}).get("email", "?")
        creator = ev.get("creator", {}).get("email", "?")
        print(
            f"\n--- EVENT ---\n"
            f"  summary:   {summary!r}\n"
            f"  status:    {status}\n"
            f"  start:     {start}\n"
            f"  id:        {ev['id']}\n"
            f"  organizer: {organizer}\n"
            f"  creator:   {creator}\n"
            f"  attendees: {attendees or '(none)'}\n"
            f"  has_moderna_email: {has_tertiary}"
        )

print(f"\nFlagged events: {flagged}")
