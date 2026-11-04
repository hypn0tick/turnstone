import yaml, pathlib
def test_compose_has_db_and_migrate_services():
    cfg = yaml.safe_load(pathlib.Path("turnstone/deploy/vllm-litellm/docker-compose.yml").read_text())
    assert "db" in cfg["services"]
    assert "litellm-migrate" in cfg["services"]
    assert cfg["services"]["litellm"]["depends_on"]["db"]["condition"] == "service_healthy"

