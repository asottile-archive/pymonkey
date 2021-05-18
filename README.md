# DEPRECATED

this library is deprecated without replacement, maybe check out `wrapt`?

___

[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/asottile.pymonkey?branchName=master)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=49&branchName=master)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/49/master.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=49&branchName=master)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/pymonkey/master.svg)](https://results.pre-commit.ci/latest/github/asottile/pymonkey/master)

pymonkey
========

A tool for applying monkeypatches to python executables.

### Installation

```
pip install pymonkey
```

### Registering a patch

Make a module:

```python
## mymod/pymonkey.py

# Be sure to not import anything at the module scope
# This ensures that import-hook patching will work better later


# This is your chance to do argument parsing before running the target
# executable.
# This will be called after all of the patch hooks have been registered.
def pymonkey_argparse(argv):
    # You'll be passed the arguments as a tuple.  Parse your specific arguments
    # and return your parsed state and the remaining arguments.
    # If you wish to forgo argparsing, simply `return None, argv`
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo')
    return parser.parse_known_args(argv)


# This is your entry point.  It will be passed module objects after they have
# been imported.  Check the module name and then apply your patch (if
# applicable).
# This will be called as a post-import hook so you'll have a chance to modify
# the module before another module would import from it.
# The parsed state computed above will be passed as `args`
def pymonkey_patch(mod, args):
    # This callback will be called with *every* module that gets imported
    # Guard against the specific module you'd like to patch
    if mod.__name__ != 'module_to_patch':
        return

    # Apply your patches here to module_to_patch
    mod.foo = args.foo
```

And add the entrypoints to setup.py:

```python
setup(
    ...,
    entry_points={
        'pymonkey': ['mymod = mymod.pymonkey:pymonkey_patch'],
        'pymonkey.argparse': ['mymod = mymod.pymonkey:pymonkey_argparse'],
    },
    ...
)
```

### Commandline usage

Applying a single patch:

```
$ pymonkey mymod -- pip install simplejson
```

Applying all the patches available:

```
$ pymonkey --all -- pip install simplejson
```

Viewing the help

```
$ pymonkey --help
```

### Making entry points with pymonkey

In a module:

```python
## mymod_main.py
from pymonkey import make_entry_point

# The first argument is a list of pymonkey patches to apply
# The second argument is the entry point to run
main = make_entry_point(('mymod',), 'pip')

if __name__ == '__main__':
    exit(main())
```

In setup.py

```python
setup(
    ...,
    entry_points={
        'console_scripts': ['pip-patched = mymod_main:main'],
        'pymonkey': ['mymod = mymod.pymonkey:pymonkey_patch'],
        'pymonkey.argparse': ['mymod = mymod.pymonkey:pymonkey_argparse'],
    },
    ...
)
```

Then instead of

```
$ pymonkey mymod -- pip ...
```

You can now do

```
$ pip-patched ...
```

### Things using pymonkey

- https://github.com/asottile/pip-custom-platform
