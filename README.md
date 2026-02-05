<img align="left" src="https://github.com/kumina/kubi_ecs_logger/blob/master/logo.png">
This Python module makes logging easy for your application.  
The logger outputs JSON formatted logs for ingesting into Elastic.  

The module implements the ECS (Elastic Common Schema) specification that
can be found at for quick reference: 
[ECS Field Reference](https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html#ecs-field-reference)

## Install
You can install the package from PyPi like this:
```bash
pip install kubi-ecs-logger
```
This package is only for Python 3.6 or newer.

## Usage
```python 
# Import 
from kubi_ecs_logger import Logger, Severity

# Set some defaults in the start of your app
# If in development mode the lib will output formatted json.
Logger().dev = True
# The minimum level of severity for outputing. E.g. If set to INFO then DEBUG logs will not 
# be printed to standard out
Logger().severity_output_level = Severity.INFO
# Set default key/value pairs for the different classes that will always be appended before final output
Logger().defaults = {
    "event": {
        "test": "test value"
    }
}

# Log loaded configuration
Logger().event(
    category="configuration",
    action="configuration loaded",
    dataset="The configuration is loaded from config.yaml"
).out(severity=Severity.INFO)

# Output
# {
#   "@timestamp": "2019-07-11T15:11:03.193759+00:00",
#   "event": {
#     "action": "configuration loaded",
#     "category": "configuration",
#     "dataset": "The configuration is loaded from config.yaml",
#     "test": "test value"  # From defaults
#   },
#   "logline": {
#     "level": "INFO"
#   }
# }

# Here is a little bit bigger example
Logger() \
    .event(category="requests", action="request received") \
    .url(path="/test", domain="test.com") \
    .source(ip="123.251.512.152") \
    .http_response(status_code=200) \
    .out(severity=Severity.INFO)

# And here is the output of this one
# {
#   "@timestamp": "2019-07-11T15:15:48.896921+00:00",
#   "event": {
#     "action": "request received",
#     "category": "requests",
#     "test": "test value"  # From defaults
#   },
#   "httpresponse": {
#     "status_code": "200"
#   },
#   "logline": {
#     "level": "INFO"
#   },
#   "source": {
#     "ip": "123.251.512.152"
#   },
#   "url": {
#     "domain": "test.com",
#     "path": "/test"
#   }
# }
```

## Available Fields

The logger supports 27+ ECS field sets. Each field set has a corresponding method:

- **agent** - Information about the agent/client reporting the event
- **client** - Client side of a network connection
- **cloud** - Cloud/infrastructure provider information
- **container** - Container runtime environment
- **destination** - Destination side of a network connection
- **ecs** - ECS version information
- **error** - Error details
- **event** - Event circumstances and context
- **file** - File information
- **geo** - Geolocation data
- **group** - User group information
- **host** - Host machine information
- **http_request** - HTTP request details
- **http_response** - HTTP response details
- **log** - Log file/subsystem metadata
- **network** - Network communication details
- **observer** - Observing entity (firewall, proxy, etc.)
- **organization** - Organization information
- **os** - Operating system information
- **process** - Process information
- **related** - Related entities
- **server** - Server side of a network connection
- **service** - Service generating events
- **source** - Source side of a network connection
- **url** - URL information
- **user** - User information
- **user_agent** - User agent (browser/app) information

For detailed field documentation, see the [ECS Field Reference](https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html).

## Type Hints and IDE Support

This library includes comprehensive type hints for better IDE autocomplete and static type checking:

```python
from kubi_ecs_logger import Logger, Severity

logger: Logger = Logger()
logger.severity_output_level = Severity.WARNING  # Type checked
logger.event(action="test")  # Parameters have type hints
```

## Exception Handling

The library uses proper exceptions instead of assertions, making it safe for production use with Python optimization (`python -O`):

```python
from kubi_ecs_logger import Logger, InvalidTypeError, InvalidSeverityError, Severity

logger = Logger()

try:
    logger.dev = "not a bool"  # Wrong type
except InvalidTypeError as e:
    print(f"Type error: {e}")

try:
    Severity.from_str("invalid")  # Invalid severity
except InvalidSeverityError as e:
    print(f"Severity error: {e}")
```

All library exceptions inherit from `LoggerError`, allowing you to catch any library-specific error:

```python
from kubi_ecs_logger.exceptions import LoggerError

try:
    # Your logging code
    pass
except LoggerError:
    # Handle any kubi_ecs_logger error
    pass
```

## Dependencies
| name        | version |
|-------------|---------|
| marshmallow | ~3.26.2 |

## Development

To run tests:

```bash
pip install -e .[dev]
pytest tests/
```
