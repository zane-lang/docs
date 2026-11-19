# Learn Zane

These pages teach Zane to a programmer who already knows another language: how to install it, how to start a project, and how the language works.

## What Zane is

Zane is a systems programming language that compiles to native code. Memory
is managed deterministically, with no garbage collector and no lifetime
annotations: every object has one owner, references can never dangle, and
every object a scope creates is destroyed when that scope ends. At each call
site, `!` or `:` shows whether the method may change its subject:
`list!push(x)` may change `list`, and `list:size()` may not. Code can reach
the console and other outside state only through objects it is given.

Many features that other languages build into the compiler are ordinary Zane
code. `Int`, `String`, `List`, `if`, `else` and loops are declared in the
`core` package of the standard library, written in Zane on top of a small set
of compiler intrinsics.

## Where to start

1. [Install Zane](install.md): the `zane` command, a compiler, editor support.
2. [Your first project](first-project.md): create, run and test a project.
3. [The language tour](tour/README.md): the language one topic at a time,
   each with programs you can run.
4. [Guides](guides/README.md): projects, dependencies and testing in more depth.
5. [Reference](reference/README.md): every `zane` command, flag and environment variable.

## The rest of the site

- **Spec** is the
  [language specification](https://github.com/zane-lang/spec/blob/main/README.md):
  the precise rules. Each tour page links to the spec sections it summarizes.
- **Stories** are the
  [design stories](https://github.com/zane-lang/spec/tree/main/stories): why
  the language looks the way it does.
- **Tools** documents
  [`zane`](https://github.com/zane-lang/zane/blob/main/README.md), the command
  you build with, and its design.
- **Library** documents
  [`std`](https://github.com/zane-lang/std/blob/main/docs/README.md): the
  `core`, `math` and `regex` packages.
- **Compiler** documents
  [`zanec`](https://github.com/zane-lang/compiler/blob/main/README.md), and
  lists where it [differs from the
  spec](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md).

These pages target `zane` v0.18, compiler v0.40 and `std` v0.15. Zane's major
version is still zero, so the language and its tools change between releases.
