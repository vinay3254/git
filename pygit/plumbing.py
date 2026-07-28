import sys

from pygit.objects import hash_object, read_object
from pygit.commit import Commit, get_identity, serialize_commit
from pygit.index import read_index, write_index, IndexEntry
from pygit.tree import TreeEntry, serialize_tree, flatten_tree


def cmd_hash_object(args):
    with open(args.file, "rb") as f:
        data = f.read()
    sha = hash_object(args.repo, data, args.type, write=args.write)
    print(sha)


def cmd_cat_file(args):
    type_, content = read_object(args.repo, args.object)
    if args.show_type:
        print(type_)
    elif args.show_size:
        print(len(content))
    elif args.pretty:
        sys.stdout.buffer.write(content)


def cmd_commit_tree(args):
    identity = get_identity()
    message = args.message if args.message.endswith("\n") else args.message + "\n"
    commit = Commit(
        tree=args.tree,
        parents=args.parent or [],
        author=identity,
        committer=identity,
        message=message,
    )
    sha = hash_object(args.repo, serialize_commit(commit), "commit", write=True)
    print(sha)


def _insert(tree_dict, parts, entry):
    if len(parts) == 1:
        tree_dict[parts[0]] = entry
    else:
        subdir = tree_dict.setdefault(parts[0], {})
        _insert(subdir, parts[1:], entry)


def _write_tree_dict(repo, tree_dict):
    tree_entries = []
    for name, value in tree_dict.items():
        if isinstance(value, dict):
            sha = _write_tree_dict(repo, value)
            tree_entries.append(TreeEntry(mode="40000", name=name, sha=sha))
        else:
            mode = "100755" if value.mode & 0o111 else "100644"
            tree_entries.append(TreeEntry(mode=mode, name=name, sha=value.sha))
    return hash_object(repo, serialize_tree(tree_entries), "tree", write=True)


def build_tree(repo, entries):
    tree_dict = {}
    for entry in entries:
        _insert(tree_dict, entry.path.split("/"), entry)
    return _write_tree_dict(repo, tree_dict)


def cmd_write_tree(args):
    print(build_tree(args.repo, read_index(args.repo)))


def read_tree_into_index(repo, tree_sha):
    flat = flatten_tree(repo, tree_sha)
    entries = []
    for path, tree_entry in flat.items():
        _, content = read_object(repo, tree_entry.sha)
        mode = int(tree_entry.mode, 8)
        entries.append(IndexEntry(0, 0, 0, 0, 0, 0, mode, 0, 0, len(content), tree_entry.sha, path))
    write_index(repo, entries)
    return entries


def cmd_read_tree(args):
    read_tree_into_index(args.repo, args.tree)
