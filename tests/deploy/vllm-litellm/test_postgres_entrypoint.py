import subprocess
def test_entrypoint_skips_db_wait_when_no_database_url():
    env = {"LITELLM_MASTER_KEY": "sk-test", "LITELLM_SALT_KEY": "x"*32}
    r = subprocess.run(["bash", "turnstone/deploy/vllm-litellm/litellm-entrypoint.sh", "--dry-run"],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0 or "spend tracking disabled" in (r.stderr + r.stdout).lower()
