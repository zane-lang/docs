# Packages

This page covers how code is split into packages, how one package imports another, and what a package keeps private.

## A package is a directory

Every `.zn` file starts by naming its package, and a package is the directory
its files are in. All files of a package form one unit: their declarations
can refer to each other in any order, with no imports between them.

A project keeps its packages in three directories:

```text
lib/geometry/        a library package, `geometry`, that others can import
lib/geometry/shapes/ a subpackage of it, reached through `geometry`
bin/viewer/          a program package: it declares `main` and builds a program
test/geometry/       a test package for `geometry`; its files say `package test;`
```

A program or test package is the root of its build: it alone declares `main`
and reaches `@program$`. Library packages are compiled into whatever program
uses them.

## Imports

An import is per file, and the form it takes decides how the file writes the
imported names:

| Import | Names are written |
|---|---|
| `import math;` | `math$sqrt` |
| `import math as m;` | `m$sqrt` |
| `import math$sqrt;` | `sqrt` |
| `import math$sqrt as root;` | `root` |
| `import math$[sqrt, pow];` | `sqrt`, `pow` |
| `import math$;` | every public name, unqualified |

`$` separates a package from its member everywhere, including the compiler's
own names such as `@primitives$String`. Keeping the prefix shows where a name
comes from:

```zane
package hello;

import core$;
import math;

Unit main() {
	console Console(@program$console);
	console!print(String(math$sqrt(Float(16.0))));
	console!print(String(math$max(Int(3), Int(7))));
	return Unit();
}
```

```output
4
7
```

and naming the members brings in just those:

```zane
package hello;

import core$;
import math$[sqrt, max];

Unit main() {
	console Console(@program$console);
	console!print(String(sqrt(Float(16.0))));
	console!print(String(max(Int(3), Int(7))));
	return Unit();
}
```

```output
4
7
```

Each imported name has one spelling in a file, so `import math;` and
`import math$sqrt;` together are an error, and two imports that bring in the
same bare name collide at the import. Imports add names, never meanings: an
operator such as `+` is always declared in the package of one of its operand
types, so no import can change what an expression means.

## Privacy

A declaration whose name starts with `_` is private to its package, and so is
a field whose name does: code in the same package can use it, code elsewhere
cannot. Everything else is public. A library package whose own name starts
with `_` can be imported only inside its project.

```zane fragment
package geometry;

import core$;

type Circle = struct {
	_radius Float;
}
Circle(radius Float) => init{ _radius = radius; }

Float area(this Circle) => _square(this._radius) * 3.14159;

Float _square(x Float) => x * x;
```

Another package can build a `Circle` and call `area` on it, but not read
`_radius` or call `_square`.

## Dependencies

A package from another project is imported the same way, once the project
depends on it: `zane add <url>` records the dependency and prints the
`import` lines for its packages. [Projects](../guides/projects.md) covers the
manifest and versions.

## In the spec

- [Packages](https://github.com/zane-lang/spec/blob/main/spec/packages.md):
  [projects and packages](https://github.com/zane-lang/spec/blob/main/spec/packages.md#2-projects-and-packages),
  [imports](https://github.com/zane-lang/spec/blob/main/spec/packages.md#3-imports-and-member-access),
  [visibility](https://github.com/zane-lang/spec/blob/main/spec/packages.md#4-package-visibility)
  and [test packages](https://github.com/zane-lang/spec/blob/main/spec/packages.md#7-test-packages)
- [Dependencies](https://github.com/zane-lang/spec/blob/main/spec/dependencies.md)
- The story behind it: [packages](https://github.com/zane-lang/spec/blob/main/stories/packages.md)
