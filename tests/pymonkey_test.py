from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

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


class FakeEntryPoint(object):
    def __init__(self, name, module_name, load_result):
        self.name = name
        self.module_name = module_name
        self._load_result = load_result

    def load(self):
        return self._load_result


def test_get_patch_callables_missing_patches(capsys):
    with pytest.raises(pymonkey.PymonkeySystemExit):
        pymonkey.get_patch_callables(False, ('patch1',), [])

    out, err = capsys.readouterr()
    assert err == 'Could not find patch(es): {}\n'.format({'patch1'})


def test_retrieve_module_specified():
    class fakemodule1(object):
        @staticmethod
        def pymonkey_patch(mod):
            raise NotImplementedError

    ret = pymonkey.get_patch_callables(
        False, ('fakemodule1',),
        [FakeEntryPoint('fakemodule1', 'fakemodule1', fakemodule1())],
    )
    assert ret == [fakemodule1.pymonkey_patch]


def test_retreive_function_specified():
    def patch(mod):
        raise NotImplementedError

    ret = pymonkey.get_patch_callables(
        False,
        ('fakemodule1',),
        [FakeEntryPoint('fakemodule1', 'fakemodule1', patch)],
    )
    assert ret == [patch]


def test_retrieve_all():
    def patch1(mod):
        raise NotImplementedError

    def patch2(mod):
        raise NotImplementedError

    ret = pymonkey.get_patch_callables(
        True, (),
        [
            FakeEntryPoint('mod1', 'mod1', patch1),
            FakeEntryPoint('mod2', 'mod2', patch2),
        ]
    )

    assert ret == [patch1, patch2]


def test_retrieve_name_doesnt_match_module_name():
    def patch1(mod):
        raise NotImplementedError

    ret = pymonkey.get_patch_callables(
        False, ('mod-1',), [FakeEntryPoint('mod-1', 'mod_1', patch1)],
    )
    assert ret == [patch1]
