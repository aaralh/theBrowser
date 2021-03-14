#!/bin/bash
echo Running mypy
echo mypy .
echo
mypy .

echo Executing unit tests
echo python -m unittest discover -s tests
echo
python -m unittest discover -s tests