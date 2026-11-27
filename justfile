set positional-arguments

# Run the example checker on the docs (needs `zane`, or add --install).
check-examples *args:
    python3 tools/check_examples.py "$@" docs/

# Unit tests of the checker (integration tests run when `zane` is on PATH).
test-tools:
    python3 -m unittest discover -s tools -v

# Check prose with the prose-lint commit pinned in .github/workflows/prose.yml.
prose:
    uvx --from git+https://github.com/zane-lang/prose-lint@107c5f768ea3ce4936d6fdff1b0f30fac9237615 prose-lint .
