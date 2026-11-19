# Enums, variants and `match`

This page covers enums, variants (sum types), `match`, reading one case of a variant, and enum maps.

## Enums

An `enum` is a closed set of named values that carry nothing else:

```zane
package hello;

import core$;

type Color = enum [ red, green, blue ];

String name(c Color) => match (c) {
	red => String("red");
	green => String("green");
	blue => String("blue");
}

Unit main() {
	console Console(@program$console);
	c Color = Color.green;
	console!print(name(c));
	console!print(name(Color.blue));
	return Unit();
}
```

```output
green
blue
```

A member is written through its type: `Color.green`. `match` picks the arm
for the value it is given. It has no default arm, so every member must be
covered, and adding a member later makes every `match` that misses it an
error. One arm may cover several members by listing them in `[ ]`.

## Variants

A `variant` is a sum type: each value is one of several **cases**, and each
case carries a payload of its own type. Its body looks like a struct's, with
cases where a struct has fields. A value is built by naming a case and passing
its payload:

```zane
package hello;

import core$;

type Size = struct {
	w Float;
	h Float;
}
Size(w Float, h Float) => init{ w; h; }

type Shape = variant {
	circle Float;
	rect Size;
	empty Unit;
}

Float area(this Shape) => match (this) {
	r circle => r * r * 3.0;
	s rect => s.w * s.h;
	empty => Float(0.0);
}

Unit main() {
	console Console(@program$console);
	shapes List<Shape> = List(Shape);
	shapes!push(Shape.circle(Float(1.0)));
	shapes!push(Shape.rect(Size(Float(2.0), Float(3.0))));
	shapes!push(Shape.empty(Unit()));
	i Int(1);
	i!to(shapes:size()) {
		console!print(String(shapes[i]:area()));
	}
	return Unit();
}
```

```output
3
6
0
```

In an arm, the name before the case (`r circle`) binds that case's payload.
An arm's body is an expression ending in `;`, or a block in braces that
returns:

```zane fragment
Float area(this Shape) => match (this) {
	r circle {
		small Bool = if(r < 1.0) {
			return Float(0.0);
		}
		return r * r * 3.0;
	}
	s rect => s.w * s.h;
	empty => Float(0.0);
}
```

The compiler writes the scrutinee in parentheses, `match (shape)`, where the
spec writes it bare (compiler
[divergence 4](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#4-a-match-parenthesizes-its-scrutinee-list)).

## Matching several values

A `match` may take several scrutinees, and each arm then names a case of
each. This replaces nested matches when the answer depends on a combination:

```zane
package hello;

import core$;

type Light = enum [ red, yellow, green ];
type Mode = enum [ normal, night ];

String action(light Light, mode Mode) => match (light, mode) {
	red, [normal, night] => String("stop");
	yellow, normal => String("slow down");
	yellow, night => String("proceed with care");
	green, [normal, night] => String("go");
}

Unit main() {
	console Console(@program$console);
	console!print(action(Light.yellow, Mode.night));
	console!print(action(Light.green, Mode.normal));
	return Unit();
}
```

```output
proceed with care
go
```

## Reading one case

`shape.circle` reads the `circle` payload directly. That fails when another
case is live, so the read takes a handler, as any call that can fail does:
`??` gives a value to use instead ([Errors](errors.md)).

```zane
package hello;

import core$;

type Reading = variant {
	celsius Float;
	missing Unit;
}

Unit main() {
	console Console(@program$console);
	good Reading = Reading.celsius(Float(21.5));
	bad Reading = Reading.missing(Unit());
	console!print(String(good.celsius ?? Float(0.0)));
	console!print(String(bad.celsius ?? Float(0.0)));
	return Unit();
}
```

```output
21.5
0
```

## Recursive variants

A variant may contain itself. Here a `Countdown` is either `done` or one
`more` step before another `Countdown`:

```zane
package hello;

import core$;

type Countdown = variant {
	more Countdown;
	done Unit;
}

Int length(c Countdown) => match (c) {
	rest more => length(rest) + 1;
	done => Int(0);
}

Unit main() {
	console Console(@program$console);
	three Countdown = Countdown.more(Countdown.more(Countdown.more(Countdown.done(Unit()))));
	console!print(String(length(three)));
	return Unit();
}
```

```output
3
```

## Enum maps

An **enum map** gives every member of an enum a value, read like a field.
Adding a member makes the map incomplete until it gets its value too:

```zane
package hello;

import core$;

type Color = enum [ red, green, blue ];

Color.hex String {
	red = "#ff0000";
	green = "#00ff00";
	blue = "#0000ff";
}

Unit main() {
	console Console(@program$console);
	c Color = Color.blue;
	console!print(c.hex);
	console!print(Color.red.hex);
	return Unit();
}
```

```output
#0000ff
#ff0000
```

## In the spec

- [Algebraic data types](https://github.com/zane-lang/spec/blob/main/spec/adt.md):
  [enums](https://github.com/zane-lang/spec/blob/main/spec/adt.md#2-enums),
  [variants](https://github.com/zane-lang/spec/blob/main/spec/adt.md#3-variants),
  [`match`](https://github.com/zane-lang/spec/blob/main/spec/adt.md#5-matching-a-variant)
  and [enum maps](https://github.com/zane-lang/spec/blob/main/spec/adt.md#6-enum-maps)
- Where the compiler differs: divergences
  [1](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#1-a-match-arms-terminator-follows-its-body),
  [4](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#4-a-match-parenthesizes-its-scrutinee-list)
  and [9](https://github.com/zane-lang/compiler/blob/main/docs/spec-divergences.md#9-a-case-is-not-a-type)
- The story behind it: [algebraic data types](https://github.com/zane-lang/spec/blob/main/stories/adt.md)
