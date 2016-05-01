from setuptools import setup


setup(
    name='patchingmod',
    py_modules=['patchingmod', 'patchingmod_main'],
    entry_points={
        'console_scripts': ['patched-targetmod = patchingmod_main:main'],
        'pymonkey': ['patchingmod = patchingmod'],
    },
)
