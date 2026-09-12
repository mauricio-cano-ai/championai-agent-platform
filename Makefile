.PHONY: install lint type test verify run docker
install:
	python -m pip install -e ".[dev]"
lint:
	python -m ruff check app tests
type:
	pyright
test:
	coverage run -m pytest
	coverage report -m
verify: lint type test
run:
	uvicorn app.api:app --reload
docker:
	docker compose up --build
