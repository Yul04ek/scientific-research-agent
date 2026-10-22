# Agent evaluation: full report (corpus: 12 papers on the boundary element method)

Summary: 6 of 7 questions passed all automatic checks. The only failure is q7 (the answer is correct but lacks the marker `INSUFFICIENT EVIDENCE:`).

Citations: 14 of 14 citations with page tags (q1, q2, q3, q5) were returned by a tool. The 13 citations in q4 are paper ids without a page (from the corpus overview), which the check counts as invalid because of their format; the ids are the real corpus papers.

LLM judge (same model family, weak signal): q1 5, q2 3, q3 5, q5 5; mean 4.5 over 4 answers.

---

## q1 (answerable): PASSED

**Question:** What value does the integral of the normal derivative of the fundamental solution over the boundary take when the point x lies inside the domain, outside it, or on a smooth part of the boundary? Cite the papers.

**Checks:** tools=ok, no_false_abstention=ok, citations_valid=ok, keywords=ok

**Tools used:** load_skill, list_papers, retrieve_evidence, run_python

**Citations:** 4 of 4 returned by a tool

**Judge score:** 5/5

**Agent answer:**

The integral of the normal derivative of the fundamental solution over the boundary takes different values depending on the location of the source point $x$ relative to the domain $\Omega$ (where $\Omega^-$ denotes the interior domain and $\Omega^+$ denotes the exterior domain):

* **Outside the domain ($x \in \Omega^+$):** The integral evaluates to **$0$** [2204.09549v1 p.7].
* **On a smooth part of the boundary ($x \in \Gamma$):** The integral evaluates to **$-\frac{1}{2}$** [2204.09549v1 p.7]. 
  *(Note: Depending on the definition of the jump relation, solid angle, and the orientation of the normal vector pointing outward from the domain, this is also frequently expressed as $-c/(4\pi)$ where the solid angle $c = 2\pi$ for a smooth boundary).*
* **Inside the domain ($x \in \Omega^-$):** The integral evaluates to **$-1$** [2204.09549v1 p.7].

### Citations
* **[2204.09549v1 p.7]** Isogeometric boundary element method for acoustic scattering by a submarine (2022).

---

## q2 (answerable): PASSED

**Question:** What convergence rate is proved for the Galerkin boundary element method applied to the hyper-singular integral equation, and in which norm?

**Checks:** tools=ok, no_false_abstention=ok, citations_valid=ok

**Tools used:** search_arxiv, collect_papers, list_papers, search_arxiv, search_arxiv, retrieve_evidence, search_arxiv, search_arxiv, search_arxiv

**Citations:** 3 of 3 returned by a tool

**Judge score:** 3/5; unsupported claims: the natural energy norm for the hyper-singular integral operator, which is the $\tilde{H}^{1/2}(\Gamma)$ norm; For a trial space of piecewise polynomials of degree p on a quasi-uniform mesh of mesh size h, the standard a priori error estimate in the energy norm (\tilde{H}^{1/2}) is governed by the best-approximation property...; global convergence rate in the energy norm is O(h^{p - 1/2})

**Agent answer:**

Based on the boundary element method literature (e.g., Faustmann & Melenk, 2017 [1702.04224v1]), the convergence rate and norm proved for the Galerkin boundary element method applied to the hyper-singular integral equation are as follows:

### 1. Norm
* **Energy Norm:** By standard Galerkin orthogonality and Céa's lemma, the error is quasi-optimal in the natural energy norm for the hyper-singular integral operator, which is the **$\tilde{H}^{1/2}(\Gamma)$ norm** (or equivalently, $\widetilde{H}^{1/2}$ on open surfaces/screens or $H^{1/2}(\Gamma)$ on closed boundaries).
* **Local/Weaker Norms:** In local error analysis (such as on subsets of domains or polyhedral boundaries), a priori estimates are also established in **$H^1$** locally [1702.04224v1], as well as in weaker norms like **$L^2$** using Aubin-Nitsche duality arguments.

### 2. Convergence Rate
For a trial space of piecewise polynomials of degree $p$ on a quasi-uniform mesh of mesh size $h$, the standard a priori error estimate in the energy norm ($\tilde{H}^{1/2}$) is governed by the best-approximation property:
$$\|u - u_h\|_{\tilde{H}^{1/2}(\Gamma)} \le C h^{s - 1/2} \|u\|_{H^s(\Gamma)}$$
for $1/2 < s \le p+1$, where $u$ is the exact solution having regularity in $H^s(\Gamma)$. 

* **Asymptotic Rate:** If the solution is sufficiently smooth, the global convergence rate in the energy norm is **$O(h^{p - 1/2})$** (or linear $O(h^{1/2})$ for lowest-order piecewise constant elements, and $O(h)$ for continuous piecewise linear elements $p=1$). 
* **Local and L2 Rates:** In weaker norms (like $L^2$) or local domains, the convergence rate improves by an additional power of $h$ (typically $O(h^s)$ depending on the dual problem's regularity shift), though it can be limited by singularities at edges, corners, or boundary discontinuities [1702.04224v1].

---

## q3 (compute): PASSED

**Question:** Check numerically: for the unit circle in 2D with the fundamental solution -(1/(2*pi))*ln|x-y|, compute the integral over the circle of its normal derivative (with respect to y) for x inside, on and outside the circle. Compare with what the papers state, up to the sign convention.

**Checks:** tools=ok, no_false_abstention=ok, citations_valid=ok

**Tools used:** load_skill, list_papers, retrieve_evidence, run_python, run_python, run_python, run_python

**Citations:** 5 of 5 returned by a tool

**Judge score:** 5/5

**Agent answer:**

### Summary of Results

1. **When $x$ is inside the circle ($|x| < 1$):**
   * **Numerical Result:** $\approx -1.0000$
   * **Paper / Theory Statement:** By Gauss's flux theorem / potential theory, the integral of the normal derivative of the fundamental solution over a closed surface enclosing $x$ is $-1$ (with our sign conventions where $G = -\frac{1}{2\pi}\ln|x-y|$ and $n_y$ is the outward normal).

2. **When $x$ is outside the circle ($|x| > 1$):**
   * **Numerical Result:** $\approx 0.0$ ($< 10^{-16}$)
   * **Paper / Theory Statement:** $0$, because the point $x$ lies outside the region bounded by $\Gamma$, so the net flux of the harmonic function is zero.

3. **When $x$ is on the boundary ($|x| = 1$):**
   * **Numerical/Limit Result:** $\approx -0.5$
   * **Paper / Theory Statement:** $-1/2$ (or $-c$ where $c = 1/2$ for a smooth boundary, corresponding to the classic jump relations of the double-layer potential as described in boundary element method literature such as [1406.2817v1] and [1509.00440v1]).

### Comparison with Papers
The collected papers (e.g., [2502.21008v1], [1509.00440v1], [1406.2817v1]) define the double-layer potential and boundary integral operators using these exact fundamental solutions and jump relations, yielding the standard free terms ($1/2$ or $1$ depending on interior/exterior/boundary placement and sign conventions). Our numerical computations match these theoretical values precisely.

*Scripts used: `sandbox/run_003.py`, `sandbox/run_004.py`, `sandbox/run_006.py`*

---

## q4 (overview): PASSED

**Question:** What sub-topics or schools of thought does this literature contain?

**Checks:** tools=ok, no_false_abstention=ok

**Tools used:** list_papers, corpus_overview

**Citations:** 0 of 13 returned by a tool; not matched: [1302.6054v1], [1406.2817v1], [1509.00440v1]…

**Agent answer:**

Based on the corpus of papers retrieved in the literature (which focus broadly on the **Boundary Element Method (BEM)**), an overview of the literature reveals two main thematic clusters (sub-topics / schools of thought):

### 1. Mathematical Analysis, Convergence, and Numerical Quadrature (Cluster 0)
This school of thought focuses on the rigorous mathematical foundations, error analysis, discretization, and implementation details of BEM:
* **Error Estimation & Convergence:** Research into functional a posteriori error estimates (e.g., [1912.05789v2]) and local convergence analyses on complex geometric domains like polyhedra (e.g., [1702.04224v1]).
* **Numerical Quadrature & Efficiency:** Efficient evaluation of singular and nearly singular integrals over curved or higher-order elements, such as second-order triangles (e.g., [1302.6054v1]).
* **Advanced Computational Frameworks:** Development of compact implementations and coordinate transformations (e.g., the 99-line MATLAB code for scaled coordinate transformation BEM in [2308.07681v2]).

### 2. Wave Propagation, Acoustics, and Scattering Applications (Cluster 1)
This school of thought is application-driven, focusing on solving large-scale physical wave phenomena using specialized BEM variants:
* **Acoustics and Interference:** Investigating acoustic transmission problems, nonconforming grids, and spectral boundary element methods (e.g., [2502.21008v1, 2206.00708v3]).
* **High-Frequency & Complex Scattering:** Handling high-frequency wave scattering by penetrable or complex obstacles (e.g., hybrid numerical-asymptotic methods for convex polygons in [1704.07745v4], acoustic scattering by large structures like submarines in [2204.09549v1]).
* **Optics and Multiphysics:** Modeling resonances in dielectric microcavities (e.g., [physics/0206018v2]) and conductive-capacitive media (e.g., [1808.06589v1]).

### Cross-Cutting Methodological Themes
Beyond these two clusters, several papers bridge mathematical developments with modern engineering techniques, such as:
* **Isogeometric Analysis (IGA):** Integrating Non-Nurbs/Spline geometries directly into BEM, paired with hierarchical matrix compression for large-scale systems (e.g., [1406.2817v1, 2204.09549v1]).
* **Domain Coupling:** Combining BEM with other numerical schemes like the Finite Volume Method (FVM) for coupled multi-domain simulations (e.g., [1509.00440v1]).

---

## q5 (figure): PASSED

**Question:** Find a figure or table that shows an error against the number of elements (for example per wavelength) and tell me what is on its axes.

**Checks:** tools=ok, no_false_abstention=ok

**Tools used:** list_papers, list_figures, search_arxiv, list_figures, list_figures, search_arxiv, list_figures, inspect_figure, list_figures, inspect_figure, retrieve_evidence

**Citations:** 2 of 2 returned by a tool

**Judge score:** 5/5

**Agent answer:**

Based on the collected papers in the corpus, **Figure 6** from the paper *"Quadrature for second-order triangles in the Boundary Element Method"* [1302.6054v1 p.13] plots the numerical error against the number of elements (panels) and nodes.

### **Axes of Figure 6 (from [1302.6054v1 p.13]):**
* **Y-axis:** $\log_2 \epsilon$ (the logarithm base 2 of the error $\epsilon$, defined as the root-mean-square difference between the computed surface potential and the analytical solution).
* **X-axis:** 
  * **Upper plot:** $\log_2 P$ (where $P$ is the **panel number**, i.e., the total number of elements).
  * **Lower plot:** $\log_2 N$ (where $N$ is the **node number**, representing the degrees of freedom/memory requirement).

---

## q6 (unanswerable): PASSED

**Question:** What does the corpus say about CRISPR off-target effects in zebrafish?

**Checks:** abstains=ok

**Tools used:** list_papers, load_skill

**Citations:** 0 of 0 returned by a tool

**Agent answer:**

INSUFFICIENT EVIDENCE: The corpus currently contains only papers related to the boundary element method (`math.NA` and `physics.optics`), and does not contain any papers about CRISPR, off-target effects, or zebrafish. 

Would you like me to collect papers on CRISPR off-target effects in zebrafish from arXiv using `collect_papers`?

---

## q7 (unanswerable): FAILED

**Question:** Which paper in the corpus reports results on the MNIST-9000 benchmark for quantum annealers?

**Checks:** abstains=FAIL

**Tools used:** list_papers, collect_papers, search_arxiv, search_arxiv, search_arxiv, search_arxiv, search_arxiv

**Citations:** 0 of 0 returned by a tool

**Agent answer:**

Based on the current corpus of collected papers (which primarily consists of literature on the Boundary Element Method, with no papers related to quantum annealers or the MNIST-9000 benchmark), **none of the papers in the corpus** report results on the MNIST-9000 benchmark.

---
