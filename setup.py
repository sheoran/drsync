__author__ = 'dsheoran'
"""
A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject

Deepak Sheoran: Customized for the need of this project
"""

from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

setup(
    name='drsync',
    version='2.0.3',

    description='Syncs directories across systems',
    url='https://github.com/sheoran/drsync',

    # Author details
    author='Deepak sheoran',
    author_email='deepak.sheoran@outlook.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='development tool rsync',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['watchdog', 'dotmap', 'docopts'],
    package_data={
        'drsync.data': ['drsync_conf.txt', 'post_reg_msg.txt', 'rsync_filter.txt']
    },
    entry_points={
        'console_scripts': [
            'drsync=drsync:main',
        ],
    },
)
