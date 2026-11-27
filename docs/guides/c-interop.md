# Calling C

This guide shows how a Zane package calls C code: where the C files go, how a Zane function names a C function, which types cross, and who owns C objects and outside state.

A package can hold C code next to its Zane source. The `zane` toolchain
compiles that C itself, for whatever target the build is for, with the C
compiler that each compiler release carries, so you install no C compiler and
write no build script. A Zane function whose body is a C function is a
**foreign verb**. A program calls a foreign verb like any other function.

## A first foreign verb

A package's C code is two kinds of file, both directly in the package's
directory next to its `.zn` files:

- **interface headers**, the `.h` files, which declare the C functions that
  the package's Zane code calls;
- **C sources**, the `.c` files, which define them.

For a program, the package directory is `bin/<name>/`, so this example's
three files are `bin/hello/checksum.h`, `bin/hello/checksum.c` and
`bin/hello/main.zn`. The header comes first:

```c file=checksum.h
#include <zane_ffi.h>

uint64_t checksum(zane_bytes data);
```

`<zane_ffi.h>` is a header that the toolchain gives every package's C code.
The header declares `zane_bytes`, the type in which C receives a Zane string: a
pointer to the string's bytes and their count, with no terminating NUL byte.
The C source defines the function:

```c file=checksum.c
#include "checksum.h"

uint64_t checksum(zane_bytes data) {
	uint64_t sum = 0;
	for (size_t i = 0; i < data.size; i++) {
		sum = sum * 31 + data.data[i];
	}
	return sum;
}
```

In the Zane source, `foreign "checksum"` takes the place of a body and names
the C function's symbol:

```zane
package hello;

import core$;

@primitives$I64 _checksum(data @primitives$String) foreign "checksum";

Int checksum(text String) => Int(_checksum(text));

Unit main() {
	console Console(@program$console);
	console!print(String(checksum("hello")));
	return Unit();
}
```

```output
99162322
```

A foreign verb's parameters and result have the compiler's storage types,
`@primitives$I64` and `@primitives$String` here, because a C function knows
nothing of `core`'s `Int` and `String`
([Intrinsics and concepts](../tour/intrinsics.md) explains the `@` names).
The checksum uses unsigned arithmetic because a `uint64_t` wraps on overflow,
where a signed overflow is undefined in C. `@primitives$I64` carries the same
64 bits, so the Zane side reads the result as a signed integer.

The usual pattern is a private foreign verb, named with a leading `_`, and a
public function in `core`'s types that calls it. The call `_checksum(text)`
needs no conversion written out, because `core` declares an implicit
conversion from `String` to `@primitives$String`, and an argument is a
coercion site. A `return` is not one, so the result is converted with
`Int(...)`, although `core` declares that conversion implicit too.

The compiler checks every foreign verb against the declaration in the
package's interface headers. A Zane signature that does not match the C
declaration is rejected:

```c file=checksum.h
#include <zane_ffi.h>

uint64_t checksum(zane_bytes data);
```

```zane error
// error: C declares `uint64_t` here
package hello;

@primitives$I32 checksum(data @primitives$String) foreign "checksum";

@primitives$Unit main() {
	return @primitives$Unit();
}
```

A foreign verb may be a function, a method or a `mut` method. A method's
subject is the C function's first parameter, and the remaining parameters
follow in order. A foreign verb is never a constructor, an operator or a
generic function, and it takes no block.

## Types that cross

Each Zane type at the boundary corresponds to a set of C types, and the C
declaration must use one of them:

| Zane type | C type |
|---|---|
| `@primitives$I32` | `int32_t`, `uint32_t`, `int`, `unsigned`; narrower integers such as `uint8_t`, `int16_t` and `char` |
| `@primitives$I64` | `int64_t`, `uint64_t`, `long long`, and `size_t`, `ptrdiff_t`, `intptr_t` on 64-bit targets |
| `@primitives$F32`, `@primitives$F64` | `float`, `double` |
| `@primitives$Bool` | `bool` |
| `@primitives$Unit` | `void`, as a result |
| `@primitives$String` | `zane_bytes`; as a parameter also `const char *` |
| `@primitives$Array<T, n>` of a scalar | `const T *` |
| `@primitives$List<T>` of a scalar | `zane_span` |
| a `struct` of scalars, arrays of scalars and such structs | a C `struct` with the same fields in the same order |
| a foreign handle | a pointer to its C type ([below](#c-objects-behind-handles)) |
| a function type | a pointer to a C function ([below](#zane-functions-as-c-callbacks)) |

An unsigned C type carries the same bits as its signed Zane primitive, so a
`uint32_t` of 4294967295 arrives in Zane as the `@primitives$I32` -1. A C type
whose size differs between targets, such as `long` or `wchar_t`, and a
variadic function such as `printf`, have no Zane counterpart. Your package
reaches them through a small C function of its own that takes and returns the
types above.

A value `struct` whose fields are all scalars crosses as a copy laid out as
the C `struct`:

```c file=vec.h
#include <zane_ffi.h>

typedef struct { double x, y; } vec2;

vec2 vec2_scale(vec2 v, double factor);
```

```c file=vec.c
#include "vec.h"

vec2 vec2_scale(vec2 v, double factor) {
	vec2 r = { v.x * factor, v.y * factor };
	return r;
}
```

```zane
package hello;

import core$;

type Vec2 = struct {
	x @primitives$F64;
	y @primitives$F64;
}

Vec2(x @primitives$F64, y @primitives$F64) => init{ x; y; }

Vec2 _scale(v Vec2, factor @primitives$F64) foreign "vec2_scale";

Unit main() {
	console Console(@program$console);
	v Vec2 = _scale(Vec2(Float(1.5), Float(2.5)), Float(2.0));
	console!print(String(Float(v.x)) + ", " + String(Float(v.y)));
	return Unit();
}
```

```output
3, 5
```

## Strings, arrays and lists are lent for the call

C receives a string, an array or a list as a read-only view that is valid
until the call returns. C reads the view, and never writes through it or keeps
a pointer to it after the call. `<zane_ffi.h>` declares the two view types:

```c fragment
typedef struct zane_bytes { const uint8_t *data; size_t size; } zane_bytes;
typedef struct zane_span  { const void    *data; size_t count; } zane_span;
```

A string parameter that the C function declares as `const char *` arrives
NUL-terminated instead, so a C function that expects a C string needs no
wrapper. A Zane string may hold a NUL byte, and C then reads only the bytes
before it. When the whole string must reach C, declare the parameter as
`zane_bytes`, which carries the length.

A C function returns a string as a `zane_bytes`. The call copies bytes that C
owns into a new Zane string after the C function has returned, so those bytes
must still be valid then: memory that a handle's object owns, or a static
buffer, but never a local array of the C function. To build a result without that copy, C asks for
the bytes with `zane_bytes_alloc`, fills them, and returns a view of them,
which becomes the Zane string as it is:

```c file=shout.h
#include <zane_ffi.h>

zane_bytes shout(zane_bytes text);
```

```c file=shout.c
#include "shout.h"

zane_bytes shout(zane_bytes text) {
	uint8_t *out = zane_bytes_alloc(text.size + 1);
	for (size_t i = 0; i < text.size; i++) {
		uint8_t c = text.data[i];
		out[i] = c >= 'a' && c <= 'z' ? c - 'a' + 'A' : c;
	}
	out[text.size] = '!';
	return (zane_bytes){ out, text.size + 1 };
}
```

```zane
package hello;

import core$;

@primitives$String _shout(text @primitives$String) foreign "shout";

String shout(text String) => String(_shout(text));

Unit main() {
	console Console(@program$console);
	console!print(shout("hello"));
	return Unit();
}
```

```output
HELLO!
```

C never frees what `zane_bytes_alloc` gives it: the string takes the bytes,
and any bytes the string does not use are released when the call returns.

## C objects behind handles

C code that keeps state between calls keeps it in C memory, and Zane reaches
that memory through a **foreign handle**. A handle type names the C type of
its objects and the C function that releases one:

```zane fragment
type Hasher = #handle{ cType = "hasher"; free = "hasher_free"; }
```

A handle is a reference type with one owner, like a `#struct`
([Memory](../tour/memory.md)). A foreign verb that returns a pointer to the C
type makes a new handle, and when the handle's owner is destroyed, Zane calls
the `free` function on the pointer, exactly once. C keeps the object at its
address until then, because Zane never moves it.

A `mut` foreign method may change the handle's object, and C receives a
writable pointer for it. In every other position C receives a `const` pointer,
and the compiler checks that the header declares the pointer that way:

```c file=hasher.h
#include <zane_ffi.h>

typedef struct hasher hasher;

hasher *hasher_new(void);
void hasher_add(hasher *h, zane_bytes data);
uint64_t hasher_sum(const hasher *h);
void hasher_free(hasher *h);
```

```c file=hasher.c
#include <stdlib.h>
#include "hasher.h"

struct hasher { uint64_t sum; };

hasher *hasher_new(void) { return calloc(1, sizeof(hasher)); }

void hasher_add(hasher *h, zane_bytes data) {
	for (size_t i = 0; i < data.size; i++) {
		h->sum = h->sum * 31 + data.data[i];
	}
}

uint64_t hasher_sum(const hasher *h) { return h->sum; }

void hasher_free(hasher *h) { free(h); }
```

```zane
package hello;

import core$;

type Hasher = #handle{ cType = "hasher"; free = "hasher_free"; }

^Hasher _hasher() foreign "hasher_new";
@primitives$Unit _add(this Hasher, data @primitives$String) mut foreign "hasher_add";
@primitives$I64 _sum(this Hasher) foreign "hasher_sum";

Unit main() {
	console Console(@program$console);
	h Hasher = _hasher();
	h!_add(String("hel"));
	h!_add(String("lo"));
	console!print(String(Int(h:_sum())));
	return Unit();
}
```

```output
99162322
```

A foreign verb that returns a handle stops the program when C returns a null
pointer. One that declares `@primitives$Unit` as its abort type, such as
`^Hasher?@primitives$Unit _hasher() foreign "hasher_new";`, aborts instead,
and the caller handles the abort as [Errors](../tour/errors.md) describes.

Two more fields of `#handle` cover the remaining cases:

- `set = "name"` names a **setter**, a C function that takes two pointers to
  the C type, releases the first object's contents and moves the second
  object's into it. Assigning a new handle to a settled owner calls the
  setter, so the object stays at its address. Without a setter, an assignment
  to a settled owner of the handle type is an error.
- A C object that depends on another, such as a prepared statement on a
  database connection, is a `#struct` holding the dependent handle and an `&`
  to the other. The reference keeps the other handle alive at least as long.

## Outside state is a capability

The compiler cannot see the effects of C code, so it relies on each foreign verb's
signature. A foreign function, or a method
on a handle like `Hasher`, is taken to read and write nothing outside the
program, so a call with arguments known at compile time may be evaluated
while the program compiles, and its result built into the program. That keeps
C code that only computes, such as a checksum or a compression routine, as
cheap as Zane code: the compiler compiles the C from source and can evaluate
it as the target would.

C that reaches outside the program, such as a file, the clock or a variable
that the next call reads, declares its reach with a **foreign capability**: a handle type
without a `free` function, whose value refers to a C global. The root package
gets one with a **foreign variable**, a declaration that names the global in
place of an initializer. A method on the capability reads outside state, and a
`mut` method writes it:

```c file=counter.h
#include <zane_ffi.h>

typedef struct counter { int64_t count; } counter;

extern counter the_counter;

int64_t counter_next(counter *c);
```

```c file=counter.c
#include "counter.h"

counter the_counter;

int64_t counter_next(counter *c) { return ++c->count; }
```

```zane
package hello;

import core$;

type Counter = #handle{ cType = "counter"; }

@primitives$I64 _next(this Counter) mut foreign "counter_next";

Unit main() {
	console Console(@program$console);
	counter Counter foreign "the_counter";
	console!print(String(Int(counter!_next())));
	console!print(String(Int(counter!_next())));
	console!print(String(Int(counter!_next())));
	return Unit();
}
```

```output
1
2
3
```

Each `counter!_next()` is a write, so it runs when the program runs, in the
order the program makes it. A binding that skips the capability would be
wrong: a C function `int64_t counter_bump(void) { return ++the_counter.count; }`
declared as the plain function `@primitives$I64 bump() foreign "counter_bump";`
reads and writes the same counter, but the compiler takes it to touch nothing
outside the program. The compiler could then evaluate each call at compile
time, from the counter's first value, and an optimized build would print `1`
three times.
Only the author of a binding can get this right, and no diagnostic reports the
mistake.

Only the root package declares foreign variables. A library package that
needs a capability receives one, as it receives the console
([Effects and capabilities](../tour/effects.md)). A handle made by a `mut`
method on a capability, such as an open file, is part of that outside state,
and only methods on the capability may use it.

## Zane functions as C callbacks

A parameter of function type becomes a C function pointer. C may call it any
number of times before the foreign verb returns, and never after:

```c file=apply.h
#include <zane_ffi.h>

double apply_twice(double (*f)(double), double x);
```

```c file=apply.c
#include "apply.h"

double apply_twice(double (*f)(double), double x) { return f(f(x)); }
```

```zane
package hello;

import core$;

alias F64 = @primitives$F64;

F64 _twice(f F64[F64], x F64) foreign "apply_twice";

Unit main() {
	console Console(@program$console);
	half F64(x F64) => @operators$divide(x, F64(2.0));
	console!print(String(Float(_twice(half, Float(10.0)))));
	return Unit();
}
```

```output
2.5
```

A callback takes and returns scalars, `Bool`, C-compatible structs and `Unit`,
and may also take strings, lists, arrays and data handles. What the Zane
function reads and writes counts as what the foreign call reads and writes.

C may call a callback that touches no capability from several threads at
once. The callbacks of one foreign call that read or write capability-backed
state, such as one that prints, C calls one at a time: while one of them runs,
C starts no other call to any of them. The compiler orders the foreign call
as a whole against other accesses to that state, but it sees none of the
calls C makes inside it.

## Build settings: `c.coda`

A package whose C needs settings has a `c.coda` file in its directory. Each
row of its `c` table gives one setting, for the targets whose triple matches
the `target` pattern, where `*` matches anything:

```coda file=c.coda
c [
    setting  value         target
    define   SCALE=3       *
    define   ON_LINUX=1    *-linux-*
]
```

```c file=scale.h
#include <zane_ffi.h>

int64_t scale(int64_t x);
```

```c file=scale.c
#include "scale.h"

int64_t scale(int64_t x) { return x * SCALE; }
```

```zane
package hello;

import core$;

@primitives$I64 _scale(x @primitives$I64) foreign "scale";

Unit main() {
	console Console(@program$console);
	console!print(String(Int(_scale(Int(14)))));
	return Unit();
}
```

```output
42
```

The settings are:

| Setting | Value | Effect |
|---|---|---|
| `source` | a path or pattern, such as `vendor/*.c` | more C sources, such as a vendored library's |
| `include` | a directory | a directory the C compiler searches for headers |
| `define` | `NAME` or `NAME=VALUE` | a macro defined for every C source of the package |
| `archive` | a path | a prebuilt static library linked with the package |
| `system` | a library name, such as `m` | a library of the target system linked with the program |

Every path stays inside the package's directory, so a package carries its
whole C build with it. To use an existing C library, copy its sources into a
folder of the package, such as `vendor/`, and list them with `source` and
`include` rows. A folder without `.zn` files is not a subpackage, so
`vendor/` belongs to the package that holds it. Each package's C symbols
belong to that package, so two packages that vendor the same library, or two
versions of one package, do not clash in one program.

C compiled from source is the only C the compiler can evaluate at compile
time. C from an `archive` or `system` row runs only in the running program.

When a package holds C code, `zane check` writes a `compile_commands.json`
for clangd, so your editor sees the same headers and macros as the build
([The `zane` command](../reference/cli.md#zane-check)).

## What C code must uphold

The compiler builds its guarantees on the foreign verbs' signatures, so a C
function reached through a foreign verb must:

- touch outside state only through a method on a capability, and write it
  only in a `mut` method;
- write only its `mut` subject, its own C memory and the bytes
  `zane_bytes_alloc` gives it, never a view or a `const` handle;
- keep no view, callback or pointer that Zane lent it after the call returns;
- be safe to call from several threads at once when it touches no capability,
  since such calls may run in parallel ([Concurrency](../tour/concurrency.md));
- call the callbacks that touch a capability one at a time, and every
  callback only while the foreign call runs;
- return normally, without `longjmp` or exiting the process.

A C function that breaks one of these rules gives the program no defined
meaning.

## In the spec

- [The C interface](https://github.com/zane-lang/spec/blob/main/spec/ffi.md):
  [a package's C code](https://github.com/zane-lang/spec/blob/main/spec/ffi.md#2-a-packages-c-code),
  [foreign verbs](https://github.com/zane-lang/spec/blob/main/spec/ffi.md#3-foreign-verbs),
  [foreign handles](https://github.com/zane-lang/spec/blob/main/spec/ffi.md#4-foreign-handles),
  [effects of foreign code](https://github.com/zane-lang/spec/blob/main/spec/ffi.md#5-effects-of-foreign-code)
  and [what foreign code upholds](https://github.com/zane-lang/spec/blob/main/spec/ffi.md#6-what-foreign-code-upholds)
- The story behind it: [the C interface](https://github.com/zane-lang/spec/blob/main/stories/ffi.md)
- How the compiler builds, calls and evaluates C:
  [the compiler's FFI design](https://github.com/zane-lang/compiler/blob/main/docs/design/ffi.md)
