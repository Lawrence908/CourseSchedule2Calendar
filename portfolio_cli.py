#!/usr/bin/env python3
"""
Portfolio CLI Tool for SchedShare
Generate portfolio reports and statistics from command line
"""

import argparse
import json
import sys
from datetime import datetime
from portfolio_analytics import PortfolioAnalytics

def main():
    parser = argparse.ArgumentParser(description='Generate SchedShare portfolio reports')
    parser.add_argument('--format', choices=['json', 'markdown', 'summary'], 
                       default='summary', help='Output format')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--stats-only', action='store_true', 
                       help='Show only key statistics')
    
    args = parser.parse_args()
    
    try:
        analytics = PortfolioAnalytics()
        
        if args.format == 'summary':
            data = analytics.get_portfolio_summary()
            achievements = analytics.get_technical_achievements()
            insights = analytics.get_business_insights()
            
            if args.stats_only:
                # Show only key metrics
                print("🚀 SchedShare Portfolio Statistics")
                print("=" * 40)
                print(f"👥 Users Served: {data['impact_metrics']['unique_users_served']}")
                print(f"📚 Courses Processed: {data['impact_metrics']['total_courses_processed']}")
                print(f"📅 Calendar Events: {data['impact_metrics']['successful_calendar_events']}")
                print(f"🏫 Departments: {data['impact_metrics']['departments_served']}")
                print(f"✅ Success Rate: {data['impact_metrics']['conversion_rate']}%")
                print(f"🔄 Recent Sessions (30d): {data['engagement_metrics']['recent_sessions_30d']}")
                
                if data['technology_adoption']:
                    print("\n🔧 Technology Adoption:")
                    for provider, count in data['technology_adoption'].items():
                        print(f"  - {provider.title()}: {count} events")
            else:
                # Show detailed summary
                print("🚀 SchedShare Portfolio Summary")
                print("=" * 50)
                
                print("\n📊 Impact Metrics:")
                for key, value in data['impact_metrics'].items():
                    print(f"  - {key.replace('_', ' ').title()}: {value}")
                
                print("\n📈 Engagement Metrics:")
                for key, value in data['engagement_metrics'].items():
                    print(f"  - {key.replace('_', ' ').title()}: {value}")
                
                print("\n🏆 Technical Achievements:")
                for achievement in achievements:
                    print(f"  - {achievement['category']}: {achievement['achievement']}")
                    print(f"    Metric: {achievement['metric']}")
                    print(f"    Impact: {achievement['impact']}")
                
                print("\n💡 Business Insights:")
                print(f"  - Average courses per user: {insights['user_behavior']['average_courses_per_user']}")
                print(f"  - User engagement: {insights['product_insights']['user_engagement_level']}")
                
                if data['technology_adoption']:
                    print("\n🔧 Technology Adoption:")
                    for provider, count in data['technology_adoption'].items():
                        print(f"  - {provider.title()}: {count} events")
        
        elif args.format == 'json':
            data = analytics.generate_portfolio_stats()
            output = json.dumps(data, indent=2)
            
        elif args.format == 'markdown':
            output = analytics.export_portfolio_data('markdown')
        
        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                if args.format == 'summary':
                    # For summary format, we already printed to stdout
                    pass
                else:
                    f.write(output)
            print(f"✅ Report saved to {args.output}")
        else:
            if args.format != 'summary':
                print(output)
    
    except Exception as e:
        print(f"❌ Error generating portfolio report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()




