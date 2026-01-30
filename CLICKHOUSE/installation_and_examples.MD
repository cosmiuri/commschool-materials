# ClickHouse on Ubuntu (WSL)  Install, Run, Examples


```
https://clickhouse.com/docs/install/debian_ubuntu
```

## 3) Start ClickHouse server
```bash
sudo service clickhouse-server start
```

## 4) Verify server
```bash
clickhouse-client --query "SELECT version()"
```

## 5) Open ClickHouse shell
```bash
clickhouse-client
```

## 6) Database setup
```sql
CREATE DATABASE IF NOT EXISTS demo;
USE demo;
```

---

# Table Engine Examples

## A) MergeTree
```sql
DROP TABLE IF EXISTS events;

CREATE TABLE events
(
  event_date Date,
  ts DateTime,
  ship_id UInt32,
  port String,
  sog Float32,
  lat Float64,
  lon Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (ship_id, ts);

INSERT INTO events VALUES
('2026-01-30','2026-01-30 10:00:00',101,'Hamburg',0.10,53.5511,9.9937),
('2026-01-30','2026-01-30 10:03:00',101,'Hamburg',0.00,53.5511,9.9937),
('2026-01-30','2026-01-30 10:06:00',101,'Hamburg',0.20,53.5512,9.9938),
('2026-01-30','2026-01-30 11:00:00',202,'Kiel',12.30,54.3233,10.1228);
```

## B) MergeTree with TTL
```sql
DROP TABLE IF EXISTS events_ttl;

CREATE TABLE events_ttl
(
  event_date Date,
  ts DateTime,
  ship_id UInt32,
  sog Float32
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (ship_id, ts)
TTL ts + INTERVAL 30 DAY;
```

---

# Other Engines

## Memory
```sql
CREATE TABLE cache_mem
(
  k String,
  v String
)
ENGINE = Memory;
```
