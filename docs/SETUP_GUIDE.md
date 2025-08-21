# 🧙 User-Friendly Setup Guide

Welcome to the **Healthcare Data System Setup Guide**! This guide is designed specifically for beginners and will walk you through setting up your synthetic healthcare database step-by-step.

## 🎯 What You'll Get

After completing this setup, you'll have:
- 🏥 A synthetic healthcare database with realistic patient data
- 📊 Interactive API documentation and endpoints
- 🔍 Sample queries and data exploration tools
- 📈 Data validation and quality reports

## 🚀 Quick Start (Recommended)

The **easiest way** to get started is using our interactive setup wizard:

```bash
python cli.py setup-wizard
```

This wizard will:
- ✅ Detect your environment automatically
- 🎯 Recommend the best setup method for you
- 📋 Guide you through configuration step-by-step
- 🎨 Provide a colorful, user-friendly interface
- ⚡ Automate the entire setup process

## 📸 Setup Wizard Screenshots

### Welcome Screen
The wizard starts with a friendly welcome and overview:

![Setup Wizard Welcome](screenshots/wizard-welcome.png)

### Environment Detection
Automatically detects your system capabilities:

![Environment Detection](screenshots/environment-detection.png)

### Setup Method Selection
Recommends the best setup method based on your environment:

![Setup Method Selection](screenshots/setup-methods.png)

### Configuration Options
Guides you through configuration with clear explanations:

![Configuration](screenshots/configuration.png)

### Progress Tracking
Shows real-time progress with colorful indicators:

![Progress Tracking](screenshots/progress.png)

### Success Message
Celebrates completion and provides next steps:

![Success](screenshots/success.png)

## 🛠️ Setup Methods Explained

### 🐳 Docker Compose (Recommended for Beginners)

**Perfect for:** First-time users, local development, isolated environments

**What it does:**
- Creates isolated containers for MySQL database and Python application
- Automatically installs all dependencies
- Sets up networking between services
- Provides consistent environment across different systems

**Requirements:**
- Docker and Docker Compose installed
- 4GB+ RAM available

**Time:** 5-7 minutes

### ⚡ Native Setup

**Perfect for:** Users with existing MySQL installation, fastest option

**What it does:**
- Uses your local MySQL server
- Installs Python dependencies locally
- Creates database schema and loads data

**Requirements:**
- MySQL 8.0+ running locally
- Python 3.8+
- Basic MySQL user privileges

**Time:** 3-5 minutes

### 📊 API Only

**Perfect for:** Quick exploration, no database setup required

**What it does:**
- Generates CSV data files only
- Starts API server serving data from files
- No database installation needed

**Requirements:**
- Python 3.8+

**Time:** 1-2 minutes

### ☁️ Google Cloud Platform (Advanced)

**Perfect for:** Production deployments, shared team access

**What it does:**
- Creates GCP Cloud SQL MySQL instance
- Deploys application to cloud
- Sets up networking and security

**Requirements:**
- GCP account with billing enabled
- gcloud CLI installed
- Understanding of cloud costs

**Time:** 20-30 minutes

## 🎛️ Configuration Options

### Data Generation Preferences

The wizard will ask you about:

1. **Number of Patients** (default: 1000)
   - Small dataset (100-500): For testing and exploration
   - Medium dataset (1000-5000): For development and demos
   - Large dataset (10000+): For realistic simulations

2. **Emergency Department Encounters** (default: Yes)
   - Generates realistic ED visit patterns
   - Includes acuity levels and discharge dispositions

3. **Inpatient Stays** (default: Yes)
   - Creates hospital admission records
   - Includes length of stay and discharge data

### Database Configuration (Native Setup)

If you choose native setup, you'll configure:

1. **MySQL Host** (default: localhost)
2. **MySQL Port** (default: 3306)
3. **MySQL User** (default: root)
4. **MySQL Password** (secure prompt)
5. **Database Name** (default: lm_synth)

### GCP Configuration (Advanced)

For GCP deployment, you'll need:

1. **GCP Project ID**
2. **Region** (default: us-central1)
3. **Cloud SQL Instance Name**
4. **Service Account Key File Path**

## 🔧 Manual Setup (Alternative)

If you prefer manual setup or need to troubleshoot, you can run individual commands:

### Option 1: Docker Compose
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start services
docker compose up -d

# 3. Generate data
docker compose exec app python generate_data.py --patients 1000

# 4. Load data
docker compose exec app python load_data.py

# 5. Access API
open http://localhost:8000/docs
```

### Option 2: Native Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database
mysql -e "CREATE DATABASE lm_synth CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
mysql lm_synth < schema.sql

# 3. Generate data
python generate_data.py --patients 1000

# 4. Load data
python load_data.py

# 5. Start API
python -m uvicorn main_api:app --reload

# 6. Access API
open http://localhost:8000/docs
```

### Option 3: API Only
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate data files
python generate_data.py --patients 1000

# 3. Start API
python -m uvicorn main_api:app --reload

# 4. Access API
open http://localhost:8000/docs
```

## ✅ Verification Steps

After setup, verify everything is working:

### Check System Status
```bash
python cli.py status
```

This should show:
- ✅ Data files found with record counts
- ✅ API server running (if applicable)
- ✅ Database connection (if applicable)

### Validate Data Quality
```bash
python cli.py validate
```

This runs quality checks and shows:
- File integrity validation
- Record count verification
- Data relationship checks
- Statistical distribution analysis

### Explore the API
Visit the interactive API documentation:
- **Local:** http://localhost:8000/docs
- **Docker:** http://localhost:8000/docs (same)

Try these sample endpoints:
- `GET /patients` - List patients
- `GET /sites` - List healthcare facilities
- `GET /encounters` - List encounters
- `GET /health` - API health check

### Sample Database Queries

If you set up with a database, try these queries:

```sql
-- Count patients by age group
SELECT 
    CASE 
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 18 THEN 'Pediatric'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 65 THEN 'Adult'
        ELSE 'Senior'
    END AS age_group,
    COUNT(*) as patient_count
FROM patients 
GROUP BY age_group;

-- Top 5 facilities by ED volume
SELECT 
    s.site_name,
    COUNT(e.encounter_id) as ed_visits
FROM dim_site s
JOIN ed_encounters e ON s.site_id = e.facility_id
GROUP BY s.site_id, s.site_name
ORDER BY ed_visits DESC
LIMIT 5;

-- Average length of stay by program
SELECT 
    p.program_name,
    ROUND(AVG(ip.los_days), 2) as avg_los
FROM dim_program p
JOIN ip_stays ip ON p.program_id = ip.program_id
GROUP BY p.program_id, p.program_name
ORDER BY avg_los DESC;
```

## 🎨 CLI Commands Reference

Our CLI provides many helpful commands:

### Setup and Management
```bash
python cli.py setup-wizard     # 🧙 Interactive setup wizard
python cli.py status           # 📊 Check system status
python cli.py clean            # 🧹 Clean generated files
```

### Data Operations
```bash
python cli.py generate --patients 1000    # 📝 Generate data
python cli.py validate                     # ✅ Validate data quality
```

### API Server
```bash
python cli.py serve --port 8000           # 🚀 Start API server
```

### Advanced Commands
```bash
# Generate specific data types
python cli.py generate --patients 5000 --no-ed --with-ip

# Validate with strict thresholds
python cli.py validate --strict

# Save validation report
python cli.py validate --output validation_report.json

# Clean specific directory
python cli.py clean --data-dir ./old_data
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### "Module not found" errors
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

#### Docker containers won't start
```bash
# Solution: Check Docker daemon and restart
docker system prune -f
docker compose down
docker compose up -d
```

#### MySQL connection refused
```bash
# Solution: Start MySQL service
sudo systemctl start mysql    # Linux
brew services start mysql     # macOS

# Or check connection settings
python cli.py setup-wizard     # Re-run wizard
```

#### Data generation fails
```bash
# Solution: Check disk space and permissions
df -h .                       # Check disk space
chmod 755 .                   # Fix permissions
python cli.py clean           # Clean and retry
```

#### API server won't start
```bash
# Solution: Check port availability
netstat -tulpn | grep 8000   # Check if port is used
python cli.py serve --port 8001  # Use different port
```

### Getting Help

1. **Built-in Help:** `python cli.py --help`
2. **Command Help:** `python cli.py COMMAND --help`
3. **Status Check:** `python cli.py status`
4. **README:** Check the main [README.md](../README.md)
5. **Logs:** Check container logs with `docker compose logs`

### Environment-Specific Issues

#### Windows Users
- Use PowerShell or Command Prompt (not Git Bash for Docker)
- Ensure Docker Desktop is running
- Use `python` instead of `python3`

#### macOS Users
- Install Docker Desktop for Mac
- Use Homebrew for MySQL: `brew install mysql`
- Some commands may need `sudo`

#### Linux Users
- Install Docker and Docker Compose separately
- Add user to docker group: `sudo usermod -aG docker $USER`
- Restart shell after adding to group

## 🎉 What's Next?

After successful setup:

1. **Explore the Data:** Browse the generated CSV files in the `data/` directory
2. **Try the API:** Visit http://localhost:8000/docs for interactive API documentation
3. **Run Queries:** Connect to your database and explore the sample queries above
4. **Customize:** Modify generation parameters for different scenarios
5. **Validate:** Use the validation tools to ensure data quality
6. **Develop:** Start building your healthcare analytics applications!

## 📖 Additional Resources

- **Main README:** [README.md](../README.md) - Comprehensive documentation
- **API Documentation:** Available at http://localhost:8000/docs when running
- **Schema Documentation:** [schema.sql](../schema.sql) - Database structure
- **Sample Queries:** [docs/sample_queries.sql](sample_queries.sql)
- **Development Guide:** [DEVELOPMENT.md](DEVELOPMENT.md)

---

**🎊 Congratulations!** You now have a fully functional synthetic healthcare database system. Happy exploring! 🏥📊✨