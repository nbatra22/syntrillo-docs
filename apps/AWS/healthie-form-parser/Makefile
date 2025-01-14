add-syntrillo:
	uv add --editable ../../../sources/syntrillo-lib

run-staging:
	cp .staging.env .env
	uv run python run.py

run-prod:
	cp .prod.env .env
	uv run python run.py