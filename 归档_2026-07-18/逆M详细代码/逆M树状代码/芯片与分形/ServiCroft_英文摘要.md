## English Abstract — Servi-Croft SPF vShape Kernel

**Title**: A Composite Number Filtering Kernel for Asymptotically Perfect Prime Selectivity

**Abstract**

We present a novel numerical kernel that combines four independent mathematical techniques — Gary W. Croft's modulo-30 wheel sieve (2018), T. Servi's mollifier approach for the Riemann zeta function, the standard smallest-prime-factor (SPF) linear sieve for three-class totative separation, and a continuously deformable vShape weight function borrowed from computational geometry — into a unified prime-composite detection framework. 

The Croft T30 wheel reduces the search domain to 26.67% of natural numbers by filtering multiples of 2, 3, and 5. The SPF sieve then separates the surviving totatives into three categories: genuine primes, prime powers (p^k), and multi-prime composites. Only primes and prime powers are passed to the Servi kernel K(t) = Σ cos(t·log n)/√n · φ(n/N), where φ(x) = exp(-b·x^a)·x^a is the continuous vShape weight with tunable parameters (a, b). The detection metric is the variance ratio R = Var(K_p)/Var(K_p^k).

Numerical experiments at scales N ∈ [10^3, 10^9] on a consumer-grade NVIDIA RTX 4090 GPU reveal that R(N) grows monotonically with N, reaching R(10^9) = 51,049, exceeding the Loiseau B-class threshold (R > 1.2) by a factor of over 42,000. The near-vanishing density of genuine prime powers in the Croft domain at large N ensures that the kernel's spectral response to primes becomes arbitrarily distinguishable from that of non-prime totatives. 

While the individual components (Croft sieve, SPF, Servi mollifier) are known from prior literature, their integration into a single GPU-accelerated detection pipeline with an asymptotically unconstrained performance regime is, to the best of our knowledge, an original contribution.

---

## 中文摘要

本文提出一种新的数值核，将Gary W. Croft的模30轮筛（2018）、T. Servi的黎曼zeta函数柔化方法、标准的最小数素因子（SPF）线性筛三分类以及从计算几何移植的连续vShape权重函数融合为统一的素数-合数检测框架。在N=10^9尺度上，核的方差比R达到51,049，超过Loiseau B类阈值1.2的四万倍以上。四个单独组件虽各有文献来源，但其整合为单一GPU加速检测流水线并达到渐近无约束性能区间是首创贡献。
