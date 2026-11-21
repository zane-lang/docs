# Basics

This page covers the shape of a Zane program: symbols, numbers, booleans, strings and comments.

Most examples on these pages are whole programs: they declare `main`. To run
one, put it in `bin/hello/main.zn` of a project that depends on `std` ([Your
first project](../first-project.md)) and run `zane run`; the first line may
name any package, as long as it matches the directory. A few examples show
only part of a package, such as one file of a library or a single function;
they run only as part of a larger program.

## A program

```zane
package hello;

import core$;

/// The program starts here.
Unit main() {
	console Console(@program$console);
	console!print("Hello!"); // a statement ends with `;`
	return Unit();
}
```

```output
Hello!
```

- `package hello;` names the package the file belongs to. A program's package
  name is the name of the program's directory under `bin/`.
- `import core$;` brings in the `core` package of the standard library, which
  declares `Unit`, `Int`, `String`, `Console` and almost everything else on
  these pages. The trailing `$` lets you write the names that `core` declares
  without a `core$` prefix ([Packages](packages.md)).
- A name that starts with `@`, such as `@program$console`, is supplied by the
  compiler rather than declared in a package. `@program$console` is the
  program's console, which `Console(...)` wraps in `core`'s type
  ([Intrinsics and concepts](intrinsics.md)).
- A function declaration starts with its return type: `Unit main()` returns
  `Unit`, the type with only one value, which a function returns when it has
  no meaningful result. Every function returns with `return`.
- `//` starts a comment, and `///` a documentation comment on the declaration
  below it.

## Symbols

A **symbol** is a named value: a local variable, a parameter or a field. A
symbol declaration puts the name first and the type second, and every symbol
gets a value when it is declared:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	width Int = Int(6);  // a type, then `=` and a value
	height Int(7);       // or the type called with its arguments
	area Int = width * height;
	console!print(String(area));

	width = width + 1;   // assigning replaces the value
	console!print(String(width * height));
	return Unit();
}
```

```output
42
49
```

An identifier's case shows whether it names a type or a value: type names
start with an upper-case letter (`Int`, `Console`), and the names of values
and functions start with a lower-case letter (`width`, `main`). An identifier
starting with `_` is private to its package.

A declaration states its type, and the value must already be of that type.
That is why `width Int = Int(6);` calls `Int` on the literal `6`: a literal is
not yet an `Int`, and a declaration never converts on its own. A literal
*is* converted when it is passed to a function or used as the operand of an
operator next to an `Int`, so `width * 2` and `print("text")` need no
conversion written out.

## Numbers and booleans

`Int` is a 64-bit integer and `Float` a 64-bit floating-point number. `core`
also has `I32`, `F32` and the byte `U8` for compact storage.

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	a Int(17);
	b Int(5);
	console!print(String(a + b) + " " + String(a - b) + " " + String(a * b));
	console!print(String(a / b));       // integer division rounds toward zero
	console!print(String(~a));          // `~` negates
	million Int(1'000'000);             // `'` separates groups of digits
	console!print(String(million));

	x Float(1.5);
	console!print(String(x * 3.0));
	console!print(String(Float(a) / 2.0));
	console!print(String(Int.truncate(x * 3.0)));

	big Bool = b < a and a ~= 0;        // `~=` is "not equal"
	small Bool = ~big or a <= b;        // `~` is also "not" on a Bool
	same Bool = big == ~small;
	return Unit();
}
```

```output
22 12 85
3
-17
1000000
4.5
8.5
4
```

`~` is Zane's only prefix operator: it negates a number and inverts a `Bool`.
`a - b` means `a + ~b`, and `>`, `<=`, `>=` and `~=` are likewise derived
from `<` and `==`, so a type that defines `+`, `~`, `<` and `==` also gets
`-`, `>`, `<=`, `>=` and `~=`. There are no implicit conversions between
number types: `Float(a)` converts an `Int` to a `Float`, and `Int.truncate(x)`
converts a `Float` to an `Int`.

An operator can't take two literals as its operands: `2 * 3` has no type to
compute in, so write one operand as `Int(2)`.

## Strings

A `String` is UTF-8 text. `+` joins strings, `String(n)` turns a number into
a string, and `\%name` inside a literal inserts the value of a `String` symbol:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	name String = String("Ada");
	year Int(1843);
	when String = String(year);
	console!print("\%name wrote the first program in \%when.");
	console!print("tab:\tquote: \"" + name + "\"");
	console!print(String(name:byteCount()));
	return Unit();
}
```

```output
Ada wrote the first program in 1843.
tab:	quote: "Ada"
3
```

`\n`, `\t`, `\r`, `\0` and `\\` are escapes inside a string literal, and
`\"` writes a double quote. An interpolation can insert only a symbol, so to
insert a field or the result of a call, bind it to a symbol first.

## In the spec

- [Lexical rules](https://github.com/zane-lang/spec/blob/main/spec/lexical.md):
  [casing](https://github.com/zane-lang/spec/blob/main/spec/lexical.md#3-casing-determines-kind),
  [literals](https://github.com/zane-lang/spec/blob/main/spec/lexical.md#7-literals)
  and [string escapes](https://github.com/zane-lang/spec/blob/main/spec/lexical.md#71-string-literals-and-structural-escapes)
- [Operators](https://github.com/zane-lang/spec/blob/main/spec/operators.md):
  [derived operators](https://github.com/zane-lang/spec/blob/main/spec/operators.md#23-derived-operators)
  and [precedence](https://github.com/zane-lang/spec/blob/main/spec/operators.md#3-precedence-and-associativity)
- [Fundamental types](https://github.com/zane-lang/spec/blob/main/spec/types.md)
