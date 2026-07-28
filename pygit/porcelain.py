import os

from pygit.index import make_entry, read_index, write_index
from pygit.objects import hash_object, read_object
from pygit.commit import Commit, get_identity, serialize_commit, parse_commit
from pygit.refs import get_head_branch, resolve_ref, set_head_detached, write_ref
from pygit.tree import flatten_tree


def _walk_files(path):
    if os.path.isfile(path):
        return [path]
    files = []
    for root, dirs, names in os.walk(path):
        if ".git" in dirs:
            dirs.remove(".git")
        for name in names:
            files.append(os.path.join(root, name))
    return files


def stage_paths(repo, paths):
    entries = {e.path: e for e in read_index(repo)}
    for path in paths:
        for file_path in _walk_files(path):
            rel_path = os.path.relpath(file_path, repo.worktree).replace(os.sep, "/")
            with open(file_path, "rb") as f:
                data = f.read()
            sha = hash_object(repo, data, "blob", write=True)
            mode = 0o100755 if os.access(file_path, os.X_OK) else 0o100644
            st = os.stat(file_path)
            entries[rel_path] = make_entry(rel_path, sha, mode, st)
    write_index(repo, list(entries.values()))


def cmd_add(args):
    stage_paths(args.repo, args.paths)


def _list_working_files(repo):
    files = []
    for root, dirs, names in os.walk(repo.worktree):
        if ".git" in dirs:
            dirs.remove(".git")
        for name in names:
            full_path = os.path.join(root, name)
            files.append(os.path.relpath(full_path, repo.worktree).replace(os.sep, "/"))
    return files


def compute_status(repo):
    index_entries = {e.path: e for e in read_index(repo)}
    head_sha = resolve_ref(repo, "HEAD")
    head_tree = {}
    if head_sha is not None:
        _, commit_data = read_object(repo, head_sha)
        head_tree = flatten_tree(repo, parse_commit(commit_data).tree)

    staged_new = [p for p in index_entries if p not in head_tree]
    staged_modified = [p for p, e in index_entries.items() if p in head_tree and head_tree[p].sha != e.sha]
    staged_deleted = [p for p in head_tree if p not in index_entries]

    not_staged_modified = []
    not_staged_deleted = []
    for path, entry in index_entries.items():
        full_path = os.path.join(repo.worktree, path)
        if not os.path.exists(full_path):
            not_staged_deleted.append(path)
            continue
        with open(full_path, "rb") as f:
            data = f.read()
        if hash_object(repo, data, "blob", write=False) != entry.sha:
            not_staged_modified.append(path)

    untracked = sorted(set(_list_working_files(repo)) - set(index_entries.keys()))

    return {
        "staged_new": sorted(staged_new),
        "staged_modified": sorted(staged_modified),
        "staged_deleted": sorted(staged_deleted),
        "not_staged_modified": sorted(not_staged_modified),
        "not_staged_deleted": sorted(not_staged_deleted),
        "untracked": untracked,
    }


def cmd_status(args):
    status = compute_status(args.repo)
    if any([status["staged_new"], status["staged_modified"], status["staged_deleted"]]):
        print("Changes to be committed:")
        for path in status["staged_new"]:
            print(f"\tnew file:   {path}")
        for path in status["staged_modified"]:
            print(f"\tmodified:   {path}")
        for path in status["staged_deleted"]:
            print(f"\tdeleted:    {path}")
    if any([status["not_staged_modified"], status["not_staged_deleted"]]):
        print("Changes not staged for commit:")
        for path in status["not_staged_modified"]:
            print(f"\tmodified:   {path}")
        for path in status["not_staged_deleted"]:
            print(f"\tdeleted:    {path}")
    if status["untracked"]:
        print("Untracked files:")
        for path in status["untracked"]:
            print(f"\t{path}")


def cmd_commit(args):
    from pygit.plumbing import build_tree

    entries = read_index(args.repo)
    if not entries:
        raise SystemExit("nothing to commit (create/copy files and use 'pygit add' to track)")

    tree_sha = build_tree(args.repo, entries)
    parent_sha = resolve_ref(args.repo, "HEAD")
    if parent_sha is not None:
        _, parent_data = read_object(args.repo, parent_sha)
        if parse_commit(parent_data).tree == tree_sha:
            raise SystemExit("nothing to commit, working tree clean")

    identity = get_identity()
    message = args.message if args.message.endswith("\n") else args.message + "\n"
    commit = Commit(
        tree=tree_sha,
        parents=[parent_sha] if parent_sha else [],
        author=identity,
        committer=identity,
        message=message,
    )
    commit_sha = hash_object(args.repo, serialize_commit(commit), "commit", write=True)

    branch = get_head_branch(args.repo)
    if branch is not None:
        write_ref(args.repo, f"refs/heads/{branch}", commit_sha)
    else:
        set_head_detached(args.repo, commit_sha)
    print(commit_sha)


def cmd_log(args):
    sha = resolve_ref(args.repo, "HEAD")
    while sha is not None:
        _, data = read_object(args.repo, sha)
        commit = parse_commit(data)
        print(f"commit {sha}")
        print(f"Author: {commit.author}")
        print()
        for line in commit.message.rstrip("\n").split("\n"):
            print(f"    {line}")
        print()
        sha = commit.parents[0] if commit.parents else None

