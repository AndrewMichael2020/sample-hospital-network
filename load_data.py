#!/usr/bin/env python3
"""
Load synthetic healthcare data into MySQL database.
Reads CSV files from data/ directory and loads them into MySQL tables.
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import sys
import os
import argparse

def create_mysql_engine(host="localhost", port=3306, user="root", password="", database="lm_synth"):
    """Create MySQL connection engine"""
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    try:
        engine = create_engine(connection_string, echo=False)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Successfully connected to MySQL at {host}:{port}/{database}")
        return engine
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        return None

def load_csv_to_table(engine, csv_file, table_name, chunksize=10000):
    """Load CSV file into MySQL table"""
    if not os.path.exists(csv_file):
        print(f"Warning: {csv_file} not found, skipping {table_name}")
        return False
    
    try:
        print(f"Loading {csv_file} into {table_name}...")
        
        # Read CSV and load in chunks
        total_rows = 0
        for chunk in pd.read_csv(csv_file, chunksize=chunksize):
            # Handle datetime columns
            if table_name == "ed_encounters":
                chunk['arrival_ts'] = pd.to_datetime(chunk['arrival_ts'])
            elif table_name == "ip_stays":
                chunk['admit_ts'] = pd.to_datetime(chunk['admit_ts'])
                chunk['discharge_ts'] = pd.to_datetime(chunk['discharge_ts'])
            elif table_name == "patients":
                chunk['dob'] = pd.to_datetime(chunk['dob']).dt.date
            
            # Load chunk to database
            chunk.to_sql(table_name, engine, if_exists="append", index=False, method="multi")
            total_rows += len(chunk)
        
        print(f"  Loaded {total_rows} rows into {table_name}")
        return True
        
    except Exception as e:
        print(f"Error loading {csv_file} into {table_name}: {e}")
        return False

def verify_data(engine):
    """Run verification queries to check data integrity"""
    print("\nVerifying data integrity...")
    
    queries = [
        ("Facilities", "SELECT COUNT(*) as count FROM dim_site"),
        ("Programs", "SELECT COUNT(*) as count FROM dim_program"),
        ("Subprograms", "SELECT COUNT(*) as count FROM dim_subprogram"),
        ("LHAs", "SELECT COUNT(*) as count FROM dim_lha"),
        ("Population records", "SELECT COUNT(*) as count FROM population_projection"),
        ("ED rates", "SELECT COUNT(*) as count FROM ed_baseline_rates"),
        ("Patients", "SELECT COUNT(*) as count FROM patients"),
        ("ED encounters", "SELECT COUNT(*) as count FROM ed_encounters"),
        ("IP stays", "SELECT COUNT(*) as count FROM ip_stays"),
    ]
    
    try:
        with engine.connect() as conn:
            for desc, query in queries:
                result = conn.execute(text(query))
                count = result.fetchone()[0]
                print(f"  {desc}: {count:,}")
        
        # Sample projection query from instructions
        print("\nSample ED projection for 2025:")
        projection_query = """
        SELECT s.site_code AS facility,
               r.ed_subservice,
               ROUND(SUM(p.population * r.baserate_per_1000 / 1000.0), 0) AS projected_volumes
        FROM population_projection p
        JOIN ed_baseline_rates r
          ON p.lha_id=r.lha_id AND p.age_group=r.age_group AND p.gender=r.gender
        JOIN dim_lha l ON l.lha_id=p.lha_id
        JOIN dim_site s ON s.site_id=l.default_site_id
        WHERE p.year=2025
        GROUP BY s.site_code, r.ed_subservice
        ORDER BY projected_volumes DESC
        LIMIT 10
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(projection_query))
            rows = result.fetchall()
            print("  Top 10 projected ED volumes by facility and service:")
            for row in rows:
                print(f"    {row[0]} - {row[1]}: {int(row[2]):,}")
                
    except Exception as e:
        print(f"Error during verification: {e}")

def main():
    parser = argparse.ArgumentParser(description="Load synthetic healthcare data into MySQL")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--user", default="root", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--database", default="lm_synth", help="MySQL database")
    parser.add_argument("--data-dir", default="data", help="Directory containing CSV files")
    
    args = parser.parse_args()
    
    # Create database connection
    engine = create_mysql_engine(
        host=args.host,
        port=args.port, 
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    if not engine:
        sys.exit(1)
    
    # Check if data directory exists
    if not os.path.exists(args.data_dir):
        print(f"Data directory '{args.data_dir}' not found. Run generate_data.py first.")
        sys.exit(1)
    
    # Load tables in dependency order (dimensions first, then facts)
    tables_to_load = [
        ("dim_site", "dim_site.csv"),
        ("dim_program", "dim_program.csv"), 
        ("dim_subprogram", "dim_subprogram.csv"),
        ("dim_lha", "dim_lha.csv"),
        ("population_projection", "population_projection.csv"),
        ("ed_baseline_rates", "ed_baseline_rates.csv"),
        ("patients", "patients.csv"),
        ("ed_encounters", "ed_encounters.csv"),
        ("ip_stays", "ip_stays.csv")
    ]
    
    success_count = 0
    for table_name, csv_file in tables_to_load:
        csv_path = os.path.join(args.data_dir, csv_file)
        if load_csv_to_table(engine, csv_path, table_name):
            success_count += 1
    
    print(f"\nLoaded {success_count}/{len(tables_to_load)} tables successfully")
    
    if success_count > 0:
        verify_data(engine)
    
    print("Data loading complete!")

if __name__ == "__main__":
    main()