# Concurrency

This page covers `spawn`, which runs a call on another thread, and the rules that keep concurrent code free of data races.

## `spawn`

Writing `spawn` before a function or method call runs it on the program's
thread pool while the code after it carries on. A symbol bound to a spawned
call holds its result once the call finishes, and reading it waits until
then:

```zane
package hello;

import core$;

Int fib(n Int) {
	small Bool = if(n < 2) {
		return n;
	}
	return fib(n - 1) + fib(n - 2);
}

Unit main() {
	console Console(@program$console);
	a Int = spawn fib(Int(25));
	b Int = spawn fib(Int(20));
	console!print(String(a) + " " + String(b));
	return Unit();
}
```

```output
75025 6765
```

There is no `async` or `await`, and a function does not change its type to
be spawned: `spawn` marks the call, not the function.

## Spawned writes

A spawned `mut` method may change its subject when the subject is a value
type, and only one running spawn may write a given place at a time. The
scope that spawned the work stays alive until every spawn in it has
finished, so the objects that work uses are never destroyed under it:

```zane
package hello;

import core$;

type Tally = struct {
	sum Int;
}
Tally() => init{ sum = Int(0); }

Unit addUpTo(this Tally, n Int) mut {
	i Int(1);
	i!to(n) {
		this.sum = this.sum + i;
	}
	return Unit();
}

Unit main() {
	console Console(@program$console);
	left Tally();
	right Tally();
	do() {
		spawn left!addUpTo(Int(100));
		spawn right!addUpTo(Int(10));
	}
	console!print(String(left.sum) + " " + String(right.sum));
	return Unit();
}
```

```output
5050 55
```

The block given to `do` ends only once both spawns are done, so the line
after it sees both sums. A lambda captures nothing, so a spawned call can
reach only what it is passed.

On a `Runtime`, `runtime!setThreads(Int(4))` sizes the thread pool, and
aborts for a count below one. Spawning a
worker (`spawn subject!setInterval(…)`) runs it in the background; the
compiler's runtime keeps a pool thread for each waiting worker (compiler
[divergence 11](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#11-a-spawned-workers-wait-holds-its-pool-thread)).

## In the spec

- [Concurrency](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md):
  [`spawn`](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md#3-spawn-and-explicit-concurrency)
  and [safety rules](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md#4-safety-rules-under-concurrency)
- Where the compiler differs: divergences
  [7](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#7-a-spawned-calls-handler-runs-where-the-call-settles),
  [8](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#8-a-block-does-not-write-an-owner-it-lent-a-running-spawn)
  and [11](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#11-a-spawned-workers-wait-holds-its-pool-thread)
- The story behind it: [implicit parallelism without async coloring](https://github.com/zane-lang/spec/blob/main/stories/concurrency.md)
