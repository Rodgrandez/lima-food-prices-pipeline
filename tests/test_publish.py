import subprocess

from foodprices import publish


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def test_push_site_replaces_branch_with_single_commit(tmp_path):
    remote = tmp_path / "remote.git"
    _git("init", "-q", "--bare", str(remote), cwd=tmp_path)
    site = tmp_path / "site"
    (site / "data").mkdir(parents=True)
    (site / "index.html").write_text("v1", encoding="utf-8")
    (site / "data" / "status.json").write_text("{}", encoding="utf-8")
    publish.push_site(site, str(remote), message="first")
    (site / "index.html").write_text("v2", encoding="utf-8")
    publish.push_site(site, str(remote), message="second")
    assert _git("show", "gh-pages:index.html", cwd=remote) == "v2"
    assert _git("show", "gh-pages:.nojekyll", cwd=remote) == ""
    assert _git("rev-list", "--count", "gh-pages", cwd=remote).strip() == "1"     # history does not grow
    assert _git("log", "-1", "--format=%an <%ae> %s", "gh-pages", cwd=remote).strip() == \
        "Rodrigo Grandez <rodfra123@gmail.com> second"
