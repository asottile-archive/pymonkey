from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import contextlib
import imp
import os
import sys

import pkg_resources


Arguments = collections.namedtuple('Arguments', ('all', 'patches', 'cmd'))


class PymonkeySystemExit(SystemExit):
    pass


class PymonkeyError(RuntimeError):
    pass


HELPMSG = '''\
usage: {} [-h] [--debug] [--all] [patches [patches ...]] -- cmd [cmd ...]

A tool for applying monkeypatches to python executables. Patches are \
registered by supplying a setuptools entrypoint for `pymonkey`. Patches are \
selected by listing them on the commandline when running the pymonkey tool. \
For example, consider a registered patch pip_faster when using pip. An \
invocation may look like `pymonkey pip_faster -- pip install ...`.

positional arguments:
  patches
  cmd

optional arguments:
  - h, --help show this help message and exit
  --all       Apply all known patches'''.format(sys.argv[0])


def print_std_err(s):
    sys.stderr.write(s + '\n')
    sys.stderr.flush()


def DEBUG(msg):
    if 'PYMONKEY_DEBUG' in os.environ:
        print_std_err('pymonkey: ' + msg)


def print_help_and_exit():
    print_std_err(HELPMSG)
    raise PymonkeySystemExit()


def manual_argument_parsing(argv):
    """sadness because argparse doesn't quite do what we want."""

    # Special case these for a better error message
    if not argv or argv == ['-h'] or argv == ['--help']:
        print_help_and_exit()

    try:
        dashdash_index = argv.index('--')
    except ValueError:
        print_std_err('Must separate command by `--`')
        print_help_and_exit()

    patches, cmd = argv[:dashdash_index], argv[dashdash_index + 1:]

    if '--help' in patches or '-h' in patches:
        print_help_and_exit()

    if '--all' in patches:
        all_patches = True
        patches.remove('--all')
    else:
        all_patches = False

    unknown_options = [patch for patch in patches if patch.startswith('-')]
    if unknown_options:
        print_std_err('Unknown options: {!r}'.format(unknown_options))
        print_help_and_exit()

    if patches and all_patches:
        print_std_err('--all and patches specified: {!r}'.format(patches))
        print_help_and_exit()

    return Arguments(all=all_patches, patches=tuple(patches), cmd=tuple(cmd))


class PymonkeyImportHook(object):
    """This is where the magic happens.

    This import hook is responsible for the following things:
        - It will load all modules
        - In loading, it'll first invoke builtin import.
        - It'll then pass the module that it imported through each of the
            pymonkey hooks.
    """

    def __init__(self, hooks):
        self._hooks = hooks
        self._entry_data = dict.fromkeys(hooks)
        self._handling = []

    def _module_exists(self, module, path):
        # First check other entries in metapath for the module
        # Otherwise, try basic python import logic
        for entry in sys.meta_path:
            if entry is not self and entry.find_module(module, path):
                return True

        # We're either passed:
        # - A toplevel module name and `None` for path
        # - The fullpath to a module and a list for path
        # imp.find_module takes the following:
        # - A toplevel module name and `None` for path
        # - A subpackage and a list for path
        # Solution:
        # Convert the full modulename we're given into the subpackage
        if path is not None:
            to_try_mod = module.split('.')[-1]
        else:
            to_try_mod = module

        try:
            imp.find_module(to_try_mod, path)
            return True  # pragma: no cover (PY3 import is via sys.meta_path)
        except ImportError:
            return False

    @contextlib.contextmanager
    def handling(self, modname):
        self._handling.append(modname)
        try:
            yield
        finally:
            popped = self._handling.pop()
            assert popped == modname, (popped, modname)

    def find_module(self, fullname, path=None):
        # Shortcut if we're already processing this module
        if fullname in self._handling:
            DEBUG('already handling {}'.format(fullname))
            return
        # Make sure we can actually handle this module
        elif self._module_exists(fullname, path):
            DEBUG('found {}'.format(fullname))
            return self
        else:
            DEBUG('not found {}'.format(fullname))
            return

    def load_module(self, fullname):
        # Since we're going to invoke the import machinery and hit ourselves
        # again, store some state so we don't recurse forever
        with self.handling(fullname):
            module = __import__(fullname, fromlist=[str('__name__')], level=0)
            for entry, hook_fn in self._hooks.items():
                hook_fn(module, self._entry_data[entry])
            return module

    def set_entry_data(self, entry, data):
        self._entry_data[entry] = data


@contextlib.contextmanager
def assert_no_other_modules_imported(imported_modname):
    def getmods():
        return {modname for modname, mod in sys.modules.items() if mod}

    before = getmods()
    yield
    after = getmods()

    unexpected_imports = sorted(
        modname for modname in after - before
        if not imported_modname.startswith(modname)
    )
    if unexpected_imports:
        raise PymonkeyError(
            'pymonkey modules must not trigger imports at the module scope.  '
            'The following modules were imported while importing {}:\n'
            '{}'.format(
                imported_modname, '\t' + '\t\n'.join(unexpected_imports),
            ),
        )


def get_entry_callables(all_patches, patches, pymonkey_entry_points, attr):
    def _to_callable(entry_point):
        """If they give us a module, retrieve `attr`"""
        with assert_no_other_modules_imported(entry_point.module_name):
            loaded = entry_point.load()
        if callable(loaded):
            return loaded
        else:
            return getattr(loaded, attr)

    if all_patches:
        entry_points = pymonkey_entry_points
    else:
        all_entries = {entry.name: entry for entry in pymonkey_entry_points}
        missing = set(patches) - set(all_entries)
        if missing:
            print_std_err('Could not find patch(es): {}'.format(missing))
            raise PymonkeySystemExit(1)
        entry_points = [all_entries[name] for name in patches]
    return {entry.name: _to_callable(entry) for entry in entry_points}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    args = manual_argument_parsing(argv)

    # Load our entry point
    # This ensures that import side-effects of pkg_resources aren't picked
    # up as module-level imports later on
    pkg_resources.load_entry_point('pymonkey', 'console_scripts', 'pymonkey')

    # Register patches
    callables = get_entry_callables(
        args.all, args.patches,
        tuple(pkg_resources.iter_entry_points('pymonkey')),
        attr='pymonkey_patch',
    )
    hook = PymonkeyImportHook(callables)
    # Important to insert at the beginning to be ahead of the stdlib importer
    sys.meta_path.insert(0, hook)

    # Allow hooks to do argument parsing
    argv_callables = get_entry_callables(
        args.all, args.patches,
        tuple(pkg_resources.iter_entry_points('pymonkey.argparse')),
        attr='pymonkey_argparse',
    )
    cmd, rest = args.cmd[0], tuple(args.cmd[1:])
    for entry_name, argv_callable in argv_callables.items():
        args, rest = tuple(argv_callable(rest))
        hook.set_entry_data(entry_name, args)

    # Call the thing
    entry, = tuple(pkg_resources.iter_entry_points('console_scripts', cmd))
    sys.argv = [cmd] + list(rest)
    return entry.load()()


def make_entry_point(patches, original_entry_point):
    """Use this to make a console_script entry point for your application
    which applies patches.
    :param patches: iterable of pymonkey patches to apply.  Ex: ('my-patch,)
    :param original_entry_point: Such as 'pip'
    """
    def entry(argv=None):
        argv = argv if argv is not None else sys.argv[1:]
        return main(
            tuple(patches) + ('--', original_entry_point) + tuple(argv)
        )

    return entry

if __name__ == '__main__':
    sys.exit(main())
