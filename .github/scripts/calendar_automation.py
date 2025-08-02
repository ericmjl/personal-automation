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
        self.secondary_email = os.getenv('SECONDARY_EMAIL')
        self.credentials = self._get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials)
        
        if not self.secondary_email:
            raise ValueError("SECONDARY_EMAIL environment variable not set")
    
    def _get_credentials(self) -> Credentials:
        """Get Google API credentials from environment variable."""
        creds_json = os.getenv('GOOGLE_CREDENTIALS')
        if not creds_json:
            raise ValueError("GOOGLE_CREDENTIALS environment variable not set")
        
        try:
            creds_info = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return credentials
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GOOGLE_CREDENTIALS: {e}")
    
    def get_recent_events(self, days_back: int = 7, days_forward: int = 30) -> List[Dict[str, Any]]:
        """Get calendar events from the past week to next month."""
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_forward)).isoformat()
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"Found {len(events)} total events")
            return events
            
        except HttpError as error:
            print(f"An error occurred while fetching events: {error}")
            return []
    
    def is_calendly_event(self, event: Dict[str, Any]) -> bool:
        """Check if an event is from Calendly."""
        # Check common Calendly indicators
        indicators = [
            'calendly.com' in event.get('description', '').lower(),
            'calendly.com' in event.get('location', '').lower(),
            'calendly' in event.get('summary', '').lower(),
            'calendly' in event.get('description', '').lower(),
        ]
        
        # Check organizer email domain
        organizer = event.get('organizer', {})
        organizer_email = organizer.get('email', '')
        if 'calendly' in organizer_email.lower():
            indicators.append(True)
        
        # Check if created by Calendly (common pattern in event source)
        source = event.get('source', {})
        if 'calendly' in source.get('title', '').lower():
            indicators.append(True)
            
        return any(indicators)
    
    def has_secondary_email_as_guest(self, event: Dict[str, Any]) -> bool:
        """Check if secondary email is already a guest."""
        attendees = event.get('attendees', [])
        for attendee in attendees:
            if attendee.get('email', '').lower() == self.secondary_email.lower():
                return True
        return False
    
    def add_secondary_email_as_guest(self, event: Dict[str, Any]) -> bool:
        """Add secondary email as guest to the event."""
        event_id = event['id']
        
        # Get current attendees
        attendees = event.get('attendees', [])
        
        # Add secondary email if not already present
        attendees.append({
            'email': self.secondary_email,
            'responseStatus': 'accepted'
        })
        
        # Update the event
        try:
            updated_event = {
                'attendees': attendees
            }
            
            self.service.events().patch(
                calendarId='primary',
                eventId=event_id,
                body=updated_event
            ).execute()
            
            print(f"✅ Added {self.secondary_email} to event: {event.get('summary', 'Untitled')}")
            return True
            
        except HttpError as error:
            print(f"❌ Error updating event {event.get('summary', 'Untitled')}: {error}")
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
        
        print(f"🎉 Successfully updated {successful_updates}/{len(events_to_update)} events")


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