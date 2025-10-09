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

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarAutomation:
    def __init__(self):
        self.primary_email = os.getenv("PRIMARY_EMAIL")
        self.secondary_email = os.getenv("SECONDARY_EMAIL")
        self.tertiary_email = os.getenv("TERTIARY_EMAIL", "eric.ma@modernatx.com")
        self.credentials = self._get_credentials()
        self.service = build("calendar", "v3", credentials=self.credentials)

        if not self.primary_email:
            raise ValueError("PRIMARY_EMAIL environment variable not set")
        if not self.secondary_email:
            raise ValueError("SECONDARY_EMAIL environment variable not set")

        # List available calendars for debugging
        self._list_calendars()

    def _get_credentials(self) -> Credentials:
        """Get Google API credentials using OAuth2."""
        creds = None
        token_path = "token.pickle"

        # Load existing token
        if os.path.exists(token_path):
            print(f"📁 Loading existing token from {token_path}")
            try:
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"⚠️  Error loading token file: {e}")
                print("🗑️  Removing corrupted token file...")
                os.remove(token_path)
                creds = None

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully")
                except Exception as e:
                    print(f"❌ Failed to refresh token: {e}")
                    print("🔄 Getting new OAuth2 credentials...")
                    creds = self._get_new_credentials()
            else:
                print("🔐 Getting new OAuth2 credentials...")
                creds = self._get_new_credentials()

            # Save credentials for next run (only in local development)
            if not os.getenv("GITHUB_ACTIONS"):
                print(f"💾 Saving token to {token_path}")
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

        print("✅ Successfully loaded OAuth2 credentials")
        return creds

    def _get_new_credentials(self) -> Credentials:
        """Get new OAuth2 credentials through browser authentication."""
        # Try to load OAuth2 credentials file
        oauth2_creds_path = "oauth2_credentials.json"
        if not os.path.exists(oauth2_creds_path):
            raise ValueError(
                f"OAuth2 credentials file not found: {oauth2_creds_path}\n"
                f"Please download OAuth2 credentials from Google Cloud Console"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            oauth2_creds_path, ["https://www.googleapis.com/auth/calendar"]
        )

        # Check if we're running in GitHub Actions (no browser available)
        if os.getenv("GITHUB_ACTIONS"):
            print("🤖 Running in GitHub Actions - using headless flow")
            # For GitHub Actions, we need to use a different approach
            # The token should already be provided via secrets
            raise ValueError(
                "Running in GitHub Actions but no valid token found.\n"
                "Please ensure GOOGLE_OAUTH_TOKEN secret is set correctly."
            )
        else:
            print("🖥️  Running locally - opening browser for authentication")
            return flow.run_local_server(port=0)

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

        # First check if this is a buffer event - if so, exclude it
        if "buffer" in summary:
            print(
                f"       ❌ Excluding buffer event: '{event.get('summary', 'No title')}'"
            )
            return False

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

    def has_email_as_guest(self, event: Dict[str, Any], email: str) -> bool:
        """Check if email is already a guest."""
        attendees = event.get("attendees", [])
        for attendee in attendees:
            if attendee.get("email", "").lower() == email.lower():
                return True
        return False

    def add_email_as_guest(self, event: Dict[str, Any], email: str) -> bool:
        """Add email as guest to the event."""
        event_id = event["id"]

        # Get current attendees
        attendees = event.get("attendees", [])

        # Add email if not already present
        attendees.append({"email": email, "responseStatus": "accepted"})

        # Update the event
        try:
            updated_event = {"attendees": attendees}

            self.service.events().patch(
                calendarId=self.primary_email, eventId=event_id, body=updated_event
            ).execute()

            print(f"✅ Added {email} to event: {event.get('summary', 'Untitled')}")
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
        events_to_update_secondary = []
        events_to_update_tertiary = []

        for event in events:
            if self.is_calendly_event(event):
                calendly_events.append(event)
                if not self.has_email_as_guest(event, self.secondary_email):
                    events_to_update_secondary.append(event)
                if not self.has_email_as_guest(event, self.tertiary_email):
                    events_to_update_tertiary.append(event)

        print(f"📅 Found {len(calendly_events)} Calendly events")
        print(
            f"🎯 {len(events_to_update_secondary)} events need {self.secondary_email} added"
        )
        print(
            f"🎯 {len(events_to_update_tertiary)} events need {self.tertiary_email} added"
        )

        if not events_to_update_secondary and not events_to_update_tertiary:
            print("✨ All Calendly events already have both emails as guests!")
            return

        # Update events with secondary email
        successful_secondary_updates = 0
        for event in events_to_update_secondary:
            if self.add_email_as_guest(event, self.secondary_email):
                successful_secondary_updates += 1

        # Update events with tertiary email
        successful_tertiary_updates = 0
        for event in events_to_update_tertiary:
            if self.add_email_as_guest(event, self.tertiary_email):
                successful_tertiary_updates += 1

        print(
            f"🎉 Successfully added {self.secondary_email} to {successful_secondary_updates}/{len(events_to_update_secondary)} events"
        )
        print(
            f"🎉 Successfully added {self.tertiary_email} to {successful_tertiary_updates}/{len(events_to_update_tertiary)} events"
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
        raise e


if __name__ == "__main__":
    main()
