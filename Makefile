.PHONY: all install estate eval test run lint clean

all: estate test eval

install:
	pip install -r requirements.txt
	pip install -e .

estate:
	python -c "from cforge.estate.loader import init_duckdb_estate; init_duckdb_estate()"
	python -m cforge.estate.generate_gold_labels
	python -c "from cforge.catalog.store import MetadataStore; from cforge.catalog.lakehouse import MetadataLakehouse; store = MetadataStore(); store.populate_from_estate(); lakehouse = MetadataLakehouse(); lakehouse.export_lakehouse()"

test:
	pytest tests/ -v

eval:
	python -m cforge.eval.runner

run:
	python -m uvicorn cforge.api.app:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info
