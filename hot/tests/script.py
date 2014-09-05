import os
import subprocess

from hot.utils import string
from hot.utils import files


def run_script(test_name, test):
    """Setup environment and run a script"""
    script_setup = test['script']
    if "hosts" in script_setup:
        # TODO: Set hosts File
        print "TODO: Setup hosts file"

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
