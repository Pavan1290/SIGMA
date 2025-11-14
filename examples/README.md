# SIGMA-OS v3 - Example Workflows & Rules

This directory contains example configurations for workflows, rules, and scheduled tasks.

## 📁 Files

### Workflows

1. **workflow_daily_report.json** - Daily system health report
   - Collects CPU, memory, disk stats
   - Generates report
   - Emails to admin

2. **workflow_screenshot_share.json** - Screenshot & share
   - Takes screenshot
   - Emails to team

3. **workflow_parallel_intelligence.json** - Multi-source data collection
   - Parallel execution
   - Web research + Email check + System status

4. **workflow_automated_backup.json** - Automated backup
   - Lists files
   - Creates archive
   - Verifies backup
   - Sends confirmation

### Rules

1. **rule_high_cpu.json** - CPU usage alert
   - Triggers when CPU > 85%
   - Sends warning alert

2. **rule_workflow_failure.json** - Workflow failure handling
   - Pauses after 3 failures
   - Sends critical alert

## 🚀 Usage

### Create a Workflow

```bash
curl -X POST http://localhost:5000/workflows \
  -H "Content-Type: application/json" \
  -d @examples/workflow_daily_report.json
```

### Schedule a Workflow

```bash
# Run daily at 9 AM
curl -X POST http://localhost:5000/scheduler/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "1",
    "schedule_type": "cron",
    "schedule_config": {
      "hour": 9,
      "minute": 0
    },
    "enabled": true
  }'
```

### Create a Rule

```bash
curl -X POST http://localhost:5000/rules \
  -H "Content-Type: application/json" \
  -d @examples/rule_high_cpu.json
```

## 📝 Customization

### Workflow Steps

Each step has:
- `id`: Unique identifier
- `command`: What to execute
- `agent`: Which agent (system/email/web)
- `depends_on`: List of prerequisite steps
- `retry_count`: Number of retries (default: 3)
- `timeout`: Timeout in seconds (default: 300)

### Schedule Types

1. **once** - Run one time
   ```json
   {
     "schedule_type": "once",
     "schedule_config": {
       "datetime": "2025-11-15T14:30:00"
     }
   }
   ```

2. **interval** - Run every N seconds
   ```json
   {
     "schedule_type": "interval",
     "schedule_config": {
       "interval_seconds": 3600
     }
   }
   ```

3. **cron** - Run at specific times
   ```json
   {
     "schedule_type": "cron",
     "schedule_config": {
       "hour": 9,
       "minute": 0
     }
   }
   ```

### Rule Conditions

Operators:
- `==`, `!=` - Equality
- `>`, `>=`, `<`, `<=` - Comparison
- `contains`, `not_contains` - String matching
- `in`, `not_in` - List membership
- `matches` - Regex matching

Sources:
- `context` - From execution context
- `metrics` - From performance monitor
- `time` - Current time

## 💡 Tips

1. Use `parallel: true` for independent tasks
2. Set realistic timeout values
3. Use dependency chains for sequential workflows
4. Test rules with low thresholds first
5. Monitor via `/dashboard` endpoint
