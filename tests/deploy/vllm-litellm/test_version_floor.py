import subprocess


def _run(version):
    script = (
        f"rm -rf /tmp/fakepkg-{version} && "
        f"mkdir -p /tmp/fakepkg-{version}/litellm-{version}.dist-info && "
        f"printf 'Name: litellm\\nVersion: {version}\\n' > /tmp/fakepkg-{version}/litellm-{version}.dist-info/METADATA && "
        f"LITELLM_MASTER_KEY=sk-test LITELLM_SALT_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx "
        f"PYTHONPATH=/tmp/fakepkg-{version} "
        f"bash turnstone/deploy/vllm-litellm/litellm-entrypoint.sh --dry-run"
    )
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True)


def test_version_floor_refuses_below():
    r = _run("1.96.0")
    assert r.returncode != 0
    assert "1.97.0" in r.stderr
    assert "floor" in r.stderr.lower()


def test_version_floor_accepts_floor():
    r = _run("1.97.0")
    assert r.returncode == 0


def test_version_floor_accepts_above():
    r = _run("1.98.5")
    assert r.returncode == 0
