set positional-arguments

# Run the example checker on the docs (needs `zane`, or add --install).
check-examples *args:
    python3 tools/check_examples.py "$@" docs/

# Unit tests of the checker (integration tests run when `zane` is on PATH).
test-tools:
    python3 -m unittest discover -s tools -v

# Check prose with the prose-lint commit and lockfile that CI pins in prose.yml.
prose:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v uv >/dev/null || { echo 'just prose needs uv on PATH: https://docs.astral.sh/uv/' >&2; exit 1; }
    dir="${XDG_CACHE_HOME:-$HOME/.cache}/prose-lint/58c23886b093aaa76d3f5281d8340813805f22c3"
    if [ ! -d "$dir" ]; then
        rm -rf "$dir.tmp"
        git clone -q https://github.com/zane-lang/prose-lint "$dir.tmp"
        git -C "$dir.tmp" checkout -q 58c23886b093aaa76d3f5281d8340813805f22c3
        mv "$dir.tmp" "$dir"
    fi
    uv run --frozen --project "$dir" prose-lint .
