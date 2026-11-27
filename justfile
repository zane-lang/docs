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
    dir="${XDG_CACHE_HOME:-$HOME/.cache}/prose-lint/107c5f768ea3ce4936d6fdff1b0f30fac9237615"
    if [ ! -d "$dir" ]; then
        rm -rf "$dir.tmp"
        git clone -q https://github.com/zane-lang/prose-lint "$dir.tmp"
        git -C "$dir.tmp" checkout -q 107c5f768ea3ce4936d6fdff1b0f30fac9237615
        mv "$dir.tmp" "$dir"
    fi
    uv run --frozen --project "$dir" prose-lint .
