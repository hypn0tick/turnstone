import yaml, pathlib
def test_base_config_has_cooldowns_and_timeouts():
    cfg = yaml.safe_load(pathlib.Path("turnstone/deploy/vllm-litellm/litellm-config.yaml").read_text())
    assert cfg["litellm_settings"]["request_timeout"] == 600
    assert cfg["litellm_settings"]["stream_timeout"] == 300
    names = {m["model_name"] for m in cfg["model_list"]}
    assert names == {"qwen3.6-27b", "gemma-4-12b"}
    for m in cfg["model_list"]:
        assert m["litellm_params"]["cooldown_time"] == 30
