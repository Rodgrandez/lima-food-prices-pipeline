PY ?= python
.PHONY: fetch update build publish daily all test lint
fetch:   ; $(PY) -m foodprices.pipeline fetch
update:  ; $(PY) -m foodprices.pipeline update
build:   ; $(PY) -m foodprices.pipeline build
publish: ; $(PY) -m foodprices.pipeline publish
daily:   ; $(PY) -m foodprices.pipeline daily
all:     ; $(PY) -m foodprices.pipeline all
test:    ; $(PY) -m pytest -q
lint:    ; ruff check src tests
