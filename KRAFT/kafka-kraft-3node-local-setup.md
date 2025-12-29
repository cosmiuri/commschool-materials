# Apache Kafka KRaft Cluster Setup (3 Nodes - Local)

This guide walks you through setting up a 3-node Apache Kafka cluster using KRaft mode (without ZooKeeper) on a local machine.

---

## STEP 1: Configure Environment

### 1.1 Install Monitoring Tool (Optional)
```bash
sudo apt install btop
```

### 1.2 Update System
```bash
sudo apt update
sudo apt install -y wget gnupg software-properties-common
```

### 1.3 Install Java 21

### 1.4 Configure Java Environment

### 1.5 Configure Hostnames
```bash
sudo nano /etc/hosts
```

Add the following entries:
```
127.0.0.1  kafka-node-1
127.0.0.2  kafka-node-2
127.0.0.3  kafka-node-3
```

### 1.6 Install Unzip
```bash
sudo apt install unzip
```

---

## STEP 2: Install Kafka 4.1.1

```bash
cd /opt

# Download Kafka
sudo wget https://downloads.apache.org/kafka/4.1.1/kafka_2.13-4.1.1.tgz

# Extract
sudo tar -xzf kafka_2.13-4.1.1.tgz

# Rename
sudo mv kafka_2.13-4.1.1 kafka

# Set ownership
sudo chown -R $USER:$USER /opt/kafka

# Verify installation
/opt/kafka/bin/kafka-topics.sh --version
```

---

## STEP 3: Create Storage Directories

You'll need separate directories for each node:

```bash
# Node 1
sudo mkdir -p /var/lib/kafka-node-1
sudo mkdir -p /var/lib/kafka-logs-node-1

# Node 2
sudo mkdir -p /var/lib/kafka-node-2
sudo mkdir -p /var/lib/kafka-logs-node-2

# Node 3
sudo mkdir -p /var/lib/kafka-node-3
sudo mkdir -p /var/lib/kafka-logs-node-3

# Set ownership
sudo chown -R $USER:$USER /var/lib/kafka-*
```

---

## STEP 4: Configure the Cluster

### 4.1 Generate Cluster ID
Run this **once** and save the output:
```bash
/opt/kafka/bin/kafka-storage.sh random-uuid
```

Example output: `7Ncgy61pSS-yJJl7uMcT-Q`

### 4.2 Create Configuration Files

Navigate to Kafka config directory:
```bash
cd /opt/kafka/config
```

#### Node 1 Configuration
Create `server-node-1.properties`:
```bash
nano server-node-1.properties
```

```properties
############################# KRaft Node Identity #############################

# This node runs both broker and controller roles
process.roles=broker,controller

# Unique ID of this node in the cluster
node.id=1

############################# Storage Directories #############################

# Metadata log (KRaft internal __cluster_metadata topic)
metadata.log.dir=/var/lib/kafka-node-1

# Broker data (topic partitions)
log.dirs=/var/lib/kafka-logs-node-1

############################# Listeners #############################

# Listeners for broker and controller
listeners=PLAINTEXT://127.0.0.1:9092,CONTROLLER://127.0.0.1:9093

# Name of listener used between brokers
inter.broker.listener.name=PLAINTEXT

# Advertised listener (what clients connect to)
advertised.listeners=PLAINTEXT://127.0.0.1:9092

# Controller listener name
controller.listener.names=CONTROLLER

# Map listeners to security protocols
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL

############################# Controller Quorum (STATIC) #############################
# Same on ALL 3 NODES
controller.quorum.voters=1@127.0.0.1:9093,2@127.0.0.1:19093,3@127.0.0.1:29093

############################# Socket Server Settings #############################

num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

############################# Log Basics #############################

# Default partitions for newly created topics
num.partitions=3

# Threads per log directory for recovery/flush
num.recovery.threads.per.data.dir=1

############################# Internal Topic Settings #############################

offsets.topic.replication.factor=3
share.coordinator.state.topic.replication.factor=3
share.coordinator.state.topic.min.isr=2
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

############################# Log Retention Policy #############################

log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

############################# Misc #############################

# Disable auto topic creation (recommended for production)
auto.create.topics.enable=false
```

#### Node 2 Configuration
Create `server-node-2.properties`:
```bash
nano server-node-2.properties
```

```properties
############################# KRaft Node Identity #############################

process.roles=broker,controller
node.id=2

############################# Storage Directories #############################

metadata.log.dir=/var/lib/kafka-node-2
log.dirs=/var/lib/kafka-logs-node-2

############################# Listeners #############################

listeners=PLAINTEXT://127.0.0.1:19092,CONTROLLER://127.0.0.1:19093
inter.broker.listener.name=PLAINTEXT
advertised.listeners=PLAINTEXT://127.0.0.1:19092
controller.listener.names=CONTROLLER
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL

############################# Controller Quorum (STATIC) #############################

controller.quorum.voters=1@127.0.0.1:9093,2@127.0.0.1:19093,3@127.0.0.1:29093

############################# Socket Server Settings #############################

num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

############################# Log Basics #############################

num.partitions=3
num.recovery.threads.per.data.dir=1

############################# Internal Topic Settings #############################

offsets.topic.replication.factor=3
share.coordinator.state.topic.replication.factor=3
share.coordinator.state.topic.min.isr=2
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

############################# Log Retention Policy #############################

log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

############################# Misc #############################

auto.create.topics.enable=false
```

#### Node 3 Configuration
Create `server-node-3.properties`:
```bash
nano server-node-3.properties
```

```properties
############################# KRaft Node Identity #############################

process.roles=broker,controller
node.id=3

############################# Storage Directories #############################

metadata.log.dir=/var/lib/kafka-node-3
log.dirs=/var/lib/kafka-logs-node-3

############################# Listeners #############################

listeners=PLAINTEXT://127.0.0.1:29092,CONTROLLER://127.0.0.1:29093
inter.broker.listener.name=PLAINTEXT
advertised.listeners=PLAINTEXT://127.0.0.1:29092
controller.listener.names=CONTROLLER
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL

############################# Controller Quorum (STATIC) #############################

controller.quorum.voters=1@127.0.0.1:9093,2@127.0.0.1:19093,3@127.0.0.1:29093

############################# Socket Server Settings #############################

num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

############################# Log Basics #############################

num.partitions=3
num.recovery.threads.per.data.dir=1

############################# Internal Topic Settings #############################

offsets.topic.replication.factor=3
share.coordinator.state.topic.replication.factor=3
share.coordinator.state.topic.min.isr=2
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

############################# Log Retention Policy #############################

log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

############################# Misc #############################

auto.create.topics.enable=false
```

### 4.3 Format Storage
Replace `YOUR-CLUSTER-ID` with the UUID generated in step 4.1:

```bash
# Node 1
/opt/kafka/bin/kafka-storage.sh format \
  --config /opt/kafka/config/server-node-1.properties \
  --cluster-id YOUR-CLUSTER-ID \
  --ignore-formatted

# Node 2
/opt/kafka/bin/kafka-storage.sh format \
  --config /opt/kafka/config/server-node-2.properties \
  --cluster-id YOUR-CLUSTER-ID \
  --ignore-formatted

# Node 3
/opt/kafka/bin/kafka-storage.sh format \
  --config /opt/kafka/config/server-node-3.properties \
  --cluster-id YOUR-CLUSTER-ID \
  --ignore-formatted
```

### 4.4 Start Kafka Brokers

Open 3 separate terminal windows and run each command:

**Terminal 1 (Node 1):**
```bash
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-1.properties
```

**Terminal 2 (Node 2):**
```bash
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-2.properties
```

**Terminal 3 (Node 3):**
```bash
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-3.properties
```

### 4.5 Verify Cluster Status
```bash
cd /opt/kafka
bin/kafka-metadata-quorum.sh \
  --bootstrap-controller 127.0.0.1:9093 \
  describe --status
```

Expected output:
```
ClusterId:              YOUR-CLUSTER-ID
LeaderId:               1
LeaderEpoch:            1
HighWatermark:          698
MaxFollowerLag:         0
MaxFollowerLagTimeMs:   404
CurrentVoters:          [{"id": 1, "endpoints": ["CONTROLLER://127.0.0.1:9093"]}, {"id": 2, "endpoints": ["CONTROLLER://127.0.0.1:19093"]}, {"id": 3, "endpoints": ["CONTROLLER://127.0.0.1:29093"]}]
CurrentObservers:       []
```

---


=====================================
=====================================
=====================================
=====================================

# OPTIONAL FROM HERE

=====================================
=====================================
=====================================
=====================================

## STEP 5: Create Systemd Services (Optional)

For production-like setup, create systemd services for each node.

### Node 1 Service
```bash
sudo nano /etc/systemd/system/kafka-node-1.service
```

```ini
[Unit]
Description=Apache Kafka Server Node 1 (KRaft)
After=network.target

[Service]
User=YOUR_USERNAME
Group=YOUR_USERNAME
Environment="JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64"
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-1.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Node 2 Service
```bash
sudo nano /etc/systemd/system/kafka-node-2.service
```

```ini
[Unit]
Description=Apache Kafka Server Node 2 (KRaft)
After=network.target

[Service]
User=YOUR_USERNAME
Group=YOUR_USERNAME
Environment="JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64"
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-2.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Node 3 Service
```bash
sudo nano /etc/systemd/system/kafka-node-3.service
```

```ini
[Unit]
Description=Apache Kafka Server Node 3 (KRaft)
After=network.target

[Service]
User=YOUR_USERNAME
Group=YOUR_USERNAME
Environment="JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64"
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server-node-3.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services
```bash
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable kafka-node-1
sudo systemctl enable kafka-node-2
sudo systemctl enable kafka-node-3

# Start services
sudo systemctl start kafka-node-1
sudo systemctl start kafka-node-2
sudo systemctl start kafka-node-3

# Check status
sudo systemctl status kafka-node-1
sudo systemctl status kafka-node-2
sudo systemctl status kafka-node-3
```

---

## Quick Reference

### Port Mappings
| Node | Broker Port | Controller Port | Connect Port |
|------|-------------|-----------------|--------------|
| 1    | 9092        | 9093            | 8083         |
| 2    | 19092       | 19093           | 18083        |
| 3    | 29092       | 29093           | 28083        |

### Bootstrap Servers
```
127.0.0.1:9092,127.0.0.1:19092,127.0.0.1:29092
```

### Common Commands
```bash
# Check cluster status
/opt/kafka/bin/kafka-metadata-quorum.sh \
  --bootstrap-controller 127.0.0.1:9093 describe --status

# List topics
/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server 127.0.0.1:9092 --list

# Create topic
/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server 127.0.0.1:9092 \
  --create --topic test-topic \
  --partitions 3 --replication-factor 3

# Describe topic
/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server 127.0.0.1:9092 \
  --describe --topic test-topic

# Produce messages
/opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server 127.0.0.1:9092 \
  --topic test-topic

# Consume messages
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server 127.0.0.1:9092 \
  --topic test-topic --from-beginning
```

### Common Issues

**Port Already in Use**
```bash
# Find process using port
sudo lsof -i :9092

# Kill process
kill -9 <PID>
```

**Storage Already Formatted**
If you need to re-format storage:
```bash
rm -rf /var/lib/kafka-node-*
rm -rf /var/lib/kafka-logs-node-*
# Then re-create directories and re-run format commands
```

**Connection Refused**
- Verify all three brokers are running
- Check firewall settings
- Confirm correct ports in configuration

---
