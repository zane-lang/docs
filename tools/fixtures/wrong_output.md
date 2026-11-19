# Wrong output

```zane
package demo;

import core$;

Unit main() {
	console Console(@program$console);
	console!print("hi");
	return Unit();
}
```

```output
bye
```
