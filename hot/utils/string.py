"""Various string functions"""


def list_to_string(values, join_char=" "):
    """Joins a list of strings and returns a string joined by a given string"""
    if isinstance(values, list):
        return join_char.join(str(value) for value in values)
    else:
        return values


def string_to_list(value):
    """Converts a space delimited string into a list"""
    if isinstance(value, str):
        return value.split()
    else:
        return value


def valid_project_name(name):
    """Validate that the project name would be a valid GitHub project name.
    GitHub appears to be super flexible on naming. It accepts special
    characters and spaces. From some testing, it appears the only limit is
    that the string needs to be under 100 characters."""
    if isinstance(name, str) and len(name) < 100:
        return True
    return False
