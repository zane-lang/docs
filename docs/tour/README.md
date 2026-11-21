# Language tour

The tour walks through Zane one topic at a time, each page built from small programs you can run.

Read the pages in order; each page builds on the pages before it.

1. [Basics](basics.md): a program, symbols, numbers, strings
2. [Functions and methods](functions.md): methods and their subject, `:` and `!` calls, overloading, lambdas
3. [Types](types.md): structs, constructors, value semantics, operators
4. [Control flow](control-flow.md): `if`, loops, `guard` and workers, all library code
5. [Enums, variants and `match`](enums-and-match.md): sum types and matching
6. [Generics](generics.md): type and number parameters, containers
7. [Intrinsics and concepts](intrinsics.md): the `@` names, storage primitives, and the types of literals and blocks
8. [Memory](memory.md): owners, references, moves and destruction
9. [Effects and capabilities](effects.md): what a call may change, and reaching the outside world
10. [Errors](errors.md): abortable functions and their handlers
11. [Packages](packages.md): imports and privacy
12. [Concurrency](concurrency.md): `spawn`, its safety rules, and worker pools

Each page links to the sections of the
[specification](https://github.com/zane-lang/spec/blob/main/README.md) that
state the page's rules precisely. The guide [Calling C](../guides/c-interop.md)
covers calling C code from Zane.
