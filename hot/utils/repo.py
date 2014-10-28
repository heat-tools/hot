"""Git and Github utility functions"""

import os
import shutil
import sys
import time

from git import Git
from subprocess import check_output, CalledProcessError
from urlparse import urlparse


def check(path):
    """ Determine if a command that expects to execute inside a template
        repo can continue. Checks for a .git directory and subsequently for
        a template.yaml file either in the working directory or the
        directory specified by the --template argument. If check passes,
        returns path to template repo.
    """

    error_message = '`%s` does not appear to be a template repo.'
    cwd = os.getcwd()

    template_attr = path

    if template_attr:
        if not os.path.isdir(os.path.join(cwd, '.git')):
            sys.exit(error_message % cwd)
        else:
            try:
                with open(os.path.join(cwd, template_attr)):
                    pass
            except IOError:
                sys.exit(error_message % cwd)

    else:
        if not os.path.isdir(os.path.join(cwd, '.git')):
            sys.exit(error_message % cwd)
        else:
            try:
                with open(template_attr):
                    pass
            except IOError:
                sys.exit(error_message % cwd)

    if not cwd.endswith('/'):
        cwd += '/'

    return cwd


def clone_repo(repo, path, branch=None, git_init=True):
    if branch:
        Git().clone('--branch', branch, repo, path)
    else:
        Git().clone(repo, path)

    starting_dir = os.getcwd()
    os.chdir(path)
    shutil.rmtree('.git')
    if git_init:
        Git().init()
    os.chdir(starting_dir)


def valid_branch_name(branch):
    try:
        Git().check_ref_format("--branch", branch)
        return True
    except GitCommandError:
        return False
