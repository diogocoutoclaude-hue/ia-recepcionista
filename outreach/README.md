# Cold Email Outreach System

Complete system for finding leads and sending personalized cold emails for the AI Receptionist service.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/ubuntu/ai_receptionist/outreach
pip install -r requirements.txt

# Install Playwright browsers (for scraping)
playwright install chromium
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Brevo (Sendinblue) API credentials
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=comercial@ia-recepcionista.com
SENDER_NAME=Diogo Couto
```

**Get your Brevo API key:**
1. Go to https://app.brevo.com/settings/keys/api
2. Create new API key
3. Copy and paste into `.env`

### 3. Scrape Leads from Google Maps

```bash
python google_maps_scraper.py
```

This will:
- Search Google Maps for businesses (dental clinics, beauty clinics, etc.)
- Extract: name, address, phone, website, rating
- Save to `leads.csv` and `leads.json`

**Customize searches** by editing `google_maps_scraper.py`:

```python
searches = [
    "clínicas dentárias Lisboa",
    "clínicas estética Porto",
    "escritórios advocacia Coimbra",
    "imobiliárias Braga",
    # Add more...
]
```

### 4. Find Email Addresses

The scraper gets phone/website but not emails. You have 3 options:

**Option A: Manual (Free)**
- Open each website and find contact email
- Add to CSV manually

**Option B: Hunter.io (Recommended)**
1. Sign up at https://hunter.io (50 free searches/month)
2. Upload domain list
3. Download emails
4. Merge into `leads.csv`

**Option C: Buy Database**
- GSAS.es: €83.7 for 10,460 dental clinics with emails
- Bancomail: 918 dentist contacts

### 5. Send Cold Emails

**Test first (doesn't actually send):**

```bash
python send_emails.py
```

This runs in test mode by default. Review the output to see what would be sent.

**Send for real:**

Edit `send_emails.py` and change:
```python
test_mode=True  # Change to False
```

Then run:
```bash
python send_emails.py
```

**Important:** Start with 10-20 emails/day to warm up your domain!

## 📊 Email Campaign Strategy

### Week 1: Warm-up (20 emails/day)
```bash
python send_emails.py  # Day 1: 20 emails
# Wait 24 hours
python send_emails.py  # Day 2: next 20 emails
# Continue...
```

### Week 2+: Scale (50-100 emails/day)

Once your domain is warmed up and deliverability is good.

## 📧 Email Templates

Templates automatically adapt based on business category:

| Industry | Keywords Detected | Template Used |
|----------|------------------|---------------|
| Dental | "dentária", "dentist" | Dental template |
| Beauty | "estética", "beleza", "spa" | Beauty template |
| Law | "advogado", "advocacia" | Law template |
| Real Estate | "imobiliária" | Real estate template |
| Accounting | "contabilista" | Accounting template |
| Other | Any | Generic template |

**Customize templates** in `email_templates.py`

## 🔄 Follow-up Sequence

1. **Day 0**: Initial email
2. **Day 3**: Soft follow-up ("não sei se viu...")
3. **Day 7**: Final follow-up ("última tentativa")

To send follow-ups, edit `send_emails.py` and use the follow-up templates.

## 📈 Tracking Results

Results are saved to `leads_results.csv` with:
- When email was sent
- Subject line used
- Status (contacted/failed)
- Industry detected

**Monitor:**
- Open Brevo dashboard: https://app.brevo.com/statistics/email
- Track opens, clicks, replies
- Adjust copy based on performance

## 🎯 Expected Results

**Industry benchmarks for cold email:**
- Open rate: 20-40%
- Reply rate: 5-15%
- Meeting booked: 1-3%

**Your target:**
- 100 emails/day = 5-15 replies = 1-3 demos booked

## ⚠️ Important Notes

### GDPR Compliance

✅ **Legitimate Interest** - B2B cold email is legal in EU under "legitimate interest"
✅ **Always include unsubscribe** - "Responda com REMOVER se não quiser mais emails"
✅ **Respect opt-outs immediately**
✅ **Be transparent** - Real sender info, no deception

### Email Deliverability

**Do:**
- ✅ Warm up slowly (20/day → 50/day → 100/day)
- ✅ Personalize every email
- ✅ Keep under 200 words
- ✅ Avoid spam words ("grátis", "garantido", "urgente")
- ✅ Monitor spam complaints

**Don't:**
- ❌ Send from new domain without warm-up
- ❌ Use purchased email lists without verification
- ❌ Send same copy to everyone
- ❌ Exceed 300 emails/day (Brevo free limit)

### Spam Score

Test your emails at https://www.mail-tester.com before sending campaign.

Target: 7/10 or higher

## 🛠️ Customization

### Change search areas:

```python
searches = [
    "clínicas dentárias Lisboa",
    "clínicas dentárias Porto",
    "clínicas dentárias Coimbra",
    "clínicas dentárias Braga",
    "clínicas dentárias Faro",
]
```

### Change daily limits:

```python
sender.send_campaign(
    leads_csv="outreach/leads.csv",
    daily_limit=50,  # Increase when warmed up
    start_from=0
)
```

### Add new industry template:

Edit `email_templates.py` and add new industry to `EMAIL_TEMPLATES` dict.

## 📞 Next Steps

1. ✅ Install dependencies
2. ✅ Get Brevo API key
3. ✅ Run scraper to get 100 leads
4. ✅ Find emails (Hunter.io or manual)
5. ✅ Test send (test_mode=True)
6. ✅ Send 20 emails (Day 1)
7. ✅ Monitor Brevo dashboard
8. ✅ Reply to interested leads
9. ✅ Scale to 50-100/day after week 1

## 🆘 Troubleshooting

**"No leads.csv found"**
- Run `google_maps_scraper.py` first

**"BREVO_API_KEY not found"**
- Add to `.env` file (see step 2)

**"Emails going to spam"**
- Warm up slower
- Check mail-tester.com
- Add SPF/DKIM records (already done for ia-recepcionista.com)

**"Low reply rate"**
- A/B test subject lines
- Make more personal (mention something specific about their business)
- Improve pain point (are you solving a real problem?)

## 📚 Resources

- Brevo Dashboard: https://app.brevo.com
- Hunter.io: https://hunter.io
- Mail Tester: https://www.mail-tester.com
- GDPR Guide: https://gdpr.eu/email-marketing-gdpr/

---

Built for **IA Recepcionista** by Diogo Couto
