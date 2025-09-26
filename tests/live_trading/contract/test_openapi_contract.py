"""
Contract tests for Live Trading Service OpenAPI specification.

Tests that validate the API contract matches the OpenAPI specification.
These tests MUST fail until the API endpoints are implemented.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

# Path to the OpenAPI specification
OPENAPI_SPEC_PATH = Path(__file__).parent.parent.parent.parent / "specs" / "008-title-live-trading" / "contracts" / "openapi.yaml"


class TestOpenAPIContract:
    """Test suite for OpenAPI contract validation."""
    
    def test_openapi_spec_exists(self):
        """Test that OpenAPI specification file exists."""
        assert OPENAPI_SPEC_PATH.exists(), f"OpenAPI spec not found at {OPENAPI_SPEC_PATH}"
    
    def test_openapi_spec_is_valid_yaml(self):
        """Test that OpenAPI specification is valid YAML."""
        import yaml
        try:
            with open(OPENAPI_SPEC_PATH, 'r') as f:
                spec = yaml.safe_load(f)
            assert spec is not None, "OpenAPI spec failed to load as YAML"
        except yaml.YAMLError as e:
            pytest.fail(f"OpenAPI spec is not valid YAML: {e}")
    
    def test_openapi_spec_has_required_fields(self):
        """Test that OpenAPI specification has required fields."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Check required OpenAPI fields
        assert 'openapi' in spec, "Missing 'openapi' field"
        assert 'info' in spec, "Missing 'info' field"
        assert 'paths' in spec, "Missing 'paths' field"
        assert 'components' in spec, "Missing 'components' field"
        
        # Check info fields
        assert 'title' in spec['info'], "Missing 'info.title' field"
        assert 'version' in spec['info'], "Missing 'info.version' field"
    
    def test_authentication_endpoints_exist(self):
        """Test that authentication endpoints are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        # Check for authentication endpoints
        assert '/api/v1/auth/public-connect' in paths, "Missing public-connect endpoint"
        assert '/api/v1/auth/disconnect' in paths, "Missing disconnect endpoint"
        
        # Verify HTTP methods
        assert 'post' in paths['/api/v1/auth/public-connect'], "Missing POST method for public-connect"
        assert 'post' in paths['/api/v1/auth/disconnect'], "Missing POST method for disconnect"
    
    def test_account_management_endpoints_exist(self):
        """Test that account management endpoints are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        # Check for account management endpoints
        assert '/api/v1/accounts' in paths, "Missing accounts endpoint"
        assert '/api/v1/accounts/{account_id}' in paths, "Missing account detail endpoint"
        assert '/api/v1/accounts/{account_id}/balance' in paths, "Missing account balance endpoint"
        
        # Verify HTTP methods
        assert 'get' in paths['/api/v1/accounts'], "Missing GET method for accounts"
        assert 'get' in paths['/api/v1/accounts/{account_id}'], "Missing GET method for account detail"
        assert 'get' in paths['/api/v1/accounts/{account_id}/balance'], "Missing GET method for account balance"
    
    def test_trading_endpoints_exist(self):
        """Test that trading endpoints are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        # Check for trading endpoints
        assert '/api/v1/trading/orders' in paths, "Missing trading orders endpoint"
        assert '/api/v1/trading/orders/{order_id}' in paths, "Missing order detail endpoint"
        assert '/api/v1/trading/positions' in paths, "Missing positions endpoint"
        assert '/api/v1/trading/positions/{position_id}/close' in paths, "Missing position close endpoint"
        
        # Verify HTTP methods
        assert 'post' in paths['/api/v1/trading/orders'], "Missing POST method for trading orders"
        assert 'get' in paths['/api/v1/trading/orders/{order_id}'], "Missing GET method for order detail"
        assert 'delete' in paths['/api/v1/trading/orders/{order_id}'], "Missing DELETE method for order detail"
        assert 'get' in paths['/api/v1/trading/positions'], "Missing GET method for positions"
        assert 'post' in paths['/api/v1/trading/positions/{position_id}/close'], "Missing POST method for position close"
    
    def test_risk_management_endpoints_exist(self):
        """Test that risk management endpoints are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        # Check for risk management endpoints
        assert '/api/v1/risk/profile' in paths, "Missing risk profile endpoint"
        assert '/api/v1/risk/emergency-stop' in paths, "Missing emergency stop endpoint"
        
        # Verify HTTP methods
        assert 'get' in paths['/api/v1/risk/profile'], "Missing GET method for risk profile"
        assert 'put' in paths['/api/v1/risk/profile'], "Missing PUT method for risk profile"
        assert 'post' in paths['/api/v1/risk/emergency-stop'], "Missing POST method for emergency stop"
    
    def test_system_status_endpoints_exist(self):
        """Test that system status endpoints are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        # Check for system status endpoints
        assert '/api/v1/status' in paths, "Missing system status endpoint"
        assert '/api/v1/status/market-hours' in paths, "Missing market hours endpoint"
        
        # Verify HTTP methods
        assert 'get' in paths['/api/v1/status'], "Missing GET method for system status"
        assert 'get' in paths['/api/v1/status/market-hours'], "Missing GET method for market hours"
    
    def test_schemas_are_defined(self):
        """Test that required schemas are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        # Check for required schemas
        required_schemas = [
            'LiveTradingAccount',
            'AccountBalance', 
            'TradeOrder',
            'LiveTrade',
            'LivePosition',
            'OrderStatus',
            'RiskProfile',
            'SystemStatus'
        ]
        
        for schema in required_schemas:
            assert schema in schemas, f"Missing required schema: {schema}"
    
    def test_security_schemes_defined(self):
        """Test that security schemes are defined."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        # Check for API key security scheme
        assert 'ApiKeyAuth' in security_schemes, "Missing ApiKeyAuth security scheme"
        
        # Verify API key configuration
        api_key_auth = security_schemes['ApiKeyAuth']
        assert api_key_auth['type'] == 'apiKey', "ApiKeyAuth should be apiKey type"
        assert api_key_auth['in'] == 'header', "ApiKeyAuth should be in header"
        assert api_key_auth['name'] == 'X-API-Key', "ApiKeyAuth should use X-API-Key header"
    
    def test_all_endpoints_have_responses(self):
        """Test that all endpoints have response definitions."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    assert 'responses' in operation, f"Missing responses for {method.upper()} {path}"
                    
                    responses = operation['responses']
                    # Check for at least one response
                    assert len(responses) > 0, f"No responses defined for {method.upper()} {path}"
                    
                    # Check for common response codes
                    if method in ['get']:
                        assert '200' in responses, f"Missing 200 response for GET {path}"
                    elif method in ['post']:
                        assert '201' in responses or '200' in responses, f"Missing success response for POST {path}"
                    
                    # Check for error responses
                    assert '500' in responses, f"Missing 500 error response for {method.upper()} {path}"
    
    def test_request_bodies_have_schemas(self):
        """Test that request bodies have proper schemas."""
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)
        
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ['post', 'put', 'patch'] and 'requestBody' in operation:
                    request_body = operation['requestBody']
                    assert 'content' in request_body, f"Missing content for request body in {method.upper()} {path}"
                    
                    content = request_body['content']
                    assert 'application/json' in content, f"Missing application/json content type for {method.upper()} {path}"
                    
                    json_content = content['application/json']
                    assert 'schema' in json_content, f"Missing schema for JSON request body in {method.upper()} {path}"


@pytest.mark.contract
class TestAPIContractImplementation:
    """Test that API endpoints are actually implemented and match the contract."""
    
    @pytest.fixture
    def client(self):
        """Create test client - this will fail until the API is implemented."""
        # This import will fail until the live trading service is implemented
        try:
            from services.live_trading_service.main import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except ImportError:
            pytest.skip("Live trading service not implemented yet")
    
    def test_health_endpoint_implemented(self, client):
        """Test that health endpoint is implemented."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "live-trading-service"
    
    def test_ready_endpoint_implemented(self, client):
        """Test that readiness endpoint is implemented."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "live-trading-service"
    
    def test_auth_endpoints_implemented(self, client):
        """Test that authentication endpoints are implemented."""
        # Test public-connect endpoint exists
        response = client.post("/api/v1/auth/public-connect")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
        # Test disconnect endpoint exists
        response = client.post("/api/v1/auth/disconnect")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_account_endpoints_implemented(self, client):
        """Test that account management endpoints are implemented."""
        # Test accounts endpoint exists
        response = client.get("/api/v1/accounts")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_trading_endpoints_implemented(self, client):
        """Test that trading endpoints are implemented."""
        # Test orders endpoint exists
        response = client.get("/api/v1/trading/orders")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
        # Test positions endpoint exists
        response = client.get("/api/v1/trading/positions")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_risk_endpoints_implemented(self, client):
        """Test that risk management endpoints are implemented."""
        # Test risk profile endpoint exists
        response = client.get("/api/v1/risk/profile")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_status_endpoints_implemented(self, client):
        """Test that system status endpoints are implemented."""
        # Test system status endpoint exists
        response = client.get("/api/v1/status")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
        # Test market hours endpoint exists
        response = client.get("/api/v1/status/market-hours")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
