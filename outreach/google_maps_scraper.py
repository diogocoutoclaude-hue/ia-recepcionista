"""
Google Maps Business Scraper for Lead Generation
Extracts business information from Google Maps searches in Portugal
"""

import time
import csv
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import re


class GoogleMapsScraper:
    def __init__(self):
        self.results = []

    def extract_email_from_website(self, website_url):
        """Try to find email on business website"""
        # This is a placeholder - in production you'd use Hunter.io API
        # or scrape the website for email patterns
        return None

    def extract_phone(self, text):
        """Extract Portuguese phone number"""
        # Match Portuguese phone formats: +351, 351, or 9 digits
        patterns = [
            r'\+351\s*\d{3}\s*\d{3}\s*\d{3}',
            r'351\s*\d{3}\s*\d{3}\s*\d{3}',
            r'\d{3}\s*\d{3}\s*\d{3}',
            r'\d{9}'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # Normalize to +351 format
                phone = phone.replace(' ', '')
                if not phone.startswith('+'):
                    if phone.startswith('351'):
                        phone = '+' + phone
                    else:
                        phone = '+351' + phone
                return phone
        return None

    def scrape_google_maps(self, search_query, max_results=50):
        """
        Scrape Google Maps for businesses

        Args:
            search_query: e.g., "clínicas dentárias Lisboa"
            max_results: maximum number of results to scrape
        """
        print(f"\n🔍 Searching Google Maps for: {search_query}")
        print(f"Target: {max_results} results\n")

        with sync_playwright() as p:
            # Launch browser in headless mode (required for CLI servers)
            browser = p.chromium.launch(headless=True)

            # Key: Set Portuguese (Portugal) locale + timezone
            context = browser.new_context(
                locale="pt-PT",                    # Browser language → pt-PT for Portugal
                timezone_id="Europe/Lisbon",       # Matches Portugal time
                # Optional but helpful: user agent with pt-PT hint
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            page = context.new_page()

            # Go to Google Maps
            maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            page.goto(maps_url)

            # Handle cookie consent popup
            print("⏳ Handling cookie consent...")
            time.sleep(2)

            try:
                # Try to find and click "Reject all" or "Accept all" button
                # Google uses different text in different languages
                buttons_to_try = [
                    'button:has-text("Re")',
                    'button:has-text("Rejeitar tudo")',
                    'button:has-text("Accept all")',
                    'button:has-text("Aceitar tudo")',
                    'button[aria-label*="Reject"]',
                    'button[aria-label*="Accept"]',
                ]

                for selector in buttons_to_try:
                    button = page.query_selector(selector)
                    if button:
                        print(f"   Found consent button, clicking...")
                        button.click()
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"   No cookie popup or already handled")

            # Wait for results to load
            print("⏳ Waiting for results to load...")
            time.sleep(3)

            # Scroll to load more results
            print("📜 Scrolling to load results...")
            results_panel = page.query_selector('[role="feed"]')

            if not results_panel:
                page.screenshot(path="debug_current_page.png", full_page=True)
                print("❌ Could not find results panel")
                browser.close()
                return []

            # Scroll until we have enough results or hit the end
            prev_count = 0
            stale_rounds = 0
            for i in range(max_results // 3):
                page.evaluate("""
                    const panel = document.querySelector('[role="feed"]');
                    if (panel) {
                        panel.scrollTo(0, panel.scrollHeight);
                    }
                """)
                time.sleep(2)
                current_count = len(page.query_selector_all('div[role="article"]'))
                print(f"   Scroll {i+1}... ({current_count} listings loaded)")
                if current_count >= max_results:
                    break
                # Stop if no new results after 3 scrolls
                if current_count == prev_count:
                    stale_rounds += 1
                    if stale_rounds >= 3:
                        print("   No more results to load.")
                        break
                else:
                    stale_rounds = 0
                prev_count = current_count

            # Extract business listings
            print("\n📊 Extracting business data...")
            listings = page.query_selector_all('div[role="article"]')

            for idx, listing in enumerate(listings[:max_results]):
                try:
                    # Scroll listing into view before clicking
                    listing.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    listing.click()
                    time.sleep(1.5)

                    # Extract business name - try multiple selectors
                    name = None
                    # First try: the aria-label on the listing itself often has the real name
                    aria_label = listing.get_attribute('aria-label')
                    if aria_label and 'Patrocinado' not in aria_label and 'Booking' not in aria_label:
                        name = aria_label.strip()

                    # Second try: h1 in the detail panel
                    if not name:
                        h1_elements = page.query_selector_all('h1')
                        for h1 in h1_elements:
                            text = h1.inner_text().strip()
                            if text and 'Patrocinado' not in text and 'Booking' not in text and len(text) > 2:
                                name = text
                                break

                    # Third try: the first heading/title in the detail panel
                    if not name:
                        for selector in ['h2.fontHeadlineSmall', '[data-value="Visão geral"] h1', '.fontHeadlineLarge']:
                            elem = page.query_selector(selector)
                            if elem:
                                text = elem.inner_text().strip()
                                if text and 'Patrocinado' not in text:
                                    name = text
                                    break

                    if not name or 'Patrocinado' in name:
                        print(f"   ⏭️  {idx+1}. Skipping sponsored listing (no real name)")
                        continue

                    # Extract rating
                    rating_elem = page.query_selector('div[role="img"][aria-label*="estrelas"]')
                    rating = rating_elem.get_attribute('aria-label') if rating_elem else None

                    # Extract address
                    address_elem = page.query_selector('button[data-item-id="address"]')
                    address = address_elem.inner_text()[2:] if address_elem else None

                    # Extract phone
                    phone_elem = page.query_selector('button[data-item-id*="phone"]')
                    phone = None
                    if phone_elem:
                        phone_text = phone_elem.get_attribute('aria-label')
                        phone = self.extract_phone(phone_text) if phone_text else None

                    # Extract website
                    website_elem = page.query_selector('a[data-item-id="authority"]')
                    website = website_elem.get_attribute('href') if website_elem else None

                    # Extract category
                    category_elem = page.query_selector('button[jsaction*="category"]')
                    category = category_elem.inner_text() if category_elem else None

                    # Skip duplicates within this session
                    if any(r['name'] == name and r['address'] == address for r in self.results):
                        print(f"   ⏭️  {idx+1}. Skipping duplicate: {name}")
                        continue

                    business = {
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'website': website,
                        'category': category,
                        'rating': rating,
                        'search_query': search_query,
                        'scraped_at': datetime.now().isoformat(),
                        'email': None,  # To be filled later with Hunter.io
                        'status': 'new',
                        'notes': ''
                    }

                    self.results.append(business)
                    print(f"   ✓ {idx+1}. {name}")

                except Exception as e:
                    print(f"   ✗ Error extracting listing {idx+1}: {e}")
                    continue

            browser.close()

        print(f"\n✅ Scraped {len(self.results)} businesses")
        return self.results

    def save_to_csv(self, filename="leads.csv"):
        """Save results to CSV file"""
        if not self.results:
            print("No results to save")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)

        print(f"\n💾 Saved {len(self.results)} leads to {filename}")

    def save_to_json(self, filename="leads.json"):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"💾 Saved to {filename}")


def main():
    """Example usage"""
    scraper = GoogleMapsScraper()

    # Define your search queries - Hotels in Porto region
    searches = [
        "hotéis Porto",
        "hotel Porto centro",
        "hotel Porto Boavista",
        "hotel Porto Ribeira",
        "hotel Matosinhos",
        "hotel Vila Nova de Gaia",
        "hotel Maia Porto",
        "hotel Gondomar",
        "hotel Valongo",
        "alojamento local Porto",
        "alojamento local Porto centro",
        "alojamento local Gaia",
        "hostels Porto",
        "hostel Porto centro",
        "guest house Porto",
        "pousada Porto",
        "pensão Porto",
        "bed and breakfast Porto",
        "turismo rural Porto",
        "hotel boutique Porto",
        "residencial Porto",
    ]

    # Scrape each search
    for search in searches:
        scraper.scrape_google_maps(search, max_results=40)
        time.sleep(5)  # Be polite, don't hammer Google

    # Save results
    scraper.save_to_csv("outreach/leads.csv")
    scraper.save_to_json("outreach/leads.json")

    print("\n🎉 Scraping complete!")
    print(f"Total leads: {len(scraper.results)}")


if __name__ == "__main__":
    main()
