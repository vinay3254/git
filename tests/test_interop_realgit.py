import shutil
import subprocess

import pytest

from pygit.objects import hash_object, read_object
from pygit.repository import GitRepository, create_repo

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="real git not on PATH")


def run_git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL)
    return result.stdout


def test_real_git_reads_pygit_blob(tmp_path):
    repo = create_repo(tmp_path)
    sha = hash_object(repo, b"interop content\n", "blob", write=True)
    output = run_git(str(tmp_path), "cat-file", "-p", sha)
    assert output == "interop content\n"


def test_pygit_reads_real_git_blob(tmp_path):
    repo = create_repo(tmp_path)
    (tmp_path / "file.txt").write_bytes(b"from real git\n")
    sha = run_git(str(tmp_path), "hash-object", "-w", "file.txt").strip()
    type_, content = read_object(repo, sha)
    assert type_ == "blob"
    assert content == b"from real git\n"


def test_real_git_reads_pygit_tree(tmp_path):
    repo = create_repo(tmp_path)
    blob_sha = hash_object(repo, b"content\n", "blob", write=True)
    from pygit.tree import TreeEntry, serialize_tree
    tree_data = serialize_tree([TreeEntry(mode="100644", name="file.txt", sha=blob_sha)])
    tree_sha = hash_object(repo, tree_data, "tree", write=True)
    output = run_git(str(tmp_path), "cat-file", "-p", tree_sha)
    assert "file.txt" in output
    assert blob_sha in output


def test_pygit_reads_real_git_tree(tmp_path):
    repo = create_repo(tmp_path)
    (tmp_path / "file.txt").write_bytes(b"content\n")
    run_git(str(tmp_path), "add", "file.txt")
    tree_sha = run_git(str(tmp_path), "write-tree").strip()
    from pygit.tree import parse_tree
    _, data = read_object(repo, tree_sha)
    entries = parse_tree(data)
    assert entries[0].name == "file.txt"


def test_real_git_reads_pygit_commit(tmp_path):
    repo = create_repo(tmp_path)
    blob_sha = hash_object(repo, b"content\n", "blob", write=True)
    from pygit.tree import TreeEntry, serialize_tree
    tree_data = serialize_tree([TreeEntry(mode="100644", name="file.txt", sha=blob_sha)])
    tree_sha = hash_object(repo, tree_data, "tree", write=True)
    identity = "Test User <test@example.com> 1700000000 +0000"
    from pygit.commit import Commit, serialize_commit
    commit = Commit(tree=tree_sha, parents=[], author=identity, committer=identity, message="Initial commit\n")
    commit_sha = hash_object(repo, serialize_commit(commit), "commit", write=True)
    output = run_git(str(tmp_path), "cat-file", "-p", commit_sha)
    assert f"tree {tree_sha}" in output
    assert "Initial commit" in output


def test_real_git_reads_pygit_index(tmp_path):
    run_git(str(tmp_path), "init", "-q")
    repo = GitRepository(str(tmp_path), str(tmp_path / ".git"))
    (tmp_path / "file.txt").write_bytes(b"hello\n")
    sha = hash_object(repo, b"hello\n", "blob", write=True)
    from pygit.index import make_entry, write_index
    write_index(repo, [make_entry("file.txt", sha, 0o100644)])
    output = run_git(str(tmp_path), "ls-files", "--stage")
    assert sha in output
    assert "file.txt" in output


def test_pygit_reads_real_git_index(tmp_path):
    run_git(str(tmp_path), "init", "-q")
    (tmp_path / "file.txt").write_bytes(b"hello\n")
    run_git(str(tmp_path), "add", "file.txt")
    repo = GitRepository(str(tmp_path), str(tmp_path / ".git"))
    from pygit.index import read_index
    entries = read_index(repo)
    assert len(entries) == 1
    assert entries[0].path == "file.txt"


def test_real_git_reads_pygit_write_tree_output(tmp_path):
    run_git(str(tmp_path), "init", "-q")
    repo = GitRepository(str(tmp_path), str(tmp_path / ".git"))
    (tmp_path / "file.txt").write_bytes(b"content\n")
    sha = hash_object(repo, b"content\n", "blob", write=True)
    from pygit.index import IndexEntry, write_index as pygit_write_index
    pygit_write_index(repo, [IndexEntry(0, 0, 0, 0, 0, 0, 0o100644, 0, 0, 8, sha, "file.txt")])
    from pygit.plumbing import build_tree
    from pygit.index import read_index
    tree_sha = build_tree(repo, read_index(repo))
    output = run_git(str(tmp_path), "cat-file", "-p", tree_sha)
    assert "file.txt" in output




