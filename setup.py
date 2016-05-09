from setuptools import setup

setup(
    name='pymonkey',
    description='A tool for applying monkeypatches to python executables.',
    url='https://github.com/asottile/pymonkey',
    version='0.2.0',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    py_modules=['pymonkey'],
    entry_points={'console_scripts': ['pymonkey = pymonkey:main']},
)
