# Investigating a bad deployment

Compare the incident start time with deployment events and inspect the changed version and configuration. Look for direct log evidence linking the new version to the failure. If the timeline and evidence support a regression, recommend a rollback for human approval; never perform it automatically.
