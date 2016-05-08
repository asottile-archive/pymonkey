import sys

import pytest
import setuptools  # Some weird import hook
import six.moves  # Assertion: can import modules with import hook hackery


global_var = 1


def main():
    assert setuptools and six.moves
    print(global_var)

    # Make sure we still get import errors for failing modules
    with pytest.raises(ImportError):
        __import__('i_dont_exist')

    # Also should import error for sub-packages of packages that exist
    with pytest.raises(ImportError):
        __import__('six.herpderpderp')

    if len(sys.argv) > 1:
        print(', '.join(sys.argv[1:]))


if __name__ == '__main__':
    exit(main())
