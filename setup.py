# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open

setup(
    name='email_validator',
    version='1.0.5',

    description='A robust email syntax and deliverability validation library for Python 2.x/3.x.',
    long_description=open("README.rst", encoding='utf-8').read(),
    url='https://github.com/JoshData/python-email-validator',

    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    license='CC0 (copyright waived)',

    # See https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    keywords="email address validator",

    packages=find_packages(),
    install_requires=[
        "idna>=2.0.0",
        "dnspython>=1.15.0"],

    entry_points={
        'console_scripts': [
            'email_validator=email_validator:main',
        ],
    },
)
