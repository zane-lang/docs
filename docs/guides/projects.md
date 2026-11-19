# Projects

This guide covers the files `zane` keeps for a project, how dependencies and their versions are recorded, and which compiler a project uses.

## The project's files

A project is a directory with a `zane.coda` at its root:

```text
zane.coda        the manifest: what the project wants
zane-lock.coda   the lock file: the exact commits that resolves to
lib/             library packages, which other projects can import
bin/             program packages, each built into a program
test/            test packages
out/             build output, ignored by Git
```

Both `.coda` files are committed, and `zane` writes them for you: the
commands below change them together, so they never disagree. `zane` finds
the project from any directory inside it.

## The manifest

After `zane add https://github.com/zane-lang/std --from-source`, a
`zane.coda` reads:

```text
zane-version v0.40
version-pattern v*.+.++

deps [
    key version from
    std v0.15 source
]
```

- `zane-version` is the compiler release that builds the project.
- `version-pattern` says which of this project's own versions can stand in
  for each other (below). It is chosen when the project is created and stays
  fixed.
- `deps` lists the dependencies, each under a **key**: the name commands use
  for it. `version` is the tag it is pinned to, and `from` says where its code
  comes from: `release` for the prebuilt archive the library publishes,
  `source` to compile it in your project, or a local path such as
  `../geometry`.

A `test-deps` table, with the same columns, holds dependencies that only the
test packages use. `fixed-region` and `spawned-fixed-region` (such as
`fixed-region 1GiB`) set how much memory a program's nested scopes, and each
spawned call's, may take.

## The lock file

```text
zane-commit c3208354223e1f0e1096a8698514bbb624f08efd

resolutions [
    key url commit
    std https://github.com/zane-lang/std cf261378362579a8e6e6a98e823bfcf4cdcbff45
]
```

Each pinned tag is recorded with the commit it pointed to when it was added,
and `zane-commit` does the same for the compiler. A tag that later points
somewhere else is refused as a security error, unless you accept the move
with `--accept-tag-move`. A package is identified by its repository URL; the
key is only a local label.

## Working with dependencies

| Command | What it does |
|---|---|
| `zane add <url> [tag]` | Depends on a library at its newest tag, or the one named, and prints the `import` lines for its packages |
| `zane add <url> --from-source` | The same, compiled in your project instead of linked from a release |
| `zane add <url> --test` | Adds it to `test-deps` |
| `zane update [key [tag]]` | Moves one dependency, or all of them, to the newest tag or the one named |
| `zane remove <key>` | Drops a dependency, and warns about imports that still use it |
| `zane dev <key> <path>` | Compiles the dependency from a local checkout while you work on both |
| `zane dev off <key>` | Goes back to its release |
| `zane tree` | Shows the resolved dependency graph |
| `zane fetch` | Downloads what a build needs, so the next one works offline |

`zane tree` for the project above prints:

```text
hello
└── std v0.15 (core, math, regex), https://github.com/zane-lang/std, from source
```

A package's code imports a dependency's packages by their own names, such as
`import core$;`, never by the key. When two dependencies have packages of the
same name, `zane add --rename pkg=name` or `zane rename <key> <pkg> <name>`
imports one under another name.

Every dependency's own dependencies are fetched as releases at the versions it
pinned. Two versions of the same library can be linked into one program side
by side; `zane remap <url>` instead links the versions its `version-pattern`
says are interchangeable as one.

## Versions

A release is a Git tag such as `v0.15`. The version pattern `v*.+.++` reads
"the first number must match (`*`); otherwise prefer the highest second
number (`+`), then the highest third (`++`)". It is what lets `zane remap`
pick one version for everyone who depends on a library.

Fetched packages are kept in a cache shared by all projects, under
`~/.zane/packages`. `zane cache list` shows it and `zane cache clean` empties
it.

## The compiler a project uses

Each project pins its compiler, so projects on different compilers build side
by side. Installing a newer compiler (`zane toolchain install`) changes no
project. To move one:

```sh
zane toolchain update          # the newest release of the project's major version
zane toolchain update v0.40    # or the one named
```

This checks the dependency graph against the new compiler before changing
`zane-version` and `zane-commit`.

To build with a compiler you built yourself, set `ZANE_COMPILER` to its
path; it takes the place of the pinned one. When the pinned compiler is not
installed, `zane` falls back to a `zanec` on your `PATH`. Neither is checked
against the pin.

## In the spec

- [Dependencies](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md):
  [the manifest](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#21-manifest-zanecoda),
  [the lock file](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#22-lock-file-zane-lockcoda),
  [importing a dependency](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#8-importing-a-dependencys-packages)
  and [version patterns](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#15-compatibility-patterns-and-remapping)
- [Project layout](https://github.com/zane-lang/spec/blob/main/spec/packages.md#2-projects-and-packages)
- [The `zane` command's design](https://github.com/zane-lang/zane/blob/main/docs/design/cli.md#3-dependency-commands)
