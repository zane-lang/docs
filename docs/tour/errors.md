# Errors

This page covers abortable functions, which fail along a second, typed return path, and the `?` and `??` handlers that deal with a failure where the call is made.

## A second way to return

A function that can fail declares an **abort type** after its return type,
separated by `?`. `Int?DivError` returns an `Int`, or aborts with a
`DivError`. `abort` leaves the function along that second path:

```zane
package hello;

import core$;

type DivError = enum [ byZero ];

Int?DivError divide(a Int, b Int) {
	zero Bool = if(b == 0) {
		abort DivError.byZero;
	}
	return a / b;
}

Unit main() {
	console Console(@program$console);
	ok Int = divide(Int(10), Int(2)) ?? Int(0);
	console!print(String(ok));
	fallback Int = divide(Int(1), Int(0)) ?? Int(0);
	console!print(String(fallback));
	return Unit();
}
```

```output
5
0
```

An abort is not an exception: it goes to the immediate caller and no
further, and the caller must handle it. `expr ?? value` is the shortest
handler: when the call aborts, `value` is used instead.

A failure that carries no information has the abort type `Unit`, and aborts
with `abort Unit();`. `core`'s `parseInt` is one:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	n Int = String("42"):parseInt() ?? Int(0);
	m Int = String("4x"):parseInt() ?? Int(~1);
	console!print(String(n) + " " + String(m));
	return Unit();
}
```

```output
42 -1
```

## Handler blocks

`? name { … }` handles an abort with a block, where `name` is bound to the
abort value. Every path through the block ends in one of three ways:

| Keyword | Leaves | Effect |
|---|---|---|
| `resolve value` | the handler | `value` stands in for the failed call |
| `return value` | the function | returns normally |
| `abort value` | the function | aborts the function in turn |

```zane
package hello;

import core$;

type DivError = enum [ byZero, negative ];

String explain(e DivError) => match (e) {
	byZero => String("division by zero");
	negative => String("negative input");
}

Int?DivError divide(a Int, b Int) {
	zero Bool = if(b == 0) {
		abort DivError.byZero;
	}
	negative Bool = if(a < 0 or b < 0) {
		abort DivError.negative;
	}
	return a / b;
}

/// Passes a failure on: the handler aborts in turn.
Int?DivError percent(a Int, b Int) {
	q Int = divide(a * 100, b) ? e {
		abort e;
	}
	return q;
}

Unit main() {
	console Console(@program$console);
	shown Int = percent(Int(1), Int(0)) ? e {
		console!print("failed: " + explain(e));
		resolve Int(0);
	}
	console!print(String(shown));
	console!print(String(percent(Int(1), Int(4)) ?? Int(0)) + "%");
	return Unit();
}
```

```output
failed: division by zero
0
25%
```

There is no operator that passes a failure on silently: a handler that wants
the caller to deal with it writes `abort` itself, so every place a failure
crosses is visible in the code.

## Handling is required

Calling an abortable function without a handler is an error, and so is a
handler that can fall through:

```zane error
// error: so the call needs a `?` or `??` handler
package hello;

import core$;

Unit main() {
	n Int = String("42"):parseInt();
	return Unit();
}
```

The abort type is part of the signature, so changing what a function can fail
with is a change every caller sees.

## Program errors

Some mistakes are not failures a caller can handle. Reading a list at a
position it does not have stops the program: the runtime writes `index out of
range` to standard error and exits with status 1 (compiler
[divergence 10](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#10-an-index-out-of-range-stops-the-program)).

## In the spec

- [Error handling](https://github.com/zane-lang/spec/blob/main/spec/error-handling.md):
  [abort types](https://github.com/zane-lang/spec/blob/main/spec/error-handling.md#2-core-concepts),
  [call-site handling](https://github.com/zane-lang/spec/blob/main/spec/error-handling.md#3-call-site-handling)
  and [`resolve`](https://github.com/zane-lang/spec/blob/main/spec/error-handling.md#4-the-resolve-keyword);
  its last sections compare it with C, Go, exceptions, Rust, Swift and Zig
- The story behind it: [failure as a second return path](https://github.com/zane-lang/spec/blob/main/stories/error-handling.md)
