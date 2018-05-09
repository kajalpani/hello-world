#!/app/python/2.7.5/RHEL6/bin/python -u

import subprocess
import argparse
import os
import textwrap

class Submodule:
    def __init__(self, name, commit):
        self.name = name
        self.commit = commit
        self.new_commit = None
        self.valid = None

def bash_exec(cmd):
    """Function to execute bash command and capture its output.

    This function will call given command in bash terminal
    (with nested env). If any of internal commands will return
    exit code different than 0, exeption will be raised.

    Parameters
    ----------
    param1 : string
        Command to be executed

    Returns
    -------
    string
        Executed command output
    """
    return subprocess.check_output(['bash','-c', cmd], stderr=subprocess.STDOUT)

def get_submodules():
    """Function to parse submodules in current workdir.

    This function reads git metadata to detect every submodule
    present in current workdir. It creates one instance of Submodule
    class for each detected submodule.

    Parameters
    ----------

    Returns
    -------
    array
        Array of 'Submodule' objects
    """
    try:
        bashCommand = "git submodule status | grep -oP \"[\d\w]+\s\w+\""
        output = subprocess.check_output(['bash','-c', bashCommand])
        submodules = output.split("\n")[0:-1]
        submodules_array = [
            Submodule(submodule.split(" ")[1], submodule.split(" ")[0])
            for submodule in submodules
        ]
        return submodules_array
    except:
        return None

def fetch_submodule(submodule_name):
    """Function to fetch changes from remote repository

    This function calls 'git fetch --all' in repository specified by path.
    Function not resistant to exceptions.

    Parameters
    ----------
    param1 : string
        Path to repository

    Returns
    -------
    """
    bash_exec("cd %s; git fetch --all" % submodule_name)

def checkout_submodule(repo_path, commit_sha):
    """Function to checkout git repository to specified commit.

    This function calls 'git checkout <commit_sha>' in repository specified by path.
    Function not resistant to exceptions.

    Parameters
    ----------
    repo_path : string
        Path to repository
    commit_sha : string
        Commit to be checkouted in repo

    Returns
    -------
    """
    bash_exec("cd %s; git checkout %s" % (repo_path, commit_sha))

def set_new_commit_to_submodule(submodules, submodule_name, commit_sha):
    """Function to update new_commit var in detected submodules.

    This function looks for <submodule_name> in <submodules>
    and sets new_commit varable in matching element.
    Function not resistant to exceptions.

    Parameters
    ----------
    submodules : array
        Array of Submodule objects
    submodule_name : string
        Name of submodule to be updated
    commit_sha : string
        Commit sha to be set in matching Submodule as new_commit variable

    Returns
    -------
    """
    for s in submodules:
        if s.name == submodule_name:
            s.new_commit = commit_sha;
            print("[INFO] Setting %s as new_commit for '%s' submodule" % (commit_sha, s.name))

def check_stage():
    """Function to check for files added to git stage area.

    This function looks for files added to staging area.

    Parameters
    ----------

    Returns
    -------
    bool
        Returns True if at least one file is staged, False otherwise.
    """
    try:
        output = bash_exec("git status --porcelain | grep -P \"^M\"")
        print("[INFO] Files staged for commit: \n%s" % output)
        return True
    except:
        print("[WARNING] Staging area empty!")
        return False

def get_submodule_old_new_commits(submodule_name):
    """Function to check for submodule checkouted commit.

    This function checks if any submodule is set to commit not
    pointed by parrent repository.

    Parameters
    ----------
    submodule_name : string
        Name of submodule to be checked

    Returns
    -------
    string, string :
        Returns pair of commits - commit pointed by parent repo and commit currently checkouted.
        If submodule have checkouted commit pointed by parent repo, then <None, None> is returned.
    """
    out = ""
    try:
         out = bash_exec("git diff %s | grep -oP \"(?<=Subproject commit )[\d\w]+\"" % submodule_name)
    except:
         print("[INFO] No new commits or modifications detected in '%s' submodule" % submodule_name)
         return None, None
    if out.count('\n') == 2:
        old_commit = out.split("\n")[0]
        new_commit = out.split("\n")[1]
        if new_commit == old_commit:
            print("[INFO] Detected modifications, but no new commits in '%s' submodule" % submodule_name)
            return None, None
        else:
            return old_commit, new_commit
    else:
        return None, None

def get_commits_log(repo_path, old_commit_sha, new_commit_sha):
    """Function get list of commits between two points.

    This function returns formatted list of commits created between two specified commits.
    Each entry in list consists of commit number (SHA), commit message and commit author.
    Function not resistant to exceptions.

    Parameters
    ----------
    repo_path : string
        Path to repo
    old_commit_sha : string
        Log start point
    new_commit_sha : string
        Log stop point

    Returns
    -------
    string :
        String with extracted git log
    """
    return bash_exec(
        "cd %s;git --no-pager log --graph \
         --pretty=format:'%%Cred %%h %%Creset - %%s %%Cgreen(%%cN)%%Creset' %s..%s"
        % (repo_path, old_commit_sha, new_commit_sha))

def get_commits_count(repo_path, old_commit_sha, new_commit_sha):
    """Function to get count of commits between two points.

    This function calculates count of commits between two points in git history.
    Function not resistant to exceptions

    Parameters
    ----------
    repo_path : string
        Path to repo
    old_commit_sha : string
        Log start point
    new_commit_sha : string
        Log stop point

    Returns
    -------
    int :
        Count of commits between two points. If start point is below stop point, 0 will be returned.
    """
    return int(bash_exec("cd %s;git rev-list %s..%s --count" % (repo_path, old_commit_sha, new_commit_sha)))

def commit_exist(repo_path, commit_sha):
    """Function to check for commit existence in specified repo.

    This function checks if given commit number exists in spedified repository (local clone)

    Parameters
    ----------
    repo_path : string
        Path to repo
    commit_sha : string
        Commit sha to be checked

    Returns
    -------
    bool :
        True if commit exists False instead
    """
    try:
        bash_exec("cd %s;git branch --contains %s &> /dev/null" % (repo_path, commit_sha))
        return True
    except:
        return False

if __name__=="__main__":
    help_string = """
    Python module designed for managing git nested repositories (submodules)
    It provides two methds for creating commits in repositories with submodules:
    1. Manual
        In this method, new commits in submodules must be manualy set to via
        dedicated flag, e.g:
            --submodule <sub_a_name> <sub_a_commit_sha> <sub_b> <sub_b_commit_sha> ...
    2. Auto
        In this mode, parent repository commit will be created from current checkouts
        in submodules
    Both methods have restriction that current commits in any submodule cannot be older
    that commits currently pointed by latest parent commit.
"""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent(help_string))
    parser.add_argument("--parent-branch-name",
        dest="parent_branch_name", type=str, default="master",
        help="Specifies remote branch name to which commit will be pushed, default 'master'")
    parser.add_argument("--submodule", nargs='+', type=str, default="none",
        help="Specifies submodules and commits in those, \
              which will be included in parent commit, eg. --submodule x <sha_x> y <sha_y> ...")
    parser.add_argument("--auto", action='store_true',
        help="This mode will skip --submodule flag ant create commit in parrent repo taking it as it is")
    parser.add_argument("--push", dest="push", action='store_true', default=False,
        help="Created commit will be pushed to remote repository")
    args = parser.parse_args()

    commit_msg_header = "Updated submodules: "
    commit_msg_body = ""
    submodules = get_submodules();
    if submodules:
    #Auto mode: User checked out submodules manualy to sort of commits
    #           This mode will create commit for those checked out ones
        if args.auto == True:
            print("[INFO] Working in auto mode")
            for s in submodules:
                print("[INFO] --------------------")
                s.commit, s.new_commit = get_submodule_old_new_commits(s.name)
                if s.new_commit != None:
                    if get_commits_count(s.name, s.commit, s.new_commit):
                        s.valid = True
                    else:
                        s.valid = False
                        print("[WARNING] Choosen commit in %s submodule is not ahead of current one" % s.name)
                        print("[WARNING] Skipping submodule %s" % s.name)
    #No auto mode: Commits for submodules will be readed from CLI
        else:
            for i in range(len(args.submodule)-1)[::2]:
                set_new_commit_to_submodule(submodules, args.submodule[i], args.submodule[i + 1])
            for s in submodules:
                fetch_submodule(s.name)
                if s.new_commit:
                    if commit_exist(s.name, s.new_commit):
                        if get_commits_count(s.name, s.commit, s.new_commit):
                            checkout_submodule(s.name, s.new_commit)
                            s.valid = True
                        else:
                            print("[ERROR] Submodule '%s' cannot be checked out to commit older than current one" % (s.name))
                    else:
                        print("[ERROR] Commit %s does not exist in '%s' submodule" % (s.new_commit[0:7], s.name))
    #Common part, both for auto & manual mode
        for s in submodules:
            if s.valid:
                bash_exec("git add %s" % (s.name))
                commit_msg_header += "%s -> ( %s ) " % (s.name, s.new_commit[0:7])
                commit_msg_body += "\nSubmodule '%s' commits: \n" %s.name
                commit_msg_body += get_commits_log(s.name, s.commit, s.new_commit).replace("\"", "'")
                s.valid = True

        if check_stage():
            bash_exec("git commit -m \"%s\"" % (commit_msg_header + "\n" + commit_msg_body))
            print("[INFO] Commit created!\n-----------------------------------\n%s" % bash_exec("git log -n 1"))
            if args.push == True:
                output = bash_exec("git push origin %s" % args.parent_branch_name)
                print("Commit pushed to remote!\n%s" % output)
        else:
            print("[WARNING] Nothing to commit!")
    else:
        print("[ERROR] Failed to detect submodule(s). Are you in correct repository?")
