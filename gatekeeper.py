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

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.successful_dir = Path("successful_patterns")
        self.failed_dir = Path("failed_patterns")
        self.successful_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)

    def _run_command(self, cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Run a command with timeout, capture all streams."""
        return subprocess.run(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout,
            env=os.environ.copy()
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
            path = Path(tmpdir)
            # Write the generated code as a temporary module
            main_file = path / "main.py"
            main_file.write_text(code)

            # If stubs provided, write them as a helper module
            if stubs:
                stub_file = path / "stubs.py"
                stub_file.write_text(stubs)

            # Write test file if provided
            test_file = None
            if test_code:
                test_file = path / "test_main.py"
                test_file.write_text(test_code)

            # Prepare linter command
            ruff_cmd = [
                "ruff", "check", "--format=json", str(main_file),
            ]
            if stubs:
                ruff_cmd.append(str(stub_file))
            if test_file:
                ruff_cmd.append(str(test_file))

            # Run ruff
            ruff_result = self._run_command(ruff_cmd, cwd=path)
            ruff_stdout = ruff_result.stdout
            ruff_stderr = ruff_result.stderr
            ruff_errors = self._parse_json_errors(ruff_stdout)
            error_count = len(ruff_errors)

            # Prepare pytest command
            pytest_cmd = ["pytest", "-q", "--tb=short"]
            if test_file:
                pytest_cmd.append(str(test_file))
            else:
                # Run main file as test if no test file
                pytest_cmd.append(str(main_file))

            # Run pytest
            pytest_result = self._run_command(pytest_cmd, cwd=path)
            pytest_stdout = pytest_result.stdout
            pytest_stderr = pytest_result.stderr
            pytest_exit = pytest_result.returncode

            # Collect logs
            logs = {
                "ruff_stdout": ruff_stdout,
                "ruff_stderr": ruff_stderr,
                "pytest_stdout": pytest_stdout,
                "pytest_stderr": pytest_stderr,
                "ruff_errors": ruff_errors,
            }

            # Determine status based on error count
            if error_count == 0 and pytest_exit == 0:
                status = "PASS"
                result_dir = self.successful_dir
            elif error_count == 1 and pytest_exit == 0:
                status = "AUTO_HEAL"
                result_dir = self.failed_dir
            else:
                status = "HARD_REJECT"
                result_dir = self.failed_dir

            # Persist diagnostic artifacts for later analysis
            code_hash = hashlib.md5(code.encode()).hexdigest()[:12]
            result_file = result_dir / f"{status.lower()}_{code_hash}.json"
            result_file.write_text(json.dumps({
                "code": code,
                "error_count": error_count,
                "logs": logs
            }, indent=2))

            return {
                "status": status,
                "error_count": error_count,
                "logs": logs
            }


# Example usage (can be removed or commented out)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        code = open(sys.argv[1]).read()
        sandbox = Sandbox()
        evaluation = sandbox.evaluate_code(code)
        print(evaluation["status"], evaluation["error_count"])
    else:
        print("Usage: python gatekeeper.py <code_file>")
