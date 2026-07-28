import pytest
from pygit.repository import create_repo
from pygit.objects import hash_object, read_object, BadObjectError


def test_hash_object_matches_git_blob_sha(tmp_path):
    repo = create_repo(tmp_path)
    sha = hash_object(repo, b"hello world\n", "blob", write=True)
    assert sha == "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"


def test_hash_object_write_false_does_not_store(tmp_path):
    repo = create_repo(tmp_path)
    sha = hash_object(repo, b"not stored", "blob", write=False)
    with pytest.raises(BadObjectError):
        read_object(repo, sha)


def test_read_object_round_trips(tmp_path):
    repo = create_repo(tmp_path)
    sha = hash_object(repo, b"round trip content", "blob", write=True)
    type_, content = read_object(repo, sha)
    assert type_ == "blob"
    assert content == b"round trip content"


def test_read_object_missing_raises(tmp_path):
    repo = create_repo(tmp_path)
    with pytest.raises(BadObjectError):
        read_object(repo, "0" * 40)
