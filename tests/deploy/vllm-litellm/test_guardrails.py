from turnstone.deploy.vllm_litellm.litellm_callbacks import guardrails


def test_guardrail_blocks_secret_leak():
    verdict = guardrails.evaluate("here is sk-ant-api03-abcdefghijklmnopqrstuvwxyz")
    assert verdict == "BLOCKED"