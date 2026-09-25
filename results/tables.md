Machine: Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1. Every value is the median of 3 runs of `llama-lookup-stats`.

### Drafting time per drafted token (µs)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| none   | 9.35     | 2.09   | 4.48x             |
| 25 MB  | 49.88    | 4.25   | 11.72x            |
| 50 MB  | 63.32    | 4.58   | 13.84x            |
| 100 MB | 90.63    | 5.46   | 16.60x            |
| 200 MB | 117.22   | 6.15   | 19.05x            |
| 541 MB | 166.99   | 6.83   | 24.45x            |

### Static cache load time (ms)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| 25 MB  | 433      | 434    | 1.00x             |
| 50 MB  | 917      | 856    | 1.07x             |
| 100 MB | 1344     | 1333   | 1.01x             |
| 200 MB | 2409     | 2533   | 0.95x             |
| 541 MB | 5137     | 5200   | 0.99x             |

### Static cache memory (MB)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| 25 MB  | 219      | 254    | 0.86x             |
| 50 MB  | 404      | 455    | 0.89x             |
| 100 MB | 709      | 747    | 0.95x             |
| 200 MB | 1220     | 1290   | 0.95x             |
| 541 MB | 2580     | 2654   | 0.97x             |

### Accepted drafted tokens (%)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| none   | 15.630   | 15.788 | 0.99x             |
| 25 MB  | 18.082   | 18.120 | 1.00x             |
| 50 MB  | 18.679   | 18.736 | 1.00x             |
| 100 MB | 19.339   | 19.402 | 1.00x             |
| 200 MB | 19.819   | 19.848 | 1.00x             |
| 541 MB | 20.532   | 20.587 | 1.00x             |

### Static cache files

| cache_format | corpus | file (MB) | peak memory of llama-lookup-create (MB) |
|--------------|--------|-----------|-----------------------------------------|
| legacy       | 25 MB  | 50        | 1572                                    |
| legacy       | 50 MB  | 85        | 2492                                    |
| legacy       | 100 MB | 143       | 4042                                    |
| legacy       | 200 MB | 239       | 7227                                    |
| legacy       | 541 MB | 485       | 10339                                   |
