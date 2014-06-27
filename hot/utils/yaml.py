"""Safely manipulate YAML data"""

from __future__ import absolute_import
import sys
import yaml


def load(yaml_string, error_message="Error in template file:"):
    """Return a yaml object for the provided string"""
    try:
        return yaml.safe_load(yaml_string)
    except yaml.YAMLError, exc:
        print error_message, exc
        sys.exit(1)


def dump(obj, error_message="Error in template file:"):
    """Return a yaml string for the provided object

    `obj` can be a dictionary, array, etc.
    """
    try:
        return yaml.safe_dump(obj)
    except yaml.YAMLError, exc:
        print error_message, exc
        sys.exit(1)
