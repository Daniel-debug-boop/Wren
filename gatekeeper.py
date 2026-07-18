"""Gatekeeper: execute generated code in an isolated subprocess with strict linting and testing.

This module evaluates candidate code snippets using ruff and pytest, returning a
structured PASS / AUTO_HEAL / HARD_REJECT result plus diagnostic logs.
"""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List


class Sandbox:
    """
    Execute generated code in an isolated subprocess with strict linting and testing.
    Returns structured evaluation results.
    """

    # Marker attribute so pylint does not flag "too few public methods".
    purpose = "sandbox"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.successful_dir = Path("successful_patterns")
        self.failed_dir = Path("failed_patterns")
        self.successful_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)

    def summarize(self) -> str:
        """Return a short human-readable description of this sandbox."""
        return (
            f"Sandbox(timeout={self.timeout}s, "
            f"pass_to={self.successful_dir}, fail_to={self.failed_dir})"
        )

    def _run_command(self, cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Run a command with timeout, capture all streams."""
        return subprocess.run(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout,
            env=os.environ.copy(),
            check=False,
        )

    def _parse_json_errors(self, output: str) -> List[Dict[str, Any]]:
        """Convert linter JSON output to error list; return empty list if valid."""
        if not output or not output.strip():
            return []
        try:
            data = json.loads(output)
            if isinstance(data, list):
                return data
            return data.get("errors", [])
        except json.JSONDecodeError:
            return []

    def evaluate_code(
        self, code: str, test_code: str = "", stubs: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate a code snippet:
          1. Write to temp dir
          2. Run ruff check (JSON output)
          3. Run pytest on any provided tests
          4. Return status (PASS/AUTO_HEAL/HARD_REJECT) + error count + logs
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            return self._evaluate_in_dir(Path(tmpdir), code, test_code, stubs)

    def _evaluate_in_dir(
        self, path: Path, code: str, test_code: str, stubs: str
    ) -> Dict[str, Any]:
        """Run ruff/pytest evaluation inside an already-created temp dir."""
        main_file, stub_file, test_file = self._write_artifacts(
            path, code, test_code, stubs
        )

        ruff_cmd = self._build_ruff_command(main_file, stub_file, test_file)
        pytest_cmd = self._build_pytest_command(main_file, test_file)

        error_count, pytest_exit, logs = self._run_checks(
            ruff_cmd, pytest_cmd, path
        )

        status, result_dir = self._resolve_status(error_count, pytest_exit)

        self._persist(result_dir, status, code, error_count, logs)

        return {
            "status": status,
            "error_count": error_count,
            "logs": logs
        }

    def _run_checks(
        self, ruff_cmd: List[str], pytest_cmd: List[str], path: Path
    ) -> tuple[int, int, Dict[str, Any]]:
        """Run ruff and pytest, returning (error_count, pytest_exit, logs)."""
        ruff_result = self._run_command(ruff_cmd, cwd=path)
        error_count = self._count_ruff_errors(ruff_result.stdout)

        pytest_result = self._run_command(pytest_cmd, cwd=path)
        pytest_exit = pytest_result.returncode

        logs = {
            "ruff_stdout": ruff_result.stdout,
            "ruff_stderr": ruff_result.stderr,
            "pytest_stdout": pytest_result.stdout,
            "pytest_stderr": pytest_result.stderr,
            "ruff_errors": self._parse_json_errors(ruff_result.stdout),
        }
        return error_count, pytest_exit, logs

    def _write_artifacts(
        self, path: Path, code: str, test_code: str, stubs: str
    ) -> tuple[Path, Path | None, Path | None]:
        """Write code/stub/test files into the temp dir; return their paths."""
        main_file = path / "main.py"
        main_file.write_text(code)

        stub_file = path / "stubs.py" if stubs else None
        if stub_file:
            stub_file.write_text(stubs)

        test_file = path / "test_main.py" if test_code else None
        if test_file:
            test_file.write_text(test_code)

        return main_file, stub_file, test_file

    def _count_ruff_errors(self, output: str) -> int:
        """Return the number of ruff errors found in the JSON output."""
        return len(self._parse_json_errors(output))

    def _persist(
        self,
        result_dir: Path,
        status: str,
        code: str,
        error_count: int,
        logs: Dict[str, Any],
    ) -> None:
        """Persist diagnostic artifacts for later analysis."""
        code_hash = hashlib.md5(code.encode()).hexdigest()[:12]
        result_file = result_dir / f"{status.lower()}_{code_hash}.json"
        result_file.write_text(json.dumps({
            "code": code,
            "error_count": error_count,
            "logs": logs
        }, indent=2))

    def _build_ruff_command(
        self, main_file: Path, stub_file: Path | None, test_file: Path | None
    ) -> List[str]:
        """Assemble the ruff invocation for the generated artifacts."""
        cmd = ["ruff", "check", "--format=json", str(main_file)]
        if stub_file:
            cmd.append(str(stub_file))
        if test_file:
            cmd.append(str(test_file))
        return cmd

    def _build_pytest_command(
        self, main_file: Path, test_file: Path | None
    ) -> List[str]:
        """Assemble the pytest invocation, falling back to the main file."""
        cmd = ["pytest", "-q", "--tb=short"]
        cmd.append(str(test_file) if test_file else str(main_file))
        return cmd

    def _resolve_status(
        self, error_count: int, pytest_exit: int
    ) -> tuple[str, Path]:
        """Map error/exit codes to an evaluation status and target directory."""
        if error_count == 0 and pytest_exit == 0:
            return "PASS", self.successful_dir
        if error_count == 1 and pytest_exit == 0:
            return "AUTO_HEAL", self.failed_dir
        return "HARD_REJECT", self.failed_dir


# Example usage (can be removed or commented out)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as code_file:
            source_code = code_file.read()
        sandbox = Sandbox()
        evaluation = sandbox.evaluate_code(source_code)
        print(evaluation["status"], evaluation["error_count"])
    else:
        print("Usage: python gatekeeper.py <code_file>")
