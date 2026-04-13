import csv
import re
import asyncio
from playwright.async_api import async_playwright
import os

# Configuration
INPUT_FILE = 'outreach/brevo_import.csv'
OUTPUT_FILE = 'outreach/brevo_import_fixed.csv'
# Regex for email detection
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

async def scrape_email_from_url(page, url, exclude_email=None):
    """Visits a URL and attempts to find an email address."""
    if not url or not url.startswith('http'):
        return None
    
    try:
        print(f"Scraping: {url}")
        # Navigate to the URL with a timeout
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        # Get the full page content
        content = await page.content()
        
        # Find all email-like strings
        emails = EMAIL_REGEX.findall(content)
        
        # Filter out common false positives (like image extensions or script names)
        # This is a simple filter; can be improved
        valid_emails = []
        for email in emails:
            email_lower = email.lower()
            if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js']):
                if exclude_email and email_lower == exclude_email.lower():
                    continue
                valid_emails.append(email)
        
        if valid_emails:
            # Return the first valid email found
            return valid_emails[0]
            
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    
    return None

async def process_rows(rows, target_emails=None):
    """Processes a list of rows, attempting to find missing or alternative emails."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        updated_rows = []
        
        for row in rows:
            # Check if email is missing or if it's in the target_emails list
            # Based on the CSV structure: name,address,phone,website,category,rating,search_query,scraped_at,email,status,notes,response_date
            # email is at index 8
            email_idx = 8
            website_idx = 3
            
            current_email = row[email_idx].strip()
            website = row[website_idx].strip()
            
            should_scrape = False
            if not current_email or current_email == "":
                should_scrape = True
            elif target_emails and current_email.lower() in target_emails:
                should_scrape = True
            
            if should_scrape:
                print(f"Targeting email for {row[0]}. Attempting to scrape from {website}...")
                found_email = await scrape_email_from_url(page, website, exclude_email=current_email)
                if found_email:
                    print(f"  -> Found: {found_email}")
                    row[email_idx] = found_email
                else:
                    print(f"  -> No alternative email found.")
            
            updated_rows.append(row)

        await browser.close()
        return updated_rows

async def main():
    # Read the input CSV
    rows = []
    fieldnames = []
    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            fieldnames = next(reader)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loaded {len(rows)} rows from {INPUT_FILE}.")

    # First, identify which emails are duplicates
    email_counts = {}
    for row in rows:
        email = row[8].strip().lower()
        if email:
            email_counts[email] = email_counts.get(email, 0) + 1
    
    target_emails = {email for email, count in email_counts.items() if count > 1}
    print(f"Found {len(target_emails)} duplicate email(s) to investigate.")

    # Process rows to find missing or alternative emails
    updated_rows = await process_rows(rows, target_emails=target_emails)

    # Write the updated rows to a new CSV
    try:
        from utils.atomic_writer import atomic_write_csv
        # Convert list of lists back to list of dicts for atomic_write_csv if needed, 
        # but atomic_write_csv expects DictWriter which needs fieldnames and rows as dicts.
        # Since the original code used csv.writer (list of lists), I'll adapt it.
        
        # Let's create a temporary file manually or use a more flexible atomic writer if I had one.
        # Actually, I can just implement a simple atomic write for list of lists here 
        # or modify atomic_writer to support it.
        # For now, let's use the existing pattern but with a temp file to be safe and consistent.
        
        import tempfile
        dir_name = os.path.dirname(os.path.abspath(OUTPUT_FILE))
        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".csv")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                writer.writerows(updated_rows)
            os.replace(temp_path, OUTPUT_FILE)
            print(f"Successfully wrote updated data to {OUTPUT_FILE}.")
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    except Exception as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
