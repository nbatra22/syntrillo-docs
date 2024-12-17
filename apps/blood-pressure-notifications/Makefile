add-syntrillo:
	uv add --editable ../../sources/syntrillo-lib

run-staging:
	cp .staging.env .env
	uv run python run.py

run-prod:
	cp .prod.env .env
	uv run python run.py

# Spin up a local development Elasticsearch and Kibana instance
start-elasticsearch-and-kibana:
	docker compose -f elasticsearch_and_kibana.yml up -d