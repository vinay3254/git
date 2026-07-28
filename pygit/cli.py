import argparse

from pygit import plumbing
from pygit import porcelain
from pygit import branch
from pygit import checkout
from pygit import diff
from pygit import merge
from pygit.repository import create_repo, find_repo


def cmd_init(args):
    path = args.path or "."
    create_repo(path)
    print(f"Initialized empty pygit repository in {path}")


def build_parser():
    parser = argparse.ArgumentParser(prog="pygit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("path", nargs="?")
    init_parser.set_defaults(func=cmd_init)

    hash_object_parser = subparsers.add_parser("hash-object")
    hash_object_parser.add_argument("file")
    hash_object_parser.add_argument("-w", dest="write", action="store_true")
    hash_object_parser.add_argument("-t", dest="type", default="blob")
    hash_object_parser.set_defaults(func=plumbing.cmd_hash_object)

    cat_file_parser = subparsers.add_parser("cat-file")
    cat_file_group = cat_file_parser.add_mutually_exclusive_group(required=True)
    cat_file_group.add_argument("-t", dest="show_type", action="store_true")
    cat_file_group.add_argument("-s", dest="show_size", action="store_true")
    cat_file_group.add_argument("-p", dest="pretty", action="store_true")
    cat_file_parser.add_argument("object")
    cat_file_parser.set_defaults(func=plumbing.cmd_cat_file)

    commit_tree_parser = subparsers.add_parser("commit-tree")
    commit_tree_parser.add_argument("tree")
    commit_tree_parser.add_argument("-p", dest="parent", action="append")
    commit_tree_parser.add_argument("-m", dest="message", required=True)
    commit_tree_parser.set_defaults(func=plumbing.cmd_commit_tree)

    write_tree_parser = subparsers.add_parser("write-tree")
    write_tree_parser.set_defaults(func=plumbing.cmd_write_tree)

    read_tree_parser = subparsers.add_parser("read-tree")
    read_tree_parser.add_argument("tree")
    read_tree_parser.set_defaults(func=plumbing.cmd_read_tree)

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("paths", nargs="+")
    add_parser.set_defaults(func=porcelain.cmd_add)

    status_parser = subparsers.add_parser("status")
    status_parser.set_defaults(func=porcelain.cmd_status)

    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("-m", dest="message", required=True)
    commit_parser.set_defaults(func=porcelain.cmd_commit)

    log_parser = subparsers.add_parser("log")
    log_parser.set_defaults(func=porcelain.cmd_log)

    branch_parser = subparsers.add_parser("branch")
    branch_parser.add_argument("name", nargs="?")
    branch_parser.set_defaults(func=branch.cmd_branch)

    checkout_parser = subparsers.add_parser("checkout")
    checkout_parser.add_argument("target")
    checkout_parser.set_defaults(func=checkout.cmd_checkout)

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("--cached", action="store_true")
    diff_parser.set_defaults(func=diff.cmd_diff)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("branch")
    merge_parser.set_defaults(func=merge.cmd_merge)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "init":
        args.repo = find_repo()
    args.func(args)
