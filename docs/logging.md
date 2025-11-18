# Logging Guide for Planted

## Overview

Planted uses a comprehensive logging system built on Python's `logging` module. The system provides:

- **Structured logging** with consistent formatting
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Automatic file rotation** (10MB max size, 5 backup files)
- **Request ID tracking** for distributed tracing
- **Separate log files** for different purposes
- **Color-coded console output** for development

## Log Files

All log files are stored in the `logs/` directory at the project root:

### `planted.log`
Main application log containing all log messages at the configured level.

- **Development**: DEBUG level and above
- **Production**: INFO level and above
- **Rotation**: 10MB max size, 5 backup files
- **Format**: Includes timestamp, logger name, level, file location, request ID, and message

### `planted_error.log`
Error-only log containing ERROR and CRITICAL level messages.

- **Level**: ERROR and above only
- **Rotation**: 10MB max size, 5 backup files
- **Use**: Quick identification of application errors

### `planted_access.log`
HTTP access log for request tracking.

- **Level**: INFO and above
- **Rotation**: 10MB max size, 5 backup files
- **Use**: Monitor API usage and user activity

## Log Levels

Use appropriate log levels for different situations:

### DEBUG
Detailed diagnostic information. Only visible in development mode.

```python
logger.debug(f'Processing plant data: {plant_data}')
logger.debug('Database query returned %d results', result_count)
```

### INFO
General informational messages about application flow.

```python
logger.info('Application started successfully')
logger.info('User %s created garden plot %s', user_id, plot_id)
```

### WARNING
Something unexpected happened but the application continues.

```python
logger.warning('Weather API rate limit approaching: %d/%d', current, limit)
logger.warning('Cache miss for key: %s', cache_key)
```

### ERROR
An error occurred that prevented an operation from completing.

```python
logger.error('Failed to save plant data: %s', error, exc_info=True)
logger.error('Database connection failed', exc_info=True)
```

### CRITICAL
A serious error that may cause the application to crash.

```python
logger.critical('Database file corrupted, application cannot start')
logger.critical('Required environment variable missing: %s', var_name)
```

## Using Logging in Code

### Basic Setup

```python
from garden_manager.config import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info('Function started')
    try:
        # Your code here
        logger.debug('Processing data...')
    except Exception as e:
        logger.error('Error in my_function: %s', e, exc_info=True)
        raise
```

### Request ID Tracking

Request IDs are automatically generated for each HTTP request in Flask. You can also set them manually:

```python
from garden_manager.config.logging_config import set_request_id, get_request_id

# Set a custom request ID
request_id = set_request_id('custom-id-123')

# Get the current request ID
current_id = get_request_id()
logger.info('Processing request %s', current_id)
```

### Function Call Logging Decorator

For debugging, you can automatically log function calls:

```python
from garden_manager.config.logging_config import log_function_call

@log_function_call
def calculate_planting_date(plant_name, zone):
    # Function implementation
    return planting_date
```

## Configuration

### Environment Variables

- **FLASK_ENV**: Set to `development` or `production`
  - Development: DEBUG level logging
  - Production: INFO level logging
  
- **LOG_LEVEL**: Override the default log level
  - Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  
- **LOG_DIR**: Override the default log directory
  - Default: `logs/` in project root

### Example

```bash
# Development mode with debug logging
export FLASK_ENV=development
python main.py

# Production mode with info logging
export FLASK_ENV=production
export LOG_LEVEL=INFO
python main.py

# Custom log directory
export LOG_DIR=/var/log/planted
python main.py
```

## Production Deployment

### Log Rotation

Logs automatically rotate when they reach 10MB. The system keeps 5 backup files:

- `planted.log` (current)
- `planted.log.1` (most recent backup)
- `planted.log.2`
- `planted.log.3`
- `planted.log.4`
- `planted.log.5` (oldest backup)

### Log Aggregation Services

For production deployments, consider integrating with log aggregation services:

#### AWS CloudWatch

```bash
pip install watchtower
```

Add to `app.py`:

```python
import watchtower

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='planted',
    stream_name='application'
)
logger.addHandler(cloudwatch_handler)
```

#### Datadog

```bash
pip install datadog
```

Configure Datadog agent and set `DD_API_KEY` environment variable.

#### Splunk

```bash
pip install splunk-handler
```

Add to `app.py`:

```python
from splunk_handler import SplunkHandler

splunk = SplunkHandler(
    host='splunk.example.com',
    token='your_token',
    index='planted'
)
logger.addHandler(splunk)
```

#### ELK Stack

```bash
pip install python-logstash
```

Add to `app.py`:

```python
import logstash

elk_handler = logstash.TCPLogstashHandler(
    'logstash.example.com', 5959, version=1
)
logger.addHandler(elk_handler)
```

#### Sentry (Error Tracking)

```bash
pip install sentry-sdk
```

Add to `app.py`:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your_sentry_dsn",
    traces_sample_rate=1.0
)
```

## Best Practices

### DO:

✅ Use appropriate log levels
✅ Include context in log messages
✅ Use parameter substitution (not string concatenation)
✅ Log exceptions with `exc_info=True`
✅ Include request IDs for tracing
✅ Log important business events

```python
# Good examples
logger.info('User %s created garden %s', user_id, garden_id)
logger.error('Failed to process plant: %s', plant_name, exc_info=True)
logger.debug('Query parameters: %s', params)
```

### DON'T:

❌ Log sensitive information (passwords, API keys, tokens)
❌ Log the same event multiple times
❌ Use string concatenation for log messages
❌ Log at inappropriate levels
❌ Ignore exceptions without logging

```python
# Bad examples
logger.info(f'User password: {password}')  # Never log passwords!
logger.info('Processing ' + str(data))  # Use % formatting or f-strings with parameters
logger.critical('Debug information')  # Wrong level
```

### Masking Sensitive Data

When logging data that might contain sensitive information:

```python
def mask_sensitive_data(data):
    """Mask sensitive fields in data."""
    if 'password' in data:
        data['password'] = '***'
    if 'api_key' in data:
        data['api_key'] = '***'
    return data

logger.info('User data: %s', mask_sensitive_data(user_data))
```

## Monitoring and Alerts

### Setting Up Alerts

Configure alerts for:

1. **High error rate**: More than 10 errors per minute
2. **Critical logs**: Any CRITICAL level log
3. **Disk space**: When log directory exceeds 80% capacity
4. **Application restarts**: When application starts (INFO level)

### Log Analysis

Use log aggregation tools to:

- Track request patterns
- Identify slow operations
- Monitor error trends
- Analyze user behavior
- Debug production issues

### Example Queries

**Find all errors in the last hour:**
```bash
grep ERROR planted.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')"
```

**Count requests by endpoint:**
```bash
grep "POST\|GET\|PUT\|DELETE" planted_access.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

**Find slow operations:**
```bash
grep "took" planted.log | awk '{if ($NF > 1000) print}'
```

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify log directory exists and is writable
3. Check file handlers are enabled
4. Ensure logging is initialized before use

### Log Files Growing Too Large

1. Reduce log level (INFO instead of DEBUG)
2. Adjust rotation settings (smaller maxBytes)
3. Reduce backup count
4. Archive old logs more frequently

### Performance Issues

1. Use asynchronous logging for high-volume applications
2. Reduce log level in production
3. Disable console logging in production
4. Use separate log files for different components

## Testing Logging

Run the test suite to verify logging configuration:

```bash
pytest tests/unit/test_logging.py -v
```

Manual testing:

```python
from garden_manager.config import setup_logging, get_logger

# Initialize logging
setup_logging('planted')

# Get logger
logger = get_logger(__name__)

# Test different log levels
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')
```

## Migration Notes

This logging system replaces all `print()` statements in the codebase. Key changes:

- `print("Success")` → `logger.info("Success")`
- `print(f"Error: {e}")` → `logger.error("Error: %s", e, exc_info=True)`
- Debug prints → `logger.debug("...")`

All print statements have been converted to use appropriate log levels based on context.
