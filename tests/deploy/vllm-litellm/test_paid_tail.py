import yaml, pathlib

DEV = pathlib.Path("turnstone/deploy/vllm-litellm/litellm-config.dev.yaml")
PROD = pathlib.Path("turnstone/deploy/vllm-litellm/litellm-config.prod.yaml")


def test_prod_overlay_strips_paid_blocks():
    cfg = yaml.safe_load(PROD.read_text()) or {}
    text = PROD.read_text()
    assert "max_budget" not in text
    assert "paid" not in text.lower()


def test_dev_overlay_retains_paid_blocks():
    text = DEV.read_text()
    cfg = yaml.safe_load(text) or {}
    assert "max_budget" in text
    assert cfg.get("litellm_settings", {}).get("max_budget") is not None or "${MAX_BUDGET_USD:-0}" in text
