#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-auth",
#     "google-auth-oauthlib",
#     "google-auth-httplib2",
#     "google-api-python-client",
# ]
# ///
"""
GitHub Action script to automatically add secondary email as guest to Calendly events.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarAutomation:
    def __init__(self):
        self.primary_email = os.getenv("PRIMARY_EMAIL")
        self.secondary_email = os.getenv("SECONDARY_EMAIL")
        self.credentials = self._get_credentials()
        self.service = build("calendar", "v3", credentials=self.credentials)

        if not self.primary_email:
            raise ValueError("PRIMARY_EMAIL environment variable not set")
        if not self.secondary_email:
            raise ValueError("SECONDARY_EMAIL environment variable not set")

        # List available calendars for debugging
        self._list_calendars()

    def _get_credentials(self) -> Credentials:
        """Get Google API credentials from default location or environment variable."""
        # Try to read from default location first
        default_creds_path = "google-credentials.json"

        if os.path.exists(default_creds_path):
            print(f"📁 Reading credentials from {default_creds_path}")
            try:
                # Use Google Auth's built-in file loading method
                credentials = Credentials.from_service_account_file(
                    default_creds_path,
                    scopes=["https://www.googleapis.com/auth/calendar"],
                )
                print("✅ Successfully loaded credentials from file")
                return credentials
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Error reading {default_creds_path}: {e}")
                # Fall through to environment variable
            except Exception as e:
                print(f"❌ Error creating credentials from {default_creds_path}: {e}")
                print(f"   Error type: {type(e).__name__}")
                # Fall through to environment variable

        # Fall back to environment variable
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if creds_json:
            print("🔧 Reading credentials from GOOGLE_CREDENTIALS environment variable")
            try:
                creds_info = json.loads(creds_json)

                # Fix private key formatting - replace \n with actual newlines
                if "private_key" in creds_info:
                    creds_info["private_key"] = creds_info["private_key"].replace(
                        "\\n", "\n"
                    )

                credentials = Credentials.from_service_account_info(
                    creds_info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
                return credentials
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in GOOGLE_CREDENTIALS environment variable: {e}"
                )

        # If neither exists, error out with helpful message
        raise ValueError(
            f"Google credentials not found. Please either:\n"
            f"1. Create a {default_creds_path} file in the project root, or\n"
            f"2. Set the GOOGLE_CREDENTIALS environment variable"
        )

    def _list_calendars(self):
        """List available calendars for debugging."""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            print(f"📋 Found {len(calendars)} available calendars:")
            for calendar in calendars:
                access_role = calendar.get("accessRole", "unknown")
                primary = calendar.get("primary", False)
                print(
                    f"  - {calendar.get('summary', 'No name')} ({calendar.get('id', 'No ID')}) - {access_role} {'[PRIMARY]' if primary else ''}"
                )
        except Exception as e:
            print(f"⚠️  Error listing calendars: {e}")

    def get_recent_events(
        self, days_back: int = 7, days_forward: int = 30
    ) -> List[Dict[str, Any]]:
        """Get calendar events from the past week to next month."""
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_forward)).isoformat()

        print(f"🔍 Searching for events from {time_min} to {time_max}")
        print(f"📅 Current time: {now.isoformat()}")

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.primary_email,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            print(f"📊 Found {len(events)} total events")

            # Debug: Print details of each event
            for i, event in enumerate(events):
                start = event.get("start", {}).get(
                    "dateTime", event.get("start", {}).get("date", "No start time")
                )
                summary = event.get("summary", "No title")
                print(f"  Event {i + 1}: {summary} at {start}")

                # Check if it's a Calendly event
                if self.is_calendly_event(event):
                    print(f"    ✅ This is a Calendly event!")
                else:
                    print(f"    ❌ Not detected as Calendly event")

            return events

        except HttpError as error:
            print(f"An error occurred while fetching events: {error}")
            return []

    def is_calendly_event(self, event: Dict[str, Any]) -> bool:
        """Check if an event is from Calendly."""
        summary = event.get("summary", "").lower()
        description = event.get("description", "").lower()
        location = event.get("location", "").lower()

        print(f"    🔍 Checking event: '{event.get('summary', 'No title')}'")
        print(
            f"       Description contains 'calendly.com': {'calendly.com' in description}"
        )
        print(f"       Description contains 'calendly': {'calendly' in description}")
        print(f"       Location contains 'calendly.com': {'calendly.com' in location}")
        print(f"       Summary contains 'calendly': {'calendly' in summary}")

        # Check common Calendly indicators
        indicators = [
            "calendly.com" in description,
            "calendly.com" in location,
            "calendly" in summary,
            "calendly" in description,
        ]

        # Check organizer email domain
        organizer = event.get("organizer", {})
        organizer_email = organizer.get("email", "")
        if "calendly" in organizer_email.lower():
            indicators.append(True)
            print(f"       Organizer email contains 'calendly': True")

        # Check if created by Calendly (common pattern in event source)
        source = event.get("source", {})
        if "calendly" in source.get("title", "").lower():
            indicators.append(True)
            print(f"       Source contains 'calendly': True")

        result = any(indicators)
        print(f"       Final result: {result}")
        return result

    def has_secondary_email_as_guest(self, event: Dict[str, Any]) -> bool:
        """Check if secondary email is already a guest."""
        attendees = event.get("attendees", [])
        for attendee in attendees:
            if attendee.get("email", "").lower() == self.secondary_email.lower():
                return True
        return False

    def add_secondary_email_as_guest(self, event: Dict[str, Any]) -> bool:
        """Add secondary email as guest to the event."""
        event_id = event["id"]

        # Get current attendees
        attendees = event.get("attendees", [])

        # Add secondary email if not already present
        attendees.append({"email": self.secondary_email, "responseStatus": "accepted"})

        # Update the event
        try:
            updated_event = {"attendees": attendees}

            self.service.events().patch(
                calendarId=self.primary_email, eventId=event_id, body=updated_event
            ).execute()

            print(
                f"✅ Added {self.secondary_email} to event: {event.get('summary', 'Untitled')}"
            )
            return True

        except HttpError as error:
            print(
                f"❌ Error updating event {event.get('summary', 'Untitled')}: {error}"
            )
            return False

    def process_calendly_events(self):
        """Main method to process Calendly events and add secondary email as guest."""
        print("🔍 Fetching recent calendar events...")
        events = self.get_recent_events()

        if not events:
            print("No events found.")
            return

        calendly_events = []
        events_to_update = []

        for event in events:
            if self.is_calendly_event(event):
                calendly_events.append(event)
                if not self.has_secondary_email_as_guest(event):
                    events_to_update.append(event)

        print(f"📅 Found {len(calendly_events)} Calendly events")
        print(f"🎯 {len(events_to_update)} events need secondary email added")

        if not events_to_update:
            print("✨ All Calendly events already have secondary email as guest!")
            return

        # Update events
        successful_updates = 0
        for event in events_to_update:
            if self.add_secondary_email_as_guest(event):
                successful_updates += 1

        print(
            f"🎉 Successfully updated {successful_updates}/{len(events_to_update)} events"
        )


def main():
    """Main entry point."""
    try:
        automation = CalendarAutomation()
        automation.process_calendly_events()

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
