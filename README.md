hot
===
WARNING: Use at your own risk! This comes with no warranties, guarantees, or
promises of any kind.

Command line helper utility for authoring and performing extended validation
testing on [Heat](https://wiki.openstack.org/wiki/Heat) templates. The name
comes from the acronym for Heat Orchestration Templates.

Requirements
============
* For Ubuntu 12.04/14.04, install the necessary packages:
  * `sudo apt-get install -y python-dev python-pip gcc libxslt1-dev python-lxml git`
* All systems: [pip](http://pip.readthedocs.org/en/latest/installing.html) must be
  installed.
* [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation)
  is recommended.
* The following environmental variables must be properly set before running
  `hot`:
  * `OS_PASSWORD`
  * `OS_USERNAME`
  * `OS_TENANT_ID`
  * `OS_AUTH_URL`
  * `HEAT_URL`

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
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py install
```

Usage
========
Ensure you have activated your virtual environment before every use.

The `hot` command takes a single verb, 'test'.  Issuing the command without a
a verb will result in the usage output:
```
(venv)~/src/hot $ hot
usage: hot [-h] {test,docs,init} ...
```
`hot` must be run inside of a template repository that contains a `tests.yaml`
file. `tests.yaml` dictates how `hot` will spin up deployments and test them.
Use the public [memcached](https://github.com/rackspace-orchestration-templates/memcached)
template repo as a starting point for using `hot`.


Creating Template Tests
=======================
Tests are specified in the `tests.yaml` file in the root of the template
repo.

`hot` supports template yaml sytax checking, stack build success verification,
and highly-flexible [fabric](http://www.fabfile.org/)-based integration testing
to test the resulting servers using [envassert](https://bitbucket.org/r_rudi/envassert)
and any other methods possible in a python script.

An example tests.yaml file for the memcached deployment mentioned above:

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
