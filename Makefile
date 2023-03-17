all: install loaddata run
.PHONY: all run

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
LAMBDA_FUNCTION_NAME:=lambda_function
CANDLE_LIGHTING_LAMBDA_NAME:=candle-lighting-scheduling-lambda
ZIP_NAME:=my-deployment-package.zip

install:
	poetry install

zip:
	rm -f ${ZIP_NAME}
	zip -r ./${ZIP_NAME} .venv/lib/python3.10/site-packages
	zip -g ./${ZIP_NAME} ${LAMBDA_FUNCTION_NAME}.py

update-code:
	aws lambda update-function-code --function-name ${CANDLE_LIGHTING_LAMBDA_NAME} --zip-file fileb://${ZIP_NAME}