from __future__ import absolute_import
from __future__ import unicode_literals

import os
import subprocess
import sys

import coverage
import mock
import patchingmod
import pytest
import six
from pkg_resources import EntryPoint

import pymonkey


@pytest.mark.parametrize(
    'args',
    (
        [],
        ['-h'],
        ['--help'],
        ['--help', '--', 'pip', 'install'],
    )
)
def test_help_message(capsys, args):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.manual_argument_parsing(args)

    out, err = capsys.readouterr()
    assert out == ''
    assert err == pymonkey.HELPMSG + '\n'


def test_DEBUG_not_debugging(capsys):
    pymonkey.DEBUG('test')
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')


def test_DEBUG_debugging(capsys):
    with mock.patch.dict(os.environ, {'PYMONKEY_DEBUG': '1'}):
        pymonkey.DEBUG('test')
    out, err = capsys.readouterr()
    assert (out, err) == ('', 'pymonkey: test\n')


def test_without_dashdash(capsys):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.manual_argument_parsing(['pip', 'install'])

    out, err = capsys.readouterr()
    assert out == ''
    assert err == 'Must separate command by `--`\n' + pymonkey.HELPMSG + '\n'


def test_unknown_options(capsys):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.manual_argument_parsing(['--foo', '--', 'pip', 'install'])

    out, err = capsys.readouterr()
    assert out == ''
    assert err == (
        'Unknown options: {!r}\n'.format(['--foo']) + pymonkey.HELPMSG + '\n'
    )


def test_all_and_some(capsys):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.manual_argument_parsing([
            'pip_faster', '--all', '--', 'pip', 'install',
        ])

    out, err = capsys.readouterr()
    assert out == ''
    assert err == (
        '--all and patches specified: {!r}\n'.format(['pip_faster']) +
        pymonkey.HELPMSG + '\n'
    )


def test_all():
    args = pymonkey.manual_argument_parsing(['--all', '--', 'pip', 'install'])
    assert args == pymonkey.Arguments(
        all=True, patches=(), cmd=('pip', 'install'),
    )


def test_some_patches():
    args = pymonkey.manual_argument_parsing([
        'pip_faster', '--', 'pip', 'install',
    ])
    assert args == pymonkey.Arguments(
        all=False, patches=('pip_faster',), cmd=('pip', 'install'),
    )


def test_help_edge_case():
    """It should be legal for cmd to contain --help"""
    args = pymonkey.manual_argument_parsing(['--', 'pip', '--help'])
    assert args == pymonkey.Arguments(
        all=False, patches=(), cmd=('pip', '--help'),
    )


def test_assert_no_other_modules_imported_ok():
    modname = 'testing.importing_test.no_imports'
    assert modname not in sys.modules
    with pymonkey.assert_no_other_modules_imported(modname):
        __import__(modname, fromlist=[str('__name__')])
    assert modname in sys.modules


def test_assert_no_other_modules_imported_error():
    modname = 'testing.importing_test.imports_others'
    assert modname not in sys.modules
    with pytest.raises(pymonkey.PymonkeyError) as excinfo:
        with pymonkey.assert_no_other_modules_imported(modname):
            __import__(modname, fromlist=[str('__name__')])
    assert modname in sys.modules
    assert excinfo.value.args == (
        'pymonkey modules must not trigger imports at the module scope.  '
        'The following modules were imported while importing '
        'testing.importing_test.imports_others:\n'
        '\ttesting.importing_test.import_target',
    )


def test_get_entry_callables_missing_patches(capsys):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.get_entry_callables(False, ('patch1',), [], 'pymonkey_patch')

    out, err = capsys.readouterr()
    assert err == 'Could not find patch(es): {}\n'.format({'patch1'})


@pytest.mark.parametrize(
    'entry_s',
    ('patchingmod = patchingmod', 'patchingmod = patchingmod:pymonkey_patch'),
)
def test_get_entry_callables(entry_s):
    ret = pymonkey.get_entry_callables(
        False, ('patchingmod',), [EntryPoint.parse(entry_s)], 'pymonkey_patch',
    )
    assert ret == {'patchingmod': patchingmod.pymonkey_patch}


def test_retrieve_name_doesnt_match_module_name():
    ret = pymonkey.get_entry_callables(
        False, ('mod-1',), [EntryPoint.parse('mod-1 = patchingmod')],
        'pymonkey_patch',
    )
    assert ret == {'mod-1': patchingmod.pymonkey_patch}


def test_retrieve_all():
    ret = pymonkey.get_entry_callables(
        True, (),
        [
            EntryPoint.parse('mod1 = patchingmod'),
            EntryPoint.parse('mod2 = patchingmod'),
        ],
        'pymonkey_patch',
    )

    assert ret == {
        'mod1': patchingmod.pymonkey_patch,
        'mod2': patchingmod.pymonkey_patch,
    }


@pytest.mark.parametrize(
    ('mod', 'path', 'expected'),
    (
        ('six', None, True),
        ('six.moves', six.__path__, True),
        ('coverage.data', coverage.__path__, True),
        ('i_dont_exist', None, False),
    ),
)
def test_module_exists(mod, path, expected):
    hook = pymonkey.PymonkeyImportHook(())
    assert hook._module_exists(mod, path) is expected


def output_with_coverage(*args):
    return subprocess.check_output(
        (sys.executable, '-m', 'coverage', 'run') + args
    ).decode('UTF-8')


def run_pymonkey(*args):
    return output_with_coverage('-m', 'pymonkey', *args)


def test_integration_without_pymonkey():
    assert output_with_coverage('-m', 'targetmod') == '1\n'
    assert output_with_coverage('-m', 'targetmod', 'test') == '1\ntest\n'


def test_integration_pymonkey_no_patches():
    assert run_pymonkey('--', 'targetmod') == '1\n'


def test_integration_with_patch():
    assert run_pymonkey('patchingmod', '--', 'targetmod') == '2\n'


def test_integration_all_patch():
    assert run_pymonkey('--all', '--', 'targetmod') == '2\n'


def test_integration_argv():
    ret = run_pymonkey('patchingmod', '--', 'targetmod', '--patch', '3')
    assert ret == '3\n'


def test_make_entry_point_simple():
    assert output_with_coverage('-m', 'patchingmod_main') == '2\n'


def test_make_entry_point_extra_args():
    out = output_with_coverage('-m', 'patchingmod_main', 'test', 'test2')
    assert out == '2\ntest, test2\n'
