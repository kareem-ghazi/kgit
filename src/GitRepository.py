import configparser
import os

class GitRepository(object):
    """A git repository"""
    
    worktree = None
    gitdir = None
    conf = None
    
    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")
        
        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a Git repository: {path}")
        
        # Read configuration file in .git/config
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")
        
        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")
        
        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion: {vers}")
    
def repo_path(repo, *path):
    """Compute path under repo's gitdir."""
    return os.path.join(repo.gitdir, *path)

def repo_dir(repo, *path, mkdir=False):
    """Same as repo_path, but mkdir *path if absent if mkdir."""
    
    path = repo_path(repo, *path)
    
    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception(f"Not a directory {path}")
        
    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

def repo_file(repo, *path, mkdir=False):
    """Same as repo_path, but create dirname(*path) if absent.  For
    example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create
    .git/refs/remotes/origin."""
    
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)

def repo_default_config():
    ret = configparser.ConfigParser()

    # Creates the ini config file 'config'.
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret

def repo_create(path):
    """Create a new repository at path."""
    
    repo = GitRepository(path, True)
    
    # First, we make sure the path either doesn't exist or is an
    # empty dir.
    
    if os.path.exists(path):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory!")
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception(f"{path} is not empty!")
    else:
        os.makedirs(repo.worktree)
        
    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)
    
    # .git/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

    # .git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo

def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    # If we haven't returned, recurse in parent, if w
    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        # Bottom case
        # os.path.join("/", "..") == "/":
        # If parent==path, then path is root.
        if required:
            raise Exception("No git directory.")
        else:
            return None

    # Recursive case
    return repo_find(parent, required)