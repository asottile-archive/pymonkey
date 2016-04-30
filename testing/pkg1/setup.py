from setuptools import setup


setup(
    name='patchingmod',
    py_modules=['patchingmod'],
    entry_points={'pymonkey': 'patchingmod = patchingmod'},
)
