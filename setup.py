from setuptools import setup, find_packages

setup(
    name='hot',
    description='Heat author command-line utility',
    keywords='heat orchestration configuration automation rackspace openstack',
    version='0.5.8',
    author='Rackspace',
    author_email='brint.ohearn@rackspace.com',
    entry_points={'console_scripts': ['hot=hot.shell:main']},
    packages=find_packages(exclude=['vagrant', 'tests', 'examples', 'doc']),
    install_requires=[
        "Babel==1.3",
        "Fabric==1.10.0",
        "GitPython==0.1.7",
        "PyYAML==3.11",
        "argh==0.26.0",
        "argparse==1.2.1",
        "ecdsa==0.11",
        "envassert==0.1.7",
        "iso8601==0.1.10",
        "netaddr==0.7.12",
        "oslo.config==1.4.0",
        "oslo.i18n==1.0.0",
        "oslo.serialization==1.0.0",
        "oslo.utils==1.0.0",
        "paramiko==1.15.1",
        "pbr==0.10.0",
        "prettytable==0.7.2",
        "pycrypto==2.6.1",
        "python-heatclient==0.2.12",
        "python-keystoneclient==0.11.2",
        "pytz==2014.7",
        "recordtype==1.1",
        "requests==2.4.3",
        "six==1.8.0",
        "stevedore==1.1.0",
        "urlparse2==1.1.1"
    ],
    license='Apache License (2.0)',
    classifiers=["Programming Language :: Python"],
    url='https://github.com/heat-tools/hot'
)
