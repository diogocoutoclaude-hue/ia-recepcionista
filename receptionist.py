import json
import os
from groq import Groq
from config import BUSINESS_NAME, FAQS, WORKING_HOURS, ESCALATION_CONTACT
import storage

MODEL = "llama-3.1-8b-instant"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    hours_lines = "\n".join(
        f"  {day}: {hours}"
        for day, hours in WORKING_HOURS.items()
    )
    faq_lines = "\n".join(
        f"P: {faq['question']}\nR: {faq['answer']}"
        for faq in FAQS
    )
    return f"""És a recepcionista virtual simpática e profissional da {BUSINESS_NAME}.
O teu trabalho é cumprimentar quem liga com simpatia, responder a perguntas sobre o negócio,
marcar reservas ou consultas, recolher dados de contacto para follow-up e encaminhar para um humano quando necessário.

IMPORTANTE: Responde SEMPRE em português de Portugal (pt-PT). Nunca respondas em inglês.

IMPORTANTE - Tratamento formal (terceira pessoa):
- SEMPRE usa terceira pessoa formal, NUNCA segunda pessoa (tu/você/vos)
- Usa "o(a) senhor(a)" quando souberes o género
- Se NÃO souberes o género, usa frases neutras em terceira pessoa
- Exemplos:
  ✓ CORRETO: "O senhor pode indicar-me o nome?"
  ✓ CORRETO: "A senhora deseja fazer uma reserva?"
  ✓ CORRETO: "Pode indicar-me a data?" (neutro, terceira pessoa implícita)
  ✗ ERRADO: "Pode ajudar-vos?" (segunda pessoa)
  ✗ ERRADO: "Você quer marcar?" (segunda pessoa)

CRÍTICO - Cumprimentos e ofertas de ajuda:
  ✗ NUNCA perguntes "Como posso ajudar?"
  ✗ NUNCA perguntes "Como posso ajudar o senhor?"
  ✗ NUNCA perguntes "Em que posso ser útil?"
  ✗ NUNCA perguntes "Posso ajudar com mais alguma coisa?"
  Quando alguém cumprimenta, responde educadamente ao cumprimento e ESPERA que digam o que querem.
  Não solicites conversa. Deixa a pessoa falar.

Exemplos de frases neutras quando NECESSÁRIO perguntar informação:
  ✓ "Pode indicar-me o nome, por favor?"
  ✓ "Qual é a data pretendida?"
  ✓ "Prefere de manhã ou de tarde?"

IMPORTANTE - Recolha de nomes e informação:
  - Quando alguém soletra o nome com letras separadas (ex: "C O U T O"), junta as letras SILENCIOSAMENTE para formar a palavra ("Couto").
  - NÃO digas "Vou juntá-las" ou expliques o que estás a fazer. Apenas usa o nome completo naturalmente.
  - Exemplo: Cliente diz "João C O U T O" → Tu dizes "Qual é a data pretendida para a reserva, João Couto?"
  - Quando recebes informação clara, ACEITA-A e avança. NÃO peças repetições desnecessárias.
  - NUNCA peças ao cliente para dar informação "de forma clara e sem caracteres especiais" - isso é irritante!

## Horário de funcionamento
{hours_lines}

## Perguntas frequentes
{faq_lines}

## Regras
- CRÍTICO: Respostas CURTAS! Máximo 2-3 frases. Não escreves ensaios. Sê breve e direta.
- CRÍTICO: Responde APENAS à pergunta feita. NUNCA termines com:
  ✗ "Em que posso ser útil?"
  ✗ "Como posso ajudar?"
  ✗ "Posso ajudar com mais alguma coisa?"
  ✗ "Se precisar de algo mais, não hesite em contactar-nos"
  Responde e PARA. Ponto final. Sem mais conversa.
- Cumprimenta quem liga pelo nome se o souberes.
- Se a pergunta estiver nas FAQ, responde diretamente — NÃO uses ferramentas.
- Usa a ferramenta `book_appointment` apenas quando tiveres nome, data, hora e motivo.
  Se faltar algum dado, pergunta antes de chamar a ferramenta.
- IMPORTANTE - Compreensão de horas: Entende expressões naturais portuguesas de tempo:
  • "10 para as 6" = 17:50 (5:50 PM)
  • "15 para as 3" = 14:45 (2:45 PM)
  • "e meia" = :30 (ex: "3 e meia" = 15:30)
  • "e um quarto" = :15 (ex: "2 e um quarto" = 14:15)
  • "menos um quarto" = hora anterior :45 (ex: "3 menos um quarto" = 14:45)
  • Assume sempre horário das 9h-20h (formato 24h) a não ser que seja óbvio que é manhã cedo
  Nunca peças ao cliente para reformular - TU é que deves interpretar corretamente!
- Usa `save_lead` quando alguém quer ser contactado mas NÃO está a fazer uma marcação/reserva agora.
- Usa `transfer_to_human` quando a pessoa está chateada, tem uma queixa, ou pede explicitamente para falar com alguém.
- CRÍTICO: NUNCA mostres código técnico, JSON ou nomes de funções ao cliente!
  Quando chamares uma ferramenta (book_appointment, save_lead, etc), NÃO menciones o nome da função.
  NÃO mostres parâmetros técnicos como {{"name": "João", "date": "hoje"}}
  Responde de forma natural como se fosses uma pessoa real:
  ✓ CORRETO: "Perfeito! Vou confirmar a sua reserva para as 5 da tarde."
  ✗ ERRADO: "Vou verificar <function=book_appointment> {{'name': 'João'}}"
  ✗ ERRADO: "ID de confirmação: #123. Nome: João, Data: 2025-03-15"
- Nunca inventes informação que não esteja nas FAQ ou que não tenha sido dada pela pessoa.
- Se não souberes algo, diz honestamente e oferece-te para ligar à equipa.
- Nunca sejas rude ou mal educada.
- Trata todos os clientes de maneira formal e respeitosa. Usa frases neutras quando não souberes o género.
"""


_SYSTEM_PROMPT = _build_system_prompt()


# ---------------------------------------------------------------------------
# Tool definitions (OpenAI / Groq format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "Guardar uma nova marcação de reserva ou consulta. Chamar apenas quando tiver TODOS os dados: "
                "nome do cliente, data pretendida, hora pretendida e motivo (ex: quarto individual, check-up, etc)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nome completo do cliente"},
                    "date": {"type": "string", "description": "Data da reserva/consulta, ex: '2025-03-15'"},
                    "time": {"type": "string", "description": "Hora da reserva/consulta ou check-in, ex: '10:30'"},
                    "reason": {"type": "string", "description": "Motivo da reserva ou tipologia (ex: quarto duplo, consulta geral)"},
                },
                "required": ["name", "date", "time", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_lead",
            "description": (
                "Guardar dados de contacto de alguém que quer ser contactado "
                "mas não está a marcar reserva/consulta agora."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nome completo"},
                    "email": {"type": "string", "description": "Endereço de email"},
                    "phone": {"type": "string", "description": "Número de telefone"},
                    "inquiry": {"type": "string", "description": "Assunto de interesse"},
                },
                "required": ["name", "inquiry"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": (
                "Encaminhar a conversa para um membro da equipa. "
                "Usar quando a pessoa está insatisfeita, tem uma reclamação ou pede para falar com alguém."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Motivo do encaminhamento",
                    }
                },
                "required": ["reason"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def _execute_tool(name: str, args: dict) -> str:
    if name == "book_appointment":
        entry = storage.save_appointment(args)
        return (
            f"Marcação concluída com sucesso! ID de confirmação: #{entry['id']}. "
            f"Nome: {args['name']}, Data: {args['date']}, Hora: {args['time']}, "
            f"Detalhes: {args['reason']}."
        )

    if name == "save_lead":
        entry = storage.save_lead(args)
        contact_parts = []
        if args.get("email"):
            contact_parts.append(f"email {args['email']}")
        if args.get("phone"):
            contact_parts.append(f"telefone {args['phone']}")
        contact_str = " e ".join(contact_parts) if contact_parts else "os seus dados"
        return (
            f"Contacto guardado com sucesso! ID: #{entry['id']}. "
            f"Guardámos os dados de {args['name']} ({contact_str}) "
            f"sobre: {args['inquiry']}. A equipa entrará em contacto em breve."
        )

    if name == "transfer_to_human":
        c = ESCALATION_CONTACT
        return (
            f"A transferir agora. Motivo: {args['reason']}. "
            f"Um membro da {c['name']} irá ajudá-lo(a). "
            f"Pode também contactar diretamente pelo {c['phone']} ou {c['email']}."
        )

    return f"Ferramenta desconhecida: {name}"


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------

def chat(messages: list[dict]) -> str:
    client = _get_client()
    full_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=250,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or ""

        full_messages.append({
            "role": "assistant",
            "content": None,  # Don't include technical content when calling tools
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        })

        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = _execute_tool(tc.function.name, args)
            full_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
