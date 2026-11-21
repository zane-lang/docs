# Contributing

## Code examples are checked

Every code example in `docs/` is built and run with the real `zane` CLI by
`tools/check_examples.py`, so a page can't show code that doesn't work. CI runs
it on every push and pull request.

### Fence convention

| Fence | Meaning |
|---|---|
| ```` ```zane ```` | A whole program. It must build and run (`zane run`) and exit 0. Its first line is `package <name>;`; the checker renames it to the package of its template project. |
| ```` ```output ```` | Directly after a `zane` fence (only blank lines between): the program's exact stdout. A single trailing newline is ignored. |
| ```` ```zane fragment ```` | Shown on the page but not run; the checker counts it as skipped. |
| ```` ```zane error ```` | Must fail `zane check`. If its first line is `// error: <text>`, the compiler's diagnostics must contain `<text>`. |
| any fence with `file=<path>` in its info string, such as ```` ```c file=binding.h ```` | A companion file: the checker writes its content at `<path>`, relative to the package directory that holds `main.zn`, for the next `zane` or `zane error` example on the page. `<path>` is relative, may name a subdirectory such as `vendor/zlib.c`, and stays inside the package directory. |
| any other fence (`sh`, `text`, `coda`, …) | Ignored. |

Companion files let an example carry the C sources, interface headers and
`c.coda` that [Calling C](docs/guides/c-interop.md) needs. Every companion
fence sits before the example it belongs to, so an `output` fence still
directly follows its `zane` fence. A `zane fragment` takes no companion files,
and a companion fence with no `zane` or `zane error` example after it, or two
companion fences with one path for one example, fail the check.

Fences follow CommonMark: three or more backticks or tildes, closed by the same
character at least as long. A `zane` block nested inside a longer
` ````markdown ` fence is part of the shown text, and the checker does not check it.

### Running it

```sh
just test-tools        # unit tests of the checker
just check-examples    # check docs/ with the `zane` on your PATH
just check-examples --install   # download the pinned toolchain first
```

Options: `--zane PATH`, `--jobs N`, `--std PATH` (a local std checkout instead
of the released one, set with `zane dev std <path>`), `--install` (downloads
the versions pinned in `toolchain.coda` to `~/.cache/zane-check-examples` and
`~/.zane/toolchains`), and `--keep` (keep the temporary projects).

Failures print as `path:line: <what failed>` with trimmed compiler or program
output, then `N passed, M failed, K skipped`; the exit code is 1 on any failure.

`toolchain.coda` pins the versions of `zane`, the compiler and `std` that the
checker uses. Update it in the same change as the docs that need the newer
release.
