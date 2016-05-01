[![Build Status](https://travis-ci.org/asottile/pymonkey.svg?branch=master)](https://travis-ci.org/asottile/pymonkey)
[![Coverage Status](https://img.shields.io/coveralls/asottile/pymonkey.svg?branch=master)](https://coveralls.io/r/asottile/pymonkey)

pymonkey
========

Register import hook monkeypatches and run python programs

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


# This is your entry point.  It will be passed module objects after they have
# been imported.  Check the module name and then apply your patch (if
# applicable).
# This will be called as a post-import hook so you'll have a chance to modify
# the module before another module would import from it.
def pymonkey_patch(mod):
    # This callback will be called with *every* module that gets imported
    # Guard against the specific module you'd like to patch
    if mod.__name__ != 'module_to_patch':
        return

    # Apply your patches here to module_to_patch
    mod.foo = 'bar'
```

And add the entrypoint to setup.py:

```python
setup(
    ...,
    entry_points={
        'pymonkey': ['mymod = mymod.pymonkey:pymonkey_patch'],
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

```
setup(
    ...,
    entry_points={
        'console_scripts': ['pip-patched = mymod_main:main'],
        'pymonkey': ['mymod = mymod.pymonkey:pymonkey_patch'],
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

(Soon!)
