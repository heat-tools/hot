import fabric
import imp
import os

from fabric.api import env, task


def run_fabric_tasks(test_name, test):
    """Setup fabric environment and run fabric script"""
    env_setup = test['fabric']
    if env_setup['env']:
        fab_file = env_setup['env']['fabfile']
        print("  Preparing environtment to run fabric tests:")
        for k, v in env_setup['env'].iteritems():
            print("    Setting env['%s'] to %s" % (k, v))
            env[k] = v
        mod_name = os.path.splitext(os.path.basename(fab_file))[0]
        mod = imp.load_source(mod_name, fab_file)
        for task in env_setup['env']['tasks']:
            print("  Run fabric test '%s', task '%s' on: %s" % (test_name,
                                                                task,
                                                                env.hosts))
            fabric.tasks.execute(getattr(mod, task))
