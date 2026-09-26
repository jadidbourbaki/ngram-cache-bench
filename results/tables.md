Machine: Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1. Every value is the median of 3 runs of `llama-lookup-stats`.

### Drafting time per drafted token (µs)

| corpus | baseline | nocopy | outermap | innervector | constmap | baseline / nocopy | nocopy / outermap | outermap / innervector | innervector / constmap |
|--------|----------|--------|----------|-------------|----------|-------------------|-------------------|------------------------|------------------------|
| none   | 8.54     | 1.89   | 1.72     | 0.76        | 0.75     | 4.52x             | 1.10x             | 2.26x                  | 1.02x                  |
| 25 MB  | 45.61    | 4.12   | 3.94     | 4.16        | 3.79     | 11.08x            | 1.05x             | 0.95x                  | 1.10x                  |
| 50 MB  | 59.73    | 4.42   | 4.11     | 4.51        | 4.16     | 13.52x            | 1.07x             | 0.91x                  | 1.09x                  |
| 100 MB | 83.46    | 4.64   | 4.55     | 5.31        | 4.63     | 17.99x            | 1.02x             | 0.86x                  | 1.15x                  |
| 200 MB | 113.46   | 5.62   | 4.96     | 5.30        | 4.90     | 20.18x            | 1.13x             | 0.94x                  | 1.08x                  |
| 541 MB | 165.48   | 6.47   | 5.81     | 6.50        | 5.86     | 25.58x            | 1.11x             | 0.89x                  | 1.11x                  |

### Static cache load time (ms)

| corpus | baseline | nocopy | outermap | innervector | constmap | baseline / nocopy | nocopy / outermap | outermap / innervector | innervector / constmap |
|--------|----------|--------|----------|-------------|----------|-------------------|-------------------|------------------------|------------------------|
| 25 MB  | 438      | 474    | 288      | 236         | 36       | 0.92x             | 1.65x             | 1.22x                  | 6.53x                  |
| 50 MB  | 904      | 845    | 528      | 502         | 64       | 1.07x             | 1.60x             | 1.05x                  | 7.89x                  |
| 100 MB | 1327     | 1297   | 922      | 933         | 83       | 1.02x             | 1.41x             | 0.99x                  | 11.20x                 |
| 200 MB | 2464     | 2517   | 1648     | 1684        | 128      | 0.98x             | 1.53x             | 0.98x                  | 13.11x                 |
| 541 MB | 5485     | 5283   | 3508     | 3742        | 239      | 1.04x             | 1.51x             | 0.94x                  | 15.67x                 |

### Static cache memory (MB)

| corpus | baseline | nocopy | outermap | innervector | constmap | baseline / nocopy | nocopy / outermap | outermap / innervector | innervector / constmap |
|--------|----------|--------|----------|-------------|----------|-------------------|-------------------|------------------------|------------------------|
| 25 MB  | 215      | 249    | 225      | 91          | 45       | 0.86x             | 1.11x             | 2.47x                  | 2.00x                  |
| 50 MB  | 399      | 451    | 409      | 169         | 77       | 0.89x             | 1.10x             | 2.42x                  | 2.20x                  |
| 100 MB | 705      | 743    | 680      | 252         | 131      | 0.95x             | 1.09x             | 2.70x                  | 1.92x                  |
| 200 MB | 1215     | 1284   | 1190     | 450         | 224      | 0.95x             | 1.08x             | 2.65x                  | 2.01x                  |
| 541 MB | 2573     | 2652   | 2481     | 864         | 463      | 0.97x             | 1.07x             | 2.87x                  | 1.87x                  |

### Accepted drafted tokens (%)

| corpus | baseline | nocopy | outermap | innervector | constmap | baseline / nocopy | nocopy / outermap | outermap / innervector | innervector / constmap |
|--------|----------|--------|----------|-------------|----------|-------------------|-------------------|------------------------|------------------------|
| none   | 15.363   | 15.513 | 15.513   | 15.591      | 15.591   | 0.99x             | 1.00x             | 0.99x                  | 1.00x                  |
| 25 MB  | 17.639   | 17.679 | 17.679   | 17.710      | 17.710   | 1.00x             | 1.00x             | 1.00x                  | 1.00x                  |
| 50 MB  | 18.181   | 18.213 | 18.213   | 18.228      | 18.228   | 1.00x             | 1.00x             | 1.00x                  | 1.00x                  |
| 100 MB | 18.789   | 18.829 | 18.829   | 18.837      | 18.837   | 1.00x             | 1.00x             | 1.00x                  | 1.00x                  |
| 200 MB | 19.227   | 19.260 | 19.260   | 19.250      | 19.250   | 1.00x             | 1.00x             | 1.00x                  | 1.00x                  |
| 541 MB | 19.896   | 19.948 | 19.948   | 19.931      | 19.931   | 1.00x             | 1.00x             | 1.00x                  | 1.00x                  |

### Static cache files

| cache_format | corpus | file (MB) | peak memory of llama-lookup-create (MB) |
|--------------|--------|-----------|-----------------------------------------|
| legacy       | 25 MB  | 50        | 2082                                    |
| legacy       | 50 MB  | 85        | 3451                                    |
| legacy       | 100 MB | 143       | 5919                                    |
| legacy       | 200 MB | 239       | 8625                                    |
| legacy       | 541 MB | 485       | 10254                                   |
| constmap     | 25 MB  | 47        | 2013                                    |
| constmap     | 50 MB  | 81        | 3279                                    |
| constmap     | 100 MB | 137       | 5047                                    |
| constmap     | 200 MB | 230       | 6513                                    |
| constmap     | 541 MB | 467       | 9867                                    |
