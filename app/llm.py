"""Provider-agnostic LLM wrapper that returns text + tokens + latency + cost. Falls back to MOCK mode without keys."""
import os
import time
from dataclasses import dataclass
from . import config


@dataclass
class LLMResult:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_usd: float


def cost(model, tin, tout):
    pin, pout = config.PRICING.get(model, (0.0, 0.0))
    return round((tin * pin + tout * pout) / 1_000_000, 6)


def _mock(prompt, system):
    # Deterministic offline answer: echoes the most relevant context so the pipeline is testable without keys.
    if "SQL" in system:
        return "SELECT part_number, name, price_eur, stock FROM parts WHERE category='Stoßdämpfer' LIMIT 5"
    if "ROUTE" in system:
        return "sql" if any(k in prompt.lower() for k in ("lager", "stock", "preis", "price", "passt", "fit")) else "rag"
    ctx = prompt.split("KONTEXT:")[-1].split("FRAGE:")[0].strip()
    return "[MOCK] Auf Basis der Quellen: " + ctx[:300].replace("\n", " ")


def is_mock(model=None):
    model = model or config.DEFAULT_MODEL
    return not ((model.startswith("claude") and os.getenv("ANTHROPIC_API_KEY")) or (model.startswith("gpt") and os.getenv("OPENAI_API_KEY")))


def complete(prompt, system="", model=None, max_tokens=800, image_b64=None, media_type="image/png") -> LLMResult:
    model = model or config.DEFAULT_MODEL
    t0 = time.time()
    tin = tout = 0
    if model.startswith("claude") and os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        content = [{"type": "text", "text": prompt}]
        if image_b64:
            content.insert(0, {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}})
        r = anthropic.Anthropic().messages.create(model=model, max_tokens=max_tokens, system=system,
                                                  messages=[{"role": "user", "content": content}])
        text, tin, tout = r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
    elif model.startswith("gpt") and os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        content = [{"type": "text", "text": prompt}]
        if image_b64:
            content.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}})
        r = OpenAI().chat.completions.create(model=model, max_tokens=max_tokens,
                                             messages=[{"role": "system", "content": system},
                                                       {"role": "user", "content": content}])
        text, tin, tout = r.choices[0].message.content, r.usage.prompt_tokens, r.usage.completion_tokens
    else:
        model = "mock"
        text = _mock(prompt, system)
        tin, tout = len((system + prompt).split()), len(text.split())
    ms = int((time.time() - t0) * 1000)
    return LLMResult(text, model, tin, tout, ms, cost(model, tin, tout))
