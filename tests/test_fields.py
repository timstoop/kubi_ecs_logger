"""Tests for field objects."""

from kubi_ecs_logger.models.fields import (
    Agent, Client, Cloud, Container, Destination, ECS, Error, Event,
    File, Geo, Group, Host, HttpRequest, HttpResponse, LogLine,
    Network, Observer, Organization, OS, Process, Related, Server,
    Service, Source, Url, User, UserAgent
)
from kubi_ecs_logger.models.fields import FieldSet


class TestFieldSetBase:
    """Test FieldSet base class."""

    def test_field_set_with_kwargs(self):
        """FieldSet accepts arbitrary kwargs."""
        fs = FieldSet(custom_field="value", another=42)
        assert fs.custom_field == "value"
        assert fs.another == 42

    def test_field_set_does_not_override_existing(self):
        """FieldSet does not override existing attributes."""
        class CustomFieldSet(FieldSet):
            def __init__(self, **kwargs):
                self.existing = "original"
                super().__init__(**kwargs)

        fs = CustomFieldSet(existing="new")
        assert fs.existing == "original"


class TestEventField:
    """Test Event field."""

    def test_event_with_action(self):
        """Event accepts action parameter."""
        event = Event(action="user-login")
        assert event.action == "user-login"

    def test_event_with_multiple_fields(self):
        """Event accepts multiple parameters."""
        event = Event(action="login", outcome="success", category="authentication")
        assert event.action == "login"
        assert event.outcome == "success"
        assert event.category == "authentication"

    def test_event_with_kwargs(self):
        """Event accepts custom fields via kwargs."""
        event = Event(action="test", custom="value")
        assert event.custom == "value"


class TestUserField:
    """Test User field."""

    def test_user_with_name(self):
        """User accepts name parameter."""
        user = User(name="alice")
        assert user.name == "alice"

    def test_user_with_multiple_fields(self):
        """User accepts multiple parameters."""
        user = User(name="alice", email="alice@example.com", id="123")
        assert user.name == "alice"
        assert user.email == "alice@example.com"
        assert user.id == "123"


class TestErrorField:
    """Test Error field."""

    def test_error_with_message(self):
        """Error accepts message parameter."""
        error = Error(message="Connection timeout")
        assert error.message == "Connection timeout"

    def test_error_with_code(self):
        """Error accepts code parameter."""
        error = Error(code="ERR_TIMEOUT", message="Timeout occurred")
        assert error.code == "ERR_TIMEOUT"


class TestHostField:
    """Test Host field."""

    def test_host_with_hostname(self):
        """Host accepts hostname parameter."""
        host = Host(hostname="web01.example.com")
        assert host.hostname == "web01.example.com"

    def test_host_with_multiple_fields(self):
        """Host accepts multiple parameters."""
        host = Host(hostname="web01", ip="10.0.0.1", name="web01")
        assert host.hostname == "web01"
        assert host.ip == "10.0.0.1"


class TestLogLineField:
    """Test LogLine field."""

    def test_logline_with_string_level(self):
        """LogLine accepts string level."""
        from kubi_ecs_logger import Severity
        logline = LogLine(level="INFO")
        assert logline.level == "INFO"

    def test_logline_with_severity_level(self):
        """LogLine accepts Severity enum level."""
        from kubi_ecs_logger import Severity
        logline = LogLine(level=Severity.WARNING)
        assert logline.level == "WARNING"

    def test_logline_with_original(self):
        """LogLine accepts original parameter."""
        logline = LogLine(original="[2024-01-01] INFO: Test message")
        assert logline.original == "[2024-01-01] INFO: Test message"


class TestNetworkFields:
    """Test network-related fields (client, server, source, destination)."""

    def test_client_with_ip(self):
        """Client accepts ip parameter."""
        client = Client(ip="192.168.1.100")
        assert client.ip == "192.168.1.100"

    def test_server_with_port(self):
        """Server accepts port parameter."""
        server = Server(ip="10.0.0.1", port=443)
        assert server.port == 443

    def test_source_with_address(self):
        """Source accepts address parameter."""
        source = Source(address="client.example.com")
        assert source.address == "client.example.com"

    def test_destination_with_domain(self):
        """Destination accepts domain parameter."""
        dest = Destination(domain="api.example.com")
        assert dest.domain == "api.example.com"


class TestHttpFields:
    """Test HTTP-related fields."""

    def test_http_request_with_method(self):
        """HttpRequest accepts method parameter."""
        request = HttpRequest(method="GET", referrer="https://example.com")
        assert request.method == "GET"

    def test_http_response_with_status_code(self):
        """HttpResponse accepts status_code parameter."""
        response = HttpResponse(status_code="200")
        assert response.status_code == "200"


class TestCloudField:
    """Test Cloud field."""

    def test_cloud_with_provider(self):
        """Cloud accepts provider parameter."""
        cloud = Cloud(provider="aws", region="us-east-1")
        assert cloud.provider == "aws"
        assert cloud.region == "us-east-1"


class TestProcessField:
    """Test Process field."""

    def test_process_with_pid(self):
        """Process accepts pid parameter."""
        process = Process(pid=1234, name="nginx")
        assert process.pid == 1234
        assert process.name == "nginx"

    def test_process_with_args(self):
        """Process accepts args list."""
        process = Process(args=["nginx", "-c", "/etc/nginx/nginx.conf"])
        assert len(process.args) == 3


class TestAllFieldsInstantiate:
    """Test that all field classes can be instantiated."""

    def test_all_fields_instantiate(self):
        """All field classes can be instantiated without errors."""
        fields = [
            Agent(), Client(), Cloud(), Container(), Destination(), ECS(),
            Error(), Event(), File(), Geo(), Group(), Host(), HttpRequest(),
            HttpResponse(), LogLine(), Network(), Observer(), Organization(),
            OS(), Process(), Related(), Server(), Service(), Source(),
            Url(), User(), UserAgent()
        ]

        for field in fields:
            assert isinstance(field, FieldSet)
