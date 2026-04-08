"""
AI-Powered Cold Email Generator
Generates unique, personalized emails per lead using OpenAI API.
Scrapes a website summary, then writes a natural cold email.
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def scrape_website_summary(url, max_chars=3000):
    """Get a text summary from a website for AI context."""
    if not url:
        return ""

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Skip booking platforms - no useful info about the business
    skip = ['booking.com', 'airbnb.com', 'abnb.me', 'tripadvisor.com',
            'expedia.com', 'facebook.com', 'instagram.com', 'google.com',
            'cloudbeds.com', 'guestready.com', 'holidu.', 'bluepillow.com']
    if any(s in domain for s in skip):
        return ""

    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, verify=False, allow_redirects=True)
        if resp.status_code != 200:
            return ""

        html = resp.text

        # Strip scripts, styles, tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.I)
        html = re.sub(r'<[^>]+>', ' ', html)
        html = re.sub(r'\s+', ' ', html).strip()

        # Decode HTML entities
        import html as html_module
        html = html_module.unescape(html)

        return html[:max_chars]
    except Exception:
        return ""


BASE_TEMPLATES = {
    "Hotel": """Olá,

Vi que o {name} é uma unidade hoteleira em {location}.

Uma pergunta rápida: o que acontece quando um turista liga às 23h para reservar ou um hóspede precisa de informação e a receção está ocupada?

Na hotelaria, quem responde primeiro ganha a reserva. E uma reserva perdida pode valer centenas de euros.

Criei uma rececionista virtual com IA para hotéis que atende 24/7 em português, inglês, espanhol e francês, gere reservas e verifica disponibilidade automaticamente, responde sobre preços, check-in/out, serviços e localização, e encaminha pedidos urgentes de hóspedes para a equipa.

Desde €199/mês +IVA — menos que um turno noturno de receção.

Quer ver uma demonstração personalizada com os dados do {name}? Pode testar aqui: https://ia-recepcionista.com/#demo

Responda a este email e preparo uma demo personalizada em 3 dias.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com""",

    "Hostel": """Olá,

Vi que o {name} é um hostel em {location}.

Com tantos viajantes internacionais a ligar a qualquer hora e em diferentes idiomas, quantas reservas escapam quando a receção está ocupada ou fechada?

Criei uma rececionista virtual com IA que atende 24/7 em português, inglês, espanhol e francês, responde sobre disponibilidade, preços e dormitórios, ajuda com reservas e informações sobre a zona, e nunca está "fora" — funciona 365 dias por ano.

Desde €199/mês +IVA — menos que um dia de funcionário.

Quer ver como funciona para o {name}? Teste aqui: https://ia-recepcionista.com/#demo

Responda e preparo uma demo personalizada em 3 dias.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com""",

    "Guest House": """Olá,

Vi que o {name} é um alojamento em {location}.

Sei que gerir um alojamento muitas vezes significa fazer tudo sozinho(a) — e não é possível atender todas as chamadas, especialmente de turistas que ligam a qualquer hora.

Criei uma rececionista virtual com IA que atende 24/7 em português, inglês, espanhol e francês, responde sobre disponibilidade, preços e comodidades, dá indicações sobre check-in, localização e arredores, e encaminha reservas e pedidos especiais para si.

Desde €199/mês +IVA — paga-se com uma reserva extra por mês.

Quer ver uma demonstração com os dados do {name}? Teste grátis: https://ia-recepcionista.com/#demo

Responda e preparo uma demo personalizada em 3 dias.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com""",
}

# Map categories to template keys
TEMPLATE_MAP = {
    "Hotel": "Hotel",
    "Hostel": "Hostel",
    "Guest House": "Guest House",
    "Alojamento Local": "Guest House",
    "Residencial": "Hotel",
    "Pousada": "Hotel",
}


def generate_email(lead, website_text=""):
    """Use AI to refine the base template with lead-specific details."""

    name = lead.get('name', '')
    category = lead.get('category', 'Hotel')
    address = lead.get('address', '')
    rating = lead.get('rating', '')

    # Get location from address
    location = "Porto"
    if address:
        for part in address.split(','):
            part = part.strip()
            for city in ['Matosinhos', 'Gaia', 'Vila Nova de Gaia', 'Maia', 'Valongo', 'Gondomar']:
                if city.lower() in part.lower():
                    location = city
                    break

    # Get base template
    template_key = TEMPLATE_MAP.get(category, "Hotel")
    base = BASE_TEMPLATES[template_key].format(name=name, location=location)

    website_context = ""
    if website_text and len(website_text) > 100:
        website_context = f"""
Website text about this business (use to personalize the opening line):
{website_text[:1500]}
"""

    prompt = f"""Here is a cold outreach email template for {name} ({category}):

---
{base}
---
{website_context}

Rewrite this email with small adjustments to make it feel personal and unique:

1. OPENING LINE: If you have website context, replace the generic "Vi que o {name} é uma unidade hoteleira em {location}" with something specific about their business (e.g. their style, what they're known for, a feature from their website). Keep it to one sentence.
2. VARY THE WORDING slightly throughout — rephrase a few sentences so it doesn't read identical to other emails, but keep the same structure, arguments and length.
3. Keep the pricing, CTA link, and signature EXACTLY as they are.
4. Write in Portuguese from Portugal (not Brazilian).
5. Do NOT add bullet points, checkmarks, or any formatting the original doesn't have.
6. Keep it the same length — do not make it longer.

Return ONLY the rewritten email, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        result = response.choices[0].message.content.strip()
        # Remove any --- delimiters the AI may include
        result = result.strip('-').strip()
        return result
    except Exception as e:
        print(f"  AI error: {e}")
        # Fallback to base template
        return base


def generate_subject(lead, email_body):
    """Generate a natural subject line for the email."""

    name = lead.get('name', '')

    prompt = f"""Generate a cold email subject line in Portuguese (Portugal) for an email to {name}.

RULES:
- Max 3-5 words
- Must look like a casual personal email, NOT marketing
- Short and vague enough to create curiosity
- Lowercase, no emojis, no exclamation marks
- Can include their name but keep it natural

GOOD examples (copy this style):
- "pergunta rápida, {name}"
- "{name}"
- "vi o vosso site"
- "pergunta sobre o {name}"
- "tentei ligar-vos"

BAD examples (never do this):
- "{name} — como lidar com hóspedes noturnos?"
- "rececionista virtual 24/7 para {name}"
- "chamadas perdidas no {name}?"
- anything with "solução", "ajuda", "melhorar", "proposta", "rececionista"

Return ONLY the subject line, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=30
        )
        return response.choices[0].message.content.strip().strip('"\'')
    except Exception as e:
        print(f"  Subject AI error: {e}")
        return f"{name} - rececionista virtual 24/7"


def process_leads(send_list_path="outreach/send_list.json", output_path="outreach/emails_ready.json", limit=None):
    """Generate personalized emails for all leads."""

    with open(send_list_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    if limit:
        leads = leads[:limit]

    print(f"Generating emails for {len(leads)} leads...\n")

    results = []
    for i, lead in enumerate(leads, 1):
        name = lead.get('name', '')
        email = lead.get('email', '')
        website = lead.get('website', '')

        print(f"[{i}/{len(leads)}] {name} ({email})")

        # Scrape website for context
        print(f"  Scraping website...")
        website_text = scrape_website_summary(website)
        has_context = len(website_text) > 100
        print(f"  {'Got' if has_context else 'No'} website context ({len(website_text)} chars)")

        # Generate email body
        print(f"  Generating email...")
        body = generate_email(lead, website_text)
        if not body:
            print(f"  FAILED — skipping")
            continue

        # Generate subject line
        subject = generate_subject(lead, body)
        print(f"  Subject: {subject}")

        results.append({
            **lead,
            'generated_subject': subject,
            'generated_body': body,
            'has_website_context': has_context,
        })

        # Rate limit
        time.sleep(0.5)

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Generated {len(results)} emails")
    print(f"Saved to {output_path}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    process_leads()
