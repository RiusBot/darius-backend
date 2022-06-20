ENV ?= $(firstword $(MAKECMDGOALS))
ifeq ($(ENV), prod)
	CLOUDBUILD = cloudbuild-prod.yaml
	PROJECT_ID = darius-prod
	APP = app-prod.yaml
	CREDENTIAL = darius-prod-5bed36160a65.json
	IMAGE_NAME = darius-backend
else ifeq ($(ENV), dev)
	CREDENTIAL = darius-332003-6391a8358dec.json
	CLOUDBUILD = cloudbuild-dev.yaml
	PROJECT_ID = darius-332003
	APP = app-dev.yaml
	IMAGE_NAME = darius-backend
else
	CREDENTIAL = darius-332003-6391a8358dec.json
	PROJECT_ID = local
endif

ifeq ($(words $(MAKECMDGOALS)), 1)
prod: build deploy
dev: build deploy
pilot: build deploy
else
dev: nan
pilot: nan
prod: nan
nan:
	@:
endif


###########################
# General
###########################

.PHONY: test
test:
	python -m pytest

style-check: flake8-check # black-check

flake8-check:
	python -m flake8

black-check:
	python -m black --line-length 188 --target-version=py37 --check ./

clean:
	@find . -name ".ipynb*" -exec rm -rv {} +


###########################
# Setup environment
###########################

install-gcloud:
	sudo apt-get install apt-transport-https ca-certificates gnupg
	echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
	sudo apt-get update && sudo apt-get install google-cloud-cli

conda-init:
	MY_SERVICE=prox3_internal
	conda create --name ${MY_SERVICE} python=3.7
	conda activate ${MY_SERVICE}
	pip install -r requirements.txt

init: create-env install version

create-env: check-env env-dependency install-env

install-env:
	@if ! [ -d $$HOME/.pyenv ]; then \
		curl https://pyenv.run | bash >/dev/null 2>&1 ; \
		if ! grep -Fq "pyenv" $$HOME/.bashrc; then\
			echo "# ===========================" >> $$HOME/.bashrc \
			echo "# Pyenv configuration        " >> $$HOME/.bashrc \
			echo "# ===========================" >> $$HOME/.bashrc \
			echo "export PATH=$$HOME/.pyenv/bin:\$$PATH" >> $$HOME/.bashrc ; \
			echo "eval \"\$$(pyenv init -)\"" >> $$HOME/.bashrc ; \
			echo "eval \"\$$(pyenv virtualenv-init -)\"" >> $$HOME/.bashrc ; \
			echo "# ===========================" >> $$HOME/.bashrc ;\
		fi \
	fi
	@. $$HOME/.bashrc
	@if ! (python3 -m pip list --disable-pip-version-check | grep pipenv > /dev/null) ; then \
		python3 -m pip install pipenv ; \
		if ! grep -Fq "\$$PATH:\$$PYTHON_BIN_PATH" $$HOME/.bashrc; then \
			echo "export PATH=\$$PATH:\$$PYTHON_BIN_PATH" >> $$HOME/.bashrc ; \
		fi \
		if ! grep -Fq "pipenv" $$HOME/.bashrc; then\
			echo "export PYTHON_BIN_PATH=$$(python3 -m site --user-base)/bin" >> $$HOME/.bashrc ; \
		fi \
	fi
	@. $$HOME/.bashrc

uninstall-env:
	python3 -m pip uninstall -y pipenv
	rm -rf $$HOME/.pyenv
	@echo "==========================="
	@echo "Need manual clean up bashrc"
	@echo "==========================="
	vim $$HOME/.bashrc

env-dependency:
	sudo apt update
	sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
	libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
	xz-utils tk-dev libffi-dev liblzma-dev python-openssl git libedit-dev

check-env:
	@if ! (python3 -m pip list --disable-pip-version-check | grep pipenv > /dev/null) ; then \
		echo "pipenv not install";\
	fi
	@if ! [ -d $$HOME/.pyenv ]; then\
		echo "pyenv not install";\
	fi
	@if ! grep -Fq "pipenv" $$HOME/.bashrc; then\
		echo "pipenv completion not in bashrc";\
	fi
	@if ! grep -Fq "pyenv" $$HOME/.bashrc; then\
		echo "pyenv not in bashrc";\
	fi
	@if ! grep -Fq "\$$PATH:\$$PYTHON_BIN_PATH" $$HOME/.bashrc; then \
		echo "pipenv PATH not in bashrc";\
	fi \

install:
	pipenv install --dev

uninstall:
	pipenv clean
	pipenv --rm

clear:
	find . -name "*.py[co]" -delete
	find . -name "*~" -delete
	find . -name "__pycache__" -delete

shell:
	pipenv shell

version:
	pipenv run python --version
	pipenv run flake8 --version
	pipenv run pytest --version


###########################
# Start at local
###########################

start-local:
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIAL) project_id=$(PROJECT_ID) python -m main.src.server.service

mysql-proxy:
	wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
	chmod +x cloud_sql_proxy
	export DB_HOST='127.0.0.1:3306'
	export DB_USER='root'
	export DB_PASS='dadarius'
	export DB_NAME='<DB_NAME>'
	./cloud_sql_proxy -instances=darius-330411:asia-east1:mysql-1=tcp:3306 -credential_file=$(CREDENTIAL) &


###########################
# Build & Deploy
###########################

build-docker: set-project
	gcloud builds submit --config cloudbuild.yaml  --timeout=60m

deploy: set-project
	gcloud app deploy --appyaml $(APP) --quiet
    
deploy-docker: set-project
	gcloud app deploy --image-url=gcr.io/$(PROJECT_ID)/darius-backend:latest --appyaml $(APP)

browse: set-project
	gcloud app browse --project=$(PROJECT_ID)

log: set-project
	gcloud app logs tail -s $(IMAGE_NAME)

set-project:
	gcloud config set project $(PROJECT_ID)
