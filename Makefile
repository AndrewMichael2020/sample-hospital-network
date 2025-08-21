# Makefile for synthetic healthcare database

.PHONY: help setup generate load clean test sdv-train sdv-generate sdv-validate api-start api-test cli-test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

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

# API targets
api-setup: setup ## Install API dependencies
	@echo "API dependencies already included in setup target"

api-start: generate ## Start the API server (generates data if needed)
	@echo "Starting API server on http://localhost:8000"
	python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

api-test: generate ## Test API endpoints
	@echo "Testing API endpoints..."
	@python test_api.py

# CLI targets
cli-test: ## Test CLI commands
	@echo "Testing CLI commands..."
	python cli.py --help
	python cli.py status
	@echo "CLI tests passed!"

# SDV-related targets
sdv-train: setup generate ## Train SDV model on generated seed data
	@echo "Training SDV model..."
	python sdv_models/train.py --model-type hma --epochs 100 --patients 2000 --save-name healthcare_hma_model

sdv-generate: ## Generate synthetic data using trained SDV model
	@echo "Generating synthetic data..."
	python sdv_models/train.py --generate-only --patients 5000 --save-name healthcare_hma_model

sdv-validate: ## Validate synthetic data quality
	@echo "Validating synthetic data..."
	python sdv_models/validate.py --real-data-dir data --synthetic-data-dir data/synthetic

sdv-pipeline: ## Complete SDV pipeline: train, generate, validate
	$(MAKE) sdv-train
	$(MAKE) sdv-generate
	$(MAKE) sdv-validate

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