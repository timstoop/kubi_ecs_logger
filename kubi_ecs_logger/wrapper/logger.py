"""Logger wrapper for ECS-based JSON logging.

This module provides the Logger singleton class, which offers a fluent
interface for building structured log entries conforming to the
Elasticsearch Common Schema (ECS).
"""
import sys
from typing import Optional, List, Union, Dict, Any
from datetime import datetime

from kubi_ecs_logger.models.fields import *

from kubi_ecs_logger.utils import pprint
from kubi_ecs_logger.models import Base, BaseSchema, Severity
from kubi_ecs_logger.exceptions import InvalidTypeError


class Logger:
    """Singleton logger for creating ECS-compliant JSON log entries.

    This class implements a fluent interface for building structured logs.
    It maintains state between method calls and resets after each log output.

    Singleton Pattern:
        Only one Logger instance exists per application. Each call to Logger()
        returns the same instance and resets its internal Base object.

    Fluent Interface:
        All methods except out() return self, enabling method chaining:
        Logger().event(action="login").user(name="alice").out(Severity.INFO)

    State Management:
        - Internal Base object holds current log entry data
        - Reset occurs on initialization and after calling out()
        - Configuration (dev, severity_output_level, defaults) persists

    First Wins Policy:
        Only the first instance of each field type is accepted per log entry.
        Subsequent calls with the same field type are ignored.

    Configuration:
        - dev: Enable pretty-printed colored output for development
        - severity_output_level: Minimum severity threshold for output
        - defaults: Default field values merged into matching field types

    Example:
        >>> logger = Logger()
        >>> logger.dev = True
        >>> logger.severity_output_level = Severity.WARNING
        >>> logger.event(action="login").user(name="alice").out(Severity.INFO)
        # No output (INFO < WARNING threshold)
        >>> logger.event(action="failed_login").out(Severity.ERROR)
        # Output (ERROR >= WARNING threshold)
    """
    __instance: 'Logger' = None
    _defaults: dict = {}
    _base: Base = None
    _dev: bool = False
    _severity_output_level: Severity = Severity.INFO

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Logger, cls).__new__(cls)
        cls.__instance.base()
        return cls.__instance

    @property
    def dev(self) -> bool:
        """Get development mode status.

        Returns:
            True if development mode is enabled, False otherwise.
        """
        return self._dev

    @dev.setter
    def dev(self, value: bool) -> None:
        """Set development mode.

        When enabled, outputs colored, pretty-printed JSON instead of
        compact single-line JSON.

        Args:
            value: True to enable development mode, False to disable.

        Raises:
            InvalidTypeError: If value is not a boolean.

        Example:
            >>> Logger().dev = True
        """
        if not isinstance(value, bool):
            raise InvalidTypeError(f"dev must be a bool, got {type(value).__name__}")
        self._dev = value

    @property
    def severity_output_level(self) -> Severity:
        """Get the minimum severity threshold for log output.

        Returns:
            The current severity threshold.
        """
        return self._severity_output_level

    @severity_output_level.setter
    def severity_output_level(self, value: Severity) -> None:
        """Set the minimum severity threshold for log output.

        Only logs with severity >= this threshold will be output.

        Args:
            value: The minimum severity level.

        Raises:
            InvalidTypeError: If value is not a Severity enum member.

        Example:
            >>> Logger().severity_output_level = Severity.WARNING
        """
        if not isinstance(value, Severity):
            raise InvalidTypeError(f"severity_output_level must be a Severity, got {type(value).__name__}")
        self._severity_output_level = value

    @property
    def defaults(self) -> Dict[str, Dict[str, Any]]:
        """Get the default field values.

        Returns:
            Dictionary mapping field type names to default values.
        """
        return self._defaults

    @defaults.setter
    def defaults(self, value: Dict[str, Dict[str, Any]]) -> None:
        """Set default field values.

        Default values are merged into matching field types when they are added.
        Field names should be lowercase (e.g., "event", "user").

        Args:
            value: Dictionary mapping field type names to default values.

        Raises:
            InvalidTypeError: If value is not a dictionary.

        Example:
            >>> Logger().defaults = {"event": {"dataset": "myapp"}}
            >>> Logger().event(action="login").out()
            # Output includes event.dataset="myapp"
        """
        if not isinstance(value, dict):
            raise InvalidTypeError(f"defaults must be a dict, got {type(value).__name__}")
        self._defaults = value

    def base(self, date: Optional[datetime] = None, labels: Optional[Dict[str, Any]] = None,
             message: Optional[str] = None, tags: Optional[List[str]] = None, **kwargs) -> 'Logger':
        """Set or reset the base log entry fields.

        This method initializes or resets the internal Base object with common
        log fields. It is called automatically when Logger() is instantiated
        and after out() is called.

        Args:
            date: Timestamp for the log entry (defaults to now)
            labels: Dictionary of custom key-value metadata
            message: The log message text
            tags: List of string tags for categorization
            **kwargs: Additional custom fields

        Returns:
            Logger instance for method chaining.

        Example:
            >>> Logger().base(message="Application started", tags=["startup"])
        """
        # Merge with defaults (defaults don't override kwargs)
        defaults = self._get_defaults_for(Base)
        if defaults:
            for key, value in defaults.items():
                if key not in kwargs:
                    kwargs[key] = value

        self._base = Base(date=date, labels=labels, message=message, tags=tags, **kwargs)
        return self

    def agent(self, ephemeral_id: Optional[str] = None, id: Optional[str] = None, name: Optional[str] = None,
              type: Optional[str] = None, version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS agent fields.

        Information about the agent/client reporting the event.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-agent.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if ephemeral_id is not None:
            params['ephemeral_id'] = ephemeral_id
        if id is not None:
            params['id'] = id
        if name is not None:
            params['name'] = name
        if type is not None:
            params['type'] = type
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Agent)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Agent(**params))
        return self

    def client(self, address: Optional[str] = None, bytes: Optional[int] = None, domain: Optional[str] = None, ip: Optional[str] = None,
               mac: Optional[str] = None, packets: Optional[int] = None, port: Optional[int] = None, **kwargs) -> 'Logger':
        """Add ECS client fields.

        Fields about the client (initiator) side of a network connection.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-client.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if address is not None:
            params['address'] = address
        if bytes is not None:
            params['bytes'] = bytes
        if domain is not None:
            params['domain'] = domain
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if packets is not None:
            params['packets'] = packets
        if port is not None:
            params['port'] = port

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Client)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Client(**params))
        return self

    def cloud(self, account_id: Optional[str] = None, availability_zone: Optional[str] = None, instance_id: Optional[str] = None,
              instance_name: Optional[str] = None, machine_type: Optional[str] = None, provider: Optional[str] = None,
              region: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS cloud fields.

        Fields related to cloud or infrastructure provider information.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-cloud.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if account_id is not None:
            params['account_id'] = account_id
        if availability_zone is not None:
            params['availability_zone'] = availability_zone
        if instance_id is not None:
            params['instance_id'] = instance_id
        if instance_name is not None:
            params['instance_name'] = instance_name
        if machine_type is not None:
            params['machine_type'] = machine_type
        if provider is not None:
            params['provider'] = provider
        if region is not None:
            params['region'] = region

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Cloud)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Cloud(**params))
        return self

    def container(self, id: Optional[str] = None, image_name: Optional[str] = None, image_tag: Optional[str] = None,
                  labels: dict = None, name: Optional[str] = None, runtime: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS container fields.

        Runtime environment information for containerized applications.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-container.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if id is not None:
            params['id'] = id
        if image_name is not None:
            params['image_name'] = image_name
        if image_tag is not None:
            params['image_tag'] = image_tag
        if labels is not None:
            params['labels'] = labels
        if name is not None:
            params['name'] = name
        if runtime is not None:
            params['runtime'] = runtime

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Container)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Container(**params))
        return self

    def destination(self, address: Optional[str] = None, bytes: Optional[int] = None, domain: Optional[str] = None, ip: Optional[str] = None,
                    mac: Optional[str] = None, packets: Optional[int] = None, port: Optional[int] = None, **kwargs) -> 'Logger':
        """Add ECS destination fields.

        Fields about the destination (responder) side of a network connection.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-destination.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if address is not None:
            params['address'] = address
        if bytes is not None:
            params['bytes'] = bytes
        if domain is not None:
            params['domain'] = domain
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if packets is not None:
            params['packets'] = packets
        if port is not None:
            params['port'] = port

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Destination)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Destination(**params))
        return self

    def ecs(self, version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS version information.

        Meta-information about the ECS version used.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-ecs.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(ECS)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(ECS(**params))
        return self

    def error(self, code: Optional[str] = None, id: Optional[str] = None,
              message: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS error fields to the log entry.

        The error fields capture details about errors that occurred during event processing.

        Args:
            code: Error code describing the error
            id: Unique identifier for the error
            message: Error message text
            **kwargs: Additional error fields (e.g., stack_trace, type)

        Returns:
            Logger instance for method chaining.

        Example:
            >>> Logger().error(code="ERR_AUTH_FAILED", message="Invalid credentials")

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-error.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if code is not None:
            params['code'] = code
        if id is not None:
            params['id'] = id
        if message is not None:
            params['message'] = message

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Error)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Error(**params))
        return self

    def event(self, action: Optional[str] = None, category: Optional[str] = None,
              created: Optional[datetime] = None, dataset: Optional[str] = None,
              risk_score: Optional[float] = None, severity: Optional[int] = None,
              **kwargs) -> 'Logger':
        """Add ECS event fields to the log entry.

        The event fields describe the circumstances of an observed event,
        such as actions taken, their outcomes, and contextual information.

        Args:
            action: The action captured by the event (e.g., "user-login", "file-delete")
            category: Event category (e.g., "authentication", "file")
            created: When the event was created
            dataset: Name of the dataset for event correlation
            risk_score: Risk score calculated for the event (0-100)
            severity: Numeric severity of the event
            **kwargs: Additional event fields (e.g., duration, outcome, type)

        Returns:
            Logger instance for method chaining.

        Example:
            >>> Logger().event(action="user-login", outcome="success", category="authentication")

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-event.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if action is not None:
            params['action'] = action
        if category is not None:
            params['category'] = category
        if created is not None:
            params['created'] = created
        if dataset is not None:
            params['dataset'] = dataset
        if risk_score is not None:
            params['risk_score'] = risk_score
        if severity is not None:
            params['severity'] = severity

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Event)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Event(**params))
        return self

    def file(self, ctime: Optional[datetime] = None, device: Optional[str] = None, extension: Optional[str] = None, gid: Optional[str] = None,
             group: Optional[str] = None, inode: Optional[str] = None, mode: Optional[str] = None, mtime: Optional[datetime] = None, owner: Optional[str] = None,
             path: Optional[str] = None, size: Optional[int] = None, target_path: Optional[str] = None, type: Optional[str] = None, uid: Optional[str] = None,
             **kwargs) -> 'Logger':
        """Add ECS file fields.

        Information about files involved in the event.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-file.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if ctime is not None:
            params['ctime'] = ctime
        if device is not None:
            params['device'] = device
        if extension is not None:
            params['extension'] = extension
        if gid is not None:
            params['gid'] = gid
        if group is not None:
            params['group'] = group
        if inode is not None:
            params['inode'] = inode
        if mode is not None:
            params['mode'] = mode
        if mtime is not None:
            params['mtime'] = mtime
        if owner is not None:
            params['owner'] = owner
        if path is not None:
            params['path'] = path
        if size is not None:
            params['size'] = size
        if target_path is not None:
            params['target_path'] = target_path
        if type is not None:
            params['type'] = type
        if uid is not None:
            params['uid'] = uid

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(File)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(File(**params))
        return self

    def geo(self, city_name: Optional[str] = None, continent_name: Optional[str] = None, country_iso_code: Optional[str] = None,
            country_name: Optional[str] = None, location: dict = None, name: Optional[str] = None, region_iso_code: Optional[str] = None,
            region_name: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS geo fields.

        Geolocation information for IP addresses.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-geo.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if city_name is not None:
            params['city_name'] = city_name
        if continent_name is not None:
            params['continent_name'] = continent_name
        if country_iso_code is not None:
            params['country_iso_code'] = country_iso_code
        if country_name is not None:
            params['country_name'] = country_name
        if location is not None:
            params['location'] = location
        if name is not None:
            params['name'] = name
        if region_iso_code is not None:
            params['region_iso_code'] = region_iso_code
        if region_name is not None:
            params['region_name'] = region_name

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Geo)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Geo(**params))
        return self

    def group(self, id: Optional[str] = None, name: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS group fields.

        Information about user groups.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-group.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if id is not None:
            params['id'] = id
        if name is not None:
            params['name'] = name

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Group)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Group(**params))
        return self

    def host(self, architecture: Optional[str] = None, hostname: Optional[str] = None, id: Optional[str] = None, ip: Optional[str] = None,
             mac: Optional[str] = None, name: Optional[str] = None, type: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS host fields.

        Information about the host machine.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-host.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if architecture is not None:
            params['architecture'] = architecture
        if hostname is not None:
            params['hostname'] = hostname
        if id is not None:
            params['id'] = id
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if name is not None:
            params['name'] = name
        if type is not None:
            params['type'] = type

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Host)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Host(**params))
        return self

    def http_request(self, body_bytes: Optional[int] = None, body_content: Optional[str] = None, bytes: Optional[int] = None, method: Optional[str] = None,
                     referrer: Optional[str] = None, version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS HTTP request fields.

        Details about HTTP requests.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-http.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if body_bytes is not None:
            params['body_bytes'] = body_bytes
        if body_content is not None:
            params['body_content'] = body_content
        if bytes is not None:
            params['bytes'] = bytes
        if method is not None:
            params['method'] = method
        if referrer is not None:
            params['referrer'] = referrer
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(HttpRequest)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(HttpRequest(**params))
        return self

    def http_response(self, body_bytes: Optional[int] = None, body_content: Optional[str] = None, bytes: Optional[int] = None,
                      status_code: Optional[str] = None, version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS HTTP response fields.

        Details about HTTP responses.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-http.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if body_bytes is not None:
            params['body_bytes'] = body_bytes
        if body_content is not None:
            params['body_content'] = body_content
        if bytes is not None:
            params['bytes'] = bytes
        if status_code is not None:
            params['status_code'] = status_code
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(HttpResponse)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(HttpResponse(**params))
        return self

    def log(self, level: Union[str, Severity] = None, original: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS log fields.

        Details about the log file or logging subsystem.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-log.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if level is not None:
            params['level'] = level
        if original is not None:
            params['original'] = original

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(LogLine)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(LogLine(**params))
        return self

    def network(self, application: Optional[str] = None, bytes: Optional[int] = None, community_id: Optional[str] = None, direction: Optional[str] = None,
                forwarded_ip: Optional[str] = None, iana_number: Optional[str] = None, name: Optional[str] = None, packets: Optional[int] = None,
                protocol: Optional[str] = None, transport: Optional[str] = None, type: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS network fields.

        Information about network communication.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-network.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if application is not None:
            params['application'] = application
        if bytes is not None:
            params['bytes'] = bytes
        if community_id is not None:
            params['community_id'] = community_id
        if direction is not None:
            params['direction'] = direction
        if forwarded_ip is not None:
            params['forwarded_ip'] = forwarded_ip
        if iana_number is not None:
            params['iana_number'] = iana_number
        if name is not None:
            params['name'] = name
        if packets is not None:
            params['packets'] = packets
        if protocol is not None:
            params['protocol'] = protocol
        if transport is not None:
            params['transport'] = transport
        if type is not None:
            params['type'] = type

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Network)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Network(**params))
        return self

    def observer(self, hostname: Optional[str] = None, ip: Optional[str] = None, mac: Optional[str] = None, serial_number: Optional[str] = None,
                 type: Optional[str] = None, vendor: Optional[str] = None, version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS observer fields.

        Information about the observing entity (e.g., firewall, proxy).

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-observer.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if hostname is not None:
            params['hostname'] = hostname
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if serial_number is not None:
            params['serial_number'] = serial_number
        if type is not None:
            params['type'] = type
        if vendor is not None:
            params['vendor'] = vendor
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Observer)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Observer(**params))
        return self

    def organization(self, id: Optional[str] = None, name: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS organization fields.

        Information about the organization.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-organization.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if id is not None:
            params['id'] = id
        if name is not None:
            params['name'] = name

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Organization)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Organization(**params))
        return self

    def os(self, family: Optional[str] = None, full: Optional[str] = None, kernel: Optional[str] = None, name: Optional[str] = None, platform: Optional[str] = None,
           version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS operating system fields.

        Information about the operating system.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-os.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if family is not None:
            params['family'] = family
        if full is not None:
            params['full'] = full
        if kernel is not None:
            params['kernel'] = kernel
        if name is not None:
            params['name'] = name
        if platform is not None:
            params['platform'] = platform
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(OS)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(OS(**params))
        return self

    def process(self, args: Optional[List[str]] = None, executable: Optional[str] = None, name: Optional[str] = None, pid: Optional[int] = None,
                ppid: Optional[int] = None, start: Optional[datetime] = None, thread_id: Optional[int] = None, title: Optional[str] = None,
                working_directory: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS process fields.

        Information about running processes.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-process.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if args is not None:
            params['args'] = args
        if executable is not None:
            params['executable'] = executable
        if name is not None:
            params['name'] = name
        if pid is not None:
            params['pid'] = pid
        if ppid is not None:
            params['ppid'] = ppid
        if start is not None:
            params['start'] = start
        if thread_id is not None:
            params['thread_id'] = thread_id
        if title is not None:
            params['title'] = title
        if working_directory is not None:
            params['working_directory'] = working_directory

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Process)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Process(**params))
        return self

    def related(self, ip: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS related fields.

        Fields for relating entities (IPs, users, hosts).

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-related.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if ip is not None:
            params['ip'] = ip

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Related)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Related(**params))
        return self

    def server(self, address: Optional[str] = None, bytes: Optional[int] = None, domain: Optional[str] = None, ip: Optional[str] = None, mac: Optional[str] = None,
               packets: Optional[int] = None, port: Optional[int] = None, **kwargs) -> 'Logger':
        """Add ECS server fields.

        Fields about the server (responder) side of a network connection.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-server.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if address is not None:
            params['address'] = address
        if bytes is not None:
            params['bytes'] = bytes
        if domain is not None:
            params['domain'] = domain
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if packets is not None:
            params['packets'] = packets
        if port is not None:
            params['port'] = port

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Server)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Server(**params))
        return self

    def service(self, ephemeral_id: Optional[str] = None, id: Optional[str] = None, name: Optional[str] = None, state: Optional[str] = None, type: Optional[str] = None,
                version: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS service fields.

        Information about the service generating events.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-service.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if ephemeral_id is not None:
            params['ephemeral_id'] = ephemeral_id
        if id is not None:
            params['id'] = id
        if name is not None:
            params['name'] = name
        if state is not None:
            params['state'] = state
        if type is not None:
            params['type'] = type
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Service)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Service(**params))
        return self

    def source(self, address: Optional[str] = None, bytes: Optional[int] = None, domain: Optional[str] = None, ip: Optional[str] = None, mac: Optional[str] = None,
               packets: Optional[int] = None, port: Optional[int] = None, **kwargs) -> 'Logger':
        """Add ECS source fields.

        Fields about the source (initiator) side of a network connection.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-source.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if address is not None:
            params['address'] = address
        if bytes is not None:
            params['bytes'] = bytes
        if domain is not None:
            params['domain'] = domain
        if ip is not None:
            params['ip'] = ip
        if mac is not None:
            params['mac'] = mac
        if packets is not None:
            params['packets'] = packets
        if port is not None:
            params['port'] = port

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Source)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Source(**params))
        return self

    def url(self, domain: Optional[str] = None, fragment: Optional[str] = None, full: Optional[str] = None, original: Optional[str] = None,
            password: Optional[str] = None, path: Optional[str] = None, port: Optional[int] = None, query: Optional[str] = None, scheme: Optional[str] = None,
            username: Optional[str] = None, **kwargs) -> 'Logger':
        """Add ECS URL fields.

        Information about parsed URLs.

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-url.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if domain is not None:
            params['domain'] = domain
        if fragment is not None:
            params['fragment'] = fragment
        if full is not None:
            params['full'] = full
        if original is not None:
            params['original'] = original
        if password is not None:
            params['password'] = password
        if path is not None:
            params['path'] = path
        if port is not None:
            params['port'] = port
        if query is not None:
            params['query'] = query
        if scheme is not None:
            params['scheme'] = scheme
        if username is not None:
            params['username'] = username

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(Url)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(Url(**params))
        return self

    def user(self, email: Optional[str] = None, full_name: Optional[str] = None,
             hash: Optional[str] = None, id: Optional[str] = None, name: Optional[str] = None,
             **kwargs) -> 'Logger':
        """Add ECS user fields to the log entry.

        The user fields describe information about the user relevant to the event.

        Args:
            email: User email address
            full_name: User's full name
            hash: Unique user hash for anonymization
            id: Unique user identifier
            name: Short username
            **kwargs: Additional user fields (e.g., domain, roles)

        Returns:
            Logger instance for method chaining.

        Example:
            >>> Logger().user(name="alice", email="alice@example.com", id="1234")

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-user.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if email is not None:
            params['email'] = email
        if full_name is not None:
            params['full_name'] = full_name
        if hash is not None:
            params['hash'] = hash
        if id is not None:
            params['id'] = id
        if name is not None:
            params['name'] = name

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(User)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(User(**params))
        return self

    def user_agent(self, device_name: Optional[str] = None, name: Optional[str] = None, original: Optional[str] = None, version: Optional[str] = None,
                   **kwargs) -> 'Logger':
        """Add ECS user agent fields.

        Information about the user agent (browser, app).

        Returns:
            Logger instance for method chaining.

        See:
            https://www.elastic.co/guide/en/ecs/current/ecs-user_agent.html
        """
        # Collect explicit parameters (only non-None values)
        params = {}
        if device_name is not None:
            params['device_name'] = device_name
        if name is not None:
            params['name'] = name
        if original is not None:
            params['original'] = original
        if version is not None:
            params['version'] = version

        # Merge with defaults (defaults don't override explicit params)
        defaults = self._get_defaults_for(UserAgent)
        if defaults:
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value

        # Merge with kwargs (kwargs override everything)
        params.update(kwargs)

        self._base.add_object(UserAgent(**params))
        return self

    def out(self, severity: Severity = Severity.DEBUG) -> None:
        """Output the current log entry and reset state.

        Serializes the current log entry to JSON and writes it to stdout,
        then resets the internal Base object for the next log entry.

        Only outputs if severity >= severity_output_level threshold.

        Args:
            severity: The severity level for this log entry. Defaults to DEBUG.

        Raises:
            InvalidTypeError: If severity is not a Severity enum member.

        Example:
            >>> Logger().event(action="login").out(Severity.INFO)
            {"@timestamp": "...", "event": {"action": "login"}, ...}
        """
        if not isinstance(severity, Severity):
            raise InvalidTypeError(f"severity must be a Severity, got {type(severity).__name__}")

        self._append_log_level(severity)

        if severity >= self._severity_output_level:
            self._output()

        # Reset for next log entry
        self.base()

    def _get_defaults_for(self, obj: type) -> Optional[Dict[str, Any]]:
        """Get default values for a field type.

        Args:
            obj: The field class to get defaults for.

        Returns:
            Dictionary of default values, or None if no defaults are configured.
        """
        name = obj.__name__.lower()
        if name in self._defaults:
            return self._defaults[name]
        return None

    def _output(self) -> None:
        """Output the current log entry to stdout.

        In development mode, outputs pretty-printed colored JSON.
        In production mode, outputs compact single-line JSON.
        """
        if self._dev:
            pprint(BaseSchema().dump(self._base), output_destination=sys.stdout)
        else:
            sys.stdout.write((BaseSchema().dumps(self._base))+'\n')

    def _append_log_level(self, severity_level: Severity) -> None:
        """Add or update the log.level field with the severity.

        If a LogLine field already exists with a level, it is not overwritten.
        Otherwise, creates a new LogLine field with the given severity.

        Args:
            severity_level: The severity level to set.
        """
        if hasattr(self._base, "logline"):
            if self._base.logline.level is None:
                self._base.logline.level = severity_level
            else:
                return

        self._base.add_object(LogLine(level=severity_level))
