# The `zane` command

This page lists every command of `zane` v0.18, with its flags, and the environment variables it reads.

`zane help` prints the same list in short. The reasons behind each command
are in its [design document](https://github.com/zane-lang/zane/blob/main/docs/design/cli.md).
Every project command works from any directory inside the project: `zane`
looks for `zane.coda` there and in each directory above.

## Project commands

### `zane init [dir]`

Creates a project in `dir`, or in the current directory. The directory must
be empty apart from the files a new repository holds (`.git/`, `README*`,
`LICENSE*`, `.gitignore` and the like). In a terminal it asks each question
below; otherwise, or with `--yes`, it takes the defaults.

| Flag | Sets | Default |
|---|---|---|
| `--name <name>` | the first package's name | the directory's name, in camelCase |
| `--lib` / `--app` | a library (`lib/` and `test/`) or a program (`bin/`) | `--app` |
| `--version-pattern <pattern>` | the project's version pattern | `v*.+.++` |
| `--zane-version <tag>` | the compiler to pin | the newest installed, else the newest release |
| `--no-git` | skips `git init` | a repository, unless already inside one |
| `--yes`, `-y` | accepts every default | |

### `zane check`

Type-checks the project's packages without building them. When a package
holds C code, it also writes `compile_commands.json` for clangd.

### `zane build [program]`

Builds every program in `bin/`, or the one named, optimized, into
`out/<target>/<name>` (`out/host/<name>` for the host).

| Flag | Effect |
|---|---|
| `--target <triple>` | builds for another system, such as `x86_64-windows-gnu`, `x86_64-linux-gnu` or `aarch64-macos` |
| `-o <file>` | names the output file, when one program is built |

### `zane run [program] [-- args]`

Builds a program for the host and runs it with `args`, exiting with its
status. A project with several programs names the one to run. The program
starts from a quick unoptimized build, and moves to optimized code as soon as
that build is ready.

### `zane test [test] [-- args]`

Builds and runs every test package in `test/`, or the one named by its path
under `test/` (such as `shapes` or `gui/opengl`). It exits with 1 when any
failed, or with the one package's status. See [Testing](../guides/testing.md).

### `zane clean`

Deletes `out/`.

### `zane inspect <view> [program]`

Prints one of the compiler's views of a program: `cst` and `sst` (the syntax
trees of each source file), `decls` (its declarations), `tst` (the typed
tree), `cgt` and `ll` (the code generated). `decls`, `tst`, `cgt` and `ll`
take `--optimize` and `--target <triple>` to show the build `zane build`
makes.

## Dependency commands

These, and `zane toolchain update`, are the commands that write `zane.coda`
and `zane-lock.coda`, always both together. See
[Projects](../guides/projects.md).

### `zane add <url> [tag]`

Depends on the library at `url`, at its newest tag or the one named, and
prints the `import` lines for its packages.

| Flag | Effect |
|---|---|
| `--as <key>` | records it under another key than the last part of the URL |
| `--from-source` | compiles it in the project instead of linking its release; on a library already added, switches it |
| `--test` | adds it to `test-deps`, for the test packages alone |
| `--rename <pkg>=<name>` | imports its package `pkg` as `name`, or drops it when `name` is `_`; may be repeated |

### `zane remove <key>`

Stops depending on `key`, and warns about each import that still uses one of
its packages.

### `zane update [key [tag]]`

Moves `key`, or every dependency, to its newest tag or the one named.
`--accept-tag-move` accepts a tag that now points to a different commit than
the lock file records.

### `zane dev <key> <path>` and `zane dev off <key>`

Compiles `key` from the local project at `path`, or links its release again.

### `zane remap <url>` and `zane unremap <url>`

Links the interchangeable versions of the package at `url` as one, by its
version pattern, or links them side by side again.

### `zane rename <key> <pkg> <name>` and `zane rename off <key> <pkg>`

Imports `key`'s package `pkg` under `name`, or drops it when `name` is `_`;
`off` imports it under its own name again.

### `zane fetch`

Fetches and prepares everything a build needs, so a later build runs
offline. `--target <triple>`, which may be repeated, fetches for those
systems.

### `zane tree`

Prints the resolved dependency graph. `--test` prints the test build's graph,
with `test-deps` marked.

### `zane cache list|path|clean`

Shows the package cache, with what each version is ready for and its size;
prints its directory; or empties it. `clean --stale` removes only what no
build uses.

## Toolchains and `zane` itself

### `zane toolchain install [version]`

Installs the latest compiler release, or the version named, under
`~/.zane/toolchains/`. It works outside a project and changes none.

### `zane toolchain update [version]`

Installs the version named, or the newest release of the project's major
version, and pins the project to it. `--accept-tag-move` accepts a release
tag that moved.

### `zane self update [version]`

Replaces this `zane` with the latest release, or the version named. A `zane`
installed by Nix or Homebrew is updated by that package manager instead.

### `zane help`, `zane version`

Print the command list, and the version of `zane`. `--help`, `-h` and
`--version` do the same.

## Environment variables

| Variable | Effect |
|---|---|
| `ZANE_COMPILER` | path of a compiler to use instead of the project's pinned one |
| `ZANE_HOME` | where `zane` keeps toolchains and the package cache; `~/.zane` when unset |
| `NO_COLOR` | when set, progress output has no color |
| `TERM` | `dumb` turns off the live progress display |
| `COLUMNS` | the width progress output fits in |
| `ZANE_INSTALL_DIR` | read by `install.sh`: where to put `zane`; `~/.local/bin` when unset |

When the pinned compiler is not installed and `ZANE_COMPILER` is unset,
`zane` runs the `zanec` on `PATH`.
