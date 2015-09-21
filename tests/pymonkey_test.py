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
