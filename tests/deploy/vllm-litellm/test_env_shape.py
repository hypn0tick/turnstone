import pathlib, re
def test_env_example_has_all_required_keys():
    text = pathlib.Path("turnstone/deploy/vllm-litellm/.env.example").read_text()
    required = ["LITELLM_MASTER_KEY", "LITELLM_SALT_KEY", "MAX_BUDGET_USD",
                "LITELLM_TAG", "VLLM_IMAGE", "HF_TOKEN", "HF_CACHE"]
    for k in required:
        assert re.search(rf"^{k}=", text, re.M), k

