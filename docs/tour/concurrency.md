# Concurrency

This page covers `spawn`, which runs a call on another thread, the rules that keep concurrent code free of data races, and worker pools.

## `spawn`

Writing `spawn` before a function or method call runs the call on the
program's thread pool while the code after the call carries on. A symbol bound
to a spawned call holds the call's result once the call finishes, and reading
the symbol waits until then:

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

There is no `async` or `await`, and a function's type is the same whether or
not a call to it is spawned: `spawn` marks the call, not the function.

## Spawned writes

A spawned `mut` method may change its subject when the subject is a value
type, and only one running spawn may write a given place at a time. The
scope that spawned the work stays alive until every spawn in it has
finished, so the objects the spawned calls use are never destroyed while those
calls run:

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
after the block sees both sums. A lambda captures nothing, so a spawned call
can reach only what is passed to it.

On a `Runtime`, `runtime!setThreads(Int(4)) ?? Unit();` sets the size of the
thread pool. `setThreads` aborts for a count below one, so the call needs a
handler ([Errors](errors.md)).

Spawning a worker, as in `spawn subject!setInterval(…)`, runs the worker beside
the code after the call. A worker's wait holds back only that worker, and a
read of a spawned call's result holds back only the reader: every other
spawned call keeps running while the wait lasts. To follow this rule, the
compiler's runtime starts a stand-in thread whenever a pool thread waits. The
pool holds at most 4095 threads, so once that many threads wait at the same
time, queued work waits until one of them is free (compiler
[divergence 11](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#11-a-wait-holds-its-pool-thread-when-the-pool-has-none-to-spare)).

## Worker pools

A **worker pool** runs many workers at once, such as one for each network
connection. Each worker is an element, which the pool owns, and a step, which
the pool calls on the element until the step returns `false`. The workers may
share a state, which only the pool's funnel writes: a step publishes an event,
and the funnel applies the events one at a time. The scope that holds a pool
ends once every step has returned `false` and the funnel has applied every
event. In this program the two workers publish seven events, and the funnel
prints the sum once it has applied the seventh:

```zane
package hello;

import core$;

type Counter = struct {
	n Int;
	limit Int;
}
Counter(limit Int) => init{ n = Int(0); limit; }

type Total = struct {
	sum Int;
	events Int;
}
Total() => init{ sum = Int(0); events = Int(0); }

Unit main() {
	do() {
		pool WorkerPool<Counter, Total, Int> = WorkerPool(Counter, Total(), Unit(this Total, n Int) mut {
			this.sum = this.sum + n;
			this.events = this.events + 1;
			if(this.events == 7) {
				console Console(@program$console);
				console!print("sum " + String(this.sum));
			}
			return Unit();
		});
		count Bool[this Counter, Total, Unit[Int]] mut = Bool(this Counter, state Total, publish Unit[Int]) mut {
			this.n = this.n + 1;
			publish(this.n);
			return this.n < this.limit;
		}
		pool!start(Counter(3), count);
		pool!start(Counter(4), count);
	}
	console Console(@program$console);
	console!print("both workers finished");
	return Unit();
}
```

```output
sum 16
both workers finished
```

`pool!start(element, sources, step)` adds a worker whose step runs again only
when one of `sources`, a `List<EventSource>`, is ready or the funnel has
changed the state. Between calls, that worker holds no thread. The
[`std` worker pool page](https://github.com/zane-lang/std/blob/main/docs/core/workers.md)
lists every verb.

## In the spec

- [Concurrency](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md):
  [`spawn`](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md#3-spawn-and-explicit-concurrency),
  [safety rules](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md#4-safety-rules-under-concurrency)
  and [worker pools](https://github.com/zane-lang/spec/blob/main/spec/concurrency.md#6-worker-pools)
- Where the compiler differs: divergences
  [7](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#7-a-spawned-calls-handler-runs-where-the-call-settles),
  [8](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#8-a-block-does-not-write-an-owner-it-lent-a-running-spawn),
  [11](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#11-a-wait-holds-its-pool-thread-when-the-pool-has-none-to-spare),
  [12](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#12-a-read-of-a-pools-state-or-elements-waits-for-a-writer),
  [13](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#13-a-publish-function-called-outside-its-pools-work-stops-the-program)
  and [14](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#14-missed-timer-ticks-merge)
- The story behind it: [implicit parallelism without async coloring](https://github.com/zane-lang/spec/blob/main/stories/concurrency.md)
