#!/bin/sh
set -eu

DRY_RUN=0

# Early empty-master-key guard (no external commands; works even without PATH)
_raw_mk="${LITELLM_MASTER_KEY:-}"
_raw_ov="${LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY:-}"
if [ -z "$_raw_mk" ]; then
    case "$_raw_ov" in
        true|TRUE|True|1|yes|YES) : ;;
        *)
            _ov="${LITELLM_OVERLAY:-dev}"
            case "$_ov" in
                prod) echo "litellm-entrypoint: prod overlay requires a real LITELLM_MASTER_KEY (master_key)" >&2; exit 2 ;;
                *) echo "litellm-entrypoint: LITELLM_MASTER_KEY empty (master_key)" >&2; exit 2 ;;
            esac
            ;;
    esac
fi

for arg in "$@"; do
    case "$arg" in
        --dry-run|--validate-only) DRY_RUN=1 ;;
    esac
done

fail() { echo "litellm-entrypoint: $*" >&2; exit 2; }
warn() { echo "litellm-entrypoint: WARN: $*" >&2; }
info() { echo "litellm-entrypoint: $*"; }

strip_cr() {
    printf '%s' "$1" | tr -d '\r' | sed 's/[[:space:]]*$//'
}

is_number() {
    case "$1" in
        ''|*[!0-9.]*) return 1 ;;
    esac
    return 0
}

OVERLAY="${LITELLM_OVERLAY:-dev}"
OVERLAY="$(strip_cr "$OVERLAY")"
case "$OVERLAY" in
    dev|prod) ;;
    *) fail "LITELLM_OVERLAY must be dev or prod (got '$OVERLAY')" ;;
esac

if [ "$OVERLAY" = "prod" ] && [ -z "${LITELLM_OVERLAY_SET:-}" ]; then
    : # overlay injected by compose normally
fi

MASTER_KEY="$(strip_cr "${LITELLM_MASTER_KEY:-}")"
SALT_KEY="$(strip_cr "${LITELLM_SALT_KEY:-}")"
OVERRIDE="$(strip_cr "${LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY:-}")"

# Prod-only requirements
if [ "$OVERLAY" = "prod" ]; then
    [ -n "$MASTER_KEY" ] || fail "prod overlay requires a real LITELLM_MASTER_KEY (master_key)"
    case "$OVERRIDE" in
        ''|false|FALSE|False|0) ;;
        *) fail "dev override flag present in prod overlay (remove it) (master_key)" ;;
    esac
fi

# Dev handling of empty master key
if [ "$OVERLAY" = "dev" ]; then
    if [ -z "$MASTER_KEY" ]; then
        case "$OVERRIDE" in
            true|TRUE|True|1|yes|YES) warn "dev overlay: gateway OPEN (no master key)" ;;
            *) fail "LITELLM_MASTER_KEY empty; set it or LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY=true (master_key)" ;;
        esac
    fi
fi

# Numeric validation
check_num() {
    v="$(strip_cr "${!1:-}")"
    [ -z "$v" ] && return 0
    is_number "$v" || fail "$1 must be numeric (got '$v')"
}
# validate known numeric vars if set
for var in MAX_BUDGET_USD LITELLM_NUM_RETRIES LITELLM_REQUEST_TIMEOUT LITELLM_HEALTH_INTERVAL \
           LITELLM_HEALTH_STALENESS LITELLM_ALERT_THRESHOLD LITELLM_CACHE_TTL LITELLM_AFFINITY_TTL \
           LITELLM_MAX_FALLBACKS LITELLM_MAX_BUDGET LITELLM_COOLDOWN_TIME QWEN_TIMEOUT QWEN_STREAM_TIMEOUT \
           QWEN_NUM_RETRIES QWEN_COOLDOWN_TIME QWEN_PAID_TIMEOUT QWEN_PAID_STREAM_TIMEOUT \
           QWEN_PAID_NUM_RETRIES QWEN_PAID_COOLDOWN_TIME GEMMA_TIMEOUT GEMMA_STREAM_TIMEOUT \
           GEMMA_NUM_RETRIES GEMMA_COOLDOWN_TIME GEMMA_PAID_TIMEOUT GEMMA_PAID_STREAM_TIMEOUT \
           GEMMA_PAID_NUM_RETRIES GEMMA_PAID_COOLDOWN_TIME LITELLM_PORT QWEN_PORT GEMMA_PORT RERANKER_PORT; do
    eval "val=\"\${$var:-}\""
    val="$(strip_cr "$val")"
    [ -z "$val" ] && continue
    is_number "$val" || fail "$var must be numeric (got '$val')"
done

# Timeout relationships
qto="$(strip_cr "${QWEN_TIMEOUT:-}")"; qst="$(strip_cr "${QWEN_STREAM_TIMEOUT:-}")"
if [ -n "$qto" ] && [ -n "$qst" ]; then
    python3 -c "import sys; sys.exit(0 if float('$qto')>=float('$qst') else 1)" 2>/dev/null || fail "QWEN_TIMEOUT must be >= QWEN_STREAM_TIMEOUT"
fi
gto="$(strip_cr "${GEMMA_TIMEOUT:-}")"; gst="$(strip_cr "${GEMMA_STREAM_TIMEOUT:-}")"
if [ -n "$gto" ] && [ -n "$gst" ]; then
    python3 -c "import sys; sys.exit(0 if float('$gto')>=float('$gst') else 1)" 2>/dev/null || fail "GEMMA_TIMEOUT must be >= GEMMA_STREAM_TIMEOUT"
fi

# JSON decode of *_JSON vars
TMP_JSON_DIR="${TMPDIR:-/tmp}/litellm-json"
mkdir -p "$TMP_JSON_DIR"
for var in $(env | sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*_JSON\)=.*/\1/p'); do
    val="$(eval echo \"\${$var}\")"
    val="$(strip_cr "$val")"
    [ -z "$val" ] && continue
    printf '%s' "$val" > "$TMP_JSON_DIR/$var.raw"
    python3 - "$var" "$TMP_JSON_DIR/$var.raw" << 'PYEOF' || fail "$var is not valid JSON"
import json, sys
name = sys.argv[1]
path = sys.argv[2]
with open(path) as f:
    raw = f.read()
try:
    obj = json.loads(raw)
except Exception as e:
    print(f"refusing: {name} is not valid JSON ({e})", file=sys.stderr)
    sys.exit(1)
with open(path + ".decoded", "w") as f:
    json.dump(obj, f)
PYEOF
done

# Version floor assert
VER="$(python3 -c "import importlib.metadata; print(importlib.metadata.version('litellm'))" 2>/dev/null || true)"
if [ -n "$VER" ]; then
    python3 -c "import sys; sys.exit(0 if '$VER' >= '1.97.0' else 1)" 2>/dev/null || fail "litellm $VER < 1.97.0 floor"
    info "version=$VER floor=1.97.0 OK"
else
    warn "litellm not installed; skipping version floor"
fi

# Paid-block removal logging
QWEN_PAID_KEY="$(strip_cr "${QWEN_PAID_API_KEY:-}")"
GEMMA_PAID_KEY="$(strip_cr "${GEMMA_PAID_API_KEY:-}")"
if [ -z "$QWEN_PAID_KEY" ]; then
    info "paid tails: qwen3.6-27b-paid DISABLED (no QWEN_PAID_API_KEY)"
fi
if [ -z "$GEMMA_PAID_KEY" ]; then
    info "paid tails: gemma-4-12b-paid DISABLED (no GEMMA_PAID_API_KEY)"
fi

# Render effective config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_CFG="$SCRIPT_DIR/litellm-config.yaml"
EFF="${TMPDIR:-/tmp}/litellm-effective.yaml"
if [ -f "$BASE_CFG" ]; then
    cp "$BASE_CFG" "$EFF"
else
    : > "$EFF"
fi

# Remove paid model entries when key missing (best-effort python yaml-ish filter)
python3 - "$EFF" "$QWEN_PAID_KEY" "$GEMMA_PAID_KEY" << 'PYEOF'
import sys
path = sys.argv[1]
qkey = sys.argv[2]
gkey = sys.argv[3]
# Minimal: if no paid key, ensure no 'paid' model entries remain (already none in base).
# This is a placeholder for full paid-block removal; base config has no paid entries.
PYEOF

info "overlay=$OVERLAY config=$EFF"

if [ "$DRY_RUN" = "1" ]; then
    exit 0
fi

PORT="$(strip_cr "${LITELLM_PORT:-4000}")"
[ -z "$PORT" ] && PORT=4000
exec litellm --config "$EFF" --port "$PORT"