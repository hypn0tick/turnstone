import yaml, pathlib
def test_compose_litellm_mounts_entrypoint_and_callbacks():
    cfg = yaml.safe_load(pathlib.Path("turnstone/deploy/vllm-litellm/docker-compose.yml").read_text())
    litellm = cfg["services"]["litellm"]
    vols = litellm["volumes"]
    assert any("litellm-entrypoint.sh" in v for v in vols)
    assert any("litellm-callbacks" in v for v in vols)
    assert litellm["entrypoint"] == ["/litellm-entrypoint.sh"]
