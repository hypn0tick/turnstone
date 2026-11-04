import subprocess, pathlib
def test_entrypoint_rejects_empty_master_key(tmp_path):
    env = {"LITELLM_MASTER_KEY": "", "LITELLM_SALT_KEY": "x" * 32}
    r = subprocess.run(["bash", "turnstone/deploy/vllm-litellm/litellm-entrypoint.sh", "--dry-run"],
                       env=env, capture_output=True, text=True)
    assert r.returncode != 0
    assert "master_key" in r.stderr.lower()
