# 🚀 Quick Start Guide - Cold Email Outreach

Get your first 20 leads and send emails in 30 minutes.

## Step 1: Install Dependencies (5 min)

```bash
cd /home/ubuntu/ai_receptionist
pip install playwright beautifulsoup4 requests sib-api-v3-sdk pandas openpyxl python-dotenv
playwright install chromium
```

## Step 2: Get Brevo API Key (5 min)

1. Go to https://app.brevo.com (sign up if needed - it's free)
2. Click your name (top right) → **SMTP & API** → **API Keys**
3. Click **Generate a new API key**
4. Copy the key
5. Edit `.env` file and paste:

```bash
BREVO_API_KEY=xkeysib-YOUR_KEY_HERE
```

## Step 3: Scrape 20 Test Leads (10 min)

```bash
cd /home/ubuntu/ai_receptionist
python -c "
from outreach.google_maps_scraper import GoogleMapsScraper
import time

scraper = GoogleMapsScraper()
scraper.scrape_google_maps('clínicas dentárias Lisboa', max_results=20)
scraper.save_to_csv('outreach/leads.csv')
print('\n✅ Done! Check outreach/leads.csv')
"
```

**This will:**
- Open Chrome browser
- Search Google Maps for dental clinics in Lisbon
- Extract 20 businesses with phone numbers and websites
- Save to `outreach/leads.csv`

## Step 4: Add Emails to CSV (10 min)

Open `outreach/leads.csv` in Excel/Numbers/Google Sheets.

**Option A: Quick Test (Manual)**
- Pick 5-10 businesses
- Visit their website
- Find contact email
- Add to "email" column

**Option B: Use Hunter.io (Faster)**
1. Sign up at https://hunter.io (50 free searches/month)
2. Copy website domains from CSV
3. Search each domain on Hunter.io
4. Copy emails back to CSV

**Your CSV should look like:**

| name | address | phone | website | email | category |
|------|---------|-------|---------|-------|----------|
| Clínica Dentária XYZ | Rua ABC, Lisboa | +351912... | https://... | contato@xyz.pt | Dentist |

## Step 5: Send Test Emails (5 min)

**First, test without actually sending:**

```bash
cd /home/ubuntu/ai_receptionist
python outreach/send_emails.py
```

You'll see output like:

```
📧 Starting email campaign
Daily limit: 20 emails
Test mode: True

1. 📨 Clínica Dentária XYZ (contato@xyz.pt)
   Industry: dental
   Subject: Clínica Dentária XYZ - está a perder pacientes por não atender o telefone?
   [TEST MODE] Would send email

...

📊 Campaign Summary
✓ Sent: 20
```

**If everything looks good, send for real:**

Edit `outreach/send_emails.py`:

```python
# Line 135 - change this:
test_mode=True  # Change to False

# to this:
test_mode=False
```

Then run again:

```bash
python outreach/send_emails.py
```

## Step 6: Monitor Results

1. Go to https://app.brevo.com/statistics/email
2. Watch opens, clicks, and replies
3. Check your comercial@ia-recepcionista.com inbox for replies

## Expected Results

**Day 1-3:**
- 20 emails sent
- 4-8 opens (20-40% open rate)
- 0-2 replies (cold takes time)

**Day 4-7:**
- Continue 20/day
- Start seeing replies
- Book 1-2 demos

## Next Steps

### Scale Up (Week 2+)

Once warmed up:

```python
# In send_emails.py, increase limit:
daily_limit=50,  # or even 100
```

### Add More Searches

```python
# In google_maps_scraper.py:
searches = [
    "clínicas dentárias Lisboa",
    "clínicas dentárias Porto",
    "clínicas estética Lisboa",
    "escritórios advocacia Lisboa",
    "imobiliárias Lisboa",
]
```

### A/B Test Subject Lines

Edit `outreach/email_templates.py` and try different subject lines.

### Set Up Follow-ups

Reply to interested leads and use the demo request template.

## ⚠️ Important Tips

1. **Start slow** - 20/day for first week to warm up your domain
2. **Personalize** - The templates auto-personalize but add more if you can
3. **Track** - Use Brevo dashboard to see what works
4. **Reply fast** - When someone replies, respond within 1 hour
5. **Be patient** - Cold email takes 3-7 days to see results

## 🆘 Troubleshooting

**"Playwright not found"**
```bash
playwright install chromium
```

**"BREVO_API_KEY not found"**
- Make sure you edited `.env` file in main directory
- No spaces around the `=`
- Quotes not needed

**"No leads.csv found"**
- Run the scraper first (Step 3)

**"Emails going to spam"**
- Make sure SPF/DKIM are set up (already done for ia-recepcionista.com)
- Start with 10-20/day
- Test at mail-tester.com

## 📞 Support

If you get stuck, check the full README.md or:
- Brevo docs: https://developers.brevo.com
- Hunter.io docs: https://hunter.io/api-documentation

---

**Let's get your first demo booked! 🎯**
