# Follow-Up Email Automation

## Overview

Single automated follow-up sent 5 days after initial email to leads who haven't responded.

## How It Works

**Integrated System** - Follow-ups are now automatically detected and sent via `send_emails.py`

1. **Initial Email** - Sent via `send_emails.py`
   - Writes `sent_at` timestamp to `notes` column in `leads.csv`
   - Sets `status` to `contacted`

2. **Response Detection** - Automatic (built into `send_emails.py`)
   - Fetches Brevo API metrics (opens/clicks) from last 7 days
   - Updates lead status to `responded` for engaged leads
   - Prevents follow-ups to people who already replied

3. **Follow-Up Detection** - Automatic (built into `send_emails.py`)
   - Checks emails sent 5+ days ago
   - Filters for `status == 'contacted'` (no response)
   - **Excludes responders** - Leads with status in `['responded', 'interested', 'contacted', 'followup_sent']`
   - Prioritizes follow-ups before new emails

4. **Follow-Up Email** - Sent automatically
   - Subject: `Re: {original_subject}`
   - Body: References original email, adds concrete value (revenue loss numbers)
   - **Clear boundary**: "Se não responder, não vou voltar a incomodar"
   - Sets expectation: No more emails after this

## Running Follow-Ups

### Automatic (Recommended)
Run `send_emails.py` as usual - follow-ups are automatically detected and sent first:
```bash
cd outreach
python3 send_emails.py
```

**How it works:**
- Follow-ups are sent BEFORE new emails
- Both count against the same `daily_limit`
- Results are tracked separately in `leads.csv`

### Manual Testing
```bash
cd outreach
python3 send_emails.py  # test_mode=True by default
```

### Production Mode
Set `test_mode=False` in `send_emails.py` to actually send emails:
```python
sender.send_campaign(
    leads_csv=os.path.join(os.path.dirname(__file__), "leads.csv"),
    daily_limit=20,
    start_from=0,
    test_mode=False  # Actually send emails
)
```

## Template

**Subject:** `Re: {original_subject}`

**Body:**
- References original email sent 5 days ago
- Adds concrete value proposition (revenue loss numbers)
- Includes demo link
- Clear CTA: "Responda 'sim' para demo personalizada"
- **Boundary statement**: "Se não responder, não vou voltar a incomodar"
- Full signature with contact info

## Results Tracking

After each campaign, `leads.csv` will include:
- `sent_at` - Initial email timestamp
- `followup_sent_at` - Follow-up timestamp (if sent)
- `followup_subject` - Follow-up subject line
- `status` - `contacted`, `followup_sent`, or `followup_failed`
- `days_since_initial` - Days since original email

## Important Notes

- ✅ Follow-ups are sent FIRST, before new emails
- ✅ Both count against the same daily limit
- ✅ Only 1 follow-up per lead (no spam)
- ✅ Clear boundary: "Se não responder, não vou voltar a incomodar"
- ✅ **Response detection** - Automatically excludes leads who opened/clicked
- ✅ Leads who respond (status changes) are automatically excluded

## Response Detection

**Automatic Engagement Tracking** - Prevents spamming engaged leads

The system automatically checks Brevo API for opens and clicks from the last 7 days:

1. **Fetches Events** - Gets all opened and clicked emails
2. **Updates Status** - Marks engaged leads as `responded`
3. **Excludes from Follow-ups** - Responders never get follow-up emails

**Example:**
```
Total leads: 144
Responders (excluded): 47
Follow-up candidates: 97
```

This ensures you're not spamming people who already engaged with your emails.

## Key Features

✅ **Single follow-up only** - No spammy sequences
✅ **5-day delay** - Gives time to process
✅ **Clear boundary** - "No more emails" statement
✅ **Value-add** - Concrete numbers, not just "bumping this up"
✅ **Easy opt-out** - Respects their inbox
✅ **Automated** - No manual tracking needed

## Metrics to Track

- Follow-up open rate
- Follow-up response rate
- Conversion from follow-up vs. initial email

## Next Steps

1. Run `send_followups.py` daily (or weekly)
2. Monitor response rates
3. Adjust 5-day timing if needed (try 3 or 7 days)
4. Consider A/B testing subject lines
