"""
Email Sender using Brevo (Sendinblue) API
Send personalized cold emails to leads
Also handles follow-up emails (5 days after initial contact)
"""

import os
import sys
import time
import csv
import json
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from email_templates import get_template, detect_industry
from brevo_api import BrevoAPI

load_dotenv()


class EmailSender:
    def __init__(self):
        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        self.sender_email = os.getenv('SENDER_EMAIL', 'comercial@ia-recepcionista.com')
        self.sender_name = os.getenv('SENDER_NAME', 'Diogo Couto')

    def send_email(self, to_email, to_name, subject, html_content):
        """
        Send email via Brevo API

        Args:
            to_email: recipient email
            to_name: recipient name
            subject: email subject
            html_content: email HTML body

        Returns:
            bool: True if sent successfully
        """
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name}],
            sender={"email": self.sender_email, "name": self.sender_name},
            subject=subject,
            html_content=html_content.replace('\n', '<br>'),  # Convert to HTML
            reply_to={"email": self.sender_email, "name": self.sender_name}
        )

        try:
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            print(f"   ✓ Email sent to {to_email}")
            return True
        except ApiException as e:
            print(f"   ✗ Error sending to {to_email}: {e}")
            return False

    def check_responses(self, leads_csv, days_back=7):
        """
        Check Brevo API for engagement (opens/clicks) and log for manual review
        
        Args:
            leads_csv: path to CSV file with leads
            days_back: check events from last N days
        """
        print(f"\n🔍 Checking for engagement (last {days_back} days)...")
        
        # Get Brevo API instance
        brevo = BrevoAPI()
        
        # Fetch opened and clicked events
        opened_emails = brevo.get_events(event_type='opened', days=days_back)
        clicked_emails = brevo.get_events(event_type='clicks', days=days_back)
        
        # Count engagement per email
        engagement_data = {}
        
        for event in opened_emails:
            email = event.get('email', '')
            if email:
                if email not in engagement_data:
                    engagement_data[email] = {'opens': 0, 'clicks': 0}
                engagement_data[email]['opens'] += 1
        
        for event in clicked_emails:
            email = event.get('email', '')
            if email:
                if email not in engagement_data:
                    engagement_data[email] = {'opens': 0, 'clicks': 0}
                engagement_data[email]['clicks'] += 1
        
        if not engagement_data:
            print("✅ No engagement found\n")
            return
        
        # Log engagement for manual review
        print(f"📊 Engagement Summary ({len(engagement_data)} contacts):\n")
        print(f"{'Name':<40} {'Email':<40} {'Opens':<8} {'Clicks':<8}")
        print("-" * 100)
        
        # Load leads to get names
        csv_file = leads_csv if os.path.exists(leads_csv) else 'brevo_import.csv'
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            leads = {
                (lead.get('email') or lead.get('EMAIL', '')).lower(): lead
                for lead in reader
            }
        
        for email, data in sorted(engagement_data.items(), key=lambda x: x[1]['clicks'], reverse=True):
            lead = leads.get(email.lower(), {})
            name = (lead.get('name') or lead.get('NOME_NEGOCIO', '') or email)[:40]
            print(f"{name:<40} {email:<40} {data['opens']:<8} {data['clicks']:<8}")
        
        print(f"\n💡 Tip: Manually update status in {csv_file} for contacts you want to follow up with")
        print(f"   Recommended statuses: 'interested', 'contacted', 'not_interested'")

    def send_campaign(self, leads_csv, daily_limit=20, start_from=0, test_mode=False):
        """
        Send cold emails to leads from CSV
        Also sends follow-ups to leads who haven't responded (5+ days old)

        Args:
            leads_csv: path to CSV file with leads
            daily_limit: maximum emails to send per day (includes follow-ups)
            start_from: index to start from (for resuming)
            test_mode: if True, only print without sending
        """
        print(f"\n📧 Starting email campaign")
        print(f"Daily limit: {daily_limit} emails")
        print(f"Starting from index: {start_from}")
        print(f"Test mode: {test_mode}\n")

        # First, check for responses and update lead statuses
        self.check_responses(leads_csv, days_back=7)

        # Load leads - try both file names for compatibility
        csv_file = leads_csv if os.path.exists(leads_csv) else 'brevo_import.csv'
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            leads = list(reader)

        print(f"Loaded {len(leads)} leads from {leads_csv}\n")

        # Track results
        sent_count = 0
        failed_count = 0
        results = []
        follow_up_count = 0
        cutoff_date = datetime.now() - timedelta(days=5)

        # First, send follow-ups to leads who haven't responded (5+ days old)
        print("🔍 Checking for follow-ups (5+ days old, no response)...\n")
        
        for idx, lead in enumerate(leads):
            if sent_count >= daily_limit:
                break

            # Skip if no email (handle both 'email' and 'EMAIL')
            email = lead.get('email') or lead.get('EMAIL')
            if not email:
                continue

            # Check if sent 5+ days ago
            sent_at = lead.get('notes', '')
            if not sent_at:
                continue

            try:
                sent_date = datetime.fromisoformat(sent_at)
                if sent_date >= cutoff_date:
                    continue  # Not old enough yet
            except ValueError:
                continue  # Invalid date format

            # Check if they responded (status changed)
            status = lead.get('status', '')
            if status in ['responded', 'interested', 'contacted', 'followup_sent']:
                continue  # They responded or already got follow-up

            # Get follow-up template
            original_subject = lead.get('subject', 'Assunto anterior')
            name = lead.get('name') or lead.get('NOME_NEGOCIO', '')
            email = lead.get('email') or lead.get('EMAIL')
            days_since = (datetime.now() - sent_date).days

            template = get_template('follow_up_5days', {})
            subject = template['subject'].format(original_subject=original_subject)
            body = template['body'].format(name=name, contact_name=name)

            print(f"{idx+1}. 🔄 Follow-up: {name} ({email})")
            print(f"   Sent {sent_date.strftime('%Y-%m-%d')} ({days_since} days ago)")
            print(f"   Subject: {subject}")

            if test_mode:
                print(f"   [TEST MODE] Would send follow-up")
                sent_count += 1
                follow_up_count += 1
                continue

            # Send follow-up
            success = self.send_email(
                to_email=email,
                to_name=name,
                subject=subject,
                html_content=body
            )

            # Update result - set status to 'not_interested' when follow-up is sent
            result = {
                **lead,
                'followup_sent_at': datetime.now().isoformat() if success else None,
                'followup_subject': subject,
                'status': 'followup_sent' if success else 'followup_failed',
                'days_since_initial': days_since
            }
            results.append(result)

            if success:
                sent_count += 1
                follow_up_count += 1
            else:
                failed_count += 1

            # Be polite - wait between emails
            time.sleep(2)

        # Then send new emails to remaining leads
        print(f"\n{'='*60}")
        print(f"📧 Sending new emails...\n")

        for idx, lead in enumerate(leads[start_from:], start=start_from):
            if sent_count >= daily_limit:
                print(f"\n✋ Daily limit reached ({daily_limit} emails)")
                break

            # Skip if no email (handle both 'email' and 'EMAIL')
            email = lead.get('email') or lead.get('EMAIL')
            if not email:
                name = lead.get('name') or lead.get('NOME_NEGOCIO', '')
                print(f"{idx+1}. ⏭️  Skipping {name} - no email")
                continue

            # Skip if already contacted (but allow 'new' status)
            status = lead.get('status', '')
            if status and status != 'new':
                name = lead.get('name') or lead.get('NOME_NEGOCIO', '')
                print(f"{idx+1}. ⏭️  Skipping {name} - already contacted (status: {status})")
                continue

            # Detect industry and get template
            industry = detect_industry(lead.get('category', ''))

            # Extract city from address
            city = ""
            if lead.get('address'):
                # Try to extract city (usually after first comma)
                parts = lead['address'].split(',')
                if len(parts) >= 2:
                    city = parts[1].strip()

            # Get personalized template
            name = lead.get('name') or lead.get('NOME_NEGOCIO', '')
            lead_data = {
                "name": name,
                "city": city,
                "contact_name": ""  # We don't have this, template will use "Dr./Dra."
            }

            template = get_template(industry, lead_data)
            subject = template['subject_lines'][0]  # Use first subject line
            body = template['body']

            print(f"\n{idx+1}. 📨 {name} ({email})")
            print(f"   Industry: {industry}")
            print(f"   Subject: {subject}")

            if test_mode:
                print(f"   [TEST MODE] Would send email")
                sent_count += 1
                continue

            # Send email
            success = self.send_email(
                to_email=email,
                to_name=name,
                subject=subject,
                html_content=body
            )

            # Update result
            result = {
                **lead,
                'sent_at': datetime.now().isoformat() if success else None,
                'subject': subject,
                'status': 'contacted' if success else 'failed',
                'industry_detected': industry
            }
            results.append(result)

            if success:
                sent_count += 1
            else:
                failed_count += 1

            # Be polite - wait between emails
            time.sleep(2)

        # Save results back to original CSV (adds sent_at and subject columns)
        # IMPORTANT: Only update the leads that were processed, don't overwrite the entire file
        if results:
            try:
                # Use the same file we loaded from
                csv_file = leads_csv if os.path.exists(leads_csv) else 'brevo_import.csv'
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    fieldnames = list(reader.fieldnames) if reader.fieldnames else []
                    all_leads = list(reader)
                
                # Update the processed leads in the full list
                for result in results:
                    email = result.get('email') or result.get('EMAIL')
                    for lead in all_leads:
                        lead_email = lead.get('email') or lead.get('EMAIL')
                        if email == lead_email:
                            # Update this lead with result data
                            for key, value in result.items():
                                lead[key] = value
                            break
                
                # Save updated leads
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_leads)
                
                print(f"✅ Results saved to {csv_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save results: {e}")
                print("   Campaign completed but lead statuses were not updated")

        print(f"\n{'='*60}")
        print(f"📊 Campaign Summary")
        print(f"{'='*60}")
        print(f"🔄 Follow-ups sent: {follow_up_count}")
        print(f"📨 New emails sent: {sent_count - follow_up_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"📝 Results saved to: {leads_csv}")
        print(f"\n💡 Resume from index {start_from + sent_count + failed_count} next time")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Send cold emails to leads via Brevo API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python send_emails.py --limit 20           # Dry run (default)
  python send_emails.py --send --limit 20    # Actually send emails
  python send_emails.py --resume 100         # Resume from index 100
        '''
    )
    
    parser.add_argument('--csv', type=str, default='brevo_import.csv',
                        help='Path to CSV file with leads (default: brevo_import.csv)')
    parser.add_argument('--limit', type=int, default=20,
                        help='Daily email limit (default: 20)')
    parser.add_argument('--resume', type=int, default=0,
                        help='Resume from index (default: 0)')
    parser.add_argument('--send', action='store_true',
                        help='Actually send emails (default: dry run only)')
    
    args = parser.parse_args()
    
    sender = EmailSender()

    # Check if API key is set
    if not os.getenv('BREVO_API_KEY'):
        print("❌ Error: BREVO_API_KEY not found in .env file")
        print("\nAdd this to your .env file:")
        print("BREVO_API_KEY=your_key_here")
        print("SENDER_EMAIL=comercial@ia-recepcionista.com")
        print("SENDER_NAME=Diogo Couto")
        return

    # Send campaign (dry run by default, use --send to actually send)
    sender.send_campaign(
        leads_csv=args.csv,
        daily_limit=args.limit,
        start_from=args.resume,
        test_mode=not args.send  # Default to True (dry run)
    )


if __name__ == "__main__":
    main()
