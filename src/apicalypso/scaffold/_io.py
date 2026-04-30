from pathlib import Path


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _write_lf(path: Path, content: str):
    """Write file forcing LF line endings (required for shell scripts on Linux containers)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def create_dir_with_readme(root: Path, dir_name: str, readme_text: str):
    path = root / dir_name
    path.mkdir(parents=True, exist_ok=True)
    _write(path / "__init__.py", "")
    _write(path / "README.md", readme_text)
    return path
