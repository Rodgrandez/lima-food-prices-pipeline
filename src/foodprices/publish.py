"""Publish the static site as a single-commit gh-pages branch (the history of the data lives in the site itself)."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from foodprices import config


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def remote_url() -> str:
    return _git("remote", "get-url", "origin", cwd=config.ROOT).strip()


def push_site(site_dir: Path, remote: str, branch: str = "gh-pages", message: str = "Update site") -> None:
    name, email = config.AUTHOR
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        work = Path(tmp) / "site"
        shutil.copytree(site_dir, work)
        (work / ".nojekyll").touch()                   # serve files as they are, no Jekyll processing
        _git("init", "-q", "-b", branch, cwd=work)
        _git("add", "-A", cwd=work)
        _git("-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "-q", "-m", message, cwd=work)
        _git("push", "-q", "--force", remote, f"{branch}:{branch}", cwd=work)
