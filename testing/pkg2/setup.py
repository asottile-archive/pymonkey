from setuptools import setup


setup(
    name='targetmod',
    py_modules=['targetmod'],
    entry_points={'console_scripts': ['targetmod = targetmod:main']},
)
