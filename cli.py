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
from typing import Optional, List, Dict
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.syntax import Syntax
import pandas as pd
import platform
import shutil

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
def setup_wizard():
    """🧙 Interactive setup wizard for beginners - guides you through the entire process!"""
    
    console.print(Panel.fit(
        "[bold blue]🏥 Welcome to the Healthcare Data System Setup Wizard![/bold blue]\n\n"
        "This wizard will guide you through setting up your synthetic healthcare database\n"
        "step-by-step. Perfect for beginners! ✨\n\n"
        "[dim]We'll help you choose the best setup method, configure everything automatically,\n"
        "and get you up and running with sample data and APIs.[/dim]",
        title="🧙 Setup Wizard",
        border_style="blue"
    ))
    
    # Step 1: Environment Detection and Recommendations
    env_info = detect_environment()
    show_environment_info(env_info)
    
    # Step 2: Choose Setup Method
    setup_method = choose_setup_method(env_info)
    
    # Step 3: Configure Based on Method
    config = configure_setup(setup_method, env_info)
    
    # Step 4: Run Setup Process
    success = run_setup_process(setup_method, config)
    
    # Step 5: Verification and Next Steps
    if success:
        show_success_message(setup_method, config)
    else:
        show_failure_message()


def detect_environment() -> Dict:
    """Detect the current environment and available tools."""
    env_info = {
        'os': platform.system(),
        'python_version': sys.version,
        'has_docker': shutil.which('docker') is not None,
        'has_mysql': False,
        'has_git': shutil.which('git') is not None,
        'in_codespace': os.environ.get('CODESPACES') == 'true',
        'has_make': shutil.which('make') is not None,
        'working_directory': os.getcwd()
    }
    
    # Check MySQL
    try:
        result = subprocess.run(['mysql', '--version'], 
                              capture_output=True, text=True, timeout=5)
        env_info['has_mysql'] = result.returncode == 0
        if result.returncode == 0:
            env_info['mysql_version'] = result.stdout.strip()
    except:
        env_info['has_mysql'] = False
    
    # Check Docker Compose
    if env_info['has_docker']:
        try:
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            env_info['has_docker_compose'] = result.returncode == 0
        except:
            env_info['has_docker_compose'] = False
    else:
        env_info['has_docker_compose'] = False
    
    return env_info


def show_environment_info(env_info: Dict):
    """Display environment detection results."""
    
    console.print("\n[bold cyan]🔍 Environment Detection Results[/bold cyan]")
    
    # Create a table for environment info
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Feature", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")
    
    # Operating System
    table.add_row("Operating System", "ℹ️", env_info['os'])
    
    # Python
    python_version = env_info['python_version'].split()[0]
    table.add_row("Python Version", "✅", python_version)
    
    # Tools availability
    table.add_row("Docker", "✅" if env_info['has_docker'] else "❌", 
                  "Available" if env_info['has_docker'] else "Not found")
    
    table.add_row("Docker Compose", "✅" if env_info.get('has_docker_compose') else "❌", 
                  "Available" if env_info.get('has_docker_compose') else "Not available")
    
    table.add_row("MySQL Client", "✅" if env_info['has_mysql'] else "❌", 
                  env_info.get('mysql_version', 'Not found'))
    
    table.add_row("GitHub Codespace", "✅" if env_info['in_codespace'] else "❌", 
                  "Yes" if env_info['in_codespace'] else "No")
    
    console.print(table)


def choose_setup_method(env_info: Dict) -> str:
    """Let user choose the setup method based on their environment."""
    
    console.print(f"\n[bold green]📋 Recommended Setup Methods[/bold green]")
    
    # Build recommendations based on environment
    methods = []
    
    if env_info['in_codespace']:
        methods.append({
            'key': 'codespace',
            'name': '🚀 GitHub Codespace (Recommended for you!)',
            'description': 'Perfect for your current environment - everything is pre-configured',
            'difficulty': 'Easy',
            'time': '2-3 minutes',
            'recommended': True
        })
    
    if env_info['has_docker'] and env_info.get('has_docker_compose'):
        methods.append({
            'key': 'docker',
            'name': '🐳 Docker Compose (Great for local development)',
            'description': 'Isolated environment with MySQL and API services',
            'difficulty': 'Easy',
            'time': '5-7 minutes',
            'recommended': not env_info['in_codespace']
        })
    
    methods.append({
        'key': 'native',
        'name': '⚡ Native Setup (Fastest if you have MySQL)',
        'description': 'Use your local MySQL installation',
        'difficulty': 'Medium' if not env_info['has_mysql'] else 'Easy',
        'time': '3-5 minutes' if env_info['has_mysql'] else '10-15 minutes',
        'recommended': False
    })
    
    methods.append({
        'key': 'api_only',
        'name': '📊 API Only (No database required)',
        'description': 'Just generate data files and start the API server',
        'difficulty': 'Easy',
        'time': '1-2 minutes',
        'recommended': False
    })
    
    methods.append({
        'key': 'gcp',
        'name': '☁️ Google Cloud Platform (Advanced)',
        'description': 'Deploy to GCP with managed MySQL',
        'difficulty': 'Advanced',
        'time': '20-30 minutes',
        'recommended': False
    })
    
    # Display options
    for i, method in enumerate(methods, 1):
        style = "bold green" if method['recommended'] else "white"
        rec_text = " ⭐ RECOMMENDED" if method['recommended'] else ""
        
        panel_content = (f"[{style}]{method['name']}{rec_text}[/{style}]\n\n"
                        f"{method['description']}\n\n"
                        f"[dim]Difficulty: {method['difficulty']} | "
                        f"Estimated time: {method['time']}[/dim]")
        
        console.print(Panel(panel_content, 
                          title=f"Option {i}",
                          border_style="green" if method['recommended'] else "white"))
    
    # Get user choice
    while True:
        choice = Prompt.ask(
            "\n[bold yellow]Which setup method would you like to use?[/bold yellow]",
            choices=[str(i) for i in range(1, len(methods) + 1)],
            default="1" if methods[0]['recommended'] else None
        )
        
        try:
            selected_method = methods[int(choice) - 1]
            console.print(f"\n[green]✅ You selected: {selected_method['name']}[/green]")
            
            if Confirm.ask("Is this correct?", default=True):
                return selected_method['key']
        except (ValueError, IndexError):
            console.print("[red]Invalid choice. Please try again.[/red]")


def configure_setup(setup_method: str, env_info: Dict) -> Dict:
    """Configure the setup based on the chosen method."""
    
    console.print(f"\n[bold blue]⚙️ Configuration Setup[/bold blue]")
    
    config = {
        'method': setup_method,
        'patients': 1000,
        'seed': 42,
        'include_ed': True,
        'include_ip': True,
        'api_port': 8000
    }
    
    if setup_method == 'codespace':
        return configure_codespace(config)
    elif setup_method == 'docker':
        return configure_docker(config)
    elif setup_method == 'native':
        return configure_native(config, env_info)
    elif setup_method == 'api_only':
        return configure_api_only(config)
    elif setup_method == 'gcp':
        return configure_gcp(config)
    
    return config


def configure_codespace(config: Dict) -> Dict:
    """Configure for GitHub Codespace environment."""
    console.print(Panel(
        "[green]🚀 GitHub Codespace Configuration[/green]\n\n"
        "Great news! Since you're in a Codespace, most configuration is automatic.\n"
        "The devcontainer has already set up MySQL and all dependencies.\n\n"
        "Let's configure your data generation preferences:",
        border_style="green"
    ))
    
    config.update(get_data_preferences())
    return config


def configure_docker(config: Dict) -> Dict:
    """Configure for Docker Compose setup."""
    console.print(Panel(
        "[blue]🐳 Docker Compose Configuration[/blue]\n\n"
        "Docker Compose will create isolated containers for:\n"
        "• MySQL database server\n"
        "• Python application with all dependencies\n\n"
        "Let's configure your preferences:",
        border_style="blue"
    ))
    
    config.update(get_data_preferences())
    
    # Check if .env exists, offer to create it
    if not Path('.env').exists():
        if Confirm.ask("Create .env configuration file?", default=True):
            create_env_file('docker')
            console.print("[green]✅ Created .env file with Docker defaults[/green]")
    
    return config


def configure_native(config: Dict, env_info: Dict) -> Dict:
    """Configure for native MySQL setup."""
    console.print(Panel(
        "[yellow]⚡ Native MySQL Configuration[/yellow]\n\n"
        "You'll use your local MySQL installation.\n"
        "We'll help you configure the database connection.",
        border_style="yellow"
    ))
    
    config.update(get_data_preferences())
    config.update(get_mysql_config(env_info))
    
    return config


def configure_api_only(config: Dict) -> Dict:
    """Configure for API-only setup (no database)."""
    console.print(Panel(
        "[cyan]📊 API-Only Configuration[/cyan]\n\n"
        "This mode generates data files (CSV) and starts the API server.\n"
        "No database setup required - perfect for quick exploration!",
        border_style="cyan"
    ))
    
    config.update(get_data_preferences())
    return config


def configure_gcp(config: Dict) -> Dict:
    """Configure for Google Cloud Platform deployment."""
    console.print(Panel(
        "[red]☁️ Google Cloud Platform Configuration[/red]\n\n"
        "⚠️  This is an advanced setup method that requires:\n"
        "• GCP account with billing enabled\n"
        "• gcloud CLI installed and configured\n"
        "• Understanding of cloud costs\n\n"
        "[bold]This will create real cloud resources that may incur charges![/bold]",
        border_style="red"
    ))
    
    if not Confirm.ask("Do you want to continue with GCP setup?", default=False):
        console.print("[yellow]Switching to Docker setup instead...[/yellow]")
        return configure_docker(config)
    
    config.update(get_data_preferences())
    config.update(get_gcp_config())
    
    return config


def get_data_preferences() -> Dict:
    """Get user preferences for data generation."""
    console.print("\n[bold]📊 Data Generation Preferences[/bold]")
    
    # Number of patients
    patients = IntPrompt.ask(
        "How many synthetic patients would you like to generate?",
        default=1000,
        show_default=True
    )
    
    if patients > 10000:
        console.print("[yellow]⚠️  Large datasets (>10k patients) may take several minutes to generate.[/yellow]")
        if not Confirm.ask("Continue with this size?", default=True):
            patients = IntPrompt.ask("Enter a smaller number", default=1000)
    
    # Data types
    include_ed = Confirm.ask("Include Emergency Department encounters?", default=True)
    include_ip = Confirm.ask("Include Inpatient stays?", default=True)
    
    return {
        'patients': patients,
        'include_ed': include_ed,
        'include_ip': include_ip
    }


def get_mysql_config(env_info: Dict) -> Dict:
    """Get MySQL configuration from user."""
    console.print("\n[bold]🔧 MySQL Database Configuration[/bold]")
    
    if not env_info['has_mysql']:
        console.print(Panel(
            "[red]⚠️  MySQL client not found![/red]\n\n"
            "You'll need to install MySQL first. Here's how:\n\n"
            "[bold]Ubuntu/Debian:[/bold] sudo apt install mysql-server mysql-client\n"
            "[bold]macOS:[/bold] brew install mysql\n"
            "[bold]Windows:[/bold] Download from https://dev.mysql.com/downloads/mysql/\n\n"
            "Or consider using Docker Compose instead (easier!)",
            border_style="red"
        ))
        
        if Confirm.ask("Switch to Docker Compose setup?", default=True):
            return {'switch_to_docker': True}
    
    host = Prompt.ask("MySQL Host", default="localhost")
    port = IntPrompt.ask("MySQL Port", default=3306)
    user = Prompt.ask("MySQL User", default="root")
    password = Prompt.ask("MySQL Password", password=True, default="")
    database = Prompt.ask("Database Name", default="lm_synth")
    
    return {
        'mysql_host': host,
        'mysql_port': port,
        'mysql_user': user,
        'mysql_password': password,
        'mysql_database': database
    }


def get_gcp_config() -> Dict:
    """Get GCP configuration from user."""
    console.print("\n[bold]☁️ Google Cloud Platform Configuration[/bold]")
    
    # Show GCP setup instructions
    console.print(Panel(
        "[bold blue]GCP Setup Instructions:[/bold blue]\n\n"
        "1. Create a GCP project: https://console.cloud.google.com/projectcreate\n"
        "2. Enable Cloud SQL Admin API: https://console.cloud.google.com/apis/library/sqladmin.googleapis.com\n"
        "3. Create a service account with Cloud SQL Admin role\n"
        "4. Download the service account JSON key file\n"
        "5. Install gcloud CLI: https://cloud.google.com/sdk/docs/install\n\n"
        "[yellow]💰 Cost estimate: ~$20-50/month for a small instance[/yellow]",
        title="📋 Prerequisites",
        border_style="blue"
    ))
    
    project_id = Prompt.ask("GCP Project ID")
    region = Prompt.ask("GCP Region", default="us-central1")
    instance_name = Prompt.ask("Cloud SQL Instance Name", default="healthcare-db")
    
    # Service account key
    key_file = Prompt.ask("Path to service account JSON key file")
    if not Path(key_file).exists():
        console.print("[red]❌ Key file not found. Please check the path.[/red]")
        return get_gcp_config()  # Retry
    
    return {
        'gcp_project': project_id,
        'gcp_region': region,
        'gcp_instance': instance_name,
        'gcp_key_file': key_file
    }


def create_env_file(setup_type: str):
    """Create .env file based on setup type."""
    if setup_type == 'docker':
        env_content = """# Docker Compose Configuration
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=healthcare123
MYSQL_DATABASE=lm_synth
MYSQL_ROOT_PASSWORD=healthcare123

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
"""
    else:
        env_content = """# Native MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=lm_synth

# API Configuration  
API_HOST=localhost
API_PORT=8000
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)


def run_setup_process(setup_method: str, config: Dict) -> bool:
    """Execute the setup process based on method and configuration."""
    
    console.print(f"\n[bold green]🚀 Starting Setup Process[/bold green]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            if setup_method == 'codespace':
                return run_codespace_setup(config, progress)
            elif setup_method == 'docker':
                return run_docker_setup(config, progress)
            elif setup_method == 'native':
                return run_native_setup(config, progress)
            elif setup_method == 'api_only':
                return run_api_only_setup(config, progress)
            elif setup_method == 'gcp':
                return run_gcp_setup(config, progress)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Setup interrupted by user.[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[red]❌ Setup failed: {str(e)}[/red]")
        return False
    
    return False


def run_codespace_setup(config: Dict, progress) -> bool:
    """Run setup for GitHub Codespace."""
    
    task1 = progress.add_task("Installing dependencies...", total=None)
    if not run_command_with_progress("pip install -r requirements.txt", progress, task1):
        return False
    progress.update(task1, completed=100)
    
    task2 = progress.add_task("Generating sample data...", total=None)
    cmd = build_generate_command(config)
    if not run_command_with_progress(cmd, progress, task2):
        return False
    progress.update(task2, completed=100)
    
    task3 = progress.add_task("Setting up database...", total=None)
    if not run_command_with_progress("python load_data.py", progress, task3):
        return False
    progress.update(task3, completed=100)
    
    return True


def run_docker_setup(config: Dict, progress) -> bool:
    """Run setup for Docker Compose."""
    
    task1 = progress.add_task("Starting Docker containers...", total=None)
    if not run_command_with_progress("docker compose up -d", progress, task1):
        return False
    progress.update(task1, completed=100)
    
    # Wait for MySQL to be ready
    task2 = progress.add_task("Waiting for MySQL to be ready...", total=None)
    if not wait_for_mysql_docker(progress, task2):
        return False
    progress.update(task2, completed=100)
    
    task3 = progress.add_task("Installing dependencies in container...", total=None)
    if not run_command_with_progress("docker compose exec -T app pip install -r requirements.txt", progress, task3):
        return False
    progress.update(task3, completed=100)
    
    task4 = progress.add_task("Generating sample data...", total=None)
    cmd = f"docker compose exec -T app {build_generate_command(config)}"
    if not run_command_with_progress(cmd, progress, task4):
        return False
    progress.update(task4, completed=100)
    
    task5 = progress.add_task("Loading data into database...", total=None)
    if not run_command_with_progress("docker compose exec -T app python load_data.py", progress, task5):
        return False
    progress.update(task5, completed=100)
    
    return True


def run_native_setup(config: Dict, progress) -> bool:
    """Run setup for native MySQL."""
    
    if config.get('switch_to_docker'):
        console.print("[yellow]Switching to Docker setup...[/yellow]")
        return run_docker_setup(config, progress)
    
    task1 = progress.add_task("Installing dependencies...", total=None)
    if not run_command_with_progress("pip install -r requirements.txt", progress, task1):
        return False
    progress.update(task1, completed=100)
    
    task2 = progress.add_task("Creating database schema...", total=None)
    create_cmd = f"mysql -h {config['mysql_host']} -P {config['mysql_port']} -u {config['mysql_user']}"
    if config['mysql_password']:
        create_cmd += f" -p{config['mysql_password']}"
    create_cmd += f" -e \"CREATE DATABASE IF NOT EXISTS {config['mysql_database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;\""
    
    if not run_command_with_progress(create_cmd, progress, task2):
        return False
    
    # Load schema
    schema_cmd = f"mysql -h {config['mysql_host']} -P {config['mysql_port']} -u {config['mysql_user']}"
    if config['mysql_password']:
        schema_cmd += f" -p{config['mysql_password']}"
    schema_cmd += f" {config['mysql_database']} < schema.sql"
    
    if not run_command_with_progress(schema_cmd, progress, task2):
        return False
    progress.update(task2, completed=100)
    
    task3 = progress.add_task("Generating sample data...", total=None)
    if not run_command_with_progress(build_generate_command(config), progress, task3):
        return False
    progress.update(task3, completed=100)
    
    task4 = progress.add_task("Loading data into database...", total=None)
    load_cmd = f"python load_data.py --host {config['mysql_host']} --port {config['mysql_port']} --user {config['mysql_user']}"
    if config['mysql_password']:
        load_cmd += f" --password {config['mysql_password']}"
    
    if not run_command_with_progress(load_cmd, progress, task4):
        return False
    progress.update(task4, completed=100)
    
    return True


def run_api_only_setup(config: Dict, progress) -> bool:
    """Run setup for API-only mode."""
    
    task1 = progress.add_task("Installing dependencies...", total=None)
    if not run_command_with_progress("pip install -r requirements.txt", progress, task1):
        return False
    progress.update(task1, completed=100)
    
    task2 = progress.add_task("Generating sample data files...", total=None)
    if not run_command_with_progress(build_generate_command(config), progress, task2):
        return False
    progress.update(task2, completed=100)
    
    return True


def run_gcp_setup(config: Dict, progress) -> bool:
    """Run setup for Google Cloud Platform."""
    
    # This is a simplified version - full GCP setup would be quite complex
    console.print("[yellow]⚠️  GCP setup is complex and not fully implemented in this wizard.[/yellow]")
    console.print("Please refer to the GCP documentation for manual setup.")
    return False


def build_generate_command(config: Dict) -> str:
    """Build the data generation command based on config."""
    cmd = f"python generate_data.py --patients {config['patients']}"
    
    if not config.get('include_ed', True):
        cmd += " --no-ed"
    if not config.get('include_ip', True):
        cmd += " --no-ip"
    
    return cmd


def run_command_with_progress(command: str, progress, task_id) -> bool:
    """Run a command and update progress."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        console.print(f"\n[red]⚠️ Command timed out: {command}[/red]")
        return False
    except Exception as e:
        console.print(f"\n[red]⚠️ Command failed: {str(e)}[/red]")
        return False


def wait_for_mysql_docker(progress, task_id) -> bool:
    """Wait for MySQL to be ready in Docker."""
    import time
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            result = subprocess.run(
                "docker compose exec -T mysql mysqladmin ping -h localhost --silent",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except:
            pass
        time.sleep(1)
    
    return False


def show_success_message(setup_method: str, config: Dict):
    """Show success message and next steps."""
    
    console.print(Panel(
        "[bold green]🎉 Setup Complete! 🎉[/bold green]\n\n"
        "Your synthetic healthcare database is ready to use!\n\n"
        f"[dim]Setup method: {setup_method}[/dim]\n"
        f"[dim]Generated {config['patients']} synthetic patients[/dim]",
        title="✅ Success",
        border_style="green"
    ))
    
    # Show next steps based on setup method
    next_steps = get_next_steps(setup_method, config)
    
    console.print(f"\n[bold cyan]🚀 What's Next?[/bold cyan]")
    for step in next_steps:
        console.print(f"• {step}")
    
    # Show useful commands
    console.print(f"\n[bold yellow]🔧 Useful Commands:[/bold yellow]")
    console.print("• [cyan]python cli.py status[/cyan] - Check system status")
    console.print("• [cyan]python cli.py validate[/cyan] - Validate generated data")
    console.print("• [cyan]python cli.py clean[/cyan] - Clean up generated files")
    
    if setup_method in ['codespace', 'native']:
        console.print("• [cyan]python -m uvicorn main_api:app --reload[/cyan] - Start API server")
    elif setup_method == 'docker':
        console.print("• [cyan]docker compose logs[/cyan] - View container logs")
        console.print("• [cyan]docker compose down[/cyan] - Stop all containers")


def get_next_steps(setup_method: str, config: Dict) -> List[str]:
    """Get next steps based on setup method."""
    
    if setup_method == 'codespace':
        return [
            "Access the API documentation at the forwarded port URL",
            "Try sample queries in the MySQL database",
            "Explore the generated data files in the ./data/ directory",
            "Use the CLI commands to manage your data"
        ]
    
    elif setup_method == 'docker':
        return [
            "Visit http://localhost:8000/docs for API documentation",
            "Connect to MySQL: docker compose exec mysql mysql -u root -p lm_synth",
            "View container logs: docker compose logs",
            "Explore data files: ls -la data/"
        ]
    
    elif setup_method == 'native':
        return [
            f"Connect to MySQL: mysql -h {config['mysql_host']} -u {config['mysql_user']} -p {config['mysql_database']}",
            "Start API server: python -m uvicorn main_api:app --reload",
            "Visit http://localhost:8000/docs for API documentation",
            "Explore data files: ls -la data/"
        ]
    
    elif setup_method == 'api_only':
        return [
            "Start API server: python -m uvicorn main_api:app --reload",
            "Visit http://localhost:8000/docs for API documentation", 
            "Explore generated CSV files: ls -la data/",
            "No database setup required - data is served from files"
        ]
    
    return ["Check the documentation for more information"]


def show_failure_message():
    """Show failure message with troubleshooting tips."""
    
    console.print(Panel(
        "[bold red]❌ Setup Failed[/bold red]\n\n"
        "Don't worry! Here are some common solutions:\n\n"
        "🔍 [bold]Troubleshooting Steps:[/bold]\n"
        "1. Check your internet connection\n"
        "2. Ensure you have sufficient disk space (>1GB)\n"
        "3. Try running with elevated privileges if needed\n"
        "4. Check for firewall or antivirus interference\n\n"
        "📞 [bold]Need Help?[/bold]\n"
        "• Check the README.md for detailed setup instructions\n"
        "• Review the troubleshooting section\n"
        "• Try a different setup method (e.g., Docker instead of native)\n"
        "• Run [cyan]python cli.py status[/cyan] to diagnose issues",
        title="🚨 Setup Failed",
        border_style="red"
    ))


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