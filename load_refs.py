#!/usr/bin/env python3
"""
Load reference data from CSV files into MySQL database.
Loads the four new reference tables: staffed_beds_schedule, clinical_baseline,
seasonality_monthly, and staffing_factors.
"""

import pandas as pd
import pymysql
import os
from pathlib import Path


def get_db_connection():
    """Get database connection using environment variables or defaults."""
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'), 
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'lm_synth'),
        'charset': 'utf8mb4'
    }
    return pymysql.connect(**config)


def load_csv_to_mysql(csv_path, table_name, connection):
    """Load CSV data into MySQL table."""
    if not Path(csv_path).exists():
        print(f"Warning: {csv_path} not found, skipping {table_name}")
        return
        
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print(f"Warning: {csv_path} is empty, skipping {table_name}")
        return
    
    # Handle NULL values for nullable columns
    df = df.where(pd.notnull(df), None)
    
    try:
        cursor = connection.cursor()
        
        # Clear existing data
        cursor.execute(f"DELETE FROM {table_name}")
        
        # Insert new data
        if table_name == 'staffed_beds_schedule':
            query = """
                INSERT INTO staffed_beds_schedule 
                (site_id, program_id, schedule_code, staffed_beds)
                VALUES (%s, %s, %s, %s)
            """
            values = [
                (row['site_id'], row['program_id'], row['schedule_code'], row['staffed_beds'])
                for _, row in df.iterrows()
            ]
            
        elif table_name == 'clinical_baseline':
            query = """
                INSERT INTO clinical_baseline 
                (site_id, program_id, baseline_year, los_base_days, alc_rate)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = [
                (row['site_id'], row['program_id'], row['baseline_year'], 
                 row['los_base_days'], row['alc_rate'])
                for _, row in df.iterrows()
            ]
            
        elif table_name == 'seasonality_monthly':
            query = """
                INSERT INTO seasonality_monthly 
                (site_id, program_id, month, multiplier)
                VALUES (%s, %s, %s, %s)
            """
            values = [
                (row['site_id'], row['program_id'], row['month'], row['multiplier'])
                for _, row in df.iterrows()
            ]
            
        elif table_name == 'staffing_factors':
            query = """
                INSERT INTO staffing_factors 
                (program_id, subprogram_id, hppd, annual_hours_per_fte, productivity_factor)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = [
                (row['program_id'], row['subprogram_id'], row['hppd'],
                 row['annual_hours_per_fte'], row['productivity_factor'])
                for _, row in df.iterrows()
            ]
        
        cursor.executemany(query, values)
        connection.commit()
        
        print(f"✓ Loaded {len(df)} records into {table_name}")
        
    except Exception as e:
        print(f"✗ Error loading {table_name}: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()


def main():
    """Load all reference CSV files into MySQL."""
    print("Loading reference data into MySQL...")
    
    data_dir = Path("data")
    
    # Check if data directory exists
    if not data_dir.exists():
        print("Error: data directory not found. Run 'make generate-refs' first.")
        return
    
    try:
        # Connect to database
        connection = get_db_connection()
        print(f"Connected to MySQL database: {connection.get_server_info()}")
        
        # Load each reference table
        tables = [
            ('staffed_beds_schedule.csv', 'staffed_beds_schedule'),
            ('clinical_baseline.csv', 'clinical_baseline'), 
            ('seasonality_monthly.csv', 'seasonality_monthly'),
            ('staffing_factors.csv', 'staffing_factors')
        ]
        
        for csv_file, table_name in tables:
            csv_path = data_dir / csv_file
            load_csv_to_mysql(csv_path, table_name, connection)
        
        print("Reference data loading complete!")
        
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()


if __name__ == "__main__":
    main()