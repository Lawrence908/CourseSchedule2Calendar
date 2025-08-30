#!/usr/bin/env python3
"""
Advanced Analytics Module for SchedShare
Tracks course details for department/time analysis while maintaining privacy
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AdvancedAnalytics:
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the analytics database with proper tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Course analytics table (anonymized)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_hash TEXT NOT NULL,
                course_code TEXT NOT NULL,
                department TEXT NOT NULL,
                days TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT NOT NULL,
                semester TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                provider TEXT NOT NULL,
                event_created BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Department statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS department_stats (
                department TEXT PRIMARY KEY,
                total_courses INTEGER DEFAULT 0,
                total_events INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Time slot statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slot_stats (
                time_slot TEXT PRIMARY KEY,
                total_courses INTEGER DEFAULT 0,
                total_events INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Day of week statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS day_stats (
                day TEXT PRIMARY KEY,
                total_courses INTEGER DEFAULT 0,
                total_events INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_session(self, session_data: str) -> str:
        """Create a hash of session data for privacy"""
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]
    
    def extract_department(self, course_code: str) -> str:
        """Extract department from course code (e.g., 'CS' from 'CS115')"""
        import re
        match = re.match(r'^([A-Z]{2,4})', course_code)
        return match.group(1) if match else 'OTHER'
    
    def normalize_time(self, time_str: str) -> str:
        """Normalize time to time slot (e.g., '09:00' -> '09:00-10:00')"""
        try:
            # Parse time and create 1-hour slots
            hour = int(time_str.split(':')[0])
            return f"{hour:02d}:00-{(hour+1):02d}:00"
        except:
            return "UNKNOWN"
    
    def track_course_selection(self, courses: List[Dict], provider: str, session_id: str):
        """Track course selections for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_hash = self.hash_session(session_id)
        
        for course in courses:
            course_code = course.get('Course', 'UNKNOWN')
            department = self.extract_department(course_code)
            days = course.get('Days', 'UNKNOWN')
            start_time = course.get('Start', 'UNKNOWN')
            end_time = course.get('End', 'UNKNOWN')
            location = course.get('Location', 'UNKNOWN')
            semester = course.get('Section', '')[:3] if course.get('Section') else 'UNKNOWN'
            
            # Insert course analytics
            cursor.execute('''
                INSERT INTO course_analytics 
                (session_hash, course_code, department, days, start_time, end_time, 
                 location, semester, provider, event_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_hash, course_code, department, days, start_time, end_time,
                  location, semester, provider, False))
            
            # Update department stats
            cursor.execute('''
                INSERT OR REPLACE INTO department_stats 
                (department, total_courses, total_events, last_updated)
                VALUES (
                    ?,
                    COALESCE((SELECT total_courses FROM department_stats WHERE department = ?), 0) + 1,
                    COALESCE((SELECT total_events FROM department_stats WHERE department = ?), 0),
                    CURRENT_TIMESTAMP
                )
            ''', (department, department, department))
            
            # Update time slot stats
            time_slot = self.normalize_time(start_time)
            cursor.execute('''
                INSERT OR REPLACE INTO time_slot_stats 
                (time_slot, total_courses, total_events, last_updated)
                VALUES (
                    ?,
                    COALESCE((SELECT total_courses FROM time_slot_stats WHERE time_slot = ?), 0) + 1,
                    COALESCE((SELECT total_events FROM time_slot_stats WHERE time_slot = ?), 0),
                    CURRENT_TIMESTAMP
                )
            ''', (time_slot, time_slot, time_slot))
            
            # Update day stats
            for day in days.split():
                cursor.execute('''
                    INSERT OR REPLACE INTO day_stats 
                    (day, total_courses, total_events, last_updated)
                    VALUES (
                        ?,
                        COALESCE((SELECT total_courses FROM day_stats WHERE day = ?), 0) + 1,
                        COALESCE((SELECT total_events FROM day_stats WHERE day = ?), 0),
                        CURRENT_TIMESTAMP
                    )
                ''', (day, day, day))
        
        conn.commit()
        conn.close()
    
    def mark_events_created(self, session_id: str, provider: str):
        """Mark events as successfully created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_hash = self.hash_session(session_id)
        
        # Update course analytics
        cursor.execute('''
            UPDATE course_analytics 
            SET event_created = TRUE 
            WHERE session_hash = ? AND provider = ?
        ''', (session_hash, provider))
        
        # Update department stats
        cursor.execute('''
            UPDATE department_stats 
            SET total_events = (
                SELECT COUNT(*) 
                FROM course_analytics 
                WHERE department = department_stats.department 
                AND event_created = TRUE
            ),
            last_updated = CURRENT_TIMESTAMP
        ''')
        
        # Update time slot stats
        cursor.execute('''
            UPDATE time_slot_stats 
            SET total_events = (
                SELECT COUNT(*) 
                FROM course_analytics 
                WHERE time_slot_stats.time_slot = (
                    CASE 
                        WHEN CAST(SUBSTR(start_time, 1, 2) AS INTEGER) IS NOT NULL 
                        THEN CAST(SUBSTR(start_time, 1, 2) AS INTEGER) || ':00-' || (CAST(SUBSTR(start_time, 1, 2) AS INTEGER) + 1) || ':00'
                        ELSE 'UNKNOWN'
                    END
                )
                AND event_created = TRUE
            ),
            last_updated = CURRENT_TIMESTAMP
        ''')
        
        # Update day stats
        cursor.execute('''
            UPDATE day_stats 
            SET total_events = (
                SELECT COUNT(*) 
                FROM course_analytics 
                WHERE days LIKE '%' || day_stats.day || '%' 
                AND event_created = TRUE
            ),
            last_updated = CURRENT_TIMESTAMP
        ''')
        
        conn.commit()
        conn.close()
    
    def get_department_analytics(self) -> List[Dict]:
        """Get department-based analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT department, total_courses, total_events,
                   ROUND(CAST(total_events AS FLOAT) / total_courses * 100, 1) as conversion_rate
            FROM department_stats
            ORDER BY total_courses DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'department': row[0],
                'total_courses': row[1],
                'total_events': row[2],
                'conversion_rate': row[3]
            })
        
        conn.close()
        return results
    
    def get_time_analytics(self) -> List[Dict]:
        """Get time-based analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT time_slot, total_courses, total_events,
                   ROUND(CAST(total_events AS FLOAT) / total_courses * 100, 1) as conversion_rate
            FROM time_slot_stats
            ORDER BY time_slot
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'time_slot': row[0],
                'total_courses': row[1],
                'total_events': row[2],
                'conversion_rate': row[3]
            })
        
        conn.close()
        return results
    
    def get_day_analytics(self) -> List[Dict]:
        """Get day-of-week analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT day, total_courses, total_events,
                   ROUND(CAST(total_events AS FLOAT) / total_courses * 100, 1) as conversion_rate
            FROM day_stats
            ORDER BY 
                CASE day
                    WHEN 'Mo' THEN 1
                    WHEN 'Tu' THEN 2
                    WHEN 'We' THEN 3
                    WHEN 'Th' THEN 4
                    WHEN 'Fr' THEN 5
                    WHEN 'Sa' THEN 6
                    WHEN 'Su' THEN 7
                    ELSE 8
                END
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'day': row[0],
                'total_courses': row[1],
                'total_events': row[2],
                'conversion_rate': row[3]
            })
        
        conn.close()
        return results
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total courses and events
        cursor.execute('''
            SELECT 
                COUNT(*) as total_courses,
                SUM(CASE WHEN event_created THEN 1 ELSE 0 END) as total_events
            FROM course_analytics
        ''')
        
        total_row = cursor.fetchone()
        total_courses = total_row[0] if total_row else 0
        total_events = total_row[1] if total_row else 0
        
        # Provider distribution
        cursor.execute('''
            SELECT provider, COUNT(*) as count
            FROM course_analytics
            WHERE event_created = TRUE
            GROUP BY provider
        ''')
        
        providers = dict(cursor.fetchall())
        
        # Top departments
        cursor.execute('''
            SELECT department, COUNT(*) as count
            FROM course_analytics
            GROUP BY department
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        top_departments = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_courses': total_courses,
            'total_events': total_events,
            'conversion_rate': (total_events / total_courses * 100) if total_courses > 0 else 0,
            'providers': providers,
            'top_departments': top_departments
        }

# Global instance
analytics = AdvancedAnalytics()
