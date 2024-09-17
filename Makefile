
PACKAGE=notion-azure-items
VERSION := $(shell sed -n -E "s/^version = \"(.+)\"/\1/p" pyproject.toml)
ITERATION ?= 1

PEX_FILE=dist/notion-azure-items

# Temporary pkgenv fpm directory
PKGENV=dist/pkgenv

#PREFIX is environment variable, but if it is not set, then set default value
ifeq ($(PREFIX),)
    PREFIX := ~/bin/
endif

all: setup build

.PHONY: setup
setup:
	poetry install --sync
build: $(PEX_FILE)

$(PEX_FILE): notion_azure_items/*.py requirements.txt
	poetry build
	rm -f $(PEX_FILE)
	poetry run pex . --disable-cache \
		--requirement=requirements.txt \
		--entry-point=notion_azure_items.main:app \
		--output-file=$(PEX_FILE)

requirements.txt: poetry.lock
	poetry export --without-hashes -f requirements.txt > requirements.txt

install: build
	@install -v -d $(DESTDIR)$(PREFIX)/bin/
	@install -v --compare -m 755 $(PEX_FILE) $(DESTDIR)$(PREFIX)/bin/

