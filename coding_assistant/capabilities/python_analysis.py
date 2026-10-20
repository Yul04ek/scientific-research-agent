import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

_MAX_OUTPUT = 6000


def _next_script(sandbox: Path) -> Path:
    """sandbox/run_001.py, run_002.py, ... (never overwrites an earlier script)."""
    numbers = [int(p.stem.split("_")[1]) for p in sandbox.glob("run_*.py") if p.stem.split("_")[1].isdigit()]
    return sandbox / f"run_{max(numbers, default=0) + 1:03d}.py"


def run_python(code: str, timeout_seconds: int = 90) -> str:
    """Run Python code in a separate process and return what it prints.
    Use it for calculations, simulations and small experiments that check a
    claim from a paper (numpy, pandas, scipy, scikit-learn and matplotlib are
    available). Every script is saved as its own file (sandbox/run_001.py, ...);
    the file name is given at the end of the result, and you must tell the user
    this file name in your answer. Files you save (e.g. plots) land in sandbox/ too.
    Print every result you need; nothing is returned except printed text.

    Parameters
    ----------
    code : str
        A complete, self-contained Python script.
    timeout_seconds : int
        Stop the script after this many seconds (max 300).

    Returns
    -------
    str
        stdout, then stderr if there was an error (long output is cut),
        then the line "[script saved: sandbox/run_NNN.py]".
    """
    sandbox = Path("sandbox").resolve()
    sandbox.mkdir(exist_ok=True)
    script = _next_script(sandbox)
    script.write_text(code, encoding="utf-8")
    note = f"\n[script saved: sandbox/{script.name}]"
    try:
        done = subprocess.run(
            [sys.executable, str(script)],
            cwd=sandbox,
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout_seconds, 300)),
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: the script ran longer than {timeout_seconds} s and was stopped. Make it smaller (fewer repetitions)." + note
    output = done.stdout
    if done.returncode != 0:
        output += f"\n--- error (exit code {done.returncode}) ---\n{done.stderr[-2000:]}"
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + "\n... [output cut]"
    return (output.strip() or "(the script printed nothing - add print() calls)") + note


@dataclass
class PythonAnalysis(AbstractCapability[Any]):
    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        toolset.add_function(run_python)
        return toolset
