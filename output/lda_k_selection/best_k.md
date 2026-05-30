# LDA K Selection Result

Best K: **15**

K=1, K=2, K=3, and K=4 are kept as coarse-reference models only. They are useful for checking whether the corpus has broad splits, but they are not eligible for the final choice because the project needs several interpretable topics rather than one or two overly broad groups.

For eligible models (K >= 5), the final K is selected by a composite score:

`0.35 * NPMI coherence + 0.25 * exclusivity + 0.20 * topic separation + 0.10 * topic diversity + 0.10 * inverse perplexity`

Topic diversity is not expected to increase monotonically with K. It measures the proportion of unique words among all topic top words, so it can go up or down depending on how much the top-word lists overlap.

| K | Status | Perplexity | UMass | NPMI | Exclusivity | Diversity | Separation | Mean Max Topic Prob. | Score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | coarse_reference | 2005.3342 | -1.3722 | 0.0293 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |  |
| 2 | coarse_reference | 1862.8406 | -1.4738 | 0.0521 | 0.7280 | 0.9000 | 0.4369 | 0.8517 |  |
| 3 | coarse_reference | 1787.3752 | -1.5078 | 0.0744 | 0.6098 | 0.8444 | 0.4784 | 0.7952 |  |
| 4 | coarse_reference | 1719.5123 | -1.5713 | 0.0750 | 0.5848 | 0.8333 | 0.5236 | 0.7190 |  |
| 5 | eligible | 1685.5710 | -1.5323 | 0.0755 | 0.5135 | 0.7333 | 0.5397 | 0.6900 | 0.5414 |
| 10 | eligible | 1656.4875 | -1.7805 | 0.0691 | 0.4601 | 0.6867 | 0.6157 | 0.5312 | 0.4120 |
| 15 | eligible | 1612.9603 | -1.8474 | 0.0939 | 0.4580 | 0.6711 | 0.6482 | 0.4966 | 0.6829 |
| 20 | eligible | 1599.7431 | -1.9878 | 0.0762 | 0.4424 | 0.6433 | 0.6650 | 0.4626 | 0.4947 |
| 25 | eligible | 1596.5886 | -2.1839 | 0.0678 | 0.4578 | 0.6693 | 0.6866 | 0.4404 | 0.5129 |
| 30 | eligible | 1590.3291 | -2.1626 | 0.0532 | 0.4500 | 0.6311 | 0.7008 | 0.4382 | 0.3537 |
| 35 | eligible | 1596.4947 | -2.2129 | 0.0548 | 0.4192 | 0.6229 | 0.7026 | 0.4037 | 0.2741 |
| 40 | eligible | 1581.1868 | -2.3460 | 0.0598 | 0.4669 | 0.6667 | 0.7172 | 0.4004 | 0.5143 |
| 45 | eligible | 1582.9998 | -2.3370 | 0.0579 | 0.4634 | 0.6607 | 0.7238 | 0.3866 | 0.4877 |
| 50 | eligible | 1588.9440 | -2.3434 | 0.0570 | 0.4402 | 0.6360 | 0.7255 | 0.3726 | 0.3928 |
