# Personal Automation

A collection of scripts and tools to automate various aspects of my life.

## Scripts

### Calendar Automation (`scripts/calendar_automation.py`)

Automatically adds secondary and tertiary email addresses as guests to Calendly events in your Google Calendar.

#### Features
- ✅ Detects Calendly events by searching for "calendly.com" in event descriptions
- ✅ Adds multiple email addresses as guests to events
- ✅ Works with personal Gmail accounts using OAuth2 authentication
- ✅ Runs automatically via GitHub Actions every 6 hours
- ✅ Prevents duplicate guest additions

#### Setup

1. **Create OAuth2 Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Calendar API
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download as `oauth2_credentials.json`

2. **Local Testing**
   ```bash
   # Set environment variables
   export PRIMARY_EMAIL="your-email@gmail.com"
   export SECONDARY_EMAIL="work-email@company.com"
   export TERTIARY_EMAIL="another-email@company.com"

   # Run the script
   python scripts/calendar_automation.py
   ```

3. **GitHub Actions Setup**
   - Add GitHub secrets:
     - `PRIMARY_EMAIL`: Your primary Gmail address
     - `SECONDARY_EMAIL`: First work email to add
     - `TERTIARY_EMAIL`: Second work email to add
     - `GOOGLE_OAUTH_TOKEN`: Base64-encoded token.pickle file

   **Note**: The OAuth2 refresh token is long-lived but not permanent. It may expire if:
   - Not used for 6 months
   - User revokes access
   - Security changes are detected
   - OAuth2 app configuration is modified

   If the token expires, regenerate it locally:
   ```bash
   rm token.pickle
   python scripts/calendar_automation.py  # Will open browser for auth
   base64 -i token.pickle  # Re-encode for GitHub secret
   ```

#### How It Works

1. **Authentication**: Uses OAuth2 to authenticate as you (not a service account)
2. **Event Detection**: Searches for events with "calendly.com" in description/location/summary
3. **Guest Addition**: Adds specified email addresses as guests if not already present
4. **Automation**: Runs every 6 hours via GitHub Actions

#### Files
- `scripts/calendar_automation.py` - Main automation script
- `oauth2_credentials.json` - OAuth2 credentials (not in git)
- `token.pickle` - Authentication token (not in git)
- `.github/workflows/calendar-automation.yml` - GitHub Actions workflow

## Development

### Environment Setup
```bash
# Install dependencies
uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Run scripts
python scripts/calendar_automation.py
```

### Project Structure
```
personal-automation/
├── scripts/                    # Automation scripts
│   └── calendar_automation.py  # Calendar guest automation
├── .github/workflows/          # GitHub Actions workflows
├── oauth2_credentials.json     # OAuth2 credentials (gitignored)
├── token.pickle               # Auth token (gitignored)
└── README.md                  # This file
```

## License

Personal use only.
