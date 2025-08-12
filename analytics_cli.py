#!/usr/bin/env python3
"""
Analytics CLI - Command line interface for viewing SchedShare analytics data
"""

import redis
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Redis connection
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_analytics_summary():
    """Get analytics summary from Redis"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's stats
    today_stats = redis_client.hgetall(f"analytics:daily:{today}")
    
    # Get total stats
    total_stats = redis_client.hgetall("analytics:total")
    
    # Get recent activity (last 7 days)
    recent_activity = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = redis_client.hgetall(f"analytics:daily:{date}")
        if day_stats:
            recent_activity.append({
                'date': date,
                'stats': day_stats
            })
    
    return {
        'today': today_stats,
        'total': total_stats,
        'recent': recent_activity
    }

def print_analytics():
    """Print analytics data in a formatted way"""
    analytics = get_analytics_summary()
    
    print("=" * 60)
    print("SchedShare Analytics Dashboard")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Total stats
    print("📊 TOTAL STATISTICS")
    print("-" * 30)
    total_uploads = int(analytics['total'].get('pdf_uploaded', 0))
    total_events = int(analytics['total'].get('events_selected', 0))
    total_google = int(analytics['total'].get('google_events_created', 0))
    total_ics = int(analytics['total'].get('ics_downloaded', 0))
    total_emails = int(analytics['total'].get('email_summary_sent', 0))
    
    print(f"📄 PDF Uploads:        {total_uploads:>6}")
    print(f"📅 Events Selected:     {total_events:>6}")
    print(f"🔗 Google Events:       {total_google:>6}")
    print(f"📥 ICS Downloads:       {total_ics:>6}")
    print(f"📧 Email Summaries:     {total_emails:>6}")
    
    # Conversion rates
    if total_uploads > 0:
        conversion_rate = (total_events / total_uploads) * 100
        print(f"📈 Conversion Rate:     {conversion_rate:>6.1f}%")
    
    if total_events > 0:
        google_rate = (total_google / total_events) * 100
        ics_rate = (total_ics / total_events) * 100
        print(f"🔗 Google Usage:        {google_rate:>6.1f}%")
        print(f"📥 ICS Usage:           {ics_rate:>6.1f}%")
    
    print()
    
    # Today's stats
    print("📅 TODAY'S ACTIVITY")
    print("-" * 30)
    today_uploads = int(analytics['today'].get('pdf_uploaded', 0))
    today_events = int(analytics['today'].get('events_selected', 0))
    today_google = int(analytics['today'].get('google_events_created', 0))
    today_ics = int(analytics['today'].get('ics_downloaded', 0))
    today_emails = int(analytics['today'].get('email_summary_sent', 0))
    
    print(f"📄 PDF Uploads:        {today_uploads:>6}")
    print(f"📅 Events Selected:     {today_events:>6}")
    print(f"🔗 Google Events:       {today_google:>6}")
    print(f"📥 ICS Downloads:       {today_ics:>6}")
    print(f"📧 Email Summaries:     {today_emails:>6}")
    
    print()
    
    # Recent activity
    print("📈 RECENT ACTIVITY (Last 7 Days)")
    print("-" * 40)
    if analytics['recent']:
        for day in analytics['recent']:
            date = day['date']
            stats = day['stats']
            total_actions = sum(int(v) for v in stats.values())
            
            print(f"{date}: {total_actions} actions")
            if stats.get('pdf_uploaded'):
                print(f"  📄 {stats['pdf_uploaded']} PDFs uploaded")
            if stats.get('events_selected'):
                print(f"  📅 {stats['events_selected']} events selected")
            if stats.get('google_events_created'):
                print(f"  🔗 {stats['google_events_created']} Google events")
            if stats.get('ics_downloaded'):
                print(f"  📥 {stats['ics_downloaded']} ICS downloads")
            if stats.get('email_summary_sent'):
                print(f"  📧 {stats['email_summary_sent']} emails sent")
            print()
    else:
        print("No recent activity found.")
    
    print("=" * 60)

def print_raw_data():
    """Print raw Redis data for debugging"""
    print("🔍 RAW REDIS DATA")
    print("=" * 60)
    
    # Get all analytics keys
    keys = redis_client.keys("analytics:*")
    
    for key in sorted(keys):
        print(f"\n📋 {key}")
        print("-" * len(key) + "-")
        
        if key.startswith("analytics:daily:"):
            data = redis_client.hgetall(key)
            for field, value in data.items():
                print(f"  {field}: {value}")
        elif key.startswith("analytics:total"):
            data = redis_client.hgetall(key)
            for field, value in data.items():
                print(f"  {field}: {value}")
        elif key.startswith("analytics:event:"):
            data = redis_client.get(key)
            if data:
                try:
                    event_data = json.loads(data)
                    print(f"  Type: {event_data.get('type')}")
                    print(f"  Time: {event_data.get('timestamp')}")
                    print(f"  Data: {event_data.get('data')}")
                except:
                    print(f"  Raw: {data}")

def main():
    """Main CLI function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--raw":
        print_raw_data()
    else:
        print_analytics()

if __name__ == "__main__":
    main()


