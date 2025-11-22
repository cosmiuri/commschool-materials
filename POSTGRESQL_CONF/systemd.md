# Running Multiple PostgreSQL Instances on WSL Using systemd

## 1. Find your PostgreSQL version

Systemd cannot use wildcards (`*`), so you must check the installed
version:

``` bash
ls /usr/lib/postgresql/
```

Example output:

    16

Pick the version you are actually using (example: 15).

------------------------------------------------------------------------

## 2. Create systemd service for Instance 1

Create:

``` bash
sudo nano /etc/systemd/system/postgres-instance1.service
```

Paste this (update the version number if needed):

``` ini
[Unit]
Description=PostgreSQL Instance 1
After=network.target

[Service]
Type=forking
User=postgres
Group=postgres
ExecStart=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance1 -l /var/lib/postgresql/instance1/logfile start
ExecStop=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance1 stop
ExecReload=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance1 reload

[Install]
WantedBy=multi-user.target
```

------------------------------------------------------------------------

## 3. Create systemd service for Instance 2

``` bash
sudo nano /etc/systemd/system/postgres-instance2.service
```

Paste:

``` ini
[Unit]
Description=PostgreSQL Instance 2
After=network.target

[Service]
Type=forking
User=postgres
Group=postgres
ExecStart=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance2 -l /var/lib/postgresql/instance2/logfile start
ExecStop=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance2 stop
ExecReload=/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/instance2 reload

[Install]
WantedBy=multi-user.target
```

------------------------------------------------------------------------

## 4. Reload systemd to register services

``` bash
sudo systemctl daemon-reload
```

------------------------------------------------------------------------

## 5. Start/Stop/Restart instances

### Instance 1:

``` bash
sudo systemctl start postgres-instance1
sudo systemctl stop postgres-instance1
sudo systemctl restart postgres-instance1
sudo systemctl status postgres-instance1
```

### Instance 2:

``` bash
sudo systemctl start postgres-instance2
sudo systemctl stop postgres-instance2
sudo systemctl restart postgres-instance2
sudo systemctl status postgres-instance2
```

------------------------------------------------------------------------

## 6. Enable autostart on boot (optional)

``` bash
sudo systemctl enable postgres-instance1
sudo systemctl enable postgres-instance2
```

------------------------------------------------------------------------

## 7. Debugging if something fails

### Check systemd logs:

``` bash
sudo journalctl -xeu postgres-instance1
```

### Check PostgreSQL logs:

``` bash
cat /var/lib/postgresql/instance1/logfile
```

------------------------------------------------------------------------

# Done

You now have simple `systemctl` commands to manage both PostgreSQL
instances on your WSL Ubuntu setup.
