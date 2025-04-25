import argparse
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch
from math import ceil
import os
import re
import sys

import GitRepository
import GitObject

# Creates the argument parser so we can accept the commands (init, commit, etc.) through the command line.
argparser = argparse.ArgumentParser(description="kgit — My own Git version control system!")
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True # Require an argument from the user.

# kgit init
argsp = argsubparsers.add_parser("init", help="Initialize an empty, new repository.")
argsp.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository.")

# kgit cat-file
argsp = argsubparsers.add_parser("cat-file",
                                 help="Provide content of repository objects")
argsp.add_argument("type",
                   metavar="type",
                   choices=["blob", "commit", "tag", "tree"],
                   help="Specify the type")
argsp.add_argument("object",
                   metavar="object",
                   help="The object to display")

# kgit hash-object
argsp = argsubparsers.add_parser(
    "hash-object",
    help="Compute object ID and optionally creates a blob from a file")

argsp.add_argument("-t",
                   metavar="type",
                   dest="type",
                   choices=["blob", "commit", "tag", "tree"],
                   default="blob",
                   help="Specify the type")

argsp.add_argument("-w",
                   dest="write",
                   action="store_true",
                   help="Actually write the object into the database")

argsp.add_argument("path",
                   help="Read object from <file>")

# kgit log
argsp = argsubparsers.add_parser("log", help="Display history of a given commit.")
argsp.add_argument("commit",
                   default="HEAD",
                   nargs="?",
                   help="Commit to start at.")

# kgit ls-tree
argsp = argsubparsers.add_parser("ls-tree", help="Pretty-print a tree object.")
argsp.add_argument("-r",
                   dest="recursive",
                   action="store_true",
                   help="Recurse into sub-trees")

argsp.add_argument("tree",
                   help="A tree-ish object.")

# kgit checkout
argsp = argsubparsers.add_parser("checkout", help="Checkout a commit inside of a directory.")

argsp.add_argument("commit",
                   help="The commit or tree to checkout.")

argsp.add_argument("path",
                   help="The EMPTY directory to checkout on.")

# kgit show-ref
argsp = argsubparsers.add_parser("show-ref", help="List references.")


def cmd_init(args):
    GitRepository.repo_create(args.path)
    
def cmd_cat_file(args):
    repo = GitRepository.repo_find()
    cat_file(repo, args.object, fmt=args.type.encode())

def cat_file(repo, obj, fmt=None):
    obj = GitObject.object_read(repo, GitObject.object_find(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())
    
def cmd_hash_object(args):
    if args.write:
        repo = GitRepository.repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = GitObject.object_hash(fd, args.type.encode(), repo)
        print(sha)
        
def log_graphviz(repo, sha, seen):

    if sha in seen:
        return
    seen.add(sha)

    commit = GitObject.object_read(repo, sha)
    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace("\"", "\\\"")

    if "\n" in message: # Keep only the first line
        message = message[:message.index("\n")]

    print(f"  c_{sha} [label=\"{sha[0:7]}: {message}\"]")
    assert commit.fmt==b'commit'

    if not b'parent' in commit.kvlm.keys():
        # Base case: the initial commit.
        return

    parents = commit.kvlm[b'parent']

    if type(parents) != list:
        parents = [ parents ]

    for p in parents:
        p = p.decode("ascii")
        print (f"  c_{sha} -> c_{p};")
        log_graphviz(repo, p, seen)

def cmd_log(args):
    repo = GitRepository.repo_find()

    print("digraph wyaglog{")
    print("  node[shape=rect]")
    log_graphviz(repo, GitObject.object_find(repo, args.commit), set())
    print("}")

def cmd_ls_tree(args):
    repo = GitRepository.repo_find()
    ls_tree(repo, args.tree, args.recursive)

def ls_tree(repo, ref, recursive=None, prefix=""):
    sha = GitObject.object_find(repo, ref, fmt=b"tree")
    obj = GitObject.object_read(repo, sha)
    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type: # Determine the type.
            case b'04': type = "tree"
            case b'10': type = "blob" # A regular file.
            case b'12': type = "blob" # A symlink. Blob contents is link target.
            case b'16': type = "commit" # A submodule
            case _: raise Exception(f"Weird tree leaf mode {item.mode}")

        if not (recursive and type=='tree'): # This is a leaf
            print(f"{'0' * (6 - len(item.mode)) + item.mode.decode('ascii')} {type} {item.sha}\t{os.path.join(prefix, item.path)}")
        else: # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))

def cmd_checkout(args):
    repo = GitRepository.repo_find()

    obj = GitObject.object_read(repo, GitObject.object_find(repo, args.commit))

    # If the object is a commit, we grab its tree
    if obj.fmt == b'commit':
        obj = GitObject.object_read(repo, obj.kvlm[b'tree'].decode("ascii"))

    # Verify that path is an empty directory
    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not a directory {args.path}!")
        if os.listdir(args.path):
            raise Exception(f"Not empty {args.path}!")
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))

def tree_checkout(repo, tree, path):
    for item in tree.items:
        obj = GitObject.object_read(repo, item.sha)
        dest = os.path.join(path, item.path)

        if obj.fmt == b'tree':
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b'blob':
            # @TODO Support symlinks (identified by mode 12****)
            with open(dest, 'wb') as f:
                f.write(obj.blobdata)

def ref_resolve(repo, ref):
    path = GitRepository.repo_file(repo, ref)

    # Sometimes, an indirect reference may be broken.  This is normal
    # in one specific case: we're looking for HEAD on a new repository
    # with no commits.  In that case, .git/HEAD points to "ref:
    # refs/heads/main", but .git/refs/heads/main doesn't exist yet
    # (since there's no commit for it to refer to).
    if not os.path.isfile(path):
        return None

    # Reads the path and stores it as 'fp'.
    with open(path, 'r') as fp:
        data = fp.read()[:-1]
        # Drop final \n ^^^^^
    # If the path is an indirect reference, recurse through it again starting from index 5
    # to drop the 'ref: '.
    if data.startswith("ref: "):
        return ref_resolve(repo, data[5:])
    # If it's just a SHA-1 hash or we reach a SHA-1 hash, return it.
    else:
        return data

def ref_list(repo, path=None):
    if not path:
        # If there is no clear refs dir path, find the 'refs' dir path in the current 'repo'.
        path = GitRepository.repo_dir(repo, "refs")
    ret = dict()
    # Git shows refs sorted.  To do the same, we sort the output of
    # listdir
    for f in sorted(os.listdir(path)):
        # Join every item in the directory to the path so we have a full path.
        can = os.path.join(path, f)
        
        # If the joined path is a directory, recurse through it so we find all the refs.
        if os.path.isdir(can):
            ret[f] = ref_list(repo, can) # This is technically a dictionary that has another dictionary (directory) at ref 'f'.
        # Recurse through each ref until we find the SHA-1 hash.
        else:
            ret[f] = ref_resolve(repo, can)

    return ret

def cmd_show_ref(args):
    repo = GitRepository.repo_find()
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")

def show_ref(repo, refs, with_hash=True, prefix=""):
    if prefix:
        prefix = prefix + '/'
    for k, v in refs.items():
        if type(v) == str and with_hash:
            print (f"{v} {prefix}{k}")
        elif type(v) == str:
            print (f"{prefix}{k}")
        else:
            show_ref(repo, v, with_hash=with_hash, prefix=f"{prefix}{k}")

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    
    match args.command:
        # case "add"          : cmd_add(args)
        case "cat-file"     : cmd_cat_file(args)
        # case "check-ignore" : cmd_check_ignore(args)
        case "checkout"     : cmd_checkout(args)
        # case "commit"       : cmd_commit(args)
        case "hash-object"  : cmd_hash_object(args)
        case "init"         : cmd_init(args)
        case "log"          : cmd_log(args)
        # case "ls-files"     : cmd_ls_files(args)
        case "ls-tree"      : cmd_ls_tree(args)
        # case "rev-parse"    : cmd_rev_parse(args)
        # case "rm"           : cmd_rm(args)
        case "show-ref"     : cmd_show_ref(args)
        # case "status"       : cmd_status(args)
        # case "tag"          : cmd_tag(args)
        case _              : print("Bad command.")

