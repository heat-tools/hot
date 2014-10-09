hot
===
WARNING: Use at your own risk! This comes with no warranties, guarantees, or
promises of any kind.

Command line helper utility for authoring and performing extended validation
testing on [Heat](https://wiki.openstack.org/wiki/Heat) templates. The name
comes from the acronym for Heat Orchestration Templates. This is a very
Rackspace-y tool. If people are willing to help contribute, we can open up some
of the more provider specific things like the linting functions.

Requirements
============
* For Ubuntu 12.04/14.04, install the necessary packages:
  * `sudo apt-get install -y python-dev python-pip gcc libxslt1-dev python-lxml git`
* All systems: [pip](http://pip.readthedocs.org/en/latest/installing.html)
  1.5.6+ must be installed.
* [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation)
  is recommended.
* The following environmental variables must be properly set before running
  `hot`:
  * `OS_PASSWORD`
  * `OS_USERNAME`
  * `OS_TENANT_ID`
  * `OS_AUTH_URL`
  * `HEAT_URL`
* Optionally, you can set `OS_AUTH_TOKEN` as opposed to `OS_PASSWORD`.

Installation
============
Install with pip (recommended):
```
pip install hot
```
Clone it down, install it:

```
git clone git@github.com:brint/hot.git
cd hot
virtualenv .hot
source .hot/bin/activate
pip install -r requirements.txt
python setup.py install
```

Usage
=====
Ensure you have activated your virtual environment before every use.

The `hot` command takes a single verb, ie: 'test'.  Issuing the command without
a verb will result in the usage output:
```
(.hot)~/src/hot $ hot
usage: hot [-h] {test,docs,init,lint} ...
hot: error: too few arguments
```
`hot` must be run inside of a template repository that contains a `tests.yaml`
file. `tests.yaml` dictates how `hot` will spin up deployments and test them.
Use the public
[memcached](https://github.com/rackspace-orchestration-templates/memcached)
template repo as a starting point for using `hot`.


Creating Template Tests
=======================
Tests are specified in the `tests.yaml` file in the root of the template repo.
If your test scripts require additional dependencies or libraries, ensure those
are installed prior to `hot` running.  `hot` will not resolve dependencies for
you.
## get_output
There is a useful function called `get_output` that can be called to plug
in outputs from your heat stack. It will replace itself with the output value
for a given `output-list` key.  The output you fetch, must be in the outputs
section of your template.  An example would be:
```yaml
hosts: { get_output: server_ip }
```
This example will look for the key `server_ip` in the `output-list` of the
stack once it comes up. This `get_output` function will then replace itself
with the value of `server_ip`.  Assuming the IP comes out to be 1.2.3.4, the
dictionary will be updated and interpreted like this when the tests are run:
```yaml
hosts: 1.2.3.4
```

## Creating/Launching a stack
The `test-cases` are a list of tests to run. They are run sequentially, and
there is no limit to the number you can run.  There are only a couple options:
- `name`: Required value that must be a string
- `create`: Hash of
  - `parameters`: Optional hash. If no parameters are provided, a heat stack
    will be launched with the default values specified in the template.  
  - `timeout`: Optional integr, in minutes. Set how long to wait for a stack to
    complete building. If it takes longer than the `timeout` value, mark it as
    a failure, and delete the stack. If something is taking hours to build,
    something's wrong.

Here's an example:
```yaml
test-cases:
- name: Default Build Test # Deploy using all default options
  create:
    parameters:
      flavor: 2GB Standard Instance
      memcached_port: 11212  
    timeout: 30 # Deployment should complete in under 30 minutes
```
The test will be considered successful if the template builds successfully
within the user defined timeout window.

## Test Options
The test options are documented if you run `hot test --help`:
```yaml
$ hot test --help
usage: hot test [-h] [--template TEMPLATE] [--tests-file TESTS_FILE] [-k]
                [-s SLEEP] [--test-cases TEST_CASES [TEST_CASES ...]]

 Test a template by going through the test scenarios in 'tests.yaml' or
    the tests file specified by the user


optional arguments:
  -h, --help            show this help message and exit
  --template TEMPLATE   Heat template to launch. (default: .catalog)
  --tests-file TESTS_FILE
                        Test file to use. (default: tests.yaml)
  -k, --keep-failed     Do not delete a failed test deployment. (default:
                        False)
  -s SLEEP, --sleep SLEEP
                        Frequency for checking test stack status. (default:
                        15)
  --test-cases TEST_CASES [TEST_CASES ...]
                        Space delimited list of tests to run. If none are
                        specified, all will be run. (default: None)
```
As a note, if you have spaces, commas, or other special characters, put the
test name in double quotes, and each string will be interpreted individually.
Example:

```bash
hot test --test-cases "First Test" "Second Test, with special options"
```

## Resource Tests
These are a list of tests with arbitrary names to run. The keys under the test
name define what test suite to run.  As of now, your options are `fabric` or
`script`.

There are two values that can be put directly under resource tests to be laid
down for all tests that are run:
- `ssh_private_key`: Actual value of the SSH private key for logging into Linux
  resources.
- `ssh_key_file`: Path where we should lay down the `ssh_private_key`. This is
  in place since the key file has specific permission requirements.

### Fabric
`hot` supports template yaml sytax checking, stack build success verification,
and highly-flexible [fabric](http://www.fabfile.org/)-based integration testing
to test the resulting servers using
[envassert](https://bitbucket.org/r_rudi/envassert) and any other methods
possible in a python script. You really can do anything.

The ideal use case for fabric tests are when you want to tests from within a
resource. This is great for checking firewall rules, running processes, and
anything else you would like to check on a system.

Under the `fabric` section, the only thing you need to define is your [fabric
environment](http://docs.fabfile.org/en/latest/usage/env.html).  All of the
settings under `env` are fabric environmental variables. At a minimum, the
`fabfile`, which defines where your test script is located, the `tasks`, which
are the `@task` sections in your fab file, and the `hosts`, which define the
IP(s) to test are required.

Here's an example `tests.yaml` showing how to setup fabric tests for our
Memcached templates:

```yaml
test-cases:
- name: Default Build Test # Deploy using all default options
  create:
    timeout: 30 # Deployment should complete in under 30 minutes
  resource_tests: # Tests to run on the resources themselves
    ssh_private_key: { get_output: private_key } # Fetch from output-list of stack
    ssh_key_file: tmp/private_key # File to write with ssh_private_key
    tests:
    - memcached_server:
        fabric:
          # Fabric environment settings to use while running envassert script
          # http://docs.fabfile.org/en/latest/usage/env.html
          env:
            user: root
            key_filename: tmp/private_key
            hosts: { get_output: server_ip } # Fetch from output-list of stack
            tasks:
              - check
            abort_on_prompts: True
            connection_attempts: 3
            disable_known_hosts: True
            use_ssh_config: True
            fabfile: test/fabric/memcached_server.py # Path to envassert test
```

The yaml syntax checks and build success verification happen by default for
each `test-case`. The test `memcached-server` invokes fabric against the
ip addresses contained in the stack output `server_ip` using the `fabfile` at
the path `test/fabric/memcached_server.py`, running the fabric task `check`.

This task uses [envassert](https://bitbucket.org/r_rudi/envassert) to ensure
the server is in the desired state:

```python
@task
def check():
    assert package.installed("memcached")
    assert file.exists("/etc/memcached.conf")
    assert port.is_listening(11211)
    assert process.is_up("memcached")
    assert service.is_enabled("memcached")
```

If an exception is encountered, the test is considered failed.

While envassert is useful for basic server state checks, any python code may
be used in the fabfile. The code runs in the context of a fabric session,
so fabric methods such as `run()` and `get()` are available to execute
remote commands and inspect their output. See the [fabric API docs](http://docs.fabfile.org/en/1.9/api/core/operations.html)
for more options.

Here is an example function to check the state of an application
and the associated fabric task to invoke it:

```python
import re
from fabric.api import env, run, hide, task


def vestacp_is_responding():
    with hide('running', 'stdout'):
        homepage = run('curl --insecure https://localhost:8083/login/')
        if re.search('Vesta Control Panel', homepage):
            return True
        else:
            return False

@task
def check():
    assert vestacp_is_responding(), 'vestacp did not respond as expected.'
```

If the `/login` endpoint does not return a document containing the string
`Vesta Control Panel`, the test will fail, and the string
`vestacp did not respond as expected.` will appear in the stack trace.

### Script
The ideal use case for script tests are when you want to tests from outside the
environment. Examples could include running selenium tests from your CI server,
verifying service availability from outside the environment, or calling third
party services to run tests such as vulnerability assessment or performance
testing. You can really do anything in here.

The setup is very similar to the fabric tests. Tests will be run in the order
they are provided, and it's possible to sequentially run a fabric test and then
a script, or vice versa. The parts of the script test are optional, no default
values will be assumed or set.  Here are the major sections:
- hosts
- files
- environment
- commands

#### Hosts
A list of hashes that include the IP and all hostnames to associate to that IP.
The user running the script either needs write access to the hosts file, or
sudo permissions to run `sudo mv /tmp/etc_hosts.tmp /etc/hosts`. `hot` will try
to overwrite `/etc/hosts`, if that fails, it'll write `/tmp/etc_hosts.tmp` and
then try to move it with the previously mentioned sudo command. The function
will append any values in the `hosts` section, so all values that were in the
hosts file before the test was run should be there after the fact. This does
not currently back up or restore the original hosts file after the run. This is
designed with containers in mind where a fresh container will be launched for
every test.

Within the list of hosts, there should be two keys within each hash:
- `ip`: string of the IPv4 or IPv6 address to set in the hosts file.
- `hostnames`: list of hostnames to associate with the `ip` value.

#### Files
A list of files to write. Each element will have a key and value. The key will
be the file name to write, the value will be what's written into the file.
Files will be written as the user that `hot` was launched as.

#### Environment
A list of environmental variables to set prior to running the command.

#### Commands
The commands are run after the optional `hosts`, `files`, and `environment`
settings are applied. This is a list of commands and optional `command_args` to
pass in. The breakdown for each command is as follows:

- `command`: The command to run
- `command_args`: Optional list of additional arguments to append to the end of
  the command.

Here's an example config:
```yaml
test-cases:
- name: Default Build Test # Deploy using all default options
  create:
    timeout: 30 # Deployment should complete in under 30 minutes
  resource_tests:
    tests:
    - site_test:
        script:
          hosts: # Requires user write access to /etc/hosts or passwordless
                 # sudo ability to overwrite the hosts file. See Hosts section
                 # in documentation.
            - ip: 1.2.3.4
              hostnames:
              - example.com
              - stats.example.com
              - { get_output: host }
            - ip: { get_output: server_ip }
              hostnames:
              - example2.com
              - admin.example.com
          files: # Write the following files as user. Syntax: File: "value to put in file"
            - tmp/key2.pem: { get_output: secondary_key }
            - groot.txt: 'I am Groot'
          environment:
            - hosts: { get_output: server_ip }
            - key: { get_output: private_key }
            - local: localhost
          commands:
            - command: "python test/script/example.py"
              command_args:
                - "--ip"
                - { get_output: server_ip }
            - command: "./special validate"
              command_args:
                - "--ip"
                - { get_output: server_ips }
```
