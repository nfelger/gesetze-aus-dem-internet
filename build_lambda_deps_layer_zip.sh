#!/bin/bash

# Cf. https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path
# and https://github.com/pypa/pipenv/issues/2705
mkdir -p lambda_deps/python
pipenv lock --requirements --keep-outdated > lambda_deps/requirements.txt
docker run --rm \
  -v ${PWD}/lambda_deps:/opt/lambda_deps \
  'lambci/lambda:build-python3.8' \
  python -m pip install -r /opt/lambda_deps/requirements.txt --no-deps --target /opt/lambda_deps/python
rm lambda_deps/requirements.txt
cd lambda_deps
zip -9yqr ../lambda_deps.zip python
cd ..
rm -r lambda_deps
