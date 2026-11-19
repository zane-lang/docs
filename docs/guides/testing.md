# Testing

This guide covers test packages: where they live, what they can import, and how `zane test` runs them.

## Test packages

Tests live in `test/`. Each directory directly in it is a **test package**,
and every one of its files starts with `package test;`. A test package is a
program: it declares `main`, and `zane test` builds and runs it.

```text
lib/shapes/shapes.zn       the library package `shapes`
test/shapes/main.zn        a test package for it
lib/shapes/solid/          a subpackage, `shapes`'s `solid`
test/shapes/solid/main.zn  its own test package, mirroring the path under lib/
```

A test package uses a library as any other user does: it imports it and
reaches only its public names. It may import every library package of its
project, including private ones whose names start with `_`, and the packages
of `deps` and `test-deps`. Only test packages may import `test-deps`.
[Your first project](../first-project.md#a-library-and-its-tests) builds one
step by step.

## Running tests

```sh
zane test                 # every test package
zane test shapes          # the one in test/shapes/
zane test shapes -- -v    # pass arguments to it
```

Each test package is built and run the way `zane run` runs a program, as the
root of its own build, with the project's library packages compiled from
`lib/`. `zane test` names each package as it starts, then says how many
passed:

```text
$ zane test
Testing test/edge/
index out of range
Testing test/shapes/
ok   area
ok   not square
1 of 2 test packages failed: edge
```

A test package fails when its program exits with a status other than 0, as
one that stops on an index out of range does. `zane test` then exits with 1.
Run on one package, it exits with that package's status.

## Writing checks

How a test reports is up to the test package. A small helper that prints each
check is enough to start with. As `test/shapes/main.zn`:

```zane fragment
package test;

import core$;

Unit check(this Console, name String, ok Bool) mut {
	passed Bool = if(ok) {
		this!print("ok   " + name);
	}
	passed:else() {
		this!print("FAIL " + name);
	}
	return Unit();
}

Unit main() {
	console Console(@program$console);
	values List<Int> = List(Int);
	values!push(Int(3));
	console!check("one element", values:size() == 1);
	console!check("first is 3", values[Int(1)] == 3);
	return Unit();
}
```

```text
$ zane test shapes
ok   one element
ok   first is 3
```

A testing library added with `zane add <url> --test` can provide richer
checks; `zane` only runs the programs and reads their exit status.

## In the spec

- [Test packages](https://github.com/zane-lang/spec/blob/main/spec/packages.md#7-test-packages)
- [Test dependencies](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md#21-manifest-zanecoda)
- [`zane test`](https://github.com/zane-lang/zane/blob/main/docs/design/cli.md#25-zane-test-test----args)
