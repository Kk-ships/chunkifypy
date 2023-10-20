# Usage
```python
from ChunkifyPy.chunkify import chunkify
long_list = list(range(0, 10**6))  # 1 million elements list
# create a generator of elements where each chunk is of size 0.01 MB (10 KB) or less
result = chunkify(long_list, 0.01)
for chunk in result:
    print(chunk)
```
