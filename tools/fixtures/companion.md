# Companion files

```c file=half.h
#include <zane_ffi.h>

int64_t half(int64_t x);
```

```c file=src/half.c
#include "half.h"

int64_t half(int64_t x) { return x / HALF_DIVISOR; }
```

```coda file=c.coda
c [
    setting  value           target
    source   src/*.c         *
    include  .               *
    define   HALF_DIVISOR=2  *
]
```

```zane
package demo;

import core$;

@primitives$I64 _half(x @primitives$I64) foreign "half";

Unit main() {
	console Console(@program$console);
	console!print(String(Int(_half(Int(84)))));
	return Unit();
}
```

```output
42
```
