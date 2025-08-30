#!/usr/bin/env python3
"""
Portfolio Analytics Module for SchedShare
Generates career-ready metrics and insights for portfolio/resume
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from advanced_analytics import AdvancedAnalytics

load_dotenv()

class PortfolioAnalytics:
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.advanced_analytics = AdvancedAnalytics(db_path)
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary for resume/portfolio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall impact metrics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_hash) as unique_users,
                COUNT(*) as total_courses_processed,
                SUM(CASE WHEN event_created THEN 1 ELSE 0 END) as successful_calendar_events,
                COUNT(DISTINCT department) as departments_served
            FROM course_analytics
        ''')
        
        impact_row = cursor.fetchone()
        unique_users = impact_row[0] if impact_row else 0
        total_courses = impact_row[1] if impact_row else 0
        successful_events = impact_row[2] if impact_row else 0
        departments_served = impact_row[3] if impact_row else 0
        
        # Time-based metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM course_analytics
            WHERE created_at >= datetime('now', '-30 days')
        ''')
        
        time_row = cursor.fetchone()
        recent_sessions = time_row[0] if time_row else 0
        active_days = time_row[1] if time_row else 0
        
        # Technology adoption
        cursor.execute('''
            SELECT provider, COUNT(*) as count
            FROM course_analytics
            WHERE event_created = TRUE
            GROUP BY provider
        ''')
        
        providers = dict(cursor.fetchall())
        
        # User engagement
        conversion_rate = (successful_events / total_courses * 100) if total_courses > 0 else 0
        
        conn.close()
        
        return {
            'impact_metrics': {
                'unique_users_served': unique_users,
                'total_courses_processed': total_courses,
                'successful_calendar_events': successful_events,
                'departments_served': departments_served,
                'conversion_rate': round(conversion_rate, 1)
            },
            'engagement_metrics': {
                'recent_sessions_30d': recent_sessions,
                'active_days_30d': active_days,
                'avg_sessions_per_day': round(recent_sessions / max(active_days, 1), 1)
            },
            'technology_adoption': providers,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_technical_achievements(self) -> List[Dict]:
        """Get technical achievements for resume/interviews"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        achievements = []
        
        # API Integration Success
        cursor.execute('''
            SELECT COUNT(*) as total_events
            FROM course_analytics
            WHERE event_created = TRUE
        ''')
        
        api_events = cursor.fetchone()[0] or 0
        if api_events > 0:
            achievements.append({
                'category': 'API Integration',
                'achievement': f'Successfully integrated Google Calendar API',
                'metric': f'{api_events} calendar events created',
                'impact': 'Automated course scheduling for students'
            })
        
        # Data Processing
        cursor.execute('''
            SELECT COUNT(*) as total_courses
            FROM course_analytics
        ''')
        
        processed_courses = cursor.fetchone()[0] or 0
        if processed_courses > 0:
            achievements.append({
                'category': 'Data Processing',
                'achievement': 'Built PDF parsing and data extraction system',
                'metric': f'{processed_courses} course schedules processed',
                'impact': 'Converted unstructured PDF data to structured calendar events'
            })
        
        # User Experience
        cursor.execute('''
            SELECT COUNT(DISTINCT session_hash) as users
            FROM course_analytics
        ''')
        
        users = cursor.fetchone()[0] or 0
        if users > 0:
            achievements.append({
                'category': 'User Experience',
                'achievement': 'Designed intuitive course scheduling workflow',
                'metric': f'{users} unique users served',
                'impact': 'Simplified course schedule management for students'
            })
        
        # System Reliability
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN event_created THEN 1 ELSE 0 END) as successful
            FROM course_analytics
        ''')
        
        reliability_row = cursor.fetchone()
        total_attempts = reliability_row[0] or 0
        successful = reliability_row[1] or 0
        
        if total_attempts > 0:
            reliability_rate = (successful / total_attempts * 100)
            achievements.append({
                'category': 'System Reliability',
                'achievement': 'Built robust error handling and validation',
                'metric': f'{reliability_rate:.1f}% success rate',
                'impact': 'Ensured reliable calendar event creation'
            })
        
        conn.close()
        return achievements
    
    def get_business_insights(self) -> Dict:
        """Get business insights for portfolio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Most popular departments
        cursor.execute('''
            SELECT department, COUNT(*) as count
            FROM course_analytics
            GROUP BY department
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        top_departments = dict(cursor.fetchall())
        
        # Peak usage times
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN CAST(SUBSTR(start_time, 1, 2) AS INTEGER) IS NOT NULL 
                    THEN CAST(SUBSTR(start_time, 1, 2) AS INTEGER) || ':00-' || (CAST(SUBSTR(start_time, 1, 2) AS INTEGER) + 1) || ':00'
                    ELSE 'UNKNOWN'
                END as time_slot,
                COUNT(*) as count
            FROM course_analytics
            GROUP BY time_slot
            ORDER BY count DESC
            LIMIT 3
        ''')
        
        peak_times = dict(cursor.fetchall())
        
        # User behavior patterns
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_hash) as total_users,
                COUNT(*) as total_courses,
                ROUND(CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT session_hash), 1) as avg_courses_per_user
            FROM course_analytics
        ''')
        
        behavior_row = cursor.fetchone()
        avg_courses_per_user = behavior_row[2] if behavior_row else 0
        
        conn.close()
        
        return {
            'user_behavior': {
                'average_courses_per_user': avg_courses_per_user,
                'most_popular_departments': top_departments,
                'peak_usage_times': peak_times
            },
            'product_insights': {
                'total_departments_served': len(top_departments),
                'user_engagement_level': 'High' if avg_courses_per_user > 3 else 'Medium'
            }
        }
    
    def generate_portfolio_stats(self) -> Dict:
        """Generate complete portfolio statistics"""
        return {
            'summary': self.get_portfolio_summary(),
            'achievements': self.get_technical_achievements(),
            'insights': self.get_business_insights(),
            'department_analytics': self.advanced_analytics.get_department_analytics(),
            'time_analytics': self.advanced_analytics.get_time_analytics(),
            'day_analytics': self.advanced_analytics.get_day_analytics()
        }
    
    def export_portfolio_data(self, format: str = 'json') -> str:
        """Export portfolio data in various formats"""
        data = self.generate_portfolio_stats()
        
        if format == 'json':
            return json.dumps(data, indent=2)
        elif format == 'markdown':
            return self._generate_markdown_report(data)
        else:
            return json.dumps(data, indent=2)
    
    def _generate_markdown_report(self, data: Dict) -> str:
        """Generate markdown report for portfolio"""
        summary = data['summary']
        achievements = data['achievements']
        insights = data['insights']
        
        report = f"""# SchedShare - Portfolio Analytics Report

## Project Impact Summary

- **Users Served**: {summary['impact_metrics']['unique_users_served']}
- **Courses Processed**: {summary['impact_metrics']['total_courses_processed']}
- **Calendar Events Created**: {summary['impact_metrics']['successful_calendar_events']}
- **Departments Served**: {summary['impact_metrics']['departments_served']}
- **Success Rate**: {summary['impact_metrics']['conversion_rate']}%

## Technical Achievements

"""
        
        for achievement in achievements:
            report += f"""### {achievement['category']}
- **Achievement**: {achievement['achievement']}
- **Metric**: {achievement['metric']}
- **Impact**: {achievement['impact']}

"""
        
        report += f"""## Business Insights

### User Behavior
- Average courses per user: {insights['user_behavior']['average_courses_per_user']}
- Most popular departments: {', '.join(list(insights['user_behavior']['most_popular_departments'].keys())[:3])}
- Peak usage times: {', '.join(list(insights['user_behavior']['peak_usage_times'].keys())[:3])}

### Technology Adoption
"""
        
        for provider, count in summary['technology_adoption'].items():
            report += f"- {provider.title()}: {count} events\n"
        
        report += f"""
## Recent Activity (30 days)
- Sessions: {summary['engagement_metrics']['recent_sessions_30d']}
- Active days: {summary['engagement_metrics']['active_days_30d']}
- Average sessions per day: {summary['engagement_metrics']['avg_sessions_per_day']}

---
*Generated on {datetime.now().strftime('%B %d, %Y')}*
"""
        
        return report

# Global instance
portfolio_analytics = PortfolioAnalytics()
