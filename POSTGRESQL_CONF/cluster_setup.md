# Installing and Running 2 PostgreSQL Instances on WSL Ubuntu

## Step 1: Install PostgreSQL
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y
```

## Step 2: Stop the default PostgreSQL service
```bash
sudo service postgresql stop
```

## Step 3: Create directories for both instances
```bash
# Create data directories
sudo mkdir -p /var/lib/postgresql/instance1
sudo mkdir -p /var/lib/postgresql/instance2

# Set ownership to postgres user
sudo chown -R postgres:postgres /var/lib/postgresql/instance1
sudo chown -R postgres:postgres /var/lib/postgresql/instance2
```

## Step 4: Initialize both database clusters
```bash
# Initialize instance 1 (will use port 5432)
sudo -u postgres /usr/lib/postgresql/*/bin/initdb -D /var/lib/postgresql/instance1

# Initialize instance 2 (will use port 5433)
sudo -u postgres /usr/lib/postgresql/*/bin/initdb -D /var/lib/postgresql/instance2
```

## Step 5: Configure the second instance to use a different port
```bash
# Change port for instance2 from 5432 to 5433
sudo -u postgres sed -i "s/#port = 5432/port = 5433/" /var/lib/postgresql/instance2/postgresql.conf
sudo -u postgres sed -i "s/port = 5432/port = 5433/" /var/lib/postgresql/instance2/postgresql.conf
```

## Step 6: Start both instances
```bash
# Start instance 1 (port 5432)
sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/instance1 -l /var/lib/postgresql/instance1/logfile start

# Start instance 2 (port 5433)
sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/instance2 -l /var/lib/postgresql/instance2/logfile start
```

## Step 7: Verify both instances are running
```bash
# Check PostgreSQL processes
ps aux | grep postgres

# Check status of instance 1
sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/instance1 status

# Check status of instance 2
sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/instance2 status

# Connect to instance 1 and check version
sudo -u postgres psql -p 5432 -c "SELECT version();"

# Connect to instance 2 and check version
sudo -u postgres psql -p 5433 -c "SELECT version();"
```

## Connection Information

### Instance 1
- **Host**: localhost
- **Port**: 5432
- **User**: postgres
- **Connection String**: `postgresql://postgres@localhost:5432/postgres`

### Instance 2
- **Host**: localhost
- **Port**: 5433
- **User**: postgres
- **Connection String**: `postgresql://postgres@localhost:5433/postgres`