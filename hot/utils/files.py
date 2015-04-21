"""Various string functions"""
import os


def write_file(f, value):
    """Write something into a file. Overwrite if existing, create if new"""
    if isinstance(f, str):
        print("Writing file '%s'" % f)
        fh = open(f, "wb")
        fh.write(value)
    else:
        raise TypeError


def delete_file(value):
    """Delete an individual file, or a list of files"""
    if isinstance(value, list):
        for f in value:
            print("Deleting file '%s'" % f)
            os.remove(f)
    elif isinstance(value, str):
        print("Deleting file '%s'" % value)
        os.remove(value)
    else:
        raise TypeError
