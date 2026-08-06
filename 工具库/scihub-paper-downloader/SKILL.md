---
name: scihub-paper-downloader
description: "Get a PDF link from Sci-Hub for a DOI."
---

# Sci-Hub Paper Downloader

Given a DOI, use the bundled Python script to resolve a direct PDF URL through the current Sci-Hub and Sci-Net flow.

Treat the script output as follows:

- If it returns a URL, use that as the final PDF link.
- If it returns `NOT_FOUND` and a second line starts with `OA_LINK `, treat that value as the OA entry link shown on the Sci-Hub page. It may be a publisher page, repository page, or another non-PDF landing page rather than a final PDF URL.
- If it returns `NOT_FOUND` with no second line, report that Sci-Hub does not currently have the paper.
- If it returns `MIRROR_ERROR`, report that Sci-Hub could not be resolved reliably and the result is inconclusive.
- If it returns `INVALID_INPUT`, ask for a valid DOI.

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
