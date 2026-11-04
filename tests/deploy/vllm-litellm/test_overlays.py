import yaml, pathlib
def test_prod_overlay_has_guardrails_and_no_paid_blocks():
    cfg = yaml.safe_load(pathlib.Path("turnstone/deploy/vllm-litellm/litellm-config.prod.yaml").read_text())
    assert "guardrails" in cfg
    assert "max_budget" not in str(cfg) or cfg.get("litellm_settings", {}).get("max_budget") == 0
