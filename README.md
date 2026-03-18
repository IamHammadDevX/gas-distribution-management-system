# Rajput Gas Management System

A comprehensive desktop application for managing gas cylinder sales, inventory, and operations. Built with PySide6 (Qt for Python) and PostgreSQL database.

## 🏢 **Business Overview**

This system is designed for gas distribution companies to manage:
- Client records and outstanding balances
- Gas product inventory (Oxygen, Nitrogen, Organ Gas, LPG)
- Sales and billing with automatic tax calculation
- Receipt generation with PDF export
- Gate pass management with driver tracking
- Employee records and salary management
- Comprehensive reporting and analytics
- Automatic daily backup system

## 🚀 **Features**

### 🔐 **Authentication & Security**
- Role-based access control (Admin, Accountant, Gate Operator, Driver)
- Secure password hashing with SHA-256
- User activity logging for audit trails
- Session management

### 👥 **Client Management**
- Complete CRUD operations for client records
- Automatic balance tracking and payment history
- Client search and filtering capabilities
- Outstanding balance management
- Purchase history tracking

### 🧪 **Gas Products Configuration**
- Support for multiple gas types:
  - **Oxygen** (Types A, B, C) - Capacities: 1.4, 3.11, 6.23
  - **Nitrogen** - Capacities: 6.79, 8.4, 9.9
  - **Organ Gas** - Capacities: 8.4, 9.9
  - **LPG** (Types 1, 2, 3) - Capacities: 12kg, 45kg
- Product pricing and inventory tracking
- Sub-type management

### 💰 **Sales & Billing Module**
- Automatic 16% tax calculation on all sales
- Shopping cart functionality for multiple products
- Real-time balance calculation and payment tracking
- Outstanding balance management
- Support for partial and full payments

### 📄 **Receipt Generation**
- Professional PDF receipt generation using ReportLab
- Print functionality and receipt validation
- Company header and terms inclusion
- Receipt numbering and tracking

### 🚪 **Gate Pass System**
- Gate pass creation requiring valid receipt validation
- Driver and vehicle tracking with time in/out logging
- Prevention of duplicate gate passes
- Vehicle number validation

### 👨‍💼 **Employee Management**
- Employee records with role-based salary tracking
- Monthly salary report generation
- Employee tenure calculation
- Contact and address management

### 📊 **Comprehensive Reporting**
- **Sales Reports** - Daily/weekly/monthly sales analysis
- **Outstanding Balances** - Client balance tracking
- **Gate Activity** - Gate pass history and driver activity
- **Employee Reports** - Employee records and salary details
- **Product Sales** - Product-wise sales analysis
- **Tax Reports** - Tax collection summary
- Export functionality to CSV and JSON formats

### 💾 **Automatic Backup System**
- Daily automatic database backups at 2:00 AM
- Timestamped backup files in 'backups' directory
- Cleanup functionality for old backups
- Manual backup creation option
- Restore from backup functionality

### 📱 **Complete Offline Functionality**
- No internet connection required
- Works fully on an office LAN (on-prem PostgreSQL)
- Supports larger datasets and multiple concurrent users reliably

## 🛠️ **Technology Stack**

- **Frontend:** PySide6 (Qt for Python)
- **Database:** PostgreSQL
- **PDF Generation:** ReportLab
- **Excel Export:** OpenPyXL, Pandas
- **Security:** Cryptography (SHA-256 hashing)
- **Scheduling:** Schedule library for automatic backups

## 📋 **System Requirements**

- **Python:** 3.8 or higher
- **Operating System:** Windows 10/11, Linux, macOS
- **RAM:** Minimum 2GB (4GB recommended)
- **Storage:** 500MB free space
- **Display:** 1366x768 resolution or higher

## 🚀 **Installation & Setup**

### **1. Clone or Download the Repository**
```bash
git clone <repository-url>
cd Rajput_Gas_Ltd
```

### **2. Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Setup PostgreSQL (One-Time)**
Create a dedicated database and user (example):

```sql
CREATE DATABASE rajput_gas;
CREATE USER rajput_gas_app WITH PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';
GRANT CONNECT ON DATABASE rajput_gas TO rajput_gas_app;
\c rajput_gas
GRANT USAGE, CREATE ON SCHEMA public TO rajput_gas_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rajput_gas_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rajput_gas_app;
```

Set connection environment variables (PowerShell example):

```powershell
$env:PGHOST="127.0.0.1"
$env:PGPORT="5432"
$env:PGDATABASE="rajput_gas"
$env:PGUSER="rajput_gas_app"
$env:PGPASSWORD="REPLACE_WITH_STRONG_PASSWORD"
$env:APP_TIMEZONE="Asia/Karachi"
```

You can also use a single `DATABASE_URL`:

```powershell
$env:DATABASE_URL="postgresql://rajput_gas_app:REPLACE_WITH_STRONG_PASSWORD@127.0.0.1:5432/rajput_gas"
```

### **Windows local bootstrap (scripted)**
If you want one-command local setup on Windows, use:

```powershell
./scripts/setup_local_postgres.ps1
```

Then run the app with PostgreSQL environment variables preloaded:

```powershell
./scripts/run_app_postgres.ps1
```

Notes:
- `setup_local_postgres.ps1` requires a **full PostgreSQL server installation** (must include `share/postgres.bki`).
- If your PostgreSQL binaries are in a custom location, pass `-PgBinDir` and `-PgShareDir`.
- Local PostgreSQL runtime files are ignored via `.gitignore` (`.postgres/`, `backups/`, dump/sql/bak files).

### **Repository housekeeping**
- Keep only source code and scripts in Git.
- Do not commit local runtime artifacts (`.postgres/`, backup dumps, logs, temporary files).
- If a failed local bootstrap leaves an empty or partial `.postgres/data` folder, it is safe to delete and re-run setup.

### **4. Run the Application**
```bash
python main.py
```

### **5. First Login**
- **Username:** admin
- **Password:** admin123
- **Role:** Administrator

## 📁 **Project Structure**

```
Rajput_Gas_Ltd/
├── main.py                 # Application entry point
├── database.py            # Database management and operations
├── auth.py                # Authentication and login dialog
├── backup.py              # Automatic backup system
├── main_window.py         # Main application window
├── clients.py             # Client management module
├── gas_products.py        # Gas product configuration
├── sales.py               # Sales and billing module
├── receipts.py            # Receipt generation and PDF export
├── gate_passes.py         # Gate pass management
├── employees.py           # Employee management
├── reports.py             # Reporting and analytics
├── settings.py            # System settings and administration
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## 🎯 **Default User Roles**

### **Administrator (Admin)**
- Full system access
- User management
- System settings
- All reports and modules

### **Accountant**
- Client management
- Sales and billing
- Receipt generation
- Financial reports

### **Gate Operator**
- Gate pass creation
- Driver management
- Gate activity reports
- Limited system access

### **Driver**
- View assigned gate passes
- Update delivery status
- Limited read-only access

## 💼 **Business Workflow**

### **Typical Sales Process:**
1. **Add Client** → Create client record with contact details
2. **Configure Products** → Set up gas products with prices
3. **Create Sale** → Add products to cart with automatic tax calculation
4. **Generate Receipt** → Create professional PDF receipt
5. **Create Gate Pass** → Generate gate pass for delivery
6. **Track Delivery** → Monitor driver and vehicle status

### **Daily Operations:**
- **Morning:** Check outstanding balances and pending deliveries
- **Throughout Day:** Process sales, generate receipts, create gate passes
- **Evening:** Generate daily sales report and backup data
- **Automatic:** System creates daily backup at 2:00 AM

## 📊 **Reports Available**

### **Financial Reports**
- Daily Sales Summary
- Monthly Sales Analysis
- Outstanding Balances
- Tax Collection Summary

### **Operational Reports**
- Gate Activity Log
- Employee Performance
- Product Sales Analysis
- Client Purchase History

### **Export Options**
- **PDF:** Professional receipts and reports
- **Excel:** Financial data and summaries
- **CSV:** Raw data for external analysis
- **JSON:** Structured data for integration

## 🔧 **Configuration Options**

### **Company Settings**
- Company name and contact information
- Tax rates and calculation methods
- Receipt numbering format
- Backup retention policy

### **User Management**
- Add/modify/delete users
- Role assignment and permissions
- Password reset functionality
- Activity monitoring

### **Product Configuration**
- Gas type and sub-type management
- Capacity and pricing setup
- Product activation/deactivation
- Inventory tracking

## 🛡️ **Security Features**

### **Data Protection**
- SHA-256 password hashing
- Encrypted sensitive data storage
- Secure database design
- Audit trail logging

### **Access Control**
- Role-based permissions
- Session management
- Activity logging
- User authentication

### **Backup Security**
- Encrypted backup files
- Secure backup storage
- Version control for backups
- Restore point management

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. Application Won't Start**
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check for missing files

**2. Database Errors**
- Verify PostgreSQL is running and reachable
- Verify `PGHOST`/`PGDATABASE`/`PGUSER`/`PGPASSWORD` (or `DATABASE_URL`) are set correctly
- Ensure the database user has permissions on schema `public`

**3. PDF Generation Issues**
- Check ReportLab installation
- Ensure write permissions for PDF directory
- Verify font availability

**4. Backup Failures**
- Check disk space availability
- Verify backup directory permissions
- Ensure system time is correct
- Ensure `pg_dump` and `pg_restore` are installed and on `PATH`
- Ensure PostgreSQL credentials are provided via `PG*` env vars or `DATABASE_URL`

## 🛡️ **Durability Notes**
PostgreSQL is crash-safe for committed transactions (WAL), but "zero data loss" in real life requires operations discipline:
- Run PostgreSQL on a reliable SSD
- Use a UPS to handle sudden power loss
- Take regular backups (pg_dump) and test restores
- For maximum resilience, use streaming replication (hot standby) and/or WAL archiving for point-in-time recovery

## 🔄 **Migrating From SQLite**
If you have an existing `rajput_gas.db` (SQLite) and want to import it into PostgreSQL:

```bash
python migrate_sqlite_to_postgres.py --sqlite rajput_gas.db
```

To wipe the destination tables before importing (dangerous):

```bash
python migrate_sqlite_to_postgres.py --sqlite rajput_gas.db --wipe
```

`scripts/migrate_sqlite_to_postgres.py` is now a wrapper around the root migration script so both entry points behave identically.

### **Support Contact:**
For technical support or questions, please contact the development team.

## 🔄 **Updates & Maintenance**

### **Regular Maintenance:**
- Check backup integrity weekly
- Monitor disk space usage
- Review user activity logs
- Update product prices as needed

### **Software Updates:**
- Check for updates monthly
- Backup data before updates
- Test updates in development environment
- Verify all modules after updates

## 📈 **Performance Optimization**

### **Database Optimization:**
- Regular database maintenance
- Index optimization
- Query performance tuning
- Data archiving for old records

### **Application Performance:**
- Memory usage monitoring
- Response time optimization
- Resource cleanup
- Efficient data loading

## 📚 **Additional Documentation**

For detailed module-specific documentation, please refer to:
- Individual module documentation
- Database schema documentation
- API documentation (if applicable)
- User training materials

---

## 🎉 **Getting Started**

1. **Install the application** following the setup guide
2. **Login with default credentials** (admin/admin123)
3. **Configure gas products** in the Gas Products module
4. **Add clients** in the Client Management module
5. **Create your first sale** in the Sales module
6. **Generate a receipt** and test the PDF export
7. **Set up automatic backups** in Settings
8. **Train your team** on the system

**Welcome to the Rajput Gas Management System!** 🚀

---

*This system is designed to streamline your gas distribution operations and provide comprehensive business management capabilities. For support or customization requests, please contact the development team.*
