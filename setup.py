# -*- coding: utf-8 -*-

# Note to self: To upload a new version to PyPI, run:
# python setup.py sdist upload

from setuptools import setup, find_packages

setup(
    name='email_validator',
    version='0.1.0',
    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    packages = find_packages(),
    url='https://github.com/JoshData/python-email-validator',
    license='CC0 (copyright waived)',
    description='A robust email syntax and deliverability validation library for Python 3.x.',
    long_description=open("README.rst").read(),
    keywords = "email address validator",
    install_requires=["dnspython"],
)
