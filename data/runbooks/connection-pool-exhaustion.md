# Connection pool exhaustion

Symptoms include requests waiting for database connections and pool-acquisition timeouts. Check active versus configured connections, recent pool-size changes, and database saturation. Compare the current setting with the last known healthy deployment before proposing a rollback or configuration change.
