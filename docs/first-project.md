# Your first project

This page creates a program, runs it, adds the standard library, and then makes a library with tests.

It assumes `zane` and a compiler are installed ([Install Zane](install.md)).

## Create and run a program

```sh
zane init hello --yes
cd hello
zane run
```

`zane init` asks a few questions (the package name, library or application,
whether to start a Git repository); `--yes` accepts every default. It creates:

```text
hello/
  zane.coda          the manifest: compiler version and dependencies
  zane-lock.coda     the lock file: the exact commits those resolve to
  bin/hello/main.zn  the program
  .gitignore         lists out/, where builds go
```

`zane run` builds the program and runs it, printing `hello world`. The
generated `main.zn` writes everything out with the compiler's built-in names,
such as `@primitives$String`, because a new project has no dependencies yet.

## Add the standard library

The types you normally write with, such as `Int`, `String`, `List`, and even
`if`, come from the `core` package of [`std`](https://github.com/zane-lang/std).
Add it:

```sh
zane add https://github.com/zane-lang/std --from-source
```

`std` publishes no prebuilt objects, so `--from-source` has `zane` compile it
in your project. Now replace `bin/hello/main.zn` with:

```zane
package hello;

import core$;

Unit main() {
	console Console(@program$console);
	name String = String("Zane");
	console!print("Hello, \%name!");

	total Int = Int(0);
	i Int = Int(1);
	i!to(Int(10)) {
		total = total + i;
	}
	console!print("1 + 2 + ... + 10 = " + String(total));
	return Unit();
}
```

```output
Hello, Zane!
1 + 2 + ... + 10 = 55
```

and run it again with `zane run`. The first line of every source file names
its package: here `hello`, the directory under `bin/`. `import core$;` makes
the names of `core` usable without a prefix. `main` is where the program
starts. `Console(@program$console)` wraps the program's console, which the
program receives from the language rather than reaching for a global, so that
code you never hand it to cannot print ([Effects](tour/effects.md)).
`"\%name"` puts a value into a string.

The [language tour](tour/README.md) explains each of these in turn.

## The commands you use most

| Command | What it does |
|---|---|
| `zane check` | Type-checks the project without building it: the fast loop while editing |
| `zane run` | Builds a program and runs it; arguments after `--` go to the program |
| `zane build` | Builds every program in `bin/`, optimized, into `out/host/` |
| `zane test` | Builds and runs every test package in `test/` |
| `zane clean` | Deletes `out/` |

They work from any directory inside the project. [The `zane`
command](reference/cli.md) lists them all.

## A library and its tests

A **library** keeps its code in `lib/` and its tests in `test/`:

```sh
zane init shapes --lib --yes
cd shapes
zane add https://github.com/zane-lang/std --from-source
```

This creates `lib/shapes/shapes.zn`, the library package `shapes`, and
`test/shapes/main.zn`, a test package for it. Put this in
`lib/shapes/shapes.zn`:

```zane fragment
package shapes;

import core$;

/// A rectangle, by its width and height.
type Rect = struct {
	width Int;
	height Int;
}
Rect(width Int, height Int) => init{ width; height; }

Int area(this Rect) => this.width * this.height;

/// Whether the rectangle is a square.
Bool isSquare(this Rect) => this.width == this.height;
```

Every declaration is public unless its name starts with `_`. A test package
uses the library as any other user does, by importing it. Put this in
`test/shapes/main.zn`; its first line is always `package test;`:

```zane fragment
package test;

import core$;
import shapes$;

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
	r Rect(Int(3), Int(4));
	console!check("area", r:area() == 12);
	console!check("not square", ~r:isSquare());
	return Unit();
}
```

Then run the tests:

```text
$ zane test
Testing test/shapes/
ok   area
ok   not square
1 test package passed.
```

A project can hold library packages, programs and tests together: add a
directory under `bin/` and it is a program. [Testing](guides/testing.md) says
more about test packages, and [Projects](guides/projects.md) about the files
`zane` keeps.
