# Functions and methods

This page covers functions, methods and their subjects, the `:` and `!` call markers, overloading, and function values.

## Functions

A function is declared at package scope with its return type first. A body
in braces returns with `return`; a body that is one expression is written
after `=>`:

```zane
package hello;

import core$;

Int square(x Int) => x * x;

Int sumOfSquares(a Int, b Int) {
	total Int = square(a) + square(b);
	return total;
}

Unit main() {
	console Console(@program$console);
	console!print(String(sumOfSquares(Int(3), Int(4))));
	console!print(String(square(9)));
	return Unit();
}
```

```output
25
81
```

Declarations at package scope can come in any order, so `sumOfSquares` may
call a function declared below it. An argument is a *coercion site*: there a
literal such as `9` is converted to the parameter's type. A `return` is not,
so a function returning `String` writes `return String("text");`.

Parameters are read-only: a function cannot assign to them or change what they
hold.

## Methods and their subject

A method is a function whose first parameter is `this`. The value it is
called on is its **subject**. Methods are declared outside the type, at
package scope, like any other function:

```zane
package hello;

import core$;

type Counter = struct {
	count Int;
}
Counter() => init{ count = Int(0); }

/// Reads its subject.
Int value(this Counter) => this.count;

/// Changes its subject: `mut`.
Unit add(this Counter, amount Int) mut {
	this.count = this.count + amount;
	return Unit();
}

Unit main() {
	console Console(@program$console);
	c Counter();
	c!add(Int(5));
	c!add(2);
	console!print(String(c:value()));
	return Unit();
}
```

```output
7
```

A method is **read-only** unless it is declared `mut`. A `mut` method may
write its subject, and nothing else of its caller's. The call says which kind
it is: `c:value()` calls a read-only method and `c!add(…)` a `mut` one, so
you can see at each call whether the subject may change. Using the wrong
marker is an error:

```zane error
// error: is a `mut` method, so it is called with `!`
package hello;

import core$;

type Counter = struct {
	count Int;
}
Counter() => init{ count = Int(0); }

Unit add(this Counter, amount Int) mut {
	this.count = this.count + amount;
	return Unit();
}

Unit main() {
	c Counter();
	c:add(Int(5));
	return Unit();
}
```

Because methods live outside the type, any package can add methods to any
type, `Int` included. A method never converts its subject, so a literal
subject is written as `Int(4)`:

```zane
package hello;

import core$;

Bool isEven(this Int) => (this / 2) * 2 == this;

Unit double(this Int) mut {
	this = this * 2;
	return Unit();
}

Unit main() {
	console Console(@program$console);
	n Int(21);
	n!double();
	even Bool = n:isEven();
	shown Bool = if(even) {
		console!print(String(n) + " is even");
	}
	return Unit();
}
```

```output
42 is even
```

A `mut` method can assign `this` itself: `n!double()` changes `n`.

## Overloading

Several functions may share a name when their parameter types differ. The
call picks the one whose parameters fit its arguments:

```zane
package hello;

import core$;

String describe(n Int) => String("a number");
String describe(s String) => String("some text");
String describe(a Int, b Int) => String("two numbers");

Unit main() {
	console Console(@program$console);
	console!print(describe(Int(1)));
	console!print(describe(String("x")));
	console!print(describe(Int(1), Int(2)));
	return Unit();
}
```

```output
a number
some text
two numbers
```

Overloads differ by their parameter types only, never by their return type.
Operators are overloaded the same way; see [Types](types.md#operators).

## Function values

A function itself is not a value, but a **lambda** is: a function declaration
without its name, which writes its parameter and return types out in full. A
function type is written as the return type followed by the parameter types in
`[ ]`: `Int[Int]` takes an `Int` and returns one.

```zane
package hello;

import core$;

Int applyTwice(f Int[Int], x Int) => f(f(x));

Unit main() {
	console Console(@program$console);
	// A lambda-variable: the name, then the lambda.
	square Int(x Int) => x * x;
	console!print(String(applyTwice(square, Int(3))));

	// A lambda written in place.
	console!print(String(applyTwice(Int(x Int) => x + 10, Int(1))));
	return Unit();
}
```

```output
81
21
```

A lambda does not capture the symbols around it: everything it uses is a
parameter. A block passed to a call, as `if` and loops take one, is not a
lambda and may use the symbols around it; see [Control flow](control-flow.md).

## In the spec

- [Functions](https://github.com/zane-lang/spec/blob/main/spec/functions.md):
  [methods](https://github.com/zane-lang/spec/blob/main/spec/functions.md#2-methods),
  [call markers](https://github.com/zane-lang/spec/blob/main/spec/functions.md#25-call-markers-are-part-of-the-surface-syntax),
  [overloading](https://github.com/zane-lang/spec/blob/main/spec/functions.md#4-overloading-rules)
  and [lambdas](https://github.com/zane-lang/spec/blob/main/spec/functions.md#7-function-values-and-lambdas)
- [Coercion sites](https://github.com/zane-lang/spec/blob/main/spec/types.md#42-coercion-sites)
- The story behind it: [functions](https://github.com/zane-lang/spec/blob/main/stories/functions.md)
