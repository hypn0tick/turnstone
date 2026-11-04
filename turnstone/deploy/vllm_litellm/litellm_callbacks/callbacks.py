class TurnstoneGuardrailCallback:
    """LiteLLM callback wiring for guardrails (placeholder)."""

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        return data