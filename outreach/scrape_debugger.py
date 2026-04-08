
import time
import csv
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

search_query="clínicas dentárias Porto"
max_results=20

with sync_playwright() as p:
        # Launch browser in headless mode (required for CLI servers)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to Google Maps
        maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        page.goto(maps_url)

        # Handle cookie consent popup
        print("⏳ Waiting for page to load...")
        time.sleep(5)

        try:
            # Try to find and click "Reject all" or "Accept all" button
            reject_button = page.query_selector('button[aria-label*="Reject"], button:has-text("Reject all"), button:has-text("Re")')
            if reject_button:
                print("   Clicking cookie consent...")
                reject_button.click()
                time.sleep(1)
            else:
                # Try accept button if reject not found
                accept_button = page.query_selector('button[aria-label*="Accept"], button:has-text("Accept all"), button:has-text("Aceitar")')
                if accept_button:
                    print("   Accepting cookies...")
                    accept_button.click()
                    time.sleep(1)
        except Exception as e:
            print(f"   No cookie popup or already handled: {e}")

        # Wait for results to load
        time.sleep(3)

        # Scroll to load more results
        print("📜 Scrolling to load results...")
        results_panel = page.query_selector('[role="feed"]')

        if not results_panel:
            page.screenshot(path="debug_current_page.png", full_page=True)
            print("❌ Could not find results panel")
            browser.close()
            exit()


        # Scroll multiple times to load more results
        for i in range(max_results // 10):
            page.evaluate("""
                const panel = document.querySelector('[role="feed"]');
                if (panel) {
                    panel.scrollTo(0, panel.scrollHeight);
                }
            """)
            time.sleep(2)
            print(f"   Scroll {i+1}...")

        # Extract business listings
        print("\n📊 Extracting business data...")
        listings = page.query_selector_all('div[role="article"]')

        for idx, listing in enumerate(listings[:max_results]):
            try:
                # Click on listing to see details
                listing.click()
                time.sleep(1.5)

                # Extract business name
                name_elem = page.query_selector('h1')
                name = name_elem.inner_text() if name_elem else "N/A"

                # Extract rating
                rating_elem = page.query_selector('div[role="img"][aria-label*="estrelas"]')
                rating = rating_elem.get_attribute('aria-label') if rating_elem else None

                # Extract address
                address_elem = page.query_selector('button[data-item-id="address"]')
                address = address_elem.inner_text() if address_elem else None

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