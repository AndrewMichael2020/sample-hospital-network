# Makefile for synthetic healthcare database

.PHONY: help setup generate load clean test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install dependencies
	pip install -r requirements.txt

generate: ## Generate sample data
	python generate_data.py

load: ## Load data into MySQL (assumes MySQL running locally)
	python load_data.py

all: setup generate load ## Run complete setup: install deps, generate data, and load to MySQL

clean: ## Remove generated data files
	rm -rf data/

test: ## Run basic tests
	@echo "Testing data generation..."
	python generate_data.py
	@echo "Testing data files exist..."
	@test -f data/dim_site.csv && echo "✓ dim_site.csv exists" || echo "✗ dim_site.csv missing"
	@test -f data/patients.csv && echo "✓ patients.csv exists" || echo "✗ patients.csv missing"
	@test -f data/ed_encounters.csv && echo "✓ ed_encounters.csv exists" || echo "✗ ed_encounters.csv missing"
	@echo "Basic tests passed!"

# Convenience targets with parameters
setup-db: ## Create database schema (requires MySQL)
	mysql -e "CREATE DATABASE IF NOT EXISTS lm_synth CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
	mysql lm_synth < schema.sql

full-setup: ## Complete automated setup (requires MySQL running locally)
	python setup.py

# Development targets  
dev-small: ## Generate small dataset (100 patients) for development
	python -c "import generate_data; generate_data.main()" --patients 100

check-mysql: ## Check if MySQL is running
	@mysql -e "SELECT 1;" > /dev/null 2>&1 && echo "✓ MySQL is running" || echo "✗ MySQL is not running or not accessible"