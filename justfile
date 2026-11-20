set positional-arguments

# Run the example checker on the docs (needs `zane`, or add --install).
check-examples *args:
    python3 tools/check_examples.py "$@" docs/

# Unit tests of the checker (integration tests run when `zane` is on PATH).
test-tools:
    python3 -m unittest discover -s tools -v
