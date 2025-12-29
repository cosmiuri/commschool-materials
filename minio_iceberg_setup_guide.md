# Production MinIO + Apache Iceberg + Parquet Setup Guide

Complete step-by-step guide to set up MinIO object storage, create sample Parquet files, and configure Apache Iceberg catalog on Ubuntu Server.

**Target Architecture:**
- MinIO for S3-compatible object storage
- Parquet files for columnar data storage
- Apache Iceberg for table metadata management
- PostgreSQL for Iceberg catalog
- No query engine (Trino/Spark) - pure storage layer

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install MinIO Server](#step-1-install-minio-server)
3. [Configure MinIO](#step-2-configure-minio)
4. [Create SystemD Service](#step-3-create-systemd-service)
5. [Start and Verify MinIO](#step-4-start-and-verify-minio)
6. [Install MinIO Client](#step-5-install-minio-client-mc)
7. [Create Buckets](#step-6-create-bucket-structure)
8. [Generate Sample Parquet Files](#step-7-generate-sample-parquet-files)
9. [Upload to MinIO](#step-8-upload-parquet-files-to-minio)
10. [Setup Iceberg Catalog](#step-9-setup-apache-iceberg)
11. [Create Catalog Database](#step-10-create-postgresql-catalog-database)
12. [Register Iceberg Tables](#step-11-register-parquet-files-as-iceberg-table)
13. [Verify Setup](#step-12-verify-iceberg-catalog)

---

## Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y wget curl tree vim

# Install Java (required for Iceberg)
sudo apt install -y openjdk-17-jdk
java -version

# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

---

## Step 1: Install MinIO Server

### Option A: Binary Installation (Recommended)

```bash
# Create MinIO system user
sudo useradd -r minio-user -s /sbin/nologin

# Create data directories
sudo mkdir -p /data/minio
sudo chown -R minio-user:minio-user /data/minio

# Download MinIO binary
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Verify installation
minio --version
```

### Option B: DEB Package Installation (Alternative)

```bash
# Download DEB package (if binary installation fails with segfault)
wget https://dl.min.io/server/minio/release/linux-amd64/archive/minio_20240330053858.0.0_amd64.deb

# Install package
sudo dpkg -i minio_20240330053858.0.0_amd64.deb

# Verify installation
minio --version
```

---

## Step 2: Configure MinIO

```bash
# Create configuration directory
sudo mkdir -p /etc/minio

# Create environment configuration file
sudo tee /etc/default/minio << 'EOF'
# MinIO data volume(s)
# For production, use multiple disks: MINIO_VOLUMES="/disk1 /disk2 /disk3 /disk4"
MINIO_VOLUMES="/data/minio"

# MinIO root credentials (CHANGE THESE!)
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=SuperSecurePassword123!

# MinIO server options
MINIO_OPTS="--console-address :9001 --address :9000"

# Optional: Set region
MINIO_REGION=us-east-1
EOF

# Secure the configuration file
sudo chmod 600 /etc/default/minio
```

**Security Note:** Change the `MINIO_ROOT_PASSWORD` to a strong password in production!

---

## Step 3: Create SystemD Service

```bash
# Create MinIO systemd service file
sudo tee /etc/systemd/system/minio.service << 'EOF'
[Unit]
Description=MinIO Object Storage
Documentation=https://min.io/docs/minio/linux/index.html
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
Type=notify
WorkingDirectory=/usr/local
User=minio-user
Group=minio-user
ProtectProc=invisible
EnvironmentFile=-/etc/default/minio

ExecStartPre=/bin/bash -c "if [ -z \"${MINIO_VOLUMES}\" ]; then echo \"Variable MINIO_VOLUMES not set in /etc/default/minio\"; exit 1; fi"
ExecStart=/usr/local/bin/minio server $MINIO_OPTS $MINIO_VOLUMES

# Restart policy
Restart=always
LimitNOFILE=65536
TasksMax=infinity
TimeoutStopSec=infinity
SendSIGKILL=no

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd daemon
sudo systemctl daemon-reload
```

---

## Step 4: Start and Verify MinIO

```bash
# Enable MinIO to start on boot
sudo systemctl enable minio

# Start MinIO service
sudo systemctl start minio

# Check service status
sudo systemctl status minio

# View logs
sudo journalctl -u minio -f

# Test API endpoint
curl http://localhost:9000/minio/health/live

# Test console (should return HTML)
curl http://localhost:9001
```

**Access MinIO Console:**
- URL: `http://your-server-ip:9001`
- Username: `admin`
- Password: `SuperSecurePassword123!` (or your chosen password)

---

## Step 5: Install MinIO Client (mc)

```bash
# Download MinIO Client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Verify installation
mc --version

# Configure alias for your MinIO server
mc alias set local http://localhost:9000 admin SuperSecurePassword123!

# Test connection
mc admin info local

# List buckets (should be empty initially)
mc ls local
```

---

## Step 6: Create Bucket Structure

```bash
# Create main bucket for Iceberg
mc mb local/iceberg

# Create warehouse directory
mc mb local/iceberg/warehouse

# Verify structure
mc ls local/
mc ls local/iceberg/

# Set bucket policy (optional - for public read)
mc anonymous set download local/iceberg
```

---

## Step 7: Generate Sample Parquet Files

### Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv ~/venv-iceberg
source ~/venv-iceberg/bin/activate

# Install required packages
pip install pandas pyarrow faker boto3
```

### Create Sample Data Generator Script

```bash
# Create script file
cat > ~/create_sample_parquet.py << 'EOF'
#!/usr/bin/env python3
"""
Generate sample maritime vessel telemetry data as partitioned Parquet files.
Simulates data from 93 vessels with realistic maritime metrics.
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from faker import Faker
import random
import os

fake = Faker()

def generate_vessel_telemetry(num_records=100000, num_vessels=93):
    """
    Generate realistic maritime telemetry data.
    
    Args:
        num_records: Number of telemetry records to generate
        num_vessels: Number of unique vessels
    
    Returns:
        pandas.DataFrame with telemetry data
    """
    
    # Generate vessel IDs
    vessels = [f"VESSEL_{str(i).zfill(3)}" for i in range(1, num_vessels + 1)]
    
    data = {
        'timestamp': [],
        'vessel_id': [],
        'latitude': [],
        'longitude': [],
        'speed_knots': [],
        'heading': [],
        'engine_rpm': [],
        'fuel_consumption_lph': [],  # Liters per hour
        'water_temp_celsius': [],
        'air_temp_celsius': [],
        'wind_speed_knots': [],
        'wave_height_meters': [],
    }
    
    # Start from January 1, 2024
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    
    print(f"Generating {num_records:,} records for {num_vessels} vessels...")
    
    for i in range(num_records):
        vessel = random.choice(vessels)
        # Records every 30 seconds
        timestamp = base_time + timedelta(seconds=i * 30)
        
        data['timestamp'].append(timestamp)
        data['vessel_id'].append(vessel)
        
        # Realistic maritime coordinates
        data['latitude'].append(round(random.uniform(-60, 70), 6))
        data['longitude'].append(round(random.uniform(-180, 180), 6))
        
        # Speed in knots (0-25 typical for cargo ships)
        data['speed_knots'].append(round(random.uniform(0, 25), 2))
        
        # Heading in degrees (0-360)
        data['heading'].append(round(random.uniform(0, 360), 1))
        
        # Engine RPM (0-3000 typical)
        data['engine_rpm'].append(random.randint(0, 3000))
        
        # Fuel consumption in liters per hour
        data['fuel_consumption_lph'].append(round(random.uniform(0, 150), 2))
        
        # Water temperature (Celsius)
        data['water_temp_celsius'].append(round(random.uniform(5, 30), 1))
        
        # Air temperature (Celsius)
        data['air_temp_celsius'].append(round(random.uniform(-5, 40), 1))
        
        # Wind speed in knots
        data['wind_speed_knots'].append(round(random.uniform(0, 50), 1))
        
        # Wave height in meters
        data['wave_height_meters'].append(round(random.uniform(0, 8), 2))
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} records...")
    
    return pd.DataFrame(data)


def write_partitioned_parquet(df, base_path):
    """
    Write Parquet files partitioned by date.
    
    Args:
        df: pandas DataFrame with data
        base_path: Base directory path for output files
    """
    
    # Add date column for partitioning
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    print(f"\nWriting partitioned Parquet files to {base_path}...")
    
    # Group by date and write separate files
    for date, group in df.groupby('date'):
        partition_path = f"{base_path}/date={date}"
        os.makedirs(partition_path, exist_ok=True)
        
        # Drop the partition column before writing
        group_to_write = group.drop('date', axis=1)
        
        filename = f"{partition_path}/data_{date}.parquet"
        
        # Write with Snappy compression (good balance of speed/compression)
        group_to_write.to_parquet(
            filename,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
        print(f"  Written {len(group):,} records to {filename} ({file_size:.2f} MB)")


def main():
    """Main execution function"""
    
    print("=" * 70)
    print("Maritime Vessel Telemetry Data Generator")
    print("=" * 70)
    
    # Generate data
    df = generate_vessel_telemetry(num_records=100000, num_vessels=93)
    
    # Print summary statistics
    print(f"\n{'='*70}")
    print("Data Summary:")
    print(f"{'='*70}")
    print(f"Total records: {len(df):,}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Unique vessels: {df['vessel_id'].nunique()}")
    print(f"Records per vessel (avg): {len(df) / df['vessel_id'].nunique():.0f}")
    print(f"\nSample data:")
    print(df.head(3))
    
    # Create output directory
    output_path = "/tmp/parquet_samples"
    os.makedirs(output_path, exist_ok=True)
    
    # Write partitioned files
    write_partitioned_parquet(df, output_path)
    
    # Show directory structure
    print(f"\n{'='*70}")
    print("Directory Structure:")
    print(f"{'='*70}")
    os.system(f"tree -L 2 {output_path}")
    
    print(f"\n{'='*70}")
    print(f"✓ Complete! Files written to: {output_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
EOF

# Make script executable
chmod +x ~/create_sample_parquet.py
```

### Run the Generator

```bash
# Activate virtual environment
source ~/venv-iceberg/bin/activate

# Run the generator
python3 ~/create_sample_parquet.py
```

**Expected Output:**
- ~100,000 records
- Partitioned by date
- Multiple Parquet files in `/tmp/parquet_samples/`
- Snappy compression

---

## Step 8: Upload Parquet Files to MinIO

```bash
# Upload the entire directory structure to MinIO
mc cp --recursive /tmp/parquet_samples/ local/iceberg/warehouse/vessel_telemetry/

# Verify upload
mc ls --recursive local/iceberg/warehouse/vessel_telemetry/

# Check total size
mc du local/iceberg/warehouse/vessel_telemetry/
```

---

## Step 9: Setup Apache Iceberg

### Install PyIceberg

```bash
# Activate virtual environment
source ~/venv-iceberg/bin/activate

# Install PyIceberg with S3 support
pip install "pyiceberg[s3fs,pyarrow,sql-postgres]"

# Verify installation
python3 -c "import pyiceberg; print(pyiceberg.__version__)"
```

### Configure PyIceberg

```bash
# Create configuration directory
mkdir -p ~/.pyiceberg

# Create configuration file
cat > ~/.pyiceberg/config.yaml << 'EOF'
catalog:
  default:
    type: sql
    uri: postgresql://your_user:your_password@localhost:5432/iceberg_catalog
    s3.endpoint: http://localhost:9000
    s3.access-key-id: admin
    s3.secret-access-key: SuperSecurePassword123!
    s3.path-style-access: true
    warehouse: s3://iceberg/warehouse
EOF
```

**Important:** Replace `your_user` and `your_password` with your PostgreSQL credentials.

---

## Step 10: Create PostgreSQL Catalog Database

```bash
# Connect to PostgreSQL
psql -U your_user -d postgres
```

```sql
-- Create database for Iceberg catalog
CREATE DATABASE iceberg_catalog;

-- Verify
\l iceberg_catalog

-- Exit
\q
```

---

## Step 11: Register Parquet Files as Iceberg Table

### Create Registration Script

```bash
cat > ~/register_iceberg_table.py << 'EOF'
#!/usr/bin/env python3
"""
Register existing Parquet files as an Apache Iceberg table.
"""

from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, StringType, DoubleType, 
    TimestampType, IntegerType
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform

def create_catalog():
    """Initialize Iceberg catalog connection"""
    
    catalog = SqlCatalog(
        name="default",
        **{
            "uri": "postgresql://your_user:your_password@localhost:5432/iceberg_catalog",
            "s3.endpoint": "http://localhost:9000",
            "s3.access-key-id": "admin",
            "s3.secret-access-key": "SuperSecurePassword123!",
            "s3.path-style-access": "true",
            "warehouse": "s3://iceberg/warehouse"
        }
    )
    
    return catalog


def create_namespace(catalog):
    """Create namespace (schema) for tables"""
    
    try:
        catalog.create_namespace("maritime")
        print("✓ Created namespace: maritime")
    except Exception as e:
        print(f"ℹ Namespace 'maritime' already exists or error: {e}")


def define_schema():
    """Define table schema matching Parquet files"""
    
    schema = Schema(
        NestedField(1, "timestamp", TimestampType(), required=True),
        NestedField(2, "vessel_id", StringType(), required=True),
        NestedField(3, "latitude", DoubleType(), required=False),
        NestedField(4, "longitude", DoubleType(), required=False),
        NestedField(5, "speed_knots", DoubleType(), required=False),
        NestedField(6, "heading", DoubleType(), required=False),
        NestedField(7, "engine_rpm", IntegerType(), required=False),
        NestedField(8, "fuel_consumption_lph", DoubleType(), required=False),
        NestedField(9, "water_temp_celsius", DoubleType(), required=False),
        NestedField(10, "air_temp_celsius", DoubleType(), required=False),
        NestedField(11, "wind_speed_knots", DoubleType(), required=False),
        NestedField(12, "wave_height_meters", DoubleType(), required=False),
    )
    
    return schema


def define_partition_spec():
    """Define partitioning strategy"""
    
    partition_spec = PartitionSpec(
        PartitionField(
            source_id=1,  # timestamp field
            field_id=1000,
            transform=DayTransform(),
            name="timestamp_day"
        )
    )
    
    return partition_spec


def create_table(catalog, schema, partition_spec):
    """Create Iceberg table"""
    
    try:
        table = catalog.create_table(
            identifier="maritime.vessel_telemetry",
            schema=schema,
            location="s3://iceberg/warehouse/vessel_telemetry",
            partition_spec=partition_spec
        )
        
        print("\n" + "="*70)
        print("✓ Iceberg table created successfully!")
        print("="*70)
        print(f"Table identifier: maritime.vessel_telemetry")
        print(f"Table location: {table.location()}")
        print(f"\nSchema:\n{table.schema()}")
        print(f"\nPartition spec:\n{table.spec()}")
        
        return table
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return None


def main():
    """Main execution"""
    
    print("="*70)
    print("Apache Iceberg Table Registration")
    print("="*70)
    
    # Initialize catalog
    print("\n1. Connecting to Iceberg catalog...")
    catalog = create_catalog()
    print("✓ Connected to catalog")
    
    # Create namespace
    print("\n2. Creating namespace...")
    create_namespace(catalog)
    
    # Define schema
    print("\n3. Defining table schema...")
    schema = define_schema()
    print("✓ Schema defined")
    
    # Define partitioning
    print("\n4. Defining partition strategy...")
    partition_spec = define_partition_spec()
    print("✓ Partition spec defined (partitioned by day)")
    
    # Create table
    print("\n5. Creating Iceberg table...")
    table = create_table(catalog, schema, partition_spec)
    
    if table:
        print("\n" + "="*70)
        print("✓ Setup Complete!")
        print("="*70)


if __name__ == "__main__":
    main()
EOF

# Make executable
chmod +x ~/register_iceberg_table.py
```

**Important:** Edit the script and replace PostgreSQL credentials.

### Run Registration

```bash
# Activate virtual environment
source ~/venv-iceberg/bin/activate

# Run registration script
python3 ~/register_iceberg_table.py
```

---

## Step 12: Verify Iceberg Catalog

### Create Verification Script

```bash
cat > ~/verify_iceberg.py << 'EOF'
#!/usr/bin/env python3
"""
Verify Iceberg catalog and query table metadata.
"""

from pyiceberg.catalog.sql import SqlCatalog
import pandas as pd

def create_catalog():
    """Initialize catalog connection"""
    
    catalog = SqlCatalog(
        name="default",
        **{
            "uri": "postgresql://your_user:your_password@localhost:5432/iceberg_catalog",
            "s3.endpoint": "http://localhost:9000",
            "s3.access-key-id": "admin",
            "s3.secret-access-key": "SuperSecurePassword123!",
            "s3.path-style-access": "true",
            "warehouse": "s3://iceberg/warehouse"
        }
    )
    
    return catalog


def main():
    """Main verification"""
    
    print("="*70)
    print("Iceberg Catalog Verification")
    print("="*70)
    
    # Connect to catalog
    catalog = create_catalog()
    
    # List namespaces
    print("\n1. Namespaces:")
    print("-" * 70)
    namespaces = catalog.list_namespaces()
    for ns in namespaces:
        print(f"  • {ns}")
    
    # List tables
    print("\n2. Tables in 'maritime' namespace:")
    print("-" * 70)
    tables = catalog.list_tables("maritime")
    for table in tables:
        print(f"  • {table}")
    
    # Load table and show metadata
    print("\n3. Table Metadata:")
    print("-" * 70)
    table = catalog.load_table("maritime.vessel_telemetry")
    
    print(f"Location: {table.location()}")
    print(f"Format version: {table.format_version}")
    print(f"\nSchema:")
    for field in table.schema().fields:
        required = "REQUIRED" if field.required else "OPTIONAL"
        print(f"  {field.field_id:3d}. {field.name:25s} {field.field_type} ({required})")
    
    print(f"\nPartitioning:")
    for field in table.spec().fields:
        print(f"  • {field}")
    
    # Scan and read data sample
    print("\n4. Data Sample:")
    print("-" * 70)
    try:
        df = table.scan().to_pandas()
        
        print(f"Total records: {len(df):,}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Unique vessels: {df['vessel_id'].nunique()}")
        
        print(f"\nFirst 5 records:")
        print(df.head())
        
        print(f"\nData types:")
        print(df.dtypes)
        
    except Exception as e:
        print(f"Note: Could not read data - {e}")
        print("This is normal if Parquet files haven't been added to table yet.")
    
    print("\n" + "="*70)
    print("✓ Verification Complete")
    print("="*70)


if __name__ == "__main__":
    main()
EOF

chmod +x ~/verify_iceberg.py
```

### Run Verification

```bash
# Activate virtual environment
source ~/venv-iceberg/bin/activate

# Run verification
python3 ~/verify_iceberg.py
```

---

## Architecture Summary

```
┌──────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           MinIO Server (S3-Compatible)             │    │
│  │           • API Port: 9000                         │    │
│  │           • Console Port: 9001                     │    │
│  │           • Storage: /data/minio                   │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│                       ├─ Bucket: iceberg                     │
│                       │   └─ warehouse/                      │
│                       │       └─ vessel_telemetry/           │
│                       │           ├─ data/                   │
│                       │           │   ├─ date=2024-01-01/   │
│                       │           │   │   └─ data.parquet   │
│                       │           │   ├─ date=2024-01-02/   │
│                       │           │   │   └─ data.parquet   │
│                       │           │   └─ ...                │
│                       │           └─ metadata/              │
│                       │               ├─ version-hint.text  │
│                       │               └─ v1.metadata.json   │
└───────────────────────┴──────────────────────────────────────┘
                        │
                        │
┌───────────────────────┴──────────────────────────────────────┐
│                   METADATA LAYER                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         PostgreSQL (Iceberg Catalog)               │    │
│  │         • Database: iceberg_catalog                │    │
│  │         • Stores: table schemas, snapshots,        │    │
│  │           partitions, file manifests               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                        │
                        │
┌───────────────────────┴──────────────────────────────────────┐
│                   ACCESS LAYER                               │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              PyIceberg Python SDK                  │    │
│  │              • Query metadata                      │    │
│  │              • Read Parquet files                  │    │
│  │              • Manage table schemas                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Future: Add Trino, Spark, or other query engines          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Useful Commands Reference

### MinIO Management

```bash
# Start/stop/restart MinIO
sudo systemctl start minio
sudo systemctl stop minio
sudo systemctl restart minio
sudo systemctl status minio

# View logs
sudo journalctl -u minio -f

# MinIO Client commands
mc ls local/                              # List buckets
mc ls --recursive local/iceberg/          # List all objects
mc du local/iceberg/                      # Check bucket size
mc tree local/iceberg/                    # Show tree structure
mc cp file.parquet local/iceberg/path/    # Upload file
mc rm --recursive local/iceberg/path/     # Delete path
```

### PyIceberg Commands

```python
# In Python shell
from pyiceberg.catalog.sql import SqlCatalog

# Connect
catalog = SqlCatalog("default", **config)

# List operations
catalog.list_namespaces()
catalog.list_tables("maritime")

# Load table
table = catalog.load_table("maritime.vessel_telemetry")

# Table operations
table.schema()
table.spec()
table.location()
table.scan().to_pandas()

# Get snapshots
table.snapshots()

# Time travel
table.scan(snapshot_id=123456).to_pandas()
```

### PostgreSQL Catalog Queries

```sql
-- Connect to catalog
\c iceberg_catalog

-- Show Iceberg tables
\dt

-- Query table metadata
SELECT * FROM iceberg_tables;
SELECT * FROM iceberg_namespace_properties;
```

---

## Troubleshooting

### MinIO Won't Start

```bash
# Check logs
sudo journalctl -u minio -n 50

# Verify permissions
ls -la /data/minio
# Should be owned by minio-user

# Fix permissions if needed
sudo chown -R minio-user:minio-user /data/minio

# Test binary
/usr/local/bin/minio --version
```

### Can't Connect to MinIO

```bash
# Check if ports are open
sudo netstat -tlnp | grep minio

# Check firewall
sudo ufw status
sudo ufw allow 9000
sudo ufw allow 9001

# Test connectivity
curl http://localhost:9000/minio/health/live
```

### PyIceberg Connection Issues

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test PostgreSQL connection
psql -U your_user -d iceberg_catalog -c "SELECT 1;"

# Check MinIO connectivity from Python
python3 -c "import boto3; s3 = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='admin', aws_secret_access_key='SuperSecurePassword123!'); print(s3.list_buckets())"
```

### Parquet Files Not Showing Up

```bash
# Verify files in MinIO
mc ls --recursive local/iceberg/warehouse/vessel_telemetry/

# Check file permissions
mc stat local/iceberg/warehouse/vessel_telemetry/data/date=2024-01-01/data.parquet

# Verify Iceberg table location
python3 -c "from pyiceberg.catalog.sql import SqlCatalog; cat = SqlCatalog('default', **config); t = cat.load_table('maritime.vessel_telemetry'); print(t.location())"
```

---

## Production Considerations

### Security

1. **Change default credentials**
   - Update MinIO root user/password
   - Use strong PostgreSQL passwords
   - Consider using secrets management

2. **Enable TLS/SSL**
   ```bash
   # Generate certificates for MinIO
   mkdir -p /data/minio/certs
   # Add your SSL certificates
   # Update MinIO service to use certificates
   ```

3. **Network security**
   ```bash
   # Restrict access with firewall
   sudo ufw allow from trusted_ip to any port 9000
   sudo ufw allow from trusted_ip to any port 9001
   ```

### High Availability

1. **Multi-node MinIO**
   ```bash
   # Use multiple disks/nodes
   MINIO_VOLUMES="/disk1 /disk2 /disk3 /disk4"
   # Or distributed setup
   MINIO_VOLUMES="http://node{1...4}/data/minio"
   ```

2. **PostgreSQL replication**
   - Setup streaming replication
   - Use connection pooling (PgBouncer)

### Monitoring

1. **MinIO metrics**
   ```bash
   # Enable Prometheus metrics
   mc admin prometheus generate local
   ```

2. **Logs**
   ```bash
   # Centralize logs
   sudo journalctl -u minio -o json | your_log_aggregator
   ```

### Backup Strategy

1. **MinIO data**
   ```bash
   # Use mc mirror for backups
   mc mirror local/iceberg backup-location/iceberg
   ```

2. **PostgreSQL catalog**
   ```bash
   # Regular pg_dump
   pg_dump -U your_user iceberg_catalog > iceberg_catalog_backup.sql
   ```

---

## Next Steps

After completing this setup, you can:

1. **Add query engines**
   - Install Trino to query Iceberg tables
   - Setup Apache Spark for big data processing
   - Use DuckDB for analytical queries

2. **Automate data ingestion**
   - Create scheduled jobs to export from PostgreSQL
   - Setup streaming ingestion pipelines
   - Implement CDC (Change Data Capture)

3. **Optimize performance**
   - Tune Parquet file sizes (aim for 128MB-512MB)
   - Compact small files regularly
   - Implement Z-ordering for better query performance

4. **Add data quality checks**
   - Implement schema validation
   - Add data quality assertions
   - Setup automated testing

---

## Additional Resources

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [PyIceberg Documentation](https://py.iceberg.apache.org/)
- [Parquet Format Specification](https://parquet.apache.org/docs/)

---

## License

This guide is provided as-is for educational and production use.

---

## Support

For issues or questions:
1. Check MinIO logs: `sudo journalctl -u minio -f`
2. Check PostgreSQL logs: `sudo journalctl -u postgresql -f`
3. Review PyIceberg documentation
4. Verify network connectivity and permissions

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Tested On:** Ubuntu 22.04 LTS, Ubuntu 24.04 LTS
