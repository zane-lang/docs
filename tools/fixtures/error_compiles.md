# Error fence that compiles

```zane error
// error: nothing
package demo;

import core$;

Unit main() {
	console Console(@program$console);
	console!print("hi");
	return Unit();
}
```
