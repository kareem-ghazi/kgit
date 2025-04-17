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

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    
    match args.command:
        # case "add"          : cmd_add(args)
        case "cat-file"     : cmd_cat_file(args)
        # case "check-ignore" : cmd_check_ignore(args)
        # case "checkout"     : cmd_checkout(args)
        # case "commit"       : cmd_commit(args)
        case "hash-object"  : cmd_hash_object(args)
        case "init"         : cmd_init(args)
        case "log"          : cmd_log(args)
        # case "ls-files"     : cmd_ls_files(args)
        # case "ls-tree"      : cmd_ls_tree(args)
        # case "rev-parse"    : cmd_rev_parse(args)
        # case "rm"           : cmd_rm(args)
        # case "show-ref"     : cmd_show_ref(args)
        # case "status"       : cmd_status(args)
        # case "tag"          : cmd_tag(args)
        case _              : print("Bad command.")

