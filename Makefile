all: update-code
.PHONY: all install zip update-code

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
LAMBDA_FUNCTION_NAME:=lambda_function
CANDLE_LIGHTING_LAMBDA_NAME:=candle-lighting-scheduling-lambda
ZIP_NAME:=my-deployment-package.zip

install:
	poetry install

zip:
	rm -f ${ZIP_NAME}
	cd .venv/lib/python3.10/site-packages && zip -r ../../../../${ZIP_NAME} . && cd ../../../../src && zip -g ../${ZIP_NAME} ${LAMBDA_FUNCTION_NAME}.py && cd ../

update-code: zip
	aws lambda update-function-code --function-name ${CANDLE_LIGHTING_LAMBDA_NAME} --zip-file fileb://${ZIP_NAME} > /dev/null