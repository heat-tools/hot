""" hot is the command-line tool for testing Heat Templates """
import json
import os
import sys
from urlparse import urlparse
import yaml

from argh import arg, alias, ArghParser

import hot.utils

@alias('test')
@arg('--template', default='template.yaml')
@arg('--tests-file', default='tests.yaml')
def do_template_test(args):
    """ Test a template by going through the test scenarios in 'tests.yaml' or
    the tests file specified by the user
    """
    path_to_template = hot.utils.repo.check(args)
    template_attr = getattr(args, 'template')
    path_to_yaml = os.path.join(path_to_template, template_attr)
    try:
        raw = get_raw_yaml_file(args, file_path=path_to_yaml)
        validated = hot.utils.yaml.load(raw)
        print "\nValidated yaml, here's the raw dump:\n\n%s" % validated
    except StandardError as exc:
        print exc
        sys.exit(1)


def get_raw_yaml_file(args, file_path=None):
    """

    Reads the contents of any YAML file in the repository as a string

    :param args: the pawn call argument
    :param file_path: the file name with optional additional path
        (subdirectory) or as a URL
    :returns: the string contents of the file

    """
    # file can be a URL or a local file
    file_contents = None
    parsed_file_url = urlparse(file_path)
    if parsed_file_url.scheme == '':
        # Local file
        try:
            _file = open(os.path.expanduser(file_path))
            file_contents = _file.read()
            _file.close()
        except IOError as ioerror:
            raise IOError('Error reading %s. [%s]' % (file_path, ioerror))
    else:
        raise Exception('URL scheme %s is not supported.' %
                        parsed_file_url.scheme)

    return file_contents


def main():
    """Shell entry point for execution"""
    try:
        argparser = ArghParser()
        argparser.add_commands([
            do_template_test,
        ])

        argparser.dispatch()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
