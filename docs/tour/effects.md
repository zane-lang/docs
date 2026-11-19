# Effects and capabilities

This page covers what a call is allowed to change, and how a program reaches the console and other outside state through capabilities.

## What a call may write

Zane has one effect modifier, `mut`, and the kind of a function says what it
may write:

| Kind | Called with | May write |
|---|---|---|
| `mut` method | `subject!name(…)` | its subject, and what is reached through it |
| method without `mut` | `subject:name(…)` | nothing its caller can see |
| function | `name(…)` | nothing its caller can see |

Every function may change its own local symbols. What it cannot do is reach
out: parameters other than the subject are read-only, there are no global
variables, and a package holds constants only. So the signature alone tells
you what a call can change, however deep its own calls go.

That bound is checked. A function that tries to write a parameter is
rejected:

```zane error
// error: is a parameter, which is read-only
package hello;

import core$;

Unit greet(console Console) {
	console!print("hi");
	return Unit();
}

Unit main() {
	console Console(@program$console);
	greet(console);
	return Unit();
}
```

Because a function that writes nothing has no effect besides its result, the
compiler is free to run such calls in parallel or ahead of time.

## Capabilities

Printing, like any interaction with the world outside the program, goes
through a **capability**: an object whose methods reach that outside state.
Capabilities are never global. The program receives its console and runtime
as `@program$console` and `@program$runtime`, which only the program's own
package (the one with `main`) can name. Everything else gets them by being
handed them.

A component that needs to print keeps a reference to the console, and writes
through it from a `mut` method:

```zane
package hello;

import core$;

type Logger = #struct {
	out &Console;
	prefix String;
}
Logger(out &Console, prefix String) => init{ out; prefix; }

Unit log(this Logger, message String) mut {
	this.out!print(this.prefix + message);
	return Unit();
}

Int compute(n Int) => n * n;

Unit main() {
	console Console(@program$console);
	logger Logger(console, String("[app] "));
	logger!log("starting");
	result Int = compute(Int(12));
	logger!log("result " + String(result));
	return Unit();
}
```

```output
[app] starting
[app] result 144
```

`compute` is a plain function that was handed nothing, so it cannot print, and
`logger!log` can print only because the logger was given the console. A
library package is never handed `@program$`, so a library you depend on can
only reach what you pass it.

## The runtime

`Runtime(@program$runtime)` gives the program's command-line arguments, and
sizes the thread pool:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	runtime Runtime(@program$runtime);
	args List<String> = runtime:arguments();
	console!print(String(args:size()) + " arguments");
	i Int(1);
	i!to(args:size()) {
		console!print(args[i]);
	}
	return Unit();
}
```

```output
0 arguments
```

`zane run -- one two` passes `one` and `two` to the program.

## In the spec

- [Effects](https://github.com/zane-lang/spec/blob/main/spec/effects.md):
  [what each kind of verb may write](https://github.com/zane-lang/spec/blob/main/spec/effects.md#3-what-each-kind-of-verb-may-write),
  [enforcement](https://github.com/zane-lang/spec/blob/main/spec/effects.md#4-effect-enforcement),
  [capability wiring](https://github.com/zane-lang/spec/blob/main/spec/effects.md#6-capability-wiring-and-explicit-state-flow)
  and [the program's console and runtime](https://github.com/zane-lang/spec/blob/main/spec/effects.md#66-the-programs-console-and-runtime)
- [The root package](https://github.com/zane-lang/spec/blob/main/spec/packages.md#6-the-root-package)
- The story behind it: [effects](https://github.com/zane-lang/spec/blob/main/stories/effects.md)
