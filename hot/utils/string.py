"""Various string functions"""


def valid_project_name(name):
    """Validate that the project name would be a valid GitHub project name.
    GitHub appears to be super flexible on naming. It accepts special
    characters and spaces. From some testing, it appears the only limit is
    that the string needs to be under 100 characters."""
    if isinstance(name, str) and len(name) < 100:
        return True
    return False
