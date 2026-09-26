Machine: Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1. Every value is the median of 3 runs of `llama-lookup-stats`.

### Drafting time per drafted token (µs)

| corpus | baseline | nocopy | outermap | constmap | baseline / nocopy | nocopy / outermap | outermap / constmap |
|--------|----------|--------|----------|----------|-------------------|-------------------|---------------------|
| none   | 8.54     | 1.89   | 1.78     | 1.74     | 4.52x             | 1.06x             | 1.02x               |
| 25 MB  | 45.61    | 4.12   | 3.88     | 4.51     | 11.08x            | 1.06x             | 0.86x               |
| 50 MB  | 59.73    | 4.42   | 4.21     | 4.97     | 13.52x            | 1.05x             | 0.85x               |
| 100 MB | 83.46    | 4.64   | 4.45     | 5.33     | 17.99x            | 1.04x             | 0.84x               |
| 200 MB | 113.46   | 5.62   | 4.87     | 5.76     | 20.18x            | 1.16x             | 0.84x               |
| 541 MB | 165.48   | 6.47   | 6.06     | 6.93     | 25.58x            | 1.07x             | 0.87x               |

### Static cache load time (ms)

| corpus | baseline | nocopy | outermap | constmap | baseline / nocopy | nocopy / outermap | outermap / constmap |
|--------|----------|--------|----------|----------|-------------------|-------------------|---------------------|
| 25 MB  | 438      | 474    | 283      | 29       | 0.92x             | 1.68x             | 9.81x               |
| 50 MB  | 904      | 845    | 503      | 48       | 1.07x             | 1.68x             | 10.51x              |
| 100 MB | 1327     | 1297   | 913      | 78       | 1.02x             | 1.42x             | 11.76x              |
| 200 MB | 2464     | 2517   | 1640     | 135      | 0.98x             | 1.53x             | 12.18x              |
| 541 MB | 5485     | 5283   | 3744     | 252      | 1.04x             | 1.41x             | 14.87x              |

### Static cache memory (MB)

| corpus | baseline | nocopy | outermap | constmap | baseline / nocopy | nocopy / outermap | outermap / constmap |
|--------|----------|--------|----------|----------|-------------------|-------------------|---------------------|
| 25 MB  | 215      | 249    | 242      | 47       | 0.86x             | 1.03x             | 5.15x               |
| 50 MB  | 399      | 451    | 423      | 82       | 0.89x             | 1.07x             | 5.17x               |
| 100 MB | 705      | 743    | 807      | 139      | 0.95x             | 0.92x             | 5.80x               |
| 200 MB | 1215     | 1284   | 1494     | 221      | 0.95x             | 0.86x             | 6.76x               |
| 541 MB | 2573     | 2652   | 3091     | 475      | 0.97x             | 0.86x             | 6.51x               |

### Accepted drafted tokens (%)

| corpus | baseline | nocopy | outermap | constmap | baseline / nocopy | nocopy / outermap | outermap / constmap |
|--------|----------|--------|----------|----------|-------------------|-------------------|---------------------|
| none   | 15.363   | 15.513 | 15.513   | 15.513   | 0.99x             | 1.00x             | 1.00x               |
| 25 MB  | 17.639   | 17.679 | 17.679   | 17.738   | 1.00x             | 1.00x             | 1.00x               |
| 50 MB  | 18.181   | 18.213 | 18.213   | 18.251   | 1.00x             | 1.00x             | 1.00x               |
| 100 MB | 18.789   | 18.829 | 18.829   | 18.860   | 1.00x             | 1.00x             | 1.00x               |
| 200 MB | 19.227   | 19.260 | 19.260   | 19.263   | 1.00x             | 1.00x             | 1.00x               |
| 541 MB | 19.896   | 19.948 | 19.948   | 19.948   | 1.00x             | 1.00x             | 1.00x               |

### Static cache files

| cache_format | corpus | file (MB) | peak memory of llama-lookup-create (MB) |
|--------------|--------|-----------|-----------------------------------------|
| legacy       | 25 MB  | 50        | 2082                                    |
| legacy       | 50 MB  | 85        | 3451                                    |
| legacy       | 100 MB | 143       | 5919                                    |
| legacy       | 200 MB | 239       | 8625                                    |
| legacy       | 541 MB | 485       | 10254                                   |
| constmap     | 25 MB  | 47        | 2069                                    |
| constmap     | 50 MB  | 81        | 3395                                    |
| constmap     | 100 MB | 137       | 5900                                    |
| constmap     | 200 MB | 230       | 9002                                    |
| constmap     | 541 MB | 467       | 9940                                    |
