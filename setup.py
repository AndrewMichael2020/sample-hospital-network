#!/usr/bin/env python3
"""
Setup script for the synthetic healthcare database.
Creates MySQL database, generates sample data, and loads it.
"""

import subprocess
import sys
import os
import argparse
import sqlalchemy as sa
from sqlalchemy import create_engine, text

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def create_database(host, port, user, password):
    """Create the database and run DDL scripts"""
    print("\nCreating MySQL database and schema...")
    
    # Connect to MySQL without specifying database
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}?charset=utf8mb4"
    
    try:
        engine = create_engine(connection_string, echo=False)
        
        # Read and execute the DDL script
        with open("schema.sql", "r") as f:
            ddl_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
        
        with engine.connect() as conn:
            for stmt in statements:
                if stmt.upper().startswith(('CREATE', 'USE', 'DROP')):
                    print(f"  Executing: {stmt[:50]}{'...' if len(stmt) > 50 else ''}")
                    conn.execute(text(stmt))
                    conn.commit()
        
        print("Database and schema created successfully")
        return True
        
    except Exception as e:
        print(f"Failed to create database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Setup synthetic healthcare database")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port") 
    parser.add_argument("--user", default="root", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--skip-deps", action="store_true", help="Skip installing dependencies")
    parser.add_argument("--skip-generate", action="store_true", help="Skip generating data")
    parser.add_argument("--skip-load", action="store_true", help="Skip loading data")
    
    args = parser.parse_args()
    
    print("=== Healthcare Database Setup ===")
    
    # Step 1: Install dependencies
    if not args.skip_deps:
        if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
            print("Failed to install dependencies. Continuing anyway...")
    
    # Step 2: Create database and schema
    if not create_database(args.host, args.port, args.user, args.password):
        print("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 3: Generate sample data
    if not args.skip_generate:
        if not run_command("python generate_data.py", "Generating sample data"):
            print("Failed to generate data. Exiting.")
            sys.exit(1)
    
    # Step 4: Load data into MySQL
    if not args.skip_load:
        load_cmd = f"python load_data.py --host {args.host} --port {args.port} --user {args.user}"
        if args.password:
            load_cmd += f" --password {args.password}"
        
        if not run_command(load_cmd, "Loading data into MySQL"):
            print("Failed to load data. Exiting.")
            sys.exit(1)
    
    print("\n=== Setup Complete! ===")
    print(f"Your synthetic healthcare database is ready at {args.host}:{args.port}/lm_synth")
    print("\nTo connect and explore the data:")
    print(f"  mysql -h {args.host} -P {args.port} -u {args.user} -p lm_synth")
    print("\nSample queries:")
    print("  SELECT COUNT(*) FROM patients;")
    print("  SELECT site_code, site_name FROM dim_site;")
    print("  SELECT * FROM ed_encounters LIMIT 5;")

if __name__ == "__main__":
    main()