# Memory

This page covers how Zane manages memory without a garbage collector: value types, reference types and their owners, references, moves, and when things are destroyed.

## Two kinds of types

Every type is either a value type or a reference type, and which of the two it
is determines how its values are stored and passed.

- A **value type** (`struct`, `variant`, `enum`, `Int`, `String`, `List`, …)
  has no identity. Assigning a value of a value type copies it deeply, so no
  two symbols ever share a value. [Types](types.md#values-are-copied) shows this.
- A **reference type** (marked `#`: `#struct`, `#variant`, and `ListRef`,
  `ArrayRef`) has identity. Each object has exactly one **owner**, and other
  code reaches the object through **references**, written `&T`, which never
  own the object.

There is no garbage collector and no reference counting. The program text
fixes the point at which each object is destroyed: when the scope of its owner
ends, when its owner is overwritten, or when it is removed from a `ListRef`
without being moved out. Every scope gets its own memory region, which is
released as a whole when the scope ends.

## Owners and references

A symbol of a reference type owns its object. Storing the owner in an `&` slot
makes a reference to the object:

```zane
package hello;

import core$;

type Account = #struct {
	owner String;
	balance Int;
}
Account(owner String, balance Int) => init{ owner; balance; }

Unit deposit(this Account, amount Int) mut {
	this.balance = this.balance + amount;
	return Unit();
}

/// A teller holds a reference to the account at the teller's desk.
type Teller = #struct {
	desk &Account;
}
Teller(desk &Account) => init{ desk; }

Unit main() {
	console Console(@program$console);
	alice Account(String("Alice"), Int(100));
	view &Account = alice;
	teller Teller(alice);

	alice!deposit(Int(5));
	console!print(String(view.balance));
	console!print(teller.desk.owner + " has " + String(teller.desk.balance));
	return Unit();
}
```

```output
105
Alice has 105
```

`view` and `teller.desk` see the deposit because they refer to the same
object as `alice`. A reference is used exactly like its owner, with no
dereferencing syntax, and it is never null. A value type may not hold an
`&`, because values are copied freely, and the copies would carry the
reference to places that outlive the owner:

```zane error
// error: is a value type, so its member
package hello;

import core$;

type Account = #struct {
	balance Int;
}

type Card = struct {
	account &Account;
}

Unit main() {
	return Unit();
}
```

## A reference never outlives its owner

The compiler checks every store of a reference against the scope of the owner
it refers to. A reference may not be stored anywhere that lives longer than
its owner, so a reference can never dangle:

```zane error
// error: whose block ends before
package hello;

import core$;

type Account = #struct {
	balance Int;
}
Account(balance Int) => init{ balance; }

Unit main() {
	outer Account(Int(1));
	view &Account = outer;
	do() {
		inner Account(Int(2));
		view = inner;
	}
	return Unit();
}
```

The check compares only the scopes in which the owner and the reference are
declared, so no function signature needs lifetime annotations.

## Settled and roaming owners

An owner that may be referenced must never move, or the references would
point at the wrong place. So an owner is either:

- **settled**: a plain symbol such as `alice Account(…)`. It may be
  referenced, and it stays where it is until its scope ends;
- **roaming**: written `^T`, such as `spare ^Account = …`. It may move, and
  nothing refers to it.

Moving a roaming owner into a settled place settles it. Elements of a
`ListRef` are roaming, since growing a list moves them:

```zane
package hello;

import core$;

type Account = #struct {
	owner String;
	balance Int;
}
Account(owner String, balance Int) => init{ owner; balance; }

type Bank = #struct {
	accounts ListRef<Account>;
}
Bank() => init{ accounts = ListRef(Account); }

/// The `^Account` parameter takes ownership of the account.
Unit open(this Bank, account ^Account) mut {
	this.accounts!push(account);
	return Unit();
}

/// A reference-type parameter without `^` or `&` borrows its argument for the call.
Int balanceOf(a Account) => a.balance;

Unit main() {
	console Console(@program$console);
	bank Bank();
	bob ^Account = Account(String("Bob"), Int(7));
	bank!open(bob);
	bank!open(Account(String("Cy"), Int(1)));
	console!print(String(bank.accounts:size()) + " accounts");
	console!print(String(balanceOf(bank.accounts[Int(1)])));
	return Unit();
}
```

```output
2 accounts
7
```

Once `bob` has been moved into the bank, it is **spent**: using it again is an
error, until something new is stored in it.

```zane error
// error: is spent until a store refills it
package hello;

import core$;

type Account = #struct {
	balance Int;
}
Account(balance Int) => init{ balance; }

Unit keep(a ^Account) {
	return Unit();
}

Unit main() {
	a ^Account = Account(Int(1));
	keep(a);
	n Int = a.balance;
	return Unit();
}
```

A settled owner cannot be moved at all; an owner that is to move is declared
`^T` from the start:

```zane error
// error: is a settled owner
package hello;

import core$;

type Account = #struct {
	balance Int;
}
Account(balance Int) => init{ balance; }

Unit main() {
	a Account(Int(1));
	b Account = a;
	return Unit();
}
```

## How arguments are passed

How a reference-type argument is passed depends on how the type of its
parameter is written:

| Parameter | Mode | The caller… |
|---|---|---|
| `a Account` | borrow | keeps the object; the callee uses it for the call |
| `a ^Account` | take | hands the object over; a roaming symbol passed here is spent |
| `a &Account` | reference | keeps the object; the callee may store the reference |

A value-type argument is always borrowed, and so is a method's subject. No
other part of the same call may write a value that the call borrows, so a
borrowed argument can't change under the callee. Spawned calls are the only
way to share a value with code that writes it: when a spawned call reads a
value that another spawned call is changing, the read sees a coherent snapshot
of the value, and two reads may see different values
([Concurrency](concurrency.md)).

## In the spec

- [Memory](https://github.com/zane-lang/spec/blob/main/spec/memory.md):
  [ownership and storage](https://github.com/zane-lang/spec/blob/main/spec/memory.md#2-ownership-and-storage),
  [references](https://github.com/zane-lang/spec/blob/main/spec/memory.md#24--is-a-reference-non-owning-storage),
  [passing modes](https://github.com/zane-lang/spec/blob/main/spec/memory.md#29-function-parameters-borrow-take-and-reference)
  and [memory layout](https://github.com/zane-lang/spec/blob/main/spec/memory.md#3-memory-layout)
- [Lifetimes](https://github.com/zane-lang/spec/blob/main/spec/lifetimes.md):
  [scope rules and moves](https://github.com/zane-lang/spec/blob/main/spec/lifetimes.md#1-scope-rules-and-moves)
  and [destruction](https://github.com/zane-lang/spec/blob/main/spec/lifetimes.md#2-lifetime-and-destruction)
- The stories behind them: [memory](https://github.com/zane-lang/spec/blob/main/stories/memory.md)
  and [lifetimes](https://github.com/zane-lang/spec/blob/main/stories/lifetimes.md)
