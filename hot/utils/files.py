"""Various string functions"""
import os


def write_file(file, value):
    """Write something into a file. Overwrite if existing, create if new"""
    if isinstance(file, str):
        print("Writing file '%s'" % files)
        f = open(file, "wb")
        f.write(value)
    else:
        raise TypeError


def delete_file(value):
    """Delete an individual file, or a list of files"""
    if isinstance(value, list):
        for file in value:
            print("Deleting file '%s'" % file)
            os.remove(file)
    elif isinstance(value, str):
        print("Deleting file '%s'" % value)
        os.remove(value)
    else:
        raise TypeError
