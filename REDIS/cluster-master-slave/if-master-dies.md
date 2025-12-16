redis-cli -p 6380 REPLICAOF NO ONE


redis-cli -p 6379 REPLICAOF 127.0.0.1 6380
