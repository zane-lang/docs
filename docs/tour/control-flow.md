# Control flow

This page covers branching, loops, early exits and workers, which in Zane are ordinary functions from `core` that take a block.

## Blocks

A call may end with a **block**, a run of statements in braces written after
its parentheses. The function decides when, and how often, the block runs.
`if`, `else`, the counting loop `to` and the rest of this page are declared
that way in `core`'s
[`controlflow.zn`](https://github.com/zane-lang/std/blob/main/lib/core/controlflow.zn);
the language has no `if` or `while` keyword.

A block may use and change the symbols around it. It is not a value: it
cannot be stored or returned, and it runs only during the call it is passed
to. A `return` written inside a block returns from the function that contains
it.

## `if`, `elif` and `else`

`if` runs its block when the condition holds, and returns whether it did.
Keep that `Bool` to continue the chain with `elif` and `else`, which are
methods on it:

```zane
package hello;

import core$;

String classify(n Int) {
	small Bool = if(n < 10) {
		return String("small");
	}
	small!elif(n < 100) {
		return String("medium");
	}
	return String("large");
}

Unit main() {
	console Console(@program$console);
	console!print(classify(Int(5)) + " " + classify(Int(50)) + " " + classify(Int(500)));

	temperature Int(25);
	warm Bool = if(temperature > 30) {
		console!print("hot");
	}
	warm!elif(temperature > 20) {
		console!print("warm");
	}
	warm:else() {
		console!print("cold");
	}
	return Unit();
}
```

```output
small medium large
warm
```

`elif` is called with `!` because it updates the chain's `Bool` to record
that a branch ran; `else` only reads it. When the result is not needed, an
`if` is written as a statement on its own.

## Counting with `to`

`i!to(end) { … }` runs its block once for each value from `i` up to `end`,
advancing `i` itself, so the counter is an ordinary symbol:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	total Int(0);
	i Int(1);
	i!to(Int(4)) {
		total = total + i;
		console!print("i = " + String(i) + ", total = " + String(total));
	}
	return Unit();
}
```

```output
i = 1, total = 1
i = 2, total = 3
i = 3, total = 6
i = 4, total = 10
```

Counting starts at 1, and so do positions in lists, arrays and strings: a list
of `n` elements has positions `1` to `n`.

Every loop runs a known number of times. A search that stops early returns
from inside the block:

```zane
package hello;

import core$;

Int firstAbove(values List<Int>, limit Int) {
	i Int(1);
	i!to(values:size()) {
		if(limit < values[i]) {
			return i;
		}
	}
	return Int(0);
}

Unit main() {
	console Console(@program$console);
	values List<Int> = List(Int);
	values!push(Int(3));
	values!push(Int(8));
	values!push(Int(12));
	console!print(String(firstAbove(values, Int(5))));
	return Unit();
}
```

```output
2
```

## `guard` and `do`

`guard(condition)` ends the block it is called in when the condition holds.
In a loop, that skips the rest of the current pass. `do` runs a block once,
which gives a `guard` a block to end:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	i Int(1);
	i!to(Int(5)) {
		guard(i == 3);
		console!print(String(i));
	}

	ready Bool = Bool(false);
	do() {
		guard(~ready);
		console!print("not printed");
	}
	console!print("done");
	return Unit();
}
```

```output
1
2
4
5
done
```

The spec has `guard` end the whole function that calls it; the compiler ends
the block instead and accepts `guard` only inside a block (compiler
[divergence 6](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#6-an-exit-ends-the-run-of-a-block)).

## Workers: loops without a count

Work that runs until its own state says it is finished is a **worker**:
`subject!work(step)` calls the function value `step` on the subject, again
and again, while it returns `true`. The step is a lambda that takes the
subject as `this`, so all the state it carries is in plain sight:

```zane
package hello;

import core$;

type Collatz = struct {
	n Int;
	steps Int;
}
Collatz(n Int) => init{ n; steps = Int(0); }

Unit main() {
	console Console(@program$console);
	c Collatz(Int(6));
	c!work(Bool(this Collatz) mut {
		half Int = this.n / 2;
		even Bool = if(half * 2 == this.n) {
			this.n = half;
		}
		even:else() {
			this.n = this.n * 3 + 1;
		}
		this.steps = this.steps + 1;
		return this.n ~= 1;
	});
	console!print("6 reaches 1 in " + String(c.steps) + " steps");
	return Unit();
}
```

```output
6 reaches 1 in 8 steps
```

`setInterval(every, step)` does the same and waits `every` (a `Duration`, such
as `Duration.milliseconds(16)`) between steps.

## Writing your own

Control flow is ordinary code, so you can declare more of it. A parameter of
type `@concepts$Block` takes a block, and the compiler's control-flow
intrinsics run it; `@controlflow$repeat(n, body)` runs it `n` times:

```zane
package hello;

import core$;

Unit times(this Int, body @concepts$Block) {
	@controlflow$repeat(this, body);
	return Unit();
}

Unit main() {
	console Console(@program$console);
	Int(3):times() {
		console!print("hip hip");
	}
	console!print("hooray");
	return Unit();
}
```

```output
hip hip
hip hip
hip hip
hooray
```

A function that takes a block is expanded where it is called, so a block
costs nothing at run time.

## In the spec

- [Control flow](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md):
  [block arguments](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#2-block-arguments),
  [branching and repetition](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#3-branching-and-repetition),
  [workers](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#37-work-and-setinterval-run-a-worker),
  [the intrinsics](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#4-control-flow-intrinsics)
  and [counting from 1](https://github.com/zane-lang/spec/blob/main/spec/control-flow.md#5-1-based-ordinal-counting)
- The story behind it: [how branching and repetition became library code](https://github.com/zane-lang/spec/blob/main/stories/control-flow.md)
