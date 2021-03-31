
PACKAGE=git2svn
VERSION := $(shell sed -n -E "s/^version = \"(.+)\"/\1/p" pyproject.toml)
ITERATION ?= 1

PEX_FILE=dist/git2svn

all: setup build

.PHONY: setup
setup:
	poetry install --remove-untracked
build: $(PEX_FILE)

$(PEX_FILE): ppro_foreman/*.py requirements.txt
	poetry build
	rm -f $(PEX_FILE)
	poetry run pex . --disable-cache \
		--requirement=requirements.txt \
		--entry-point=ppro_foreman.cli:main \
		--output-file=$(PEX_FILE)

requirements.txt: poetry.lock
	poetry export --without-hashes -f requirements.txt > requirements.txt
