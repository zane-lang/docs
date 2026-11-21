# Testing

This guide covers test packages: where they live, what they can import, and how `zane test` runs them.

## Test packages

Tests live in `test/`. Each directory directly inside `test/` is a **test
package**, and every file of a test package starts with `package test;`. A test package is a
program: it declares `main`, and `zane test` builds and runs it.

```text
lib/shapes/shapes.zn       the library package `shapes`
test/shapes/main.zn        a test package for `shapes`
lib/shapes/solid/          a subpackage, `shapes`'s `solid`
test/shapes/solid/main.zn  the test package for `solid`, at the same path as under lib/
```

A test package uses a library the way any other user does: it imports the
library and can use only the library's public names. A test package may
import every library package of its project, including private packages whose
names start with `_`, and the packages
of `deps` and `test-deps`. Only test packages may import `test-deps`.
[Your first project](../first-project.md#a-library-and-its-tests) builds a
test package step by step.

## Running tests

```sh
zane test                 # every test package
zane test shapes          # only the test package in test/shapes/
zane test shapes -- -v    # pass arguments to that test package
```

Each test package is built and run the way `zane run` runs a program, as the
root of its own build, with the project's library packages compiled from
`lib/`. `zane test` prints each package's name as the package starts, then
prints how many packages passed:

```text
$ zane test
Testing test/edge/
index out of range
Testing test/shapes/
ok   area
ok   not square
1 of 2 test packages failed: edge
```

A test package fails when its program exits with a status other than 0. A
program that stops on an index out of range is one example. A `main` that
aborts is another: `main` may declare `@primitives$String` as its abort type,
and when `main` aborts, the program writes the abort message to stderr and
exits with 1. If any test
package fails, `zane test` exits with 1. When `zane test` runs a single
package, it exits with that package's status.

## Writing checks

Each test package reports its results in its own way. The helper below prints
the result of each check and counts the checks that fail. Its `finish` method
aborts when any check failed, and `main` passes that abort on, so a failed
check fails the test package. For example, as `test/shapes/main.zn`:

```zane
package test;

import core$;

/// Prints each check's result, and counts the checks that fail.
type Checks = #struct {
	_console Console;
	_failed Int;
}
Checks() => init{
	_console = Console(@program$console);
	_failed = Int(0);
}

Unit check(this Checks, name String, ok Bool) mut {
	passed Bool = if(ok) {
		this._console!print("ok   " + name);
	}
	passed:else() {
		this._failed = this._failed + 1;
		this._console!print("FAIL " + name);
	}
	return Unit();
}

/// Aborts with a message when any check failed.
Unit?@primitives$String finish(this Checks) {
	if(this._failed > 0) {
		abort @primitives$String(String(this._failed) + " of the checks failed");
	}
	return Unit();
}

Unit?@primitives$String main() {
	checks Checks();
	values List<Int> = List(Int);
	values!push(Int(3));
	checks!check("one element", values:size() == 1);
	checks!check("first is 3", values[Int(1)] == 3);
	checks:finish() ? report {
		abort report;
	}
	return Unit();
}
```

`zane test shapes` runs this package, and the package prints:

```output
ok   one element
ok   first is 3
```

When a check fails, the package prints the abort message and fails:

```text
$ zane test shapes
FAIL one element
ok   first is 3
1 of the checks failed
```

A testing library added with `zane add <url> --test` can provide richer
checks; `zane` only runs the programs and reads their exit status.

## In the spec

- [Test packages](https://github.com/zane-lang/spec/blob/main/spec/packages.md#7-test-packages)
- [Test dependencies](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#21-manifest-zanecoda)
- [`zane test`](https://github.com/zane-lang/zane/blob/main/docs/design/cli.md#25-zane-test-test---build-argument-a-----args)
