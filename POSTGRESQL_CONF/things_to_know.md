# Important PostgreSQL Configuration Settings

This markdown file provides a practical breakdown of the most important PostgreSQL configuration parameters from the `postgresql.conf` file. It focuses on the settings that truly matter in real-world deployments.

---

## 1. Memory Settings

### `shared_buffers`

Memory PostgreSQL uses for caching data pages. Increasing this improves read performance.

Typical: about 25% of system RAM for dedicated DB servers.

### `work_mem`

Memory used for each sort or hash operation (ORDER BY, JOIN, GROUP BY). Too large can exhaust RAM.

Typical: 4MB–64MB depending on workload.

### `maintenance_work_mem`

Used by VACUUM, ANALYZE, and CREATE INDEX operations.

Typical: 512MB–2GB.

### `effective_cache_size`

PostgreSQL's estimate of total cache available between shared buffers and OS cache. Helps planner choose better strategies.

Typical: 50–75% of total RAM.

---

## 2. WAL and Checkpoint Settings

### `wal_level`

Controls how much write-ahead log information PostgreSQL records.

* `minimal`: fastest, no replication.
* `replica`: for streaming replication.
* `logical`: for logical decoding or CDC.

### `checkpoint_timeout`

How often a full checkpoint occurs.

Typical: 15–30 minutes.

### `max_wal_size`

Maximum size that WAL files may grow before forcing a checkpoint.

Typical: 1–4GB.

### `min_wal_size`

Minimum amount of WAL kept on disk.

Default is usually fine.

### `synchronous_commit`

Controls whether a transaction waits for WAL to be flushed to durable storage.

* `on`: safest.
* `off`: faster, but risks losing a few milliseconds of data.

---

## 3. Connection Settings

### `max_connections`

Maximum number of client connections.

Typical: 100–200 on servers; use PgBouncer for pooling.

### `superuser_reserved_connections`

Prevents lockout by reserving some connections for superusers.

---

## 4. Autovacuum Settings

### `autovacuum`

Ensures table bloat is kept under control.

Must remain enabled.

### `autovacuum_naptime`

How often the autovacuum launcher runs.

Default: 1 minute.

### `autovacuum_vacuum_cost_limit`

A higher value makes autovacuum more aggressive.

### `autovacuum_vacuum_scale_factor`

Percentage of table updates before vacuum runs.

Default 20% is far too high. More realistic:

* OLTP workloads: around 2% (0.02)
* Large tables: about 0.5% (0.005)

### `autovacuum_analyze_scale_factor`

Same concept as above but applies to ANALYZE.

---

## 5. Logging Settings

### `logging_collector`

Enables logging to files.

### `log_directory` and `log_filename`

Control where logs go and how they are named.

### `log_statement`

Controls which SQL statements get logged. Valid options: `none`, `ddl`, `mod`, `all`.

### `log_min_duration_statement`

Logs only slow queries taking longer than the defined time.

Typical: 500–2000ms.

---

## 6. Query Planner Settings

### `random_page_cost`

Planner's estimated cost for random disk reads. On SSD systems, reduce from the old default.

SSD typical: ~1.1.

### `seq_page_cost`

Cost for sequential reads. Normally unchanged.

---

## 7. Monitoring & Extensions

### `track_activities`

Shows what queries are running.

### `track_io_timing`

Enables tracking of I/O timings in statistics.

### `pg_stat_statements.track`

Controls which statements are tracked by the extension.

### `pg_stat_statements.max`

Maximum distinct queries to track.

---

## 8. Authentication and Networking

### `listen_addresses`

Defines which IPs PostgreSQL listens on.

Default: `localhost`. Use `0.0.0.0` only when needed.

### `password_encryption`

Controls hashing algorithm for stored passwords.

Typical: `scram-sha-256`.

### `port`

Default PostgreSQL port.

Standard: `5432`.

---

## Summary: Essential Parameters to Remember

If you only remember a few, these matter most:

* `shared_buffers`
* `work_mem`
* `maintenance_work_mem`
* `effective_cache_size`
* `max_wal_size`
* `checkpoint_timeout`
* `wal_level`
* `synchronous_commit`
* `autovacuum_vacuum_scale_factor`
* `autovacuum_analyze_scale_factor`
* `max_connections`
* `log_min_duration_statement`

---

This file covers the essential settings you need for a healthy and well-performing PostgreSQL deployment. Adjust these based on hardware, workload, and operational requirements.
