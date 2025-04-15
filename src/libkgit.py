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

argsp = argsubparsers.add_parser("init", help="Initialize an empty, new repository.")
argsp.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository.")

def cmd_init(args):
    GitRepository.repo_create(args.path)

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    
    match args.command:
        # case "add"          : cmd_add(args)
        # case "cat-file"     : cmd_cat_file(args)
        # case "check-ignore" : cmd_check_ignore(args)
        # case "checkout"     : cmd_checkout(args)
        # case "commit"       : cmd_commit(args)
        # case "hash-object"  : cmd_hash_object(args)
        case "init"         : cmd_init(args)
        # case "log"          : cmd_log(args)
        # case "ls-files"     : cmd_ls_files(args)
        # case "ls-tree"      : cmd_ls_tree(args)
        # case "rev-parse"    : cmd_rev_parse(args)
        # case "rm"           : cmd_rm(args)
        # case "show-ref"     : cmd_show_ref(args)
        # case "status"       : cmd_status(args)
        # case "tag"          : cmd_tag(args)
        case _              : print("Bad command.")

