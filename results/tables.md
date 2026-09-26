Machine: Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1. Every value is the median of 3 runs of `llama-lookup-stats`.

### Drafting time per drafted token (µs)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| none   | 8.54     | 1.89   | 4.52x             |
| 25 MB  | 45.61    | 4.12   | 11.08x            |
| 50 MB  | 59.73    | 4.42   | 13.52x            |
| 100 MB | 83.46    | 4.64   | 17.99x            |
| 200 MB | 113.46   | 5.62   | 20.18x            |
| 541 MB | 165.48   | 6.47   | 25.58x            |

### Static cache load time (ms)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| 25 MB  | 438      | 474    | 0.92x             |
| 50 MB  | 904      | 845    | 1.07x             |
| 100 MB | 1327     | 1297   | 1.02x             |
| 200 MB | 2464     | 2517   | 0.98x             |
| 541 MB | 5485     | 5283   | 1.04x             |

### Static cache memory (MB)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| 25 MB  | 215      | 249    | 0.86x             |
| 50 MB  | 399      | 451    | 0.89x             |
| 100 MB | 705      | 743    | 0.95x             |
| 200 MB | 1215     | 1284   | 0.95x             |
| 541 MB | 2573     | 2652   | 0.97x             |

### Accepted drafted tokens (%)

| corpus | baseline | nocopy | baseline / nocopy |
|--------|----------|--------|-------------------|
| none   | 15.363   | 15.513 | 0.99x             |
| 25 MB  | 17.639   | 17.679 | 1.00x             |
| 50 MB  | 18.181   | 18.213 | 1.00x             |
| 100 MB | 18.789   | 18.829 | 1.00x             |
| 200 MB | 19.227   | 19.260 | 1.00x             |
| 541 MB | 19.896   | 19.948 | 1.00x             |

### Static cache files

| cache_format | corpus | file (MB) | peak memory of llama-lookup-create (MB) |
|--------------|--------|-----------|-----------------------------------------|
| legacy       | 25 MB  | 50        | 2082                                    |
| legacy       | 50 MB  | 85        | 3451                                    |
| legacy       | 100 MB | 143       | 5919                                    |
| legacy       | 200 MB | 239       | 8625                                    |
| legacy       | 541 MB | 485       | 10254                                   |
