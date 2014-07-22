hot
===
Command line helper utility for authoring and performing extended validation
testing on [Heat](https://wiki.openstack.org/wiki/Heat) templates.

Requirements
============
* [Pip](http://pip.readthedocs.org/en/latest/installing.html) must be
  installed.
* [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation)
  must be installed
* The following environmental variables must be properly set before running
  `hot`:
    * `OS_PASSWORD`
    * `OS_USERNAME`
    * `OS_TENANT_ID`
    * `OS_AUTH_URL`
    * `HEAT_URL`

Installation
============
Clone it down, install it!

```
git clone git@github.rackspace.com:brint-ohearn/hot.git
cd hot
virtualenv venv
source venv/bin/activate
pip install -r pip-requirements.txt
python setup.py install
```

Usage
========
Ensure you have activated your virtual environment before every use.

The `hot` command takes a single verb, 'test'.  Issuing the command without a
a verb will result in the usage output:
```
(venv)~/src/hot $ hot
usage: hot [-h] {test,docs} ...
```
`hot` must be run inside of a template repository that contains a `tests.yaml`
file. `tests.yaml` dictates how `hot` will spin up deployments and test them.
Use the public [memcached](https://github.com/rackspace-orchestration-templates/memcached)
template repo as a starting point for using `hot`.


Creating Template Tests
=======================
To be drafted.
