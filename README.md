# pygit

A minimal, from-scratch reimplementation of Git's core object model and a working subset of its plumbing/porcelain commands, in pure Python (stdlib only).

## The object model

Every object pygit stores is content-addressed: its name *is* the SHA-1 hash of its own bytes. An object is serialized as `<type> <size>\0<content>`, hashed with SHA-1, zlib-compressed, and written to `.git/objects/<sha[:2]>/<sha[2:]>`. This is exactly what real Git does, which is why a real `git cat-file -p <sha>` can read an object pygit wrote, and vice versa.

- **Blob** — the raw bytes of a file, unmodified.
- **Tree** — a sorted list of `<mode> <name>\0<20-raw-sha-bytes>` entries, one per file/directory in a directory snapshot. Directories are sorted as if their name had a trailing `/`, which is Git's actual (slightly surprising) sort rule.
- **Commit** — a small text format: `tree <sha>`, zero or more `parent <sha>` lines, `author` and `committer` lines (`name <email> <unix-epoch> <±HHMM>`), a blank line, then the message.

## The index

pygit implements Git's real binary index format (version 2, the `DIRC` format) rather than a simplified JSON file. This was a deliberate choice: the design goal was for a real `git` install to be able to read a repo pygit created, and the index is part of that surface (`git status`, `git ls-files`, `git commit` all read it directly). The format: a 12-byte header, then one 62-byte-plus-path entry per staged file (stat metadata, mode, size, SHA-1, flags, NUL-padded path), then a trailing SHA-1 checksum over everything before it.

## Command-to-internals map

| Command | What it touches |
|---|---|
| `init` | Creates `.git/objects`, `.git/refs/heads`, `.git/refs/tags`, `.git/HEAD` (→ `refs/heads/main`) |
| `hash-object` | Hashes/writes a blob object |
| `cat-file` | Reads and decompresses an object, prints type/size/content |
| `write-tree` | Groups the index by directory, recursively writes tree objects bottom-up |
| `read-tree` | Recursively walks a tree object, writes a matching index |
| `commit-tree` | Writes a commit object from an explicit tree/parents/message |
| `add` | Hashes/writes blobs for given paths, updates the index |
| `status` | Diffs working directory vs index vs `HEAD`'s tree |
| `commit` | `write-tree` + `commit-tree` (parent = current `HEAD`) + moves the current branch ref |
| `log` | Walks first-parent pointers from `HEAD`, printing each commit |
| `branch` | Lists/creates refs under `refs/heads` |
| `checkout` | Resolves a branch/commit, rewrites the working directory and index to match its tree, updates `HEAD` |
| `diff` | Line diff, working dir vs index (default) or index vs `HEAD` (`--cached`) |
| `merge` | Fast-forward only: moves the current branch ref if it's a strict ancestor of the target |

## Known limitations

- No networking: no `clone`/`fetch`/`push`/`pull`, no packfiles, no garbage collection.
- `merge` only supports fast-forward; there is no three-way content merge, so a real divergent merge will refuse with an error rather than attempt to combine changes.
- No rebase, cherry-pick, stash, submodules, or hooks.
- Object/ref names must be full 40-character SHA-1 hex strings or branch names — no abbreviated SHA resolution.
- Symlinks are stored with Git's `120000` mode if encountered inside a tree, but `add`/`checkout` do not have dedicated symlink handling (they read/write file contents as regular files).
- No `.gitignore` support in `add`/`status`.

## Running the tests

```bash
pip install -e .
pytest tests/ -v
```

Interop tests in `tests/test_interop_realgit.py` and the end-to-end test in `tests/test_cli_e2e.py` skip automatically if a real `git` binary or the installed `pygit` console script isn't available, but they are the strongest evidence of compatibility and should be run whenever possible.
