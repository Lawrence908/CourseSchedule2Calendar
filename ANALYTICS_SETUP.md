# Analytics Setup Guide

## Quick Start

### 1. Set Your Analytics Token
Add this to your `.env` file:
```bash
ANALYTICS_TOKEN=your-secret-token-here
```

### 2. Access Analytics Dashboards

#### Basic Analytics (Redis-based)
```
https://yourdomain.com/analytics?token=your-secret-token-here
```

#### Advanced Analytics (SQLite-based)
```
https://yourdomain.com/advanced-analytics?token=your-secret-token-here
```

### 3. Command Line Access
```bash
# View basic analytics
python analytics_cli.py

# View raw Redis data
python analytics_cli.py --raw
```

## What You Get

### Basic Analytics Dashboard
- 📊 Total uploads, events, conversions
- 📅 Daily activity timeline
- 🔗 Provider usage (Google vs ICS)
- 📈 Real-time metrics

### Advanced Analytics Dashboard
- 🏢 Department analysis (CS, MATH, ENGL, etc.)
- ⏰ Time slot analysis (9:00-10:00, 10:00-11:00, etc.)
- 📅 Day of week analysis (Monday, Tuesday, etc.)
- 📊 Provider distribution
- 🎯 Conversion rates by category

## Privacy & Security

### What's Protected
- ✅ Analytics pages require token authentication
- ✅ No personal data stored
- ✅ Session data is hashed
- ✅ Course details are anonymized

### What's Tracked
- 📄 PDF uploads (count only)
- 📅 Course selections (department, time, day)
- 🔗 Provider choices (Google/ICS)
- 📧 Email summary requests
- ✅ Successful event creations

## Database Files

### Redis (Basic Analytics)
- Stored in Redis server
- Auto-cleanup after 30 days
- No manual management needed

### SQLite (Advanced Analytics)
- File: `analytics.db`
- Created automatically
- Backup recommended for long-term data

## Environment Variables

```bash
# Required for analytics access
ANALYTICS_TOKEN=schedshare-analytics-2025

# Optional: Custom token
ANALYTICS_TOKEN=your-custom-token
```

## Usage Examples

### For Beta Testing
1. Share the analytics URL with your CS colleagues
2. Monitor usage patterns during testing
3. Identify any issues or bottlenecks

### For University Release
1. Set a strong analytics token
2. Monitor adoption rates
3. Track which departments use it most
4. Analyze peak usage times

### For Research/Reporting
1. Export data from SQLite database
2. Create custom reports
3. Share insights with university administration

## Troubleshooting

### No Data Appearing
```bash
# Check Redis connection
redis-cli ping

# Check SQLite database
sqlite3 analytics.db "SELECT COUNT(*) FROM course_analytics;"
```

### Permission Issues
```bash
# Make sure analytics.db is writable
chmod 666 analytics.db
```

### Database Issues
```bash
# Reset advanced analytics (if needed)
rm analytics.db
# Restart application - database will be recreated
```

## Security Best Practices

1. **Use a strong token**: Don't use the default token in production
2. **Limit access**: Only share analytics URLs with trusted people
3. **Regular backups**: Backup `analytics.db` for long-term data
4. **Monitor access**: Check logs for analytics page access

## Example Analytics URLs

```bash
# Basic analytics
https://schedshare.chrislawrence.ca/analytics?token=your-token

# Advanced analytics  
https://schedshare.chrislawrence.ca/advanced-analytics?token=your-token
```

## Data Retention

- **Redis events**: 30 days
- **SQLite data**: Indefinite (until manually deleted)
- **Daily aggregates**: Indefinite
- **Session data**: 7 days

---

*This analytics system is designed to give you insights while respecting user privacy.*




