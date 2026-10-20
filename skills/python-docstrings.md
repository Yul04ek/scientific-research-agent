---
name: python-docstrings
description: Load this skill when writing or improving docstrings in Python code.
---

* Write docstrings in NumPy format (clear sections, readable for non-programmers).
* Add a docstring to every module, class, method, and function.
* Include Parameters, Returns, and Raises sections when applicable.
* Start with a one-line summary of *what* the function does, then details.
* Write for a scientist reading the code later: explain the purpose, not just the mechanics.

Example:

    def mean(values: list[float]) -> float:
        """Compute the arithmetic mean of a list of numbers.

        Parameters
        ----------
        values : list[float]
            The numbers to average. Must not be empty.

        Returns
        -------
        float
            The arithmetic mean.

        Raises
        ------
        ZeroDivisionError
            If the list is empty.
        """
