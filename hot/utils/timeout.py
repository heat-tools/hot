"""Set timeout value for a given operation"""


def handler(signum, frame):
    print("  Failure! Operation failed to complete within timeout window.")
    raise Exception("Operation timed out")
