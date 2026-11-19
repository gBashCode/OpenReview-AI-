"""Model Token Pricing Catalog and Cost Estimation."""

from typing import Dict, Tuple

# Pricing format: (input_price_per_million_usd, output_price_per_million_usd)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "o1": (15.00, 60.00),
    "o1-preview": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
    # Google Gemini
    "gemini-2.5-flash": (0.075, 0.30),
    "gemini-2.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    # Anthropic Claude
    "claude-3-7-sonnet": (3.00, 15.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    # Mock / Local
    "mock-model": (0.0, 0.0),
}

DEFAULT_FALLBACK_PRICING = (1.00, 3.00)


def calculate_model_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculates dollar cost for a model request based on token consumption."""
    normalized_model = model.lower()

    # Search pricing by model name or prefix
    pricing = MODEL_PRICING.get(normalized_model)
    if not pricing:
        for m_key, m_price in MODEL_PRICING.items():
            if m_key in normalized_model or normalized_model in m_key:
                pricing = m_price
                break

    if not pricing:
        pricing = DEFAULT_FALLBACK_PRICING

    input_rate, output_rate = pricing
    prompt_cost = (prompt_tokens / 1_000_000.0) * input_rate
    completion_cost = (completion_tokens / 1_000_000.0) * output_rate
    return round(prompt_cost + completion_cost, 6)
