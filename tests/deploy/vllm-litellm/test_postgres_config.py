import yaml, pathlib
def test_prod_overlay_has_database_url():
    cfg = yaml.safe_load(pathlib.Path("turnstone/deploy/vllm-litellm/litellm-config.prod.yaml").read_text())
    gs = cfg.get("general_settings", {})
    assert "database_url" in gs
    assert "proxy_batch_write_at" in gs
    assert "allow_requests_on_db_unavailable" in gs
