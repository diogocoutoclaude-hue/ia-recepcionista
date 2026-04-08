"""
Brevo API Helper Module
Fetch transactional email metrics (opens, clicks, bounces, etc.)
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()


class BrevoAPI:
    """Helper class for Brevo transactional email API"""
    
    def __init__(self):
        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
    
    def get_events(self, event_type='opened', start_date=None, end_date=None, days=7):
        """
        Fetch events from Brevo API
        
        Args:
            event_type: Type of event ('opened', 'clicks', 'hardBounces', 'softBounces', 'spam', 'unsubscribed')
            start_date: Start date in 'YYYY-MM-DD' format (optional)
            end_date: End date in 'YYYY-MM-DD' format (optional)
            days: Number of days to look back (used if start_date not provided)
        
        Returns:
            list: List of event objects with email, _date, and other metadata
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Get events using the API
            api_response = self.api_instance.get_email_event_report(
                start_date=start_date,
                end_date=end_date,
                event=event_type,
                limit=1000  # Maximum allowed
            )
            
            events = []
            if api_response and api_response.events:
                for event in api_response.events:
                    events.append({
                        'email': event.email,
                        '_date': event._date,
                        'event': event.event,
                        'message_id': event.message_id,
                        'subject': event.subject
                    })
            
            return events
            
        except ApiException as e:
            if e.status == 429:  # Rate limit
                print(f"⚠️  Rate limited for {event_type} events. Waiting 60 seconds...")
                time.sleep(60)
                # Retry once
                try:
                    api_response = self.api_instance.get_email_event_report(
                        start_date=start_date,
                        end_date=end_date,
                        event=event_type,
                        limit=1000
                    )
                    if api_response and api_response.events:
                        for event in api_response.events:
                            events.append({
                                'email': event.email,
                                '_date': event._date,
                                'event': event.event,
                                'message_id': event.message_id,
                                'subject': event.subject
                            })
                    return events
                except ApiException as e2:
                    print(f"❌ Error fetching {event_type} events (retry failed): {e2}")
                    return []
            else:
                print(f"❌ Error fetching {event_type} events: {e}")
                return []
    
    def get_email_stats(self, email):
        """
        Get statistics for a specific email address
        
        Args:
            email: Email address to check
        
        Returns:
            dict: Statistics including opens, clicks, bounces, etc.
        """
        stats = {
            'email': email,
            'opened': 0,
            'clicked': 0,
            'bounced': 0,
            'spam': 0,
            'unsubscribed': 0
        }
        
        # Check opened events
        opened = self.get_events(event_type='opened', days=30)
        stats['opened'] = sum(1 for e in opened if e['email'] == email)
        
        # Check clicked events
        clicked = self.get_events(event_type='clicks', days=30)
        stats['clicked'] = sum(1 for e in clicked if e['email'] == email)
        
        # Check bounces
        bounces = self.get_events(event_type='hardBounces', days=30)
        bounces += self.get_events(event_type='softBounces', days=30)
        stats['bounced'] = sum(1 for e in bounces if e['email'] == email)
        
        # Check spam complaints
        spam = self.get_events(event_type='spam', days=30)
        stats['spam'] = sum(1 for e in spam if e['email'] == email)
        
        # Check unsubscribes
        unsubscribed = self.get_events(event_type='unsubscribed', days=30)
        stats['unsubscribed'] = sum(1 for e in unsubscribed if e['email'] == email)
        
        return stats
    
    def check_if_responded(self, email, days_back=7):
        """
        Check if an email has responded (opened or clicked) in the last N days
        
        Args:
            email: Email address to check
            days_back: Number of days to look back
        
        Returns:
            bool: True if email has responded
        """
        # Check opened events
        opened = self.get_events(event_type='opened', days=days_back)
        if any(e['email'] == email for e in opened):
            return True
        
        # Check clicked events
        clicked = self.get_events(event_type='clicks', days=days_back)
        if any(e['email'] == email for e in clicked):
            return True
        
        return False
    
    def check_all_responses(self, leads_csv, days_back=7):
        """
        Check all leads in CSV for responses
        
        Args:
            leads_csv: Path to leads CSV file
            days_back: Number of days to look back
        
        Returns:
            dict: {email: stats} for all responsive leads
        """
        responsive_leads = {}
        
        with open(leads_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            leads = list(reader)
        
        for lead in leads:
            email = lead.get('email', '')
            if email and self.check_if_responded(email, days_back):
                responsive_leads[email] = self.get_email_stats(email)
        
        return responsive_leads


if __name__ == "__main__":
    # Test the API
    brevo = BrevoAPI()
    
    print("Testing Brevo API connection...")
    
    # Get recent opened events
    opened = brevo.get_events(event_type='opened', days=7)
    print(f"\n📧 Opened events (last 7 days): {len(opened)}")
    for event in opened[:5]:  # Show first 5
        print(f"   - {event['email']} at {event['_date']}")
    
    # Get recent clicked events
    clicked = brevo.get_events(event_type='clicks', days=7)
    print(f"\n🖱️  Clicked events (last 7 days): {len(clicked)}")
    for event in clicked[:5]:  # Show first 5
        print(f"   - {event['email']} at {event['_date']}")
