# SchedShare Analytics System

## Overview

The SchedShare analytics system tracks key usage metrics to help you understand how your application is being used by students. The system is designed to be lightweight, privacy-friendly, and provide actionable insights.

## What We Track

### Core Metrics
- **PDF Uploads**: Number of course schedule PDFs uploaded and processed
- **Events Selected**: Number of courses selected for calendar creation
- **Google Calendar Events**: Number of events successfully created in Google Calendar
- **ICS Downloads**: Number of .ICS files downloaded for Apple/Outlook calendars
- **Email Summaries**: Number of email summaries sent to users

### Derived Metrics
- **Conversion Rate**: Percentage of uploads that result in event selection
- **Provider Usage**: Distribution between Google Calendar and ICS downloads
- **Daily Trends**: Activity patterns over time

## How It Works

### Data Storage
- Uses Redis for fast, lightweight storage
- Events are stored with 30-day TTL (Time To Live)
- Daily aggregates are stored indefinitely
- No personal data is stored - only anonymous metrics

### Event Tracking
The system tracks events at key user interaction points:

1. **PDF Upload** (`pdf_uploaded`)
   - Triggered when a PDF is successfully uploaded and parsed
   - Tracks filename, number of courses found, upload ID

2. **Event Selection** (`events_selected`)
   - Triggered when user selects courses and chooses a provider
   - Tracks provider choice, number of courses selected

3. **Google Calendar Events** (`google_events_created`)
   - Triggered when events are successfully created in Google Calendar
   - Tracks number of events created, courses selected

4. **ICS Downloads** (`ics_downloaded`)
   - Triggered when user downloads ICS file
   - Tracks number of courses in download

5. **Email Summaries** (`email_summary_sent`)
   - Triggered when email summary is successfully sent
   - Tracks number of events, email domain

## Accessing Analytics

### Web Dashboard
Visit `/analytics` in your browser to see the interactive dashboard with:
- Real-time metrics
- Daily activity charts
- Provider usage statistics
- Recent activity timeline

### Command Line Interface
Use the CLI tool for quick checks:

```bash
# View formatted analytics summary
python analytics_cli.py

# View raw Redis data for debugging
python analytics_cli.py --raw
```

### Direct Redis Access
Connect to Redis directly for advanced queries:

```bash
# Connect to Redis
redis-cli

# View total statistics
HGETALL analytics:total

# View today's activity
HGETALL analytics:daily:2025-01-15

# View recent events
KEYS analytics:event:*
```

## Privacy & Compliance

### Data Minimization
- No personal information is stored
- No email addresses, names, or course details are tracked
- Only anonymous usage metrics are collected

### Data Retention
- Individual events: 30 days
- Daily aggregates: Indefinite (for trend analysis)
- Session data: 7 days

### GDPR Compliance
- No personal data collection
- Users can request data deletion (though no personal data exists)
- Clear privacy policy in place

## Interpreting the Data

### Key Metrics to Watch

1. **Conversion Rate**
   - Target: >70% of uploads should result in event selection
   - Low rates may indicate PDF parsing issues or UX problems

2. **Provider Distribution**
   - Google Calendar vs ICS downloads
   - Helps understand user preferences

3. **Daily Patterns**
   - Peak usage times (likely during registration periods)
   - Seasonal trends

4. **Email Usage**
   - Percentage of users who request email summaries
   - Popular email domains (can indicate student body composition)

### Actionable Insights

- **High upload, low conversion**: Check PDF parsing accuracy
- **Low Google Calendar usage**: Consider improving OAuth flow
- **High ICS downloads**: Users prefer manual import
- **Email domain patterns**: Understand your user base

## Troubleshooting

### No Data Appearing
1. Check Redis connection: `redis-cli ping`
2. Verify analytics tracking is enabled in `app.py`
3. Check application logs for errors

### Inconsistent Data
1. Check for multiple Redis instances
2. Verify timezone settings
3. Check for application restarts affecting counters

### Performance Issues
1. Monitor Redis memory usage
2. Consider data archival for old events
3. Implement data aggregation for long-term storage

## Future Enhancements

### Potential Additions
- Geographic usage patterns (if IP tracking is desired)
- Course popularity analysis
- Error tracking and debugging
- A/B testing framework
- Export capabilities for external analysis

### Scaling Considerations
- Move to dedicated analytics database (PostgreSQL, TimescaleDB)
- Implement data aggregation jobs
- Add real-time alerts for unusual activity
- Create automated reporting

## Security Notes

- Analytics endpoint should be protected in production
- Consider rate limiting for analytics queries
- Monitor for unusual activity patterns
- Regular backup of analytics data

## Support

For questions about the analytics system:
1. Check the application logs
2. Use the CLI tool for debugging
3. Review Redis data directly
4. Contact the development team

---

*This analytics system is designed to provide insights while respecting user privacy and maintaining application performance.*
