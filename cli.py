"""
Command Line Interface for the synthetic healthcare data system.
Implements CLI commands for generate, validate, and API server management.
Based on copilot instruction for creating cli.py with typer.
"""

import typer
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import track
import pandas as pd

# Initialize typer app and rich console
app = typer.Typer(help="Synthetic Healthcare Data CLI")
console = Console()

# Constants
DATA_DIR = Path("./data")
DEFAULT_PATIENTS = 1000
DEFAULT_SEED = 42
SUPPORTED_FORMATS = ["csv", "parquet", "json"]


@app.command()
def generate(
    patients: int = typer.Option(DEFAULT_PATIENTS, "--patients", "-p", help="Number of patients to generate"),
    seed: int = typer.Option(DEFAULT_SEED, "--seed", "-s", help="Random seed for reproducibility"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, parquet, json)"),
    output_dir: str = typer.Option("./data", "--output", "-o", help="Output directory"),
    with_ed: bool = typer.Option(True, "--with-ed/--no-ed", help="Generate ED encounters"),
    with_ip: bool = typer.Option(True, "--with-ip/--no-ip", help="Generate IP stays"),
    start_year: int = typer.Option(2025, "--start-year", help="Start year for projections"),
    years: int = typer.Option(10, "--years", help="Number of years to project"),
):
    """Generate synthetic healthcare data."""
    
    console.print(f"[bold green]Generating synthetic healthcare data...[/bold green]")
    console.print(f"Patients: {patients}")
    console.print(f"Seed: {seed}")
    console.print(f"Format: {format}")
    console.print(f"Output: {output_dir}")
    
    if format not in SUPPORTED_FORMATS:
        console.print(f"[red]Error: Unsupported format '{format}'. Supported formats: {', '.join(SUPPORTED_FORMATS)}[/red]")
        raise typer.Exit(1)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Run the data generation script
        cmd = [
            sys.executable, "generate_data.py",
            "--patients", str(patients),
            "--seed", str(seed),
            "--output", output_dir
        ]
        
        if not with_ed:
            cmd.append("--no-ed")
        if not with_ip:
            cmd.append("--no-ip")
            
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        console.print("[green]✓ Data generation completed successfully[/green]")
        
        # Show summary of generated files
        show_data_summary(output_dir)
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error generating data: {e.stderr}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    data_dir: str = typer.Option("./data", "--data-dir", "-d", help="Data directory to validate"),
    strict: bool = typer.Option(False, "--strict", help="Use strict validation thresholds"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save validation report to file"),
):
    """Validate synthetic healthcare data quality."""
    
    console.print(f"[bold blue]Validating data in {data_dir}...[/bold blue]")
    
    if not Path(data_dir).exists():
        console.print(f"[red]Error: Data directory '{data_dir}' does not exist[/red]")
        raise typer.Exit(1)
    
    try:
        # Check if validation script exists
        if Path("sdv_models/validate.py").exists():
            # Use SDV validation if available
            cmd = [
                sys.executable, "sdv_models/validate.py",
                "--real-data-dir", data_dir,
                "--synthetic-data-dir", f"{data_dir}/synthetic"
            ]
            if strict:
                cmd.append("--strict")
            if output:
                cmd.extend(["--output", output])
                
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            console.print("[green]✓ SDV validation completed[/green]")
            
        else:
            # Basic validation
            validation_results = perform_basic_validation(data_dir)
            
            # Display results
            display_validation_results(validation_results)
            
            # Save to file if requested
            if output:
                with open(output, 'w') as f:
                    json.dump(validation_results, f, indent=2, default=str)
                console.print(f"[green]✓ Validation report saved to {output}[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Validation failed: {e.stderr}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Validation error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the API server."""
    
    console.print(f"[bold cyan]Starting API server on {host}:{port}...[/bold cyan]")
    
    try:
        # Check if FastAPI is available
        import uvicorn
        from api import app as api_app
        
        # Start the server
        uvicorn.run(
            "api:app",
            host=host,
            port=port,
            reload=reload
        )
        
    except ImportError as e:
        console.print("[red]Error: FastAPI or uvicorn not installed. Run: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting server: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show status of data files and API server."""
    
    console.print("[bold]Synthetic Healthcare Data Status[/bold]\n")
    
    # Check data files
    check_data_files()
    
    # Check if API server is running
    check_api_server()


@app.command()
def clean(
    data_dir: str = typer.Option("./data", "--data-dir", "-d", help="Data directory to clean"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Clean generated data files."""
    
    if not confirm:
        confirm = typer.confirm(f"Are you sure you want to delete all files in {data_dir}?")
        
    if not confirm:
        console.print("Operation cancelled.")
        return
    
    try:
        data_path = Path(data_dir)
        if data_path.exists():
            import shutil
            shutil.rmtree(data_path)
            console.print(f"[green]✓ Cleaned data directory: {data_dir}[/green]")
        else:
            console.print(f"[yellow]Data directory {data_dir} does not exist[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error cleaning data directory: {str(e)}[/red]")
        raise typer.Exit(1)


def show_data_summary(data_dir: str):
    """Display a summary of generated data files."""
    
    table = Table(title="Generated Data Files")
    table.add_column("File", style="cyan")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Size", justify="right", style="yellow")
    
    data_path = Path(data_dir)
    total_records = 0
    
    for csv_file in sorted(data_path.glob("*.csv")):
        try:
            df = pd.read_csv(csv_file)
            record_count = len(df)
            file_size = csv_file.stat().st_size
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            table.add_row(csv_file.name, f"{record_count:,}", size_str)
            total_records += record_count
            
        except Exception as e:
            table.add_row(csv_file.name, "Error", str(e))
    
    console.print(table)
    console.print(f"\n[bold]Total records: {total_records:,}[/bold]")


def perform_basic_validation(data_dir: str) -> dict:
    """Perform basic validation of data files."""
    
    required_files = [
        "dim_site.csv", "dim_program.csv", "dim_subprogram.csv", "dim_lha.csv",
        "population_projection.csv", "ed_baseline_rates.csv",
        "patients.csv", "ed_encounters.csv", "ip_stays.csv"
    ]
    
    results = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "data_directory": data_dir,
        "files": {},
        "summary": {
            "total_files": len(required_files),
            "passed": 0,
            "failed": 0,
            "total_records": 0
        }
    }
    
    data_path = Path(data_dir)
    
    for filename in track(required_files, description="Validating files..."):
        file_path = data_path / filename
        file_result = {"exists": False, "records": 0, "errors": [], "warnings": []}
        
        if file_path.exists():
            file_result["exists"] = True
            try:
                df = pd.read_csv(file_path)
                file_result["records"] = len(df)
                
                # Basic checks
                if len(df) == 0:
                    file_result["errors"].append("File is empty")
                
                # Check for required columns (basic validation)
                if "patients" in filename and "patient_id" not in df.columns:
                    file_result["errors"].append("Missing patient_id column")
                
                if len(file_result["errors"]) == 0:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1
                
                results["summary"]["total_records"] += len(df)
                
            except Exception as e:
                file_result["errors"].append(f"Error reading file: {str(e)}")
                results["summary"]["failed"] += 1
        else:
            file_result["errors"].append("File does not exist")
            results["summary"]["failed"] += 1
        
        results["files"][filename] = file_result
    
    return results


def display_validation_results(results: dict):
    """Display validation results in a formatted table."""
    
    console.print("[bold]Validation Results[/bold]\n")
    
    table = Table(title="File Validation")
    table.add_column("File", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Issues", style="yellow")
    
    for filename, file_result in results["files"].items():
        if file_result["exists"] and not file_result["errors"]:
            status = "[green]✓ Pass[/green]"
        else:
            status = "[red]✗ Fail[/red]"
        
        records = f"{file_result['records']:,}" if file_result["records"] > 0 else "-"
        
        issues = []
        issues.extend(file_result["errors"])
        issues.extend(file_result["warnings"])
        issues_str = "; ".join(issues) if issues else "-"
        
        table.add_row(filename, status, records, issues_str)
    
    console.print(table)
    
    # Summary
    summary = results["summary"]
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Total files: {summary['total_files']}")
    console.print(f"Passed: [green]{summary['passed']}[/green]")
    console.print(f"Failed: [red]{summary['failed']}[/red]")
    console.print(f"Total records: {summary['total_records']:,}")


def check_data_files():
    """Check status of data files."""
    
    console.print("[bold]Data Files Status:[/bold]")
    
    if not DATA_DIR.exists():
        console.print("[red]✗ Data directory does not exist[/red]")
        return
    
    csv_files = list(DATA_DIR.glob("*.csv"))
    if csv_files:
        console.print(f"[green]✓ Found {len(csv_files)} CSV files[/green]")
        for file in csv_files[:5]:  # Show first 5 files
            try:
                df = pd.read_csv(file)
                console.print(f"  - {file.name}: {len(df):,} records")
            except:
                console.print(f"  - {file.name}: Error reading file")
        
        if len(csv_files) > 5:
            console.print(f"  ... and {len(csv_files) - 5} more files")
    else:
        console.print("[yellow]⚠ No CSV files found[/yellow]")
    
    console.print()


def check_api_server():
    """Check if API server is running."""
    
    console.print("[bold]API Server Status:[/bold]")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            console.print("[green]✓ API server is running on http://localhost:8000[/green]")
            console.print(f"  - Documentation: http://localhost:8000/docs")
        else:
            console.print(f"[yellow]⚠ API server responding with status {response.status_code}[/yellow]")
    except ImportError:
        console.print("[yellow]⚠ requests library not available to check server status[/yellow]")
    except:
        console.print("[red]✗ API server is not running[/red]")
    
    console.print()


if __name__ == "__main__":
    app()