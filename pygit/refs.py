import os

from pygit.repository import repo_path


def read_ref_raw(repo, ref_name):
    path = repo_path(repo, *ref_name.split("/"))
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read().strip()


def resolve_ref(repo, ref_name):
    content = read_ref_raw(repo, ref_name)
    if content is None:
        return None
    if content.startswith("ref: "):
        return resolve_ref(repo, content[len("ref: "):])
    return content


def write_ref(repo, ref_name, sha):
    path = repo_path(repo, *ref_name.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(sha + "\n")


def get_head_branch(repo):
    content = read_ref_raw(repo, "HEAD")
    if content and content.startswith("ref: refs/heads/"):
        return content[len("ref: refs/heads/"):]
    return None


def set_head_branch(repo, branch_name):
    with open(repo_path(repo, "HEAD"), "w") as f:
        f.write(f"ref: refs/heads/{branch_name}\n")


def set_head_detached(repo, sha):
    with open(repo_path(repo, "HEAD"), "w") as f:
        f.write(sha + "\n")


def list_branches(repo):
    heads_dir = repo_path(repo, "refs", "heads")
    if not os.path.isdir(heads_dir):
        return []
    return sorted(os.listdir(heads_dir))


def branch_exists(repo, name):
    return os.path.exists(repo_path(repo, "refs", "heads", name))


def create_branch(repo, name, sha):
    if branch_exists(repo, name):
        raise ValueError(f"branch '{name}' already exists")
    write_ref(repo, f"refs/heads/{name}", sha)
