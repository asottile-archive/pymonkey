import pytest
import six.moves  # Assertion: can import modules with import path hackery


global_var = 1


def main():
    assert six.moves
    print(global_var)

    # Make sure we still get import errors for failing modules
    with pytest.raises(ImportError):
        __import__('i_dont_exist')


if __name__ == '__main__':
    exit(main())
