from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import sys

import pkg_resources


Arguments = collections.namedtuple('Arguments', ('all', 'patches', 'cmd'))


class PymonkeySystemExit(SystemExit):
    pass


HELPMSG = '''\
usage: {} [-h] [--all] [patches [patches ...]] -- cmd [cmd ...]

A tool for applying monkeypatches to python executables. Patches are
registered by supplying a setuptools entrypoint for `pymonkey`. Patches are
selected by listing them on the commandline when running the pymonkey tool.
For example, consider a registered patch pip_faster when using pip. An
invocation may look like `pymonkey pip_faster -- pip install ...`.

positional arguments:
  patches
  cmd

optional arguments:
  - h, --help show this help message and exit
  --all       Apply all known patches'''.format(sys.argv[0])


def print_help_and_exit():
    print(HELPMSG, file=sys.stderr)
    raise PymonkeySystemExit()


def manual_argument_parsing(argv):
    """sadness because argparse doesn't quite do what we want."""

    # Special case these for a better error message
    if not argv or argv == ['-h'] or argv == ['--help']:
        print_help_and_exit()

    try:
        dashdash_index = argv.index('--')
    except ValueError:
        print('Must separate command by `--`', file=sys.stderr)
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
        print('Unknown options: {!r}'.format(unknown_options), file=sys.stderr)
        print_help_and_exit()

    if patches and all_patches:
        print(
            '--all and patches specified: {!r}'.format(patches),
            file=sys.stderr,
        )
        print_help_and_exit()

    return Arguments(all=all_patches, patches=tuple(patches), cmd=tuple(cmd))


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    args = manual_argument_parsing(argv)

    # TODO: Register patches
    if args.all:
        # TODO: hook up all the things
        pass
    else:
        # TODO: hook up specific things
        pass

    # Call the thing
    entry, = list(pkg_resources.iter_entry_points(
        'console_scripts', args.cmd[0],
    ))
    sys.argv = list(args.cmd)
    sys.exit(entry.load()())

if __name__ == '__main__':
    sys.exit(main())
