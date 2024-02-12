#!/bin/bash
source env/bin/activate
pip3 install --upgrade build twine
rm -rf dist
python3 -m build
twine upload -u __token__ dist/* # username: __token__ password: pypi API token
