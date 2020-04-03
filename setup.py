# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('dispertech/__init__.py', 'r') as f:
    version_line = f.readline()

version = version_line.split('=')[1].strip().replace("'", "")

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='dispertech',
    version=version,
    description='Dispertech Controller Software',
    packages=find_packages(),
    url='https://github.com/aquilesC/DisperPy',
    license='GPLv3',
    author='Aquiles Carattino',
    author_email='aquiles@dispertech.com',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Development Status :: 4 - Beta',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
    ],
    include_package_data=True,
    install_requires=[
        # 'pyqt5',
        'numpy',
        'pyqtgraph',
        'pint',
        'h5py',
        'trackpy',
        'pandas',
        'pyyaml',
        'pyzmq',
        'numba',
        'pyvisa',
        'pyvisa-py',
        'experimentor',
        'scipy',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "dispertech=dispertech.__main__:main"
        ]
    }
)
