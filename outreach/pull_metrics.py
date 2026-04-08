"""
Pull Brevo Transactional Email Metrics
Retrieve statistics from your Brevo transactional emails (not campaigns)
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()


class BrevoMetrics:
    def __init__(self):
        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
    def get_email_event_report(self, start_date=None, end_date=None, days=None, limit=100, offset=0):
        """
        Get email event report (sent, opened, clicked, bounced, etc.)
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            days: Number of days to look back (alternative to start_date/end_date)
            limit: Maximum number of events to retrieve
            offset: Offset for pagination
        """
        try:
            # Build parameters dict with only non-None values
            params = {
                'limit': limit,
                'offset': offset
            }
            
            # Only add date parameters if they have values
            if days is not None:
                params['days'] = days
            if start_date is not None:
                params['start_date'] = start_date
            if end_date is not None:
                params['end_date'] = end_date
            
            api_response = self.api_instance.get_email_event_report(**params)
            return api_response.events
        except ApiException as e:
            print(f"Error fetching email events: {e}")
            return []
    
    def get_contact_stats(self, email):
        """Get statistics for a specific contact"""
        try:
            api_response = self.api_instance.get_stats_for_contact(email)
            return api_response
        except ApiException as e:
            print(f"Error fetching contact stats: {e}")
            return None
    
    def get_all_contacts_stats(self, limit=100):
        """Get statistics for all contacts"""
        try:
            api_response = self.api_instance.get_all_contacts_stats(limit=limit, offset=0)
            return api_response
        except ApiException as e:
            print(f"Error fetching contact stats: {e}")
            return None
            return None
    
    def get_contact_stats(self, email):
        """Get statistics for a specific contact"""
        try:
            api_response = self.api_instance.get_stats_for_contact(email)
            return api_response
        except ApiException as e:
            print(f"Error fetching contact stats: {e}")
            return None
    
    def print_transactional_metrics(self, limit=100):
        """Print summary of transactional email metrics"""
        print(f"\n{'='*80}")
        print(f"📊 BREVO TRANSACTIONAL EMAIL METRICS")
        print(f"{'='*80}\n")
        
        # Get all events
        all_events = self.get_email_event_report(limit=limit)
        
        if not all_events:
            print("No email events found!")
            return
        
        # Count by event type
        event_counts = {}
        for event in all_events:
            event_type = event.event
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        print(f"📧 Email Events Summary (Last {limit} events):\n")
        for event_type, count in sorted(event_counts.items()):
            print(f"   • {event_type.capitalize()}: {count}")
        
        # Get detailed stats for each event type
        print(f"\n{'─'*80}")
        print(f"📈 Detailed Breakdown:\n")
        
        # Use actual Brevo event type names (plural forms)
        event_type_mapping = {
            'requests': 'Sent',
            'opened': 'Opened',
            'clicks': 'Clicked',
            'hardBounces': 'Hard Bounced',
            'softBounces': 'Soft Bounced',
            'loadedByProxy': 'Loaded by Proxy',
            'blocked': 'Blocked',
            'spam': 'Spam',
            'unsubscribed': 'Unsubscribed'
        }
        
        for event_type, display_name in event_type_mapping.items():
            events = self.get_email_event_report(limit=1000)
            filtered_events = [e for e in events if e.event == event_type]
            if filtered_events:
                print(f"   {display_name}: {len(filtered_events)} events")
                
                # Show recent examples
                if len(filtered_events) > 0:
                    print(f"      Recent:")
                    for event in filtered_events[:3]:
                        email = event.email
                        timestamp = event._date
                        print(f"         • {email} at {timestamp}")
        
        print(f"\n{'='*80}")
    
    def get_contact_email_stats(self, email):
        """Get detailed stats for a specific email address"""
        stats = self.get_contact_stats(email)
        if stats:
            return {
                'email': email,
                'total_sent': stats.total_count,
                'total_opened': stats.opened_count,
                'total_clicked': stats.clicked_count,
                'total_bounced': stats.bounced_count,
                'last_activity': stats.last_activity_date
            }
        return None
    
    def export_metrics_to_json(self, filename='brevo_transactional_metrics.json', limit=1000):
        """Export all transactional email metrics to a JSON file"""
        # Get all events
        all_events = self.get_email_event_report(limit=limit)
        
        # Organize by email address
        email_stats = {}
        
        for event in all_events:
            email = event.email or 'unknown'
            event_type = event.event
            
            if email not in email_stats:
                email_stats[email] = {
                    'email': email,
                    'sent': 0,
                    'opened': 0,
                    'clicked': 0,
                    'bounced': 0,
                    'blocked': 0,
                    'spam': 0,
                    'unsubscribed': 0,
                    'events': []
                }
            
            # Map Brevo event types to stats keys
            if event_type == 'requests':
                email_stats[email]['sent'] += 1
            elif event_type == 'opened':
                email_stats[email]['opened'] += 1
            elif event_type == 'clicks':
                email_stats[email]['clicked'] += 1
            elif event_type in ['hardBounces', 'softBounces']:
                email_stats[email]['bounced'] += 1
            elif event_type == 'blocked':
                email_stats[email]['blocked'] += 1
            elif event_type == 'spam':
                email_stats[email]['spam'] += 1
            elif event_type == 'unsubscribed':
                email_stats[email]['unsubscribed'] += 1
            
            # Add event to history
            email_stats[email]['events'].append({
                'type': event_type,
                'timestamp': event._date
            })
        
        # Convert to list and sort by total sent
        metrics_list = list(email_stats.values())
        metrics_list.sort(key=lambda x: x['sent'], reverse=True)
        
        metrics_data = {
            'generated_at': datetime.now().isoformat(),
            'total_emails_tracked': len(metrics_list),
            'total_events': limit,
            'emails': metrics_list
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        print(f"✅ Metrics exported to {filename}")
        return metrics_data
    
    def get_summary_statistics(self, limit=1000):
        """Get overall summary statistics"""
        all_events = self.get_email_event_report(limit=limit)
        
        summary = {
            'total_sent': 0,
            'total_opened': 0,
            'total_clicked': 0,
            'total_bounced': 0,
            'total_blocked': 0,
            'total_spam': 0,
            'total_unsubscribed': 0
        }
        
        for event in all_events:
            event_type = event.event
            # Map Brevo event types to summary keys
            if event_type == 'requests':
                summary['total_sent'] += 1
            elif event_type == 'opened':
                summary['total_opened'] += 1
            elif event_type == 'clicks':
                summary['total_clicked'] += 1
            elif event_type in ['hardBounces', 'softBounces']:
                summary['total_bounced'] += 1
            elif event_type == 'blocked':
                summary['total_blocked'] += 1
            elif event_type == 'spam':
                summary['total_spam'] += 1
            elif event_type == 'unsubscribed':
                summary['total_unsubscribed'] += 1
        
        # Calculate rates
        if summary['total_sent'] > 0:
            summary['open_rate'] = (summary['total_opened'] / summary['total_sent']) * 100
            summary['click_rate'] = (summary['total_clicked'] / summary['total_sent']) * 100
            summary['bounce_rate'] = (summary['total_bounced'] / summary['total_sent']) * 100
        else:
            summary['open_rate'] = 0
            summary['click_rate'] = 0
            summary['bounce_rate'] = 0
        
        return summary


def main():
    """Main function to pull and display metrics"""
    # Check if API key is set
    if not os.getenv('BREVO_API_KEY'):
        print("❌ Error: BREVO_API_KEY not found in .env file")
        return
    
    print("🔄 Connecting to Brevo API...")
    metrics = BrevoMetrics()
    
    # Get summary statistics
    summary = metrics.get_summary_statistics(limit=1000)
    
    print(f"\n{'='*80}")
    print(f"📊 OVERALL SUMMARY")
    print(f"{'='*80}\n")
    print(f"   📧 Total Sent: {summary['total_sent']}")
    print(f"   👁️  Total Opened: {summary['total_opened']}")
    print(f"   🖱️  Total Clicked: {summary['total_clicked']}")
    print(f"   ⚠️  Total Bounced: {summary['total_bounced']}")
    print(f"   🚫 Total Blocked: {summary['total_blocked']}")
    print(f"   🚨 Total Spam: {summary['total_spam']}")
    print(f"   📉 Total Unsubscribed: {summary['total_unsubscribed']}")
    
    print(f"\n   📊 Rates:")
    print(f"      • Open Rate: {summary['open_rate']:.2f}%")
    print(f"      • Click Rate: {summary['click_rate']:.2f}%")
    print(f"      • Bounce Rate: {summary['bounce_rate']:.2f}%")
    
    # Print detailed metrics
    metrics.print_transactional_metrics(limit=100)
    
    # Export to JSON
    export_file = 'brevo_transactional_metrics.json'
    metrics.export_metrics_to_json(export_file)
    
    print(f"\n💡 You can view detailed metrics in: {export_file}")


if __name__ == "__main__":
    main()
