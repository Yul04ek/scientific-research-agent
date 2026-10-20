---
name: error-help
description: Load this skill when the user has a Python error, traceback, or exception to debug.
---

* Read the traceback from the BOTTOM up: the last line names the error type and message.
* Restate the error in plain language first — what Python is complaining about — before any fix.
* Find the line in the user's own code that triggered it (ignore deep library frames unless relevant).
* Explain the likely *cause*, not just the symptom (e.g. "the file path is wrong" vs "FileNotFoundError").
* Give the smallest fix that solves it; show the corrected line or block.
* Mention how to avoid this class of error next time, in one short tip.
* Common cases to recognize: NameError (typo / undefined variable), TypeError (wrong type or wrong arguments), IndexError / KeyError (item not in list / dict), FileNotFoundError (wrong path), IndentationError (spacing), ModuleNotFoundError (package not installed).
* Stay calm and reassuring — errors are normal and fixable.
