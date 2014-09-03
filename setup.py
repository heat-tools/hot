from setuptools import setup, find_packages

setup(
    name='hot',
    description='Heat author command-line utility',
    keywords='heat orchestration configuration automation rackspace openstack',
    version='0.1.3',
    author='Rackspace',
    author_email='brint.ohearn@rackspace.com',
    entry_points={'console_scripts': ['hot=hot.shell:main']},
    packages=find_packages(exclude=['vagrant', 'tests', 'examples', 'doc']),
    install_requires=[
        'argh',
        'envassert',
        'fabric',
        'gitpython',
        'python-heatclient',
        'python-keystoneclient',
        'PyYAML',
        'urlparse2',
    ],
    license='Apache License (2.0)',
    classifiers=["Programming Language :: Python"],
    url='https://github.com/brint/hot'
)
