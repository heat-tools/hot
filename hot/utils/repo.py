"""Git and Github utility functions"""

import os
import sys
import re
import time

from subprocess import check_output, CalledProcessError
from urlparse import urlparse


def check(args):
    """ Determine if a command that expects to execute inside a template
        repo can continue. Checks for a .git directory and subsequently for
        a template.yaml file either in the working directory or the
        directory specified by the --template argument. If check passes,
        returns path to template repo.
    """

    error_message = '`%s` does not appear to be a template repo.'
    cwd = os.getcwd()

    #see if there is a 'template' attribute in args namespace
    template_attr = getattr(args, 'template')

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
