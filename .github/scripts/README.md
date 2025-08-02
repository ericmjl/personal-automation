# Calendar Guest Automation

This GitHub Action automatically adds your secondary email as a guest to Calendly events in your Google Calendar.

## Setup Instructions

### 1. Google Cloud Project Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 2. Service Account Creation

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the service account details and create
4. Click on the created service account
5. Go to the "Keys" tab
6. Click "Add Key" → "Create new key" → "JSON"
7. Download the JSON file - this contains your credentials

### 3. Calendar Sharing

1. Open Google Calendar
2. Find your calendar in the left sidebar
3. Click the three dots next to your calendar name
4. Select "Settings and sharing"
5. Under "Share with specific people", add your service account email (found in the JSON file)
6. Give it "Make changes to events" permission

### 4. GitHub Secrets Setup

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- **GOOGLE_CREDENTIALS**: The entire contents of the JSON file from step 2.6
- **SECONDARY_EMAIL**: The email address you want to add as a guest to Calendly events

### 5. Testing

The action runs automatically:
- Every hour during business hours (9 AM - 6 PM EST, Monday-Friday)
- You can also trigger it manually from the Actions tab

## How It Works

1. **Event Detection**: The script fetches recent calendar events and identifies Calendly events by looking for:
   - "calendly.com" in the event description or location
   - "calendly" in the event title or description
   - Organizer email containing "calendly"

2. **Guest Management**: For each Calendly event found:
   - Checks if your secondary email is already a guest
   - If not, adds your secondary email as an accepted guest

3. **Error Handling**: The script includes comprehensive error handling and logging to help debug any issues

## Customization

You can modify the automation by editing `.github/scripts/calendar_automation.py`:

- **Time Range**: Change `days_back` and `days_forward` in `get_recent_events()`
- **Event Detection**: Modify `is_calendly_event()` to change how Calendly events are identified
- **Schedule**: Update the cron schedule in `.github/workflows/calendar-automation.yml`

## Troubleshooting

### Common Issues

1. **"GOOGLE_CREDENTIALS environment variable not set"**
   - Ensure you've added the GOOGLE_CREDENTIALS secret in GitHub

2. **"Invalid JSON in GOOGLE_CREDENTIALS"**
   - Verify the JSON format of your Google service account key

3. **"403 Forbidden" errors**
   - Check that your service account has access to your calendar
   - Verify the Google Calendar API is enabled

4. **Events not being detected as Calendly events**
   - Check the event details to see what identifiers are available
   - Modify the `is_calendly_event()` method accordingly

### Viewing Logs

1. Go to your repository's Actions tab
2. Click on a workflow run
3. Click on the "add-calendar-guests" job
4. Expand the "Run calendar automation" step to see detailed logs

## Security Notes

- The service account only has access to your calendar, not your entire Google account
- All credentials are stored securely as GitHub secrets
- The script only modifies attendee lists, not event content