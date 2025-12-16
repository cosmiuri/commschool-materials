# Redis Replication on WSL Ubuntu (2 Instances)

---

## 0) Install Redis

```bash
sudo apt update
sudo apt install -y redis-server
redis-server --version
```

---

## 1) Create Separate Config Files

```bash
sudo cp /etc/redis/redis.conf /etc/redis/redis-primary.conf
sudo cp /etc/redis/redis.conf /etc/redis/redis-replica.conf
```

---

## 2) Configure Redis Primary (Port 6379)

```bash
sudo nano /etc/redis/redis-primary.conf
```

```conf
port 6379
bind 127.0.0.1 ::1
protected-mode yes
appendonly yes
pidfile /run/redis/redis-primary.pid
logfile /var/log/redis/redis-primary.log
dir /var/lib/redis/primary
```

```bash
sudo mkdir -p /var/lib/redis/primary
sudo chown redis:redis /var/lib/redis/primary
```

---

## 3) Configure Redis Replica (Port 6380)

```bash
sudo nano /etc/redis/redis-replica.conf
```

```conf
port 6380
bind 127.0.0.1 ::1
protected-mode yes
replicaof 127.0.0.1 6379
pidfile /run/redis/redis-replica.pid
logfile /var/log/redis/redis-replica.log
dir /var/lib/redis/replica
```

```bash
sudo mkdir -p /var/lib/redis/replica
sudo chown redis:redis /var/lib/redis/replica
```

## 4) Run cluster

```bash
sudo redis-server /etc/redis/redis-primary.conf

```

```bash
sudo redis-server /etc/redis/redis-replica.conf
```