# Intrinsics and concepts

This page explains the names that start with `@`, which the compiler supplies: the storage types and operations that `core` is built on, and the concept types of literals and blocks.

## What `@` marks

Every name that starts with `@` is an **intrinsic**: a type, an operation or an
instance that the compiler supplies rather than a package declares. The
`$` after the namespace separates it from the member, as it does after a
package name, so `@program$console` is the member `console` of the intrinsic
namespace `@program$`.

Zane keeps the language itself small. `Int`, `String`, `+`, `if` and the
loops are not built into the compiler: the `core` package declares them, in
ordinary Zane, on top of the intrinsics. So `core`'s
[`primitives.zn`](https://github.com/zane-lang/std/blob/main/lib/core/primitives.zn)
declares `Int` as a struct around a 64-bit machine integer:

```zane fragment
type Int = struct {
	_value @primitives$I64;
}

Int +(left Int, right Int) => Int(@operators$add(left._value, right._value));
```

The `@` makes the line between language and library visible in the source:
whatever has no `@` is declared in some package, and you can read its
declaration.

Each intrinsic namespace holds one kind of intrinsic:

| Namespace | Holds | Examples |
|---|---|---|
| `@primitives$` | storage types with a fixed machine layout | `I32`, `I64`, `F32`, `F64`, `Bool`, `String`, `Unit`, `Array<T, n>`, `List<T>` |
| `@concepts$` | the types of literals and blocks, which have no storage of their own | `Int`, `Float`, `String`, `Array<T, n>`, `Map<K, V>`, `Block` |
| `@operators$` | machine operations on primitives | `add`, `multiply`, `lessThan`, `equal`, `not` |
| `@math$` | math functions on scalar primitives | square root, rounding, trigonometry, bit operations |
| `@controlflow$` | the operations that branch, repeat and exit | `branch`, `repeat`, `exitFromCall`, `work`, `register` |
| `@runtime$` | the runtime's types | `Console`, `Runtime` |
| `@program$` | the running program's console and runtime | `console`, `runtime` |

Every package reaches every namespace without an import, except `@program$`,
which only the root package reaches ([Effects and capabilities](effects.md)).

## Storage primitives

A **storage primitive** fixes exactly what the machine holds:
`@primitives$I64` is a 64-bit integer, `@primitives$F64` a 64-bit IEEE float,
and `@primitives$String` a string's bytes. A primitive has no operators and no
methods. A program can use primitives without `core`, calling the machine
operations directly, which is what the `main.zn` of a new project does before
it has any dependency:

```zane
package hello;

alias I64 = @primitives$I64;

@primitives$Unit main() {
	sum I64 = @operators$add(I64(40), I64(2));
	@program$console!print(@primitives$String(sum));
	return @primitives$Unit();
}
```

```output
42
```

`core` wraps each primitive in a type of its own: `Int` around
`@primitives$I64`, `Float` around `@primitives$F64`, `String` around
`@primitives$String`. A struct with one primitive field has that primitive's
layout, so an `Int` costs exactly what an `@primitives$I64` costs. The
wrapper is where operators, methods and conversions live, and it is library
code that you can read and that a new version of `std` can change without a
new compiler.

`core` also declares implicit conversions in both directions, such as
`implicit @primitives$I64(v Int)`, so an `Int` passes wherever a function
takes an `@primitives$I64`. That is why a foreign verb, which uses primitive
types ([Calling C](../guides/c-interop.md)), accepts `core`'s types as
arguments.

## Concepts: what a literal is

In most languages the compiler gives a literal a type of the compiler's own
choosing: `42` is an `int` in C and Java, and Rust picks `i32` when nothing
else decides. Zane's compiler picks no type. The literal `42` has the
**concept type** `@concepts$Int`, the type of an integer literal, and stays
one until a parameter declares what it becomes. `2.5` is a `@concepts$Float`
and `"text"` a `@concepts$String`.

A concept type stands only in a parameter, never in storage: a symbol, a field
or a list element cannot have one. A function that takes a literal declares a
concept-typed parameter, and a type that accepts literals declares an implicit
constructor from the concept. `core`'s `Int` has one:

```zane fragment
implicit Int(v @concepts$Int) => Int(@primitives$I64(v));
```

So `print(Int(20))` and `width * 2` work because `core` declares how `20` becomes
an `Int`, not because the compiler knows about `Int`. A declaration does not
convert on its own, so `width Int = 6;` is an error, and `width Int = Int(6);`
calls the constructor ([Basics](basics.md)). A concept cannot be stored:

```zane error
// error: is never storage
package hello;

import core$;

Unit main() {
	n @concepts$Int = 3;
	return Unit();
}
```

### What concepts buy

Because the compiler privileges no type, any package's type takes a literal on
exactly the terms `Int` does. A type for temperatures, money or big integers
declares a constructor from the concept and is then as easy to use as a
built-in type:

```zane
package hello;

import core$;

type Celsius = struct {
	degrees Float;
}

implicit Celsius(v @concepts$Float) => init{ degrees = Float(v); }

String describe(t Celsius) => String(t.degrees) + " degrees";

Unit main() {
	console Console(@program$console);
	console!print(describe(21.5));
	return Unit();
}
```

```output
21.5 degrees
```

A function can also overload on concepts: `@concepts$Int` and
`@concepts$Float` are different types, so one overload can take an integer
literal and another a float literal ([Generics](generics.md)).

A literal is known at compile time, so the conversion is checked at compile
time too. A literal that its primitive cannot hold is a compile-time error
rather than a value that wraps when the program runs:

```zane error
// error: is out of range for `@primitives$I32`
package hello;

import core$;

Unit main() {
	big @primitives$I32 = @primitives$I32(99999999999);
	return Unit();
}
```

Go's untyped constants and Swift's literal protocols come closest to this: in
both, a literal waits for its context to give it a type. A Go constant becomes
only a type built on one of Go's numeric types, and Swift lets any type opt
in, as Zane's implicit constructors do. Zane has no numeric type built into the
compiler at all, so `core`'s `Int` takes literals through the same mechanism
as every other package's types.

### Concepts that are not literals

The same rule, a parameter type and never storage, covers the source
constructs that are not values:

- `@concepts$Block` is the type of a block argument. A function that takes a
  block is expanded at each call site, so a block costs nothing at run time,
  and `if` and loops are ordinary functions ([Control flow](control-flow.md)).
- `Type` marks a type parameter, and `@concepts$Int` a number parameter, as in
  `Array<T, n @concepts$Int>`: both are values known at compile time
  ([Generics](generics.md)).
- `@concepts$Array<T, n>` and `@concepts$Map<K, V>` are the types of
  `[ ]` and `{ }` literals. An array literal carries its element type and
  length, which is how `Array([Int(1), Int(2)])` knows it holds two `Int`s.
- `@concepts$String` carries a string literal's text and its `\%name`
  interpolations.

## Operations and control flow

`@operators$` and `@math$` are the machine operations that a package's own
operators and math functions are written over, as `core`'s `+` on `Int` is
written over `@operators$add` above. An intrinsic is never an operator itself,
so every operator a program uses is declared in some package and can be read
there.

`@controlflow$` holds the five operations that every branch and loop is built
from. `core`'s `if` is three lines:

```zane fragment
Bool if(condition Bool, body @concepts$Block) {
	@controlflow$branch(condition, body);
	return condition;
}
```

Every intrinsic takes storage primitives, function values or type
parameters, and never a type that a package declares. That is what keeps
`core` an ordinary package: `@controlflow$branch` takes an
`@primitives$Bool`, `core`'s `Bool` reaches it through an implicit conversion
that `core` declares, and any other package can declare its own control flow
on exactly the same footing. A compiler release therefore fixes the
language without fixing any library, so `std` versions move independently of
the compiler ([Projects](../guides/projects.md)).

## The program's console and runtime

`@runtime$Console` and `@runtime$Runtime` are the runtime's types, and
`@program$console` and `@program$runtime` are the running program's only
instances of them. Only the root package, the one that declares `main`,
reaches `@program$`, and it passes the console on to the code that may print.
`Console(@program$console)` wraps the runtime's console in `core`'s `Console`,
whose methods take `core`'s `String`
([Effects and capabilities](effects.md)).

## Where you write `@` yourself

Most code uses `core`'s types and never names an intrinsic. You write one:

- to reach the console and runtime in `main`: `Console(@program$console)`;
- as `main`'s abort type, `@primitives$String`, because the program writes
  the abort message itself ([Testing](../guides/testing.md));
- to take a literal or a block in a parameter of your own:
  `@concepts$Int`, `@concepts$Float`, `@concepts$Block`;
- to declare a number parameter: `n @concepts$Int`;
- in a foreign verb's signature, whose types are primitives
  ([Calling C](../guides/c-interop.md));
- to write a type, operator or control-flow function of your own over the
  machine operations, as `core` does.

## In the spec

- [Syntax](https://github.com/zane-lang/spec/blob/main/spec/syntax.md):
  [intrinsic namespaces](https://github.com/zane-lang/spec/blob/main/spec/syntax.md#27-intrinsic-namespaces),
  [compiler concept types](https://github.com/zane-lang/spec/blob/main/spec/syntax.md#28-compiler-concept-types)
  and [the block-argument type](https://github.com/zane-lang/spec/blob/main/spec/syntax.md#212-the-block-argument-type)
- [Types](https://github.com/zane-lang/spec/blob/main/spec/types.md):
  [literals and their storage primitives](https://github.com/zane-lang/spec/blob/main/spec/types.md#27-literals-and-their-storage-primitives)
- [Operators](https://github.com/zane-lang/spec/blob/main/spec/operators.md),
  [math](https://github.com/zane-lang/spec/blob/main/spec/math.md) and
  [the control-flow intrinsics](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#4-control-flow-intrinsics)
- The stories behind it:
  [`intrinsic` names the whole `@` space](https://github.com/zane-lang/spec/blob/main/stories/syntax.md#intrinsic-names-the-whole--space),
  [how a literal lowers into primitive storage](https://github.com/zane-lang/spec/blob/main/stories/types.md#how-a-literal-lowers-into-primitive-storage)
  and [what the control-flow intrinsics are stated over](https://github.com/zane-lang/spec/blob/main/stories/control-flow.md#two-intrinsics-and-what-they-are-stated-over)
