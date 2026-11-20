# Language tour

The tour walks through Zane one topic at a time, each page built from small programs you can run.

Read the pages in order; each page builds on the pages before it.

1. [Basics](basics.md): a program, symbols, numbers, strings
2. [Functions and methods](functions.md): methods and their subject, `:` and `!` calls, overloading, lambdas
3. [Types](types.md): structs, constructors, value semantics, operators
4. [Control flow](control-flow.md): `if`, loops, `guard` and workers, all library code
5. [Enums, variants and `match`](enums-and-match.md): sum types and matching
6. [Generics](generics.md): type and number parameters, containers
7. [Memory](memory.md): owners, references, moves and destruction
8. [Effects and capabilities](effects.md): what a call may change, and reaching the outside world
9. [Errors](errors.md): abortable functions and their handlers
10. [Packages](packages.md): imports and privacy
11. [Concurrency](concurrency.md): `spawn` and its safety rules

Each page links to the sections of the
[specification](https://github.com/zane-lang/spec/blob/main/README.md) that
state the page's rules precisely. Calling C from Zane is covered by the spec's
[FFI chapter](https://github.com/zane-lang/spec/blob/main/spec/ffi.md) and
the compiler's
[FFI design](https://github.com/zane-lang/compiler/blob/main/docs/design/ffi.md).
