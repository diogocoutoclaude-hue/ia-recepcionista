"""
Email Scraper for Hotel Leads
Crawls hotel websites to find contact email addresses.
Checks homepage, contact page, and common paths.
"""

import re
import json
import time
import requests
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


# Common email patterns to ignore (generic/useless)
IGNORE_EMAILS = {
    'noreply', 'no-reply', 'mailer-daemon', 'postmaster',
    'webmaster', 'admin@wordpress', 'email@example',
    'wix.com', 'squarespace.com', 'wordpress.com',
    'sentry.io', 'cloudflare.com',
}

# Pages likely to have contact emails
CONTACT_PATHS = [
    '/contacto', '/contactos', '/contact', '/contacts',
    '/sobre', '/about', '/about-us', '/sobre-nos',
    '/reservas', '/reservations', '/booking',
    '/info', '/informacoes',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.5',
}

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)


def is_valid_email(email):
    """Filter out junk/system emails"""
    email_lower = email.lower()
    if any(ignore in email_lower for ignore in IGNORE_EMAILS):
        return False
    # Skip image file extensions mistakenly caught
    if email_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
        return False
    # Must have a reasonable TLD
    domain = email.split('@')[1]
    if '.' not in domain or len(domain) < 4:
        return False
    return True


def decode_cf_email(encoded):
    """Decode Cloudflare-obfuscated email from data-cfemail attribute"""
    try:
        r = int(encoded[:2], 16)
        return ''.join(chr(int(encoded[i:i+2], 16) ^ r) for i in range(2, len(encoded), 2))
    except Exception:
        return ''


def extract_emails_from_html(html):
    """Extract all valid emails from HTML content"""
    emails = set(EMAIL_REGEX.findall(html))

    # Decode Cloudflare-protected emails
    for encoded in re.findall(r'data-cfemail="([^"]+)"', html):
        decoded = decode_cf_email(encoded)
        if decoded and '@' in decoded:
            emails.add(decoded)

    # Extract from JSON-LD structured data
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.DOTALL):
        ld_emails = EMAIL_REGEX.findall(block)
        emails.update(ld_emails)

    return {e for e in emails if is_valid_email(e)}


def scrape_website_emails(website_url, timeout=10):
    """
    Scrape a website for email addresses.
    Checks the homepage and common contact pages.
    Returns a set of found emails.
    """
    if not website_url:
        return set()

    # Normalize URL
    url = website_url.strip()
    if not url.startswith('http'):
        url = 'https://' + url

    # Skip non-website URLs (social media, booking platforms, etc.)
    domain = urlparse(url).netloc.lower()
    skip_domains = [
        'facebook.com', 'instagram.com', 'booking.com',
        'airbnb.com', 'abnb.me', 'tripadvisor.com',
        'expedia.com', 'www.hotels.com', 'decolar.com',
        'google.com', 'youtube.com', 'linkedin.com',
        'cloudbeds.com', 'twitter.com', 'x.com',
    ]
    if any(domain == d or domain.endswith('.' + d) for d in skip_domains):
        return set()

    all_emails = set()
    pages_to_check = [url]
    checked = set()

    # Add common contact pages
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    for path in CONTACT_PATHS:
        pages_to_check.append(urljoin(base_url, path))
    # Also add /pt/ and /en/ prefixed versions
    for path in CONTACT_PATHS:
        pages_to_check.append(urljoin(base_url, '/pt' + path))
        pages_to_check.append(urljoin(base_url, '/en' + path))

    for page_url in pages_to_check:
        if page_url in checked:
            continue
        checked.add(page_url)

        try:
            resp = requests.get(
                page_url,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True,
                verify=False
            )
            if resp.status_code == 200:
                html = resp.text

                # Handle meta http-equiv refresh redirects
                meta_redirect = re.search(
                    r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d+;\s*URL=([^"\'>\s]+)',
                    html, re.IGNORECASE
                )
                if meta_redirect and len(html) < 500:
                    redirect_url = urljoin(page_url, meta_redirect.group(1))
                    if redirect_url not in checked:
                        pages_to_check.insert(0, redirect_url)
                        continue

                emails = extract_emails_from_html(html)
                all_emails.update(emails)

                # Discover more pages: contact links, nav links with relevant keywords
                link_patterns = ['contact', 'contacto', 'sobre', 'about', 'reserv', 'info']
                for pattern in link_patterns:
                    for match in re.finditer(
                        rf'href=["\']([^"\']*{pattern}[^"\']*)["\']',
                        html, re.IGNORECASE
                    ):
                        found_url = urljoin(base_url, match.group(1))
                        parsed = urlparse(found_url)
                        # Only follow links on the same domain
                        if parsed.netloc == urlparse(base_url).netloc and found_url not in checked:
                            pages_to_check.append(found_url)

                # If homepage had few emails, also follow any internal links
                # to catch pages like /en/casas.php that may have footer emails
                if page_url == url and not all_emails:
                    for match in re.finditer(
                        r'href=["\']([^"\'#][^"\']*)["\']',
                        html, re.IGNORECASE
                    ):
                        href = match.group(1)
                        found_url = urljoin(base_url, href)
                        parsed = urlparse(found_url)
                        if parsed.netloc == urlparse(base_url).netloc and found_url not in checked:
                            pages_to_check.append(found_url)

        except (requests.RequestException, Exception):
            continue

        # Small delay between pages on same site
        time.sleep(0.3)

        # Stop early if we found emails (no need to crawl everything)
        if all_emails and len(checked) > 3:
            break

    return all_emails


def pick_best_email(emails):
    """Pick the most relevant email from a set (prefer reservas@, info@, geral@, contacto@)"""
    if not emails:
        return ''

    priority_prefixes = [
        'reservas', 'reservations', 'booking',
        'info', 'geral', 'general',
        'contacto', 'contact', 'recepcao', 'reception',
        'comercial',
    ]

    emails_list = list(emails)
    for prefix in priority_prefixes:
        for email in emails_list:
            if email.lower().startswith(prefix):
                return email

    # Return the first one that's not a personal-looking email
    return emails_list[0]


def scrape_lead(lead):
    """Scrape emails for a single lead. Returns (index, name, email, all_emails)."""
    website = lead.get('website', '')
    name = lead.get('name', '')

    if not website:
        return (name, '', set())

    emails = scrape_website_emails(website)
    best = pick_best_email(emails)
    return (name, best, emails)


def main():
    # Load leads
    with open('outreach/leads.json', 'r', encoding='utf-8') as f:
        leads = json.load(f)

    # Filter to leads with websites and no email yet (re-run safe)
    to_scrape = [l for l in leads if l.get('website') and not l.get('email')]
    already_have = sum(1 for l in leads if l.get('email'))
    print(f"Already have email: {already_have}")
    print(f"No website: {sum(1 for l in leads if not l.get('website'))}")
    print(f"Scraping emails for {len(to_scrape)} leads with websites...\n")

    found_count = 0
    total = len(to_scrape)

    # Use thread pool for parallel scraping
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_lead = {
            executor.submit(scrape_lead, lead): lead
            for lead in to_scrape
        }

        for i, future in enumerate(as_completed(future_to_lead), 1):
            lead = future_to_lead[future]
            try:
                name, best_email, all_emails = future.result()
                if best_email:
                    lead['email'] = best_email
                    found_count += 1
                    extras = f" (also: {', '.join(all_emails - {best_email})})" if len(all_emails) > 1 else ""
                    print(f"  [{i}/{total}] ✓ {name}: {best_email}{extras}")
                else:
                    print(f"  [{i}/{total}]   {name}: no email found")
            except Exception as e:
                print(f"  [{i}/{total}] ✗ {lead.get('name')}: error - {e}")

    # Save updated leads
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.atomic_writer import atomic_write_json, atomic_write_csv
    atomic_write_json('outreach/leads.json', leads, indent=2)

    if leads and len(leads) > 0:
        atomic_write_csv('outreach/leads.csv', list(leads[0].keys()), leads)

    print(f"\n{'='*60}")
    print(f"Emails found: {found_count} / {total} websites scraped")
    print(f"Leads with email: {sum(1 for l in leads if l.get('email'))}")
    print(f"Leads total: {len(leads)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
