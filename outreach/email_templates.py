"""
Cold Email Templates for Different Industries
Portuguese templates for AI receptionist outreach
"""

# Email templates by industry
EMAIL_TEMPLATES = {
    "hotel": {
        "subject_lines": [
            "{name} - quantas reservas perde fora do horário da receção?",
            "Rececionista virtual 24/7 para {name} - desde €199/mês",
            "Como o {name} gere chamadas de hóspedes à noite?",
        ],
        "body": """Olá {contact_name},

Uma questão prática: quantas reservas perde o {name} por mês quando a receção está fechada ou ocupada?

Hotéis no Porto perdem em média **8-12 reservas/mês** fora do horário comercial - cada reserva perdida representa **€120-€180 de lucro**.

Criei uma rececionista IA que resolve isso:

✓ Atende 24/7 (PT, EN, ES, FR)
✓ Reserva diretamente no seu sistema
✓ Custa €199/mês (paga-se com o lucro de 1-2 reservas)

Teste grátis: https://ia-recepcionista.com/#demo

Posso criar uma demo personalizada com os dados do {name}? Responda "sim".

**Sem compromisso:** pode cancelar a qualquer momento e tem **100% de reembolso nos primeiros 30 dias**.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
https://ia-recepcionista.com
""",
    },

    "hostel": {
        "subject_lines": [
            "{name} - está a perder reservas por não atender chamadas?",
            "Rececionista virtual para {name} - desde €199/mês",
            "{name} - nunca mais perca uma reserva fora do horário",
        ],
        "body": """Olá {contact_name},

Com tantos viajantes internacionais a ligar a qualquer hora, quantas reservas escapam ao {name} quando a receção está fechada?

Hostels perdem em média **6-10 reservas/mês** fora do horário - cada reserva perdida representa **€70-€120 de lucro**.

Minha rececionista IA resolve:

✓ 24/7 em PT, EN, ES, FR
✓ Responde sobre dormitórios, preços e disponibilidade
✓ Custa €199/mês (paga-se com o lucro de 2-3 reservas)

Demo grátis: https://ia-recepcionista.com/#demo

Quer ver como funciona para o {name}? Responda "sim".

**Sem compromisso:** pode cancelar a qualquer momento e tem **100% de reembolso nos primeiros 30 dias**.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
https://ia-recepcionista.com
""",
    },

    "guesthouse": {
        "subject_lines": [
            "{name} - como gere reservas quando não está disponível?",
            "Rececionista virtual 24/7 para {name}",
            "{name} - nunca mais perca uma chamada de turista",
        ],
        "body": """Olá {contact_name},

Gerir um alojamento local significa fazer tudo sozinho — e não é possível atender todas as chamadas, especialmente de turistas que ligam a qualquer hora.

Alojamentos locais perdem **5-8 reservas/mês** fora do horário - cada reserva perdida representa **€90-€150 de lucro**.

Criei uma rececionista IA que:

✓ Atende 24/7 (PT, EN, ES, FR)
✓ Responde sobre disponibilidade, preços e comodidades
✓ Custa €199/mês (paga-se com o lucro de 2 reservas)

Teste grátis: https://ia-recepcionista.com/#demo

Posso preparar uma demo com os dados do {name}? Responda "sim".

**Sem compromisso:** pode cancelar a qualquer momento e tem **100% de reembolso nos primeiros 30 dias**.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
https://ia-recepcionista.com
""",
    },

    "generic": {
        "subject_lines": [
            "{name} - está a perder clientes por não atender?",
            "Rececionista virtual 24/7 - desde €199/mês",
            "Como {name} gere chamadas fora do horário?",
        ],
        "body": """Olá {contact_name},

Uma pergunta rápida: quantas chamadas perdem por dia quando estão ocupados?

Negócios locais perdem em média **15-25 chamadas/dia** fora do horário comercial - cada chamada perdida representa **€50-€100 de lucro**.

Criei uma rececionista IA que:

✓ Atende 24/7 (fins de semana, feriados, noites)
✓ Responde às perguntas mais frequentes
✓ Custa €199/mês (paga-se com 2-3 chamadas convertidas)

Teste grátis: https://ia-recepcionista.com/#demo

Posso preparar uma demo com os dados de {name}? Responda "sim".

**Sem compromisso:** pode cancelar a qualquer momento e tem **100% de reembolso nos primeiros 30 dias**.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
https://ia-recepcionista.com
""",
    }
}


# Follow-up email templates (single follow-up, 5 days after initial)
FOLLOWUP_TEMPLATES = {
    "follow_up_5days": {
        "subject": "Re: {original_subject}",
        "body": """Olá {contact_name},

Enviei um email há 5 dias sobre uma rececionista virtual para o {name}, mas sei que a correria não deixa espaço para tudo.

Deixo só um número: **hotéis no Porto perdem 8-12 reservas/mês fora do horário da receção**. Cada reserva = **€120-€180 de lucro**.

A rececionista IA resolve isso por **€199/mês** (paga-se com 1-2 reservas recuperadas).

**Teste grátis:** https://ia-recepcionista.com/#demo

**Sem compromisso:** pode cancelar a qualquer momento e tem **100% de reembolso nos primeiros 30 dias**.

Se tiver interesse, responda "sim" e crio uma demo personalizada com os dados do {name}.

**Se não responder, não vou voltar a incomodar** — entendo perfeitamente.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
https://ia-recepcionista.com
"""
    },

    "demo_request": {
        "subject": "Demo personalizada para {name} - próximos passos",
        "body": """Olá {contact_name},

Obrigado pelo interesse na rececionista virtual para o {name}!

Para preparar uma demonstração personalizada, preciso de algumas informações:

1. **Tipos de quartos/alojamento** que oferecem?
2. **Idiomas** mais comuns dos vossos hóspedes?
3. **Principais perguntas** que recebem (check-in, preços, localização)?
4. **Como gerem reservas** atualmente (telefone, Booking, email, outro)?

Com estas informações, preparo uma demo em 2-3 dias onde a rececionista virtual já responde especificamente sobre o {name}.

Quando tiver disponibilidade para uma videochamada de 15min?

Pode agendar aqui: https://ia-recepcionista.com/#agendar

Ou responder com algumas datas/horas e eu confirmo.

Cumprimentos,
Diogo Couto
IA Recepcionista
+351 964 065 744
diogo-couto@ia-recepcionista.com
"""
    }
}


def get_template(industry, lead_data):
    """
    Get email template for specific industry and fill with lead data

    Args:
        industry: "dental", "beauty", "law", "real_estate", "accounting", or "generic"
        lead_data: dict with keys: name, city, contact_name (optional)

    Returns:
        dict with subject_lines (list) and body (str)
    """
    # Get template or fallback to generic
    template = EMAIL_TEMPLATES.get(industry, EMAIL_TEMPLATES["generic"])

    # Fill in placeholders
    contact_name = lead_data.get("contact_name", "")
    city = lead_data.get("city", "").split(",")[0] if lead_data.get("city") else ""

    subject_lines = [
        s.format(
            name=lead_data.get("name", ""),
            city=city,
            contact_name=contact_name
        )
        for s in template["subject_lines"]
    ]

    body = template["body"].format(
        name=lead_data.get("name", ""),
        city=city,
        contact_name=contact_name or "Dr./Dra.",
    )

    return {
        "subject_lines": subject_lines,
        "body": body
    }


# Map categories to industries
CATEGORY_MAPPING = {
    "hotel": "hotel",
    "hotéis": "hotel",
    "alojamento": "hotel",
    "resort": "hotel",
    "pousada": "hotel",
    "pensão": "hotel",

    "hostel": "hostel",
    "hostels": "hostel",
    "albergue": "hostel",

    "guesthouse": "guesthouse",
    "guest house": "guesthouse",
    "alojamento local": "guesthouse",
    "casa de hóspedes": "guesthouse",
    "bed and breakfast": "guesthouse",
    "b&b": "guesthouse",
    "turismo rural": "guesthouse",
}


def detect_industry(business_category):
    """Detect industry from business category"""
    if not business_category:
        return "generic"

    category_lower = business_category.lower()

    for keyword, industry in CATEGORY_MAPPING.items():
        if keyword in category_lower:
            return industry

    return "generic"
