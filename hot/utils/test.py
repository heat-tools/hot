"""Functions to help with testing."""
import os
import re
import requests
from fabric.api import get, hide, run


def get_artifacts(artifacts, envvar='CIRCLE_ARTIFACTS'):
    """Uses Fabric to get each artifact provided by the artifacts list."""

    # Pull artifacts directory target from env vars
    directory = os.environ.get(envvar, 'tmp')

    for artifact in artifacts:
        target = directory + "/%(host)s/%(path)s"
        try:
            get(artifact, target)
        except:
            pass


def http_check(site, string):
    """Search the html of site with the string provided."""
    with hide('running', 'stdout'):
        wget_cmd = "wget --quiet --output-document - --no-check-certificate"
        homepage = run("{0} {1}".format(wget_cmd, site))
        if re.search(string, homepage):
            return True
        else:
            return False


def local_http_check(url, string):
    """Run a local http request and search the html for the provided string."""
    try:
        r = requests.get(url)
        if re.search(string, r.content):
            return True
        else:
            return False
    except:
        return False
