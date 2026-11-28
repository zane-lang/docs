# Types

This page covers structs, their constructors, value semantics, operators on your own types, and type aliases.

## Structs

A `struct` groups named fields. The type body holds only fields; the type's
constructors and methods are declared next to the type, at package scope:

```zane
package hello;

import core$;

type Vec = struct {
	x Int;
	y Int;
}
Vec(x Int, y Int) => init{ x; y; }

String show(this Vec) {
	sx String = String(this.x);
	sy String = String(this.y);
	return String("(\%sx, \%sy)");
}

Unit main() {
	console Console(@program$console);
	a Vec(Int(1), Int(2));
	a.y = a.y + 5;
	console!print(a:show());
	console!print(String(a.x));
	return Unit();
}
```

```output
(1, 7)
1
```

A **constructor** is a function named after its type. It returns the new
value with `init{ … }`, which sets every field: `init{ x = Int(0); }` sets `x`
to a value, and `init{ x; }` is short for `init{ x = x; }`, taking the
parameter of the same name. `a Vec(Int(1), Int(2));` declares `a` by calling
the constructor; `a Vec = Vec(Int(1), Int(2));` is an equivalent declaration.

A field whose name starts with `_` is private to the package that declares the
type.

## Values are copied

A plain `struct` is a **value type**: assigning it or storing it copies the
whole value, so two symbols never share a value.

```zane
package hello;

import core$;

type Vec = struct {
	x Int;
	y Int;
}
Vec(x Int, y Int) => init{ x; y; }

Unit main() {
	console Console(@program$console);
	a Vec(Int(1), Int(2));
	b Vec = a;
	b.x = Int(10);
	console!print(String(a.x) + " " + String(b.x));
	return Unit();
}
```

```output
1 10
```

A value type may hold only other value types. A type that needs identity, so
that other code can refer to one particular instance, is declared with `#`:
`type Node = #struct { … }` is a **reference type**, which has one owner and
is moved rather than copied. [Memory](memory.md) covers reference types.

## More ways to construct

A type can have several constructors. A **field constructor** lists fields in
braces, optionally with defaults, and the call names the fields it sets. A
**named constructor** adds an identifier after the type:

```zane
package hello;

import core$;

type Weapon = struct {
	name String;
	damage Int;
	rate Float;
}
Weapon{
	name String("Pistol");
	damage Int(10);
	rate Float(1.0);
} {
	return init{ name; damage; rate; }
}
Weapon.fists() => init{ name = String("Fists"); damage = Int(1); rate = Float(2.0); }

Unit main() {
	console Console(@program$console);
	pistol Weapon{}
	rifle Weapon{ name = String("Rifle"); damage = Int(40); }
	bare Weapon.fists();
	console!print(pistol.name + " " + String(pistol.damage));
	console!print(rifle.name + " " + String(rifle.damage));
	console!print(bare.name + " " + String(bare.rate));
	return Unit();
}
```

```output
Pistol 10
Rifle 40
Fists 2
```

A statement that ends in `}`, like `pistol Weapon{}`, is closed by that brace
and takes no `;`.

A constructor marked `implicit` and taking one argument is a conversion: when
an argument has the constructor's parameter type and the function expects the
constructor's type, the compiler calls the constructor for you. That is how
`core` turns the literal `"text"`, whose type is the concept
`@concepts$String`, into a `String` when you pass it
([Intrinsics and concepts](intrinsics.md#concepts-what-a-literal-is)), and
implicit constructors work the same way for your own types:

```zane
package hello;

import core$;

type Meters = struct {
	value Float;
}
implicit Meters(value Float) => init{ value; }

Meters twice(m Meters) => Meters(m.value * 2.0);

Unit main() {
	console Console(@program$console);
	d Meters = twice(Float(1.25));
	console!print(String(d.value));
	return Unit();
}
```

```output
2.5
```

Conversions happen only at arguments, never at a declaration, an assignment
or a `return`, and never more than one at a time.

## Operators

Operators are functions whose name is the operator. Declaring `+`, `~`, `==`
and `<` for a type also gives it `-`, `~=`, `>`, `<=` and `>=`, which are
derived from them:

```zane
package hello;

import core$;

type Vec = struct {
	x Int;
	y Int;
}
Vec(x Int, y Int) => init{ x; y; }

Vec +(left Vec, right Vec) => Vec(left.x + right.x, left.y + right.y);
Vec ~(v Vec) => Vec(~v.x, ~v.y);
Bool ==(left Vec, right Vec) => left.x == right.x and left.y == right.y;

Unit main() {
	console Console(@program$console);
	a Vec(Int(1), Int(2));
	b Vec(Int(10), Int(20));
	c Vec = b - a;
	console!print(String(c.x) + " " + String(c.y));
	same Bool = if(a + c == b) {
		console!print("a + c == b");
	}
	return Unit();
}
```

```output
9 18
a + c == b
```

The operators are a fixed set (`~`, `*`, `/`, `+`, `==`, `<`, `and`, `or`,
and the operators derived from them), with fixed precedence. An operator is
declared in the package of one of its operand types, so importing a package
never changes the meaning of `a + b`.

## `type` and `alias`

`type` declares a new, distinct type: a `Meters` is not a `Float`, even
though a `Meters` holds a `Float`. `alias` gives another name to an existing type, and the two
names are interchangeable:

```zane
package hello;

import core$;

alias Score = Int;

Score bonus(s Score) => s + 10;

Unit main() {
	console Console(@program$console);
	points Int(5);
	console!print(String(bonus(points)));
	return Unit();
}
```

```output
15
```

## In the spec

- [Types](https://github.com/zane-lang/spec/blob/main/spec/types.md):
  [value and reference types](https://github.com/zane-lang/spec/blob/main/spec/types.md#2-value-and-reference-types),
  [constructors](https://github.com/zane-lang/spec/blob/main/spec/types.md#3-constructors-and-initialization),
  [implicit constructors](https://github.com/zane-lang/spec/blob/main/spec/types.md#4-implicit-constructors)
  and [`type` and `alias`](https://github.com/zane-lang/spec/blob/main/spec/types.md#5-type-definitions-and-aliases)
- [Operators](https://github.com/zane-lang/spec/blob/main/spec/operators.md)
- The stories behind them: [types](https://github.com/zane-lang/spec/blob/main/stories/types.md)
  and [operators](https://github.com/zane-lang/spec/blob/main/stories/operators.md)
