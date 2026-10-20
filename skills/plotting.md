---
name: plotting
description: Load this skill when creating charts or visualizations of data.
---

* Use matplotlib for plotting. Import as `import matplotlib.pyplot as plt`.
* Always label axes (`plt.xlabel`, `plt.ylabel`) and add a title (`plt.title`).
* Choose the chart type to match the data: line for trends over time, bar for categories, scatter for relationships, histogram for distributions.
* Save the figure to the sandbox with `plt.savefig("plot.png")` so the user can open it.
* Keep colors and styling simple and readable; avoid clutter.
* After plotting, explain in one sentence what the chart shows, in plain language.
