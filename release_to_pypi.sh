#!/bin/sh
pip3 install --upgrade twine
rm -rf dist
python3 setup.py sdist
python3 setup.py bdist_wheel
twine upload -u __token__ dist/* # username: __token__ password: pypi API token
