# Generics

This page covers types and functions that take type parameters or number parameters, and the container types built on them.

## Generic types

A type can take parameters in `< >` after its name. `Type` marks a parameter
that ranges over types:

```zane
package hello;

import core$;

type Pair<A Type, B Type> = struct {
	first A;
	second B;
}
Pair<A, B>(first A Type, second B Type) => init{ first; second; }

B second(this Pair<A Type, B Type>) => this.second;

Unit main() {
	console Console(@program$console);
	p Pair(String("answer"), Int(42));
	console!print(p.first + " = " + String(p:second()));
	q Pair<Int, Bool> = Pair(Int(1), Bool(true));
	console!print(String(q.first));
	return Unit();
}
```

```output
answer = 42
1
```

`Pair<String, Int>` and `Pair<Int, Bool>` are two separate concrete types,
each with its own fixed layout.

A function, method or constructor has no `< >` header of its own. It
introduces a parameter where the parameter first appears with its concept:
`first A Type` introduces `A`, and after that `A` is written bare. The call
writes no `< >` either: `Pair(String("answer"), Int(42))` infers `A` and `B`
from the arguments.

## Generic functions

A generic function is checked for each type it is used with, so its body can
use any operation those types have:

```zane
package hello;

import core$;

T largest(values List<T Type>) {
	best T = values[Int(1)];
	i Int(2);
	i!to(values:size()) {
		if(best < values[i]) {
			best = values[i];
		}
	}
	return best;
}

Unit main() {
	console Console(@program$console);
	ints List<Int> = List(Int);
	ints!push(Int(4));
	ints!push(Int(9));
	ints!push(Int(2));
	console!print(String(largest(ints)));

	floats List<Float> = List(Float);
	floats!push(Float(0.5));
	floats!push(Float(1.5));
	console!print(String(largest(floats)));
	return Unit();
}
```

```output
9
1.5
```

Calling it with a list of a type that has no `<` is a compile-time error that
names both the `<` and the call that asked for it.

## Passing a type as an argument

A parameter of type `Type` takes a type as an ordinary argument. That is how
an empty container is made: `List(Int)` is an empty `List<Int>`, because
nothing else would tell the constructor what the elements are.

```zane
package hello;

import core$;

type Stack<T Type> = struct {
	items List<T>;
}
Stack<T>(T Type) => init{ items = List(T); }

Unit push(this Stack<T Type>, item T) mut {
	this.items!push(item);
	return Unit();
}
T pop(this Stack<T Type>) mut => this.items!remove(this.items:size());
Int size(this Stack<T Type>) => this.items:size();

Unit main() {
	console Console(@program$console);
	s Stack(String);
	s!push("first");
	s!push("second");
	top String = s!pop();
	console!print(top + ", " + String(s:size()) + " left");
	return Unit();
}
```

```output
second, 1 left
```

## Number parameters

A parameter written `n @concepts$Int` ranges over whole numbers known at
compile time. `Array<T, n>` uses one for its length, which is part of its
type:

```zane
package hello;

import core$;

Int total(values Array<Int, n @concepts$Int>) {
	sum Int(0);
	i Int(1);
	i!to(values:size()) {
		sum = sum + values[i];
	}
	return sum;
}

Unit main() {
	console Console(@program$console);
	three Array<Int, 3> = Array([Int(1), Int(2), Int(3)]);
	five Array<Int, 5> = Array([Int(1), Int(1), Int(1), Int(1), Int(1)]);
	console!print(String(total(three)) + " " + String(total(five)));
	return Unit();
}
```

```output
6 5
```

## Containers

`core` has four containers, all generic over their element type:

| Type | Size | Elements |
|---|---|---|
| `Array<T, n>` | fixed, `n` | values, copied with the array |
| `List<T>` | grows | values, copied with the list |
| `ArrayRef<T, n>` | fixed, `n` | elements that stay in place; the container is a reference type |
| `ListRef<T>` | grows | owners, moved in and out |

`List` and `Array` are value types themselves: assigning a list copies it
with its elements. `ListRef` holds owners of reference types, which
[Memory](memory.md) explains. The [`core`
library](https://github.com/zane-lang/std/blob/main/docs/core/containers.md) pages list
their methods.

## In the spec

- [Generics](https://github.com/zane-lang/spec/blob/main/spec/generics.md):
  [types as templated functions](https://github.com/zane-lang/spec/blob/main/spec/generics.md#2-types-as-templated-functions),
  [the parameter model](https://github.com/zane-lang/spec/blob/main/spec/generics.md#3-the-parameter-model),
  [calls](https://github.com/zane-lang/spec/blob/main/spec/generics.md#5-constructor-and-function-calls-)
  and [container primitives](https://github.com/zane-lang/spec/blob/main/spec/generics.md#8-container-storage-primitives)
- The story behind it: [generics](https://github.com/zane-lang/spec/blob/main/stories/generics.md)
