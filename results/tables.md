Machine: Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1. Every value is the median of 3 runs of `llama-lookup-stats`.

### Drafting time per drafted token (µs)

| corpus | baseline | nocopy | flatmap | baseline / nocopy | nocopy / flatmap |
|--------|----------|--------|---------|-------------------|------------------|
| none   | 8.54     | 1.89   | 0.74    | 4.52x             | 2.56x            |
| 25 MB  | 45.61    | 4.12   | 3.82    | 11.08x            | 1.08x            |
| 50 MB  | 59.73    | 4.42   | 4.20    | 13.52x            | 1.05x            |
| 100 MB | 83.46    | 4.64   | 4.74    | 17.99x            | 0.98x            |
| 200 MB | 113.46   | 5.62   | 5.00    | 20.18x            | 1.12x            |
| 541 MB | 165.48   | 6.47   | 5.96    | 25.58x            | 1.09x            |

### Static cache load time (ms)

| corpus | baseline | nocopy | flatmap | baseline / nocopy | nocopy / flatmap |
|--------|----------|--------|---------|-------------------|------------------|
| 25 MB  | 438      | 474    | 241     | 0.92x             | 1.97x            |
| 50 MB  | 904      | 845    | 488     | 1.07x             | 1.73x            |
| 100 MB | 1327     | 1297   | 989     | 1.02x             | 1.31x            |
| 200 MB | 2464     | 2517   | 1921    | 0.98x             | 1.31x            |
| 541 MB | 5485     | 5283   | 4483    | 1.04x             | 1.18x            |

### Static cache memory (MB)

| corpus | baseline | nocopy | flatmap | baseline / nocopy | nocopy / flatmap |
|--------|----------|--------|---------|-------------------|------------------|
| 25 MB  | 215      | 249    | 110     | 0.86x             | 2.27x            |
| 50 MB  | 399      | 451    | 184     | 0.89x             | 2.45x            |
| 100 MB | 705      | 743    | 357     | 0.95x             | 2.08x            |
| 200 MB | 1215     | 1284   | 650     | 0.95x             | 1.98x            |
| 541 MB | 2573     | 2652   | 1341    | 0.97x             | 1.98x            |

### Accepted drafted tokens (%)

| corpus | baseline | nocopy | flatmap | baseline / nocopy | nocopy / flatmap |
|--------|----------|--------|---------|-------------------|------------------|
| none   | 15.363   | 15.513 | 15.591  | 0.99x             | 0.99x            |
| 25 MB  | 17.639   | 17.679 | 17.710  | 1.00x             | 1.00x            |
| 50 MB  | 18.181   | 18.213 | 18.228  | 1.00x             | 1.00x            |
| 100 MB | 18.789   | 18.829 | 18.837  | 1.00x             | 1.00x            |
| 200 MB | 19.227   | 19.260 | 19.250  | 1.00x             | 1.00x            |
| 541 MB | 19.896   | 19.948 | 19.931  | 1.00x             | 1.00x            |

### Static cache files

| cache_format | corpus | file (MB) | peak memory of llama-lookup-create (MB) |
|--------------|--------|-----------|-----------------------------------------|
| legacy       | 25 MB  | 50        | 2082                                    |
| legacy       | 50 MB  | 85        | 3451                                    |
| legacy       | 100 MB | 143       | 5919                                    |
| legacy       | 200 MB | 239       | 8625                                    |
| legacy       | 541 MB | 485       | 10254                                   |
