import os
import subprocess

from hot.utils import files
from hot.utils import hosts
from hot.utils import string


def run_script(test_name, test):
    """Setup environment and run a script"""
    script_setup = test['script']
    if "hosts" in script_setup:
        if os.name == 'nt':
            hosts_path = os.path.join(os.environ['SYSTEMROOT'],
                                      'system32/drivers/etc/hosts')
        elif os.name == 'posix':
            hosts_path = '/etc/hosts'
        h = hosts.Hosts(hosts_path)
        for entry in script_setup['hosts']:
            if "ip" in entry:
                ip = entry["ip"]
                if "hostnames" in entry:
                    for hostname in entry['hostnames']:
                        print("  Setting host entry '%s\t%s'" % (ip, hostname))
                        if isinstance(hostname, str):
                            h.set_one(hostname, ip)
                        elif isinstance(hostname, list):
                            h.set_all(hostname, ip)
            else:
                raise TypeError
        h.write(hosts_path)

    # Write Files
    if "files" in script_setup:
        for file, value in files:
            files.write_file(file, value)

    # Set Environment Variables
    if "environment" in script_setup:
        for k, v in script_setup["environment"]:
            os.environ[k] = str(v)

    # Run commands
    if "commands" in script_setup:
        # TODO: Run scripts
        for cmd in script_setup["commands"]:
            if "command" in cmd:
                command = cmd["command"]
                if "command_args" in cmd:
                    args = cmd['command_args']
                    command = " ".join((command, string.list_to_string(args)))
                cmd_list = string.string_to_list(command)
                subprocess.check_call(cmd_list)
