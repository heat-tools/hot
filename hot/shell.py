""" hot is the command-line tool for testing Heat Templates """
import collections
import json
import os
import re
import signal
import string
import sys
import yaml

from argh import arg, ArghParser
from heatclient.common import utils
from heatclient.v1 import Client as heatClient
from time import sleep, time
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import hot.lint
import hot.tests
import hot.utils
import hot.utils.auth
from hot.utils.yaml import OrderedDictYAMLLoader as OrderedDictYAMLLoader


ENV_VARS = ['OS_PASSWORD', 'OS_USERNAME', 'OS_TENANT_ID', 'OS_AUTH_URL']

DOC_SECTIONS = ['parameters', 'outputs']


def verify_environment_vars(variables):
    for variable in variables:
        env_list = ', '.join([str(env) for env in ENV_VARS])
        if os.environ.get(variable):
            next
        elif variable == 'OS_PASSWORD':
            if not os.environ.get('OS_AUTH_TOKEN'):
                raise KeyError("Tool requires either OS_PASSWORD or OS_AUTH_TO"
                               "KEN to be set.")
        else:
            raise KeyError("%s not set. Tool requires the following enviro"
                           "nmental variables to be set %s" % (variable,
                                                               env_list))


@arg('--template', default='.catalog')
@arg('--metadata', default='rackspace.yaml', help='Metadata file.')
@arg('--badge', default='None', help='Badge to add to the top of the output.')
@arg('-a', '--alphabetical', default=False, help='Alphabetically sort keys '
                                                 'when creating docs.')
def docs(**kwargs):
    """Generate the basics for the README.md based on the information in a
    given template.
    """
    template_attr = kwargs['template']
    badge_attr = kwargs['badge']
    metadata_attr = kwargs['metadata']
    alphabetical = kwargs['alphabetical']
    verified_template_directory = hot.utils.repo.check(template_attr)
    path_to_template = os.path.join(verified_template_directory, template_attr)
    path_to_metadata = os.path.join(verified_template_directory,
                                    metadata_attr)
    try:
        raw_template = get_raw_yaml_file(file_path=path_to_template)
        validated_template = yaml.load(raw_template, OrderedDictYAMLLoader)
        raw_metadata = get_raw_yaml_file(file_path=path_to_metadata)
        validated_metadata = yaml.load(raw_metadata, OrderedDictYAMLLoader)
    except StandardError as exc:
        sys.exit(exc)
    # Set necessary variables for CI badges based on rackspace.yaml information
    if 'github-organization' in validated_metadata:
        github_org = validated_metadata['github-organization']
    else:
        github_org = 'rackspace-orchestration-templates'
    if 'github-repository-name' in validated_metadata:
        github_repo = validated_metadata['github-repository-name']
    else:
        github_repo = False
    # If the --badge arg is passed let's print the badges out first
    # Also check and make sure we have values for the badge pieces
    if badge_attr and github_repo and github_org:
        if badge_attr == 'circle':
            url_prefix = "https://circleci.com/gh/"
            print("[![Circle CI]({0}{1}/{2}.png?style=badge)]({0}{1}/{2})"
                  .format(url_prefix, github_org, github_repo))
        else:
            pass
    # print validated_template['parameters']
    if 'description' in validated_template:
        print("Description\n===========\n\n%s\n" %
              validated_template['description'])
    # Pull out the instructions from rackspace.yaml
    if 'instructions' in validated_metadata:
        print("Instructions\n===========\n\n{0}\n".format(
              validated_metadata['instructions']))
    if 'resources' in validated_template:
        resources = get_resource_types(validated_template['resources'])
        print("Requirements\n============\n* A Heat provider that supports the"
              " following:\n  * %s\n* An OpenStack username, password, and ten"
              "ant id.\n* [python-heatclient](https://github.com/openstack/pyt"
              "hon-heatclient)\n`>= v0.2.8`:\n\n```bash\npip install python-he"
              "atclient\n```\n\nWe recommend installing the client within a [P"
              "ython virtual\nenvironment](http://www.virtualenv.org/).\n" %
              '\n  * '.join(map(str, sorted(resources))))
    for section in DOC_SECTIONS:
        if section in validated_template:
            header = ""
            footer = ""
            if section is 'parameters':
                header = "Parameters\n==========\nParameters can be replaced "\
                         "with your own values when standing up a stack. Use"\
                         "\nthe `-P` flag to specify a custom parameter.\n"
            if section is 'outputs':
                header = "Outputs\n=======\nOnce a stack comes online, use `h"\
                         "eat output-list` to see all available outputs.\nUse"\
                         " `heat output-show <OUTPUT NAME>` to get the value "\
                         "of a specific output.\n"
                footer = "\nFor multi-line values, the response will come in "\
                         "an escaped form. To get rid of\nthe escapes, use `e"\
                         "cho -e '<STRING>' > file.txt`. For vim users, a sub"\
                         "stitution\ncan be done within a file using `%s/\\\\"\
                         "n/\\r/g`."
            convert_to_markdown(header, footer, validated_template[section],
                                alphabetical)


def convert_to_markdown(header, footer, values, alphabetical):
    """Convert input to markdown format"""
    if alphabetical:
        values = collections.OrderedDict(sorted(values.items()))
    outputs = "%s" % header
    for value in values:
        key = value
        outputs = outputs + "\n* `%s`: " % key
        v = values[key]
        if 'description' in v:
            description = values[key]['description']
            outputs = outputs + "%s " % description
        if 'default' in v:
            default = values[key]['default']
            if isinstance(default, str) and len(default) == 0:
                default = "''"
            outputs = outputs + "(Default: %s)" % default
    outputs = outputs + "\n%s" % footer
    print(outputs)


def get_resource_types(resources):
    resources_list = set()
    for resource in resources:
        if 'type' in resources[resource]:
            resources_list.add(resources[resource]['type'])
    return resources_list


@arg('project', help='name of the template project to begin')
@arg('-s', '--skeleton', default='https://github.com/brint/template-skeleton',
     help='git repo to clone when initializing this project')
@arg('-b', '--branch', help='optional: specify the branch to clone')
@arg('--no-git-init', default=False, help="Do not use 'git init' to initialize"
                                          " the project")
@arg('-v', '--verbose', default=False, help='show more verbose output while in'
                                            'itializing the project')
def init(project, **kwargs):
    """ Initialize a template project by cloning a skeleton repo.

    TODO: Implement verbose functionality
    """
    skeleton = kwargs['skeleton']
    branch = kwargs['branch']
    verbose = kwargs['verbose']
    no_git = kwargs['no_git_init']

    if hot.utils.string.valid_project_name(project):
        if branch:
            if hot.utils.repo.valid_branch_name(branch):
                if no_git:
                    hot.utils.repo.clone_repo(skeleton, project, branch,
                                              'False')
                else:
                    hot.utils.repo.clone_repo(skeleton, project, branch)
            else:
                raise Exception("Invalid branch name: '%s'" % branch)
        else:
            if no_git:
                hot.utils.repo.clone_repo(skeleton, project, git_init=False)
            else:
                hot.utils.repo.clone_repo(skeleton, project)

    else:
        raise Exception("Invalid project name. Name must be a string <100 char"
                        "acters. Name provided: %s" % project)


@arg('--template', default='.catalog', help='Heat template to launch.')
@arg('--metadata', default='rackspace.yaml', help='Metadata file to audit')
def lint(**kwargs):
    """Check a template against a set of best practices"""
    verified_template_directory = hot.utils.repo.check(kwargs['template'])
    template = kwargs['template']
    metadata = kwargs['metadata']

    path_to_template = os.path.join(verified_template_directory, template)
    path_to_metadata = os.path.join(verified_template_directory, metadata)

    try:
        raw_template = get_raw_yaml_file(file_path=path_to_template)
        validated_template = hot.utils.yaml.load(raw_template)
        raw_metadata = get_raw_yaml_file(file_path=path_to_metadata)
        validated_metadata = hot.utils.yaml.load(raw_metadata)

    except StandardError as exc:
        sys.exit(exc)

    for rule_object_name in hot.lint.RULES:
        rule = getattr(hot.lint, rule_object_name)(validated_template,
                                                   validated_metadata)
        rule.check()


def tests_subset_ci(tests):
    if 'CIRCLE_NODE_TOTAL' in os.environ and \
       'CIRCLE_NODE_INDEX' in os.environ:
        increment = 0
        node_total = int(os.environ.get('CIRCLE_NODE_TOTAL'))
        node_index = int(os.environ.get('CIRCLE_NODE_INDEX'))
        tests_to_run = []
        for case in tests:
            if (increment % node_total) == node_index:
                tests_to_run.append(case)
            increment += 1
        print "selecting {}/{} tests for node {}/{}. Running:\n{}\n".format(
            len(tests_to_run),
            len(tests),
            node_index,
            node_total,
            "\n".join([test.get('name') for test in tests_to_run]))
        return tests_to_run
    else:
        return tests


@arg('--template', default='.catalog', help='Heat template to launch.')
@arg('--tests-file', default='tests.yaml', help='Test file to use.')
@arg('-k', '--keep-failed', default=False, help='Do not delete a failed test '
                                                'deployment.')
@arg('-s', '--sleep', default=15, type=int, help='Frequency for checking test '
                                                 'stack status.')
@arg('--test-cases', nargs='+', type=str, help='Space delimited list of '
                                               'tests to run. If none are '
                                               'specified, all will be run.')
@arg('-P', '--parameters', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
     help='Parameter values used to create the stack. This can be specified '
     'multiple times, or once with parameters separated by a semicolon. The '
     'parameters specified here will override anything defined in the tests.',
     action='append')
@arg('--insecure', default=False, help='Same as to -k flag with curl, do not '
     'strictly validate SSL certificates.')
@arg('--ci-parallel', default=False, help='Parallelize using CI provider '
     'methods. CircleCI is supported using the '
     'CIRCLE_NODE_TOTAL & CIRCLE_NODE_INDEX environment variables.')
def test(**kwargs):
    """ Test a template by going through the test scenarios in 'tests.yaml' or
    the tests file specified by the user
    """
    verified_template_directory = hot.utils.repo.check(kwargs['template'])
    template_attr = kwargs['template']
    tests_attr = kwargs['tests_file']
    test_cases = kwargs['test_cases']
    sleeper = kwargs['sleep']
    keep_failed = kwargs['keep_failed']
    parameter_overrides = kwargs['parameters']
    insecure = kwargs['insecure']
    parallelize_ci = kwargs['ci_parallel']

    path_to_template = os.path.join(verified_template_directory, template_attr)
    path_to_tests = os.path.join(verified_template_directory, tests_attr)
    try:
        verify_environment_vars(ENV_VARS)
        raw_template = get_raw_yaml_file(file_path=path_to_template)
        validated_template = hot.utils.yaml.load(raw_template)
        raw_tests = get_raw_yaml_file(file_path=path_to_tests)
        validated_tests = hot.utils.yaml.load(raw_tests)
        tests = update_dict_env(validated_tests['test-cases'])
    except StandardError as exc:
        sys.exit(exc)

    auth = hot.utils.auth.OSAuth()

    if insecure:
        hc = heatClient(endpoint=auth.get_heat_url(), token=auth.get_token(),
                        insecure=True)
    else:
        hc = heatClient(endpoint=auth.get_heat_url(), token=auth.get_token())

    if test_cases:
        user_tests = []
        for case in test_cases:
            for test in tests:
                if test['name'] == case:
                    user_tests.append(test)
        if not user_tests or len(user_tests) < len(test_cases):
            user_defined_tests = ', '.join([str(t) for t in test_cases])
            sys.exit("Error: One or more of the following test cases not "
                     "found: %s" % user_defined_tests)
        tests = user_tests

    if parallelize_ci:
        tests = tests_subset_ci(tests)

    for test in tests:
        stack = launch_test_deployment(hc, validated_template,
                                       parameter_overrides, test, keep_failed,
                                       sleeper)
        if 'resource_tests' in test:
            try:
                run_resource_tests(hc, stack['stack']['id'],
                                   test)
                print("  Test Passed!")
            except:
                exctype, value = sys.exc_info()[:2]
                delete_test_deployment(hc, stack, keep_failed)
                sys.exit("Test Failed! %s: %s" %
                         (exctype, value))
        delete_test_deployment(hc, stack)


def run_resource_tests(hc, stack_id, resource_tests):
    stack_info = hc.stacks.get(stack_id)
    outputs = stack_info.to_dict().get('outputs', [])
    # Sub out {get_output: value} lines
    resource_tests = update_dict(resource_tests['resource_tests'], outputs)

    # For debugging purposes
    # print resource_tests

    if 'ssh_key_file' in resource_tests:
        ssh_key_file = resource_tests['ssh_key_file']
    else:
        ssh_key_file = 'tmp/private_key'

    # If the file path specified does not exist, create it.
    if not os.path.exists(os.path.dirname(ssh_key_file)):
        os.makedirs(os.path.dirname(ssh_key_file))

    if 'ssh_private_key' in resource_tests:
        with os.fdopen(os.open(ssh_key_file, os.O_WRONLY | os.O_CREAT, 0o600),
                       'w') as handle:
            handle.write(resource_tests['ssh_private_key'])

    for test in resource_tests['tests']:
        test_name = test.keys()[0]
        # print test[test_name]
        if "fabric" in test[test_name]:
            hot.tests.fab.run_fabric_tasks(test_name, test[test_name])
        elif "script" in test[test_name]:
            hot.tests.script.run_script(test_name, test[test_name])
        else:
            print("  No tests defined.")
    if 'ssh_private_key' in resource_tests:
        hot.utils.files.delete_file(ssh_key_file)


def update_dict(items, outputs):
    """Update dict based on user input.  This will take anything things like
       { get_output: server_ip } and replace it with the value of the given
       output.
    """
    try:
        for k, v in items.items():
            if isinstance(v, dict):
                items[k] = update_dict(v, outputs)
            elif isinstance(v, list):
                new_list = []
                for e in v:
                    new_list.append(update_dict(e, outputs))
                items[k] = new_list
            elif isinstance(v, int):
                items[k] = v
            elif k == 'get_output':
                return get_output(v, outputs)
            else:
                items[k] = v
    except:
        pass
    return items


def update_dict_env(tests):
    updated_list = []
    for test in tests:
        updated_list.append(test_dict_env_update(test))
    return updated_list


def test_dict_env_update(items):
    """Update the dict that will be used for provisioning. This will take
       anything like { get_env: ENVIRONMENT_VAR } and replace it with the value
       of the specified environment variable.
    """
    try:
        for k, v in items.items():
            if isinstance(v, dict):
                items[k] = test_dict_env_update(v)
            elif isinstance(v, list):
                new_list = []
                for e in v:
                    new_list.append(test_dict_env_update(e))
                items[k] = new_list
            elif isinstance(v, int):
                items[k] = v
            elif k == 'get_env':
                return get_env(v)
            else:
                items[k] = v
    except KeyError:
        raise
    except:
        pass
    return items


def convert_to_array(value):
    """Converts string to array, if `value` is an array, returns `value`"""
    if isinstance(value, list):
        return value
    elif isinstance(value, basestring):
        return [value]


def get_output(key, outputs):
    for output in outputs:
        if output['output_key'] == key:
            return output['output_value']


def get_env(key):
    try:
        return os.environ[key]
    except KeyError:
        raise KeyError("KeyError: Environment variable `%s` is not defined" %
                       (key))


def delete_test_deployment(hc, stack, keep_deployment=False):
    if keep_deployment:
        print("  Keeping %s up." % stack['stack']['id'])
    else:
        print("  Deleting %s" % stack['stack']['id'])
        hc.stacks.delete(stack['stack']['id'])


def launch_test_deployment(hc, template, overrides, test, keep_failed,
                           sleeper):
    pattern = re.compile('[\W]')
    stack_name = pattern.sub('_', "%s-%s" % (test['name'], time()))
    data = {"stack_name": stack_name, "template": yaml.safe_dump(template)}

    timeout = get_create_value(test, 'timeout')
    parameters = get_create_value(test, 'parameters')

    if overrides:
        if parameters:
            parameters = dict(parameters.items() +
                              utils.format_parameters(overrides).items())
        else:
            parameters = utils.format_parameters(overrides)

    retries = get_create_value(test, 'retries')  # TODO: Implement retries

    if timeout:
        timeout_value = timeout * 60
        signal.signal(signal.SIGALRM, hot.utils.timeout.handler)
        signal.alarm(timeout_value)
    if parameters:
        data.update({"parameters": parameters})

    print("Launching: %s" % stack_name)
    stack = hc.stacks.create(**data)

    if timeout_value:
        print("  Timeout set to %s seconds." % timeout_value)

    try:
        monitor_stack(hc, stack['stack']['id'], sleeper)
        if timeout_value:
            signal.alarm(0)
    except Exception as exc:
        print exc
        if "Script exited with code 1" not in str(exc):
            print("Infrastructure failure. Skipping tests.")
        else:
            print("Automation scripts failed. Running tests anyway:")
            try:
                run_resource_tests(hc, stack['stack']['id'], test)
                print("  Test Passed!")
            except:
                exctype, value = sys.exc_info()[:2]
                print("Test Failed! {0}: {1}".format(exctype, value))
        delete_test_deployment(hc, stack, keep_failed)
        sys.exit("Stack failed to deploy")
    return stack


def get_create_value(test, key):
    if key in test['create']:
        return test['create'][key]
    return None


def monitor_stack(hc, stack_id, sleeper=15):
    incomplete = True
    while incomplete:
        print("  Stack %s in progress, checking in %s seconds.." % (stack_id,
                                                                    sleeper))
        sleep(sleeper)
        status = hc.stacks.get(stack_id)
        if status.stack_status == u'CREATE_COMPLETE':
            incomplete = False
            print("  Stack %s built successfully!" % stack_id)
        elif status.stack_status == u'CREATE_FAILED':
            stack_status = status.stack_status_reason
            print("  Stack %s build failed! Reason:\n  %s" % (stack_id,
                                                              stack_status))
            raise Exception("Stack build {0} failed! Reason: {1}".format(
                stack_id, stack_status))


def get_raw_yaml_file(file_path=None):
    """

    Reads the contents of any YAML file in the repository as a string

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
            test,
            docs,
            init,
            lint,
        ])

        argparser.dispatch()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
