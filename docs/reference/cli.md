# The `zane` command

This page lists every command of `zane` v0.20, with its flags, and the environment variables it reads.

`zane help` prints a short version of the same list. The
[design document](https://github.com/zane-lang/zane/blob/main/docs/design/cli.md)
explains the reasons behind each command.
Every project command works from any directory inside the project: `zane`
looks for `zane.coda` there and in each directory above.

## Project commands

### `zane init [dir]`

Creates a project in `dir`, or in the current directory. The directory must
be empty apart from the files a new repository holds (`.git/`, `README*`,
`LICENSE*`, `.gitignore`, and similar repository files). In a terminal, `zane init` asks each
question below; outside a terminal, or with `--yes`, it uses the defaults.

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
holds C code ([Calling C](../guides/c-interop.md)), it also writes
`compile_commands.json` for clangd.

### `zane build [program]`

Builds every program in `bin/`, or only the program you name, with
optimizations, into
`out/<target>/<name>` (`out/host/<name>` for the host).

| Flag | Effect |
|---|---|
| `--target <triple>` | builds for another system, such as `x86_64-windows-gnu`, `x86_64-linux-gnu` or `aarch64-macos` |
| `-o <file>` | names the output file, when one program is built |
| `--build-argument <arg>` | adds `arg` to the arguments that a call marked `comptime` reads; repeatable |

`zane run`, `zane test` and `zane inspect` take `--build-argument` too, and
pass it to every compiler run of the program's or test package's own build.
A dependency's object is compiled without the build's arguments.

### `zane run [program] [-- args]`

Builds a program for the host, runs it with `args`, and exits with the
program's status. In a project with several programs, name the program to run.
The program first runs from a quick unoptimized build, and switches to
optimized code as soon as the optimized build is ready.

### `zane test [test] [-- args]`

Builds and runs every test package in `test/`, or only the test package you
name by its path under `test/` (such as `shapes` or `gui/opengl`). It exits
with 1 when any test package failed; when it runs a single package, it exits
with that package's status. See [Testing](../guides/testing.md).

### `zane clean`

Deletes `out/`.

### `zane inspect <view> [program]`

Prints one of the compiler's views of a program: `cst` and `sst` (the syntax
trees of each source file), `decls` (the program's declarations), `tst` (the
typed tree), `cgt` and `ll` (the generated code). `decls`, `tst`, `cgt` and
`ll` take `--optimize`, `--target <triple>` and `--build-argument <arg>` to
show the code that `zane build` produces.

### `zane builds`

Prints the builds that `zane check` checks, as one JSON object on standard
output, and runs no compiler. Each build has the label `zane check` shows for
it and the flags `zane check` passes the compiler. The language server runs
`zane builds` in each project an editor opens, so the editor shows the
problems `zane check` reports.

### `zane lsp`

Runs the language server that an editor starts for Zane files: the
compiler's own server, on standard input and output. Inside a project,
`zane lsp` runs the project's pinned compiler; anywhere else, it runs the
compiler `ZANE_COMPILER` names, then the newest installed toolchain, then
`zanec` on `PATH`. The compiler's
[`language-server.md`](https://github.com/zane-lang/compiler/blob/main/docs/design/language-server.md)
describes the server's editor features.

## Dependency commands

The commands in this section, and `zane toolchain update`, are the only
commands that write `zane.coda` and `zane-lock.coda`, and they always write
both files together. See
[Projects](../guides/projects.md).

### `zane add <url> [tag]`

Depends on the library at `url`, at the library's newest tag or at the tag you
name, and prints the `import` lines for the library's packages.

| Flag | Effect |
|---|---|
| `--as <key>` | records the dependency under `key` instead of the last part of the URL |
| `--from-source` | compiles the library in the project instead of linking its release; for a library that is already a dependency, switches that dependency to compiling from source |
| `--test` | adds the library to `test-deps`, which only the test packages use |
| `--rename <pkg>=<name>` | imports the library's package `pkg` as `name`, or leaves `pkg` out when `name` is `_`; may be repeated |

### `zane remove <key>`

Stops depending on `key`, and warns about each import that still uses one of
the dependency's packages.

### `zane update [key [tag]]`

Moves `key`, or every dependency, to its newest tag or to the tag you name.
`--accept-tag-move` accepts a tag that now points to a different commit than
the lock file records.

### `zane dev <key> <path>` and `zane dev off <key>`

`zane dev` compiles `key` from the local project at `path`; `zane dev off`
links `key`'s release again.

### `zane remap <url>` and `zane unremap <url>`

`zane remap` links a single version in place of all the versions of the
package at `url` that its version pattern marks as interchangeable;
`zane unremap` links those versions side by side again.

### `zane rename <key> <pkg> <name>` and `zane rename off <key> <pkg>`

`zane rename` imports `key`'s package `pkg` under `name`, or leaves `pkg` out
when `name` is `_`; `zane rename off` imports `pkg` under its own name again.

### `zane fetch`

Fetches and prepares everything a build needs, so a later build runs
offline. `--target <triple>` also fetches what builds for that system need,
and may be repeated.

### `zane tree`

Prints the resolved dependency graph. `--test` prints the test build's graph,
with `test-deps` marked.

### `zane cache list|path|clean`

`list` shows the package cache, with each cached version's size and the
builds it is prepared for; `path` prints the cache's directory; `clean`
empties the cache. `clean --stale` removes only the entries that no build
uses.

## Toolchains and `zane` itself

### `zane toolchain install [version]`

Installs the latest compiler release, or the version you name, under
`~/.zane/toolchains/`. It works outside a project and doesn't change any
project.

### `zane toolchain update [version]`

Installs the version you name, or the newest release of the project's major
version, and pins the project to that version. `--accept-tag-move` accepts a release
tag that moved.

### `zane self update [version]`

Replaces this `zane` with the latest release, or with the version you name,
then puts the newest `std` in the package cache, as `zane self install-std`
does. A `zane` installed by Nix or Homebrew is updated by that package
manager instead.

### `zane self install-std`

Puts the newest release of `std` in the package cache, so `zane init` can add
`std` without network access. The installers run it. It works outside a
project and changes no project.

### `zane help`, `zane version`

`zane help` prints the command list, and `zane version` prints the version of
`zane`. `--help` and `-h` do the same as `zane help`, and `--version` the same
as `zane version`.

## Environment variables

| Variable | Effect |
|---|---|
| `ZANE_COMPILER` | path of a compiler to use instead of the project's pinned one |
| `ZANE_HOME` | where `zane` keeps toolchains and the package cache; `~/.zane` when unset |
| `NO_COLOR` | when set, progress output has no color |
| `TERM` | `dumb` turns off the live progress display |
| `COLUMNS` | the width that progress output is fitted to |
| `ZANE_INSTALL_DIR` | read by `install.sh`: where to put `zane`; `~/.local/bin` when unset |

When the pinned compiler is not installed and `ZANE_COMPILER` is unset,
`zane` runs the `zanec` on `PATH`.
