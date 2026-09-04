import subprocess
from pathlib import Path


def test_integration():
    script_dir = Path(__file__).resolve().parent
    script_path = script_dir / "integration_test.sh"

    result = subprocess.run(
        ["bash", script_path], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Done! All tests passed!\n"
