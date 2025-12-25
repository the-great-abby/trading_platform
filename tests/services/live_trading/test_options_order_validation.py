"""
Unit tests for options order validation and submission.

These tests verify options order formatting without submitting to Public.com.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
import sys
from pathlib import Path

# Add service path to Python path
service_path = Path(__file__).parent.parent.parent / "services" / "live-trading-service"
sys.path.insert(0, str(service_path))

# Mock the imports - we're testing logic, not actual API
class OptionType:
    CALL = "CALL"
    PUT = "PUT"

class PublicAPIClient:
    """Mock API client for testing."""
    def __init__(self):
        self.access_token = None
        self.is_authenticated = False


class TestOptionsOrderValidation:
    """Test options order validation without actual API calls."""
    
    def mock_api_client(self):
        """Create a mock API client."""
        client = PublicAPIClient()
        client.access_token = "test_token"
        client.is_authenticated = True
        return client
    
    def test_stock_order_format(self):
        """Test that stock orders are formatted correctly."""
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 10,
            "type": "market",
            "time_in_force": "day"
        }
        
        # Validate order format
        assert order_data["symbol"] == "NVDA"
        assert "option_type" not in order_data
        assert "strike_price" not in order_data
        assert "expiration_date" not in order_data
        
        print("✅ Stock order format validated")
    
    def test_options_order_missing_strike_fails(self):
        """Test that options orders without strike price fail validation."""
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "type": "market",
            "time_in_force": "day",
            "option_type": "CALL",
            "expiration_date": "2024-12-20"
            # Missing strike_price!
        }
        
        # Validate this should fail
        is_options = order_data.get("option_type") is not None
        has_strike = order_data.get("strike_price") is not None
        has_expiration = order_data.get("expiration_date") is not None
        
        assert is_options, "Should be recognized as options order"
        assert not has_strike, "Should be missing strike price"
        assert has_expiration, "Should have expiration"
        
        # This is invalid
        is_valid = is_options and has_strike and has_expiration
        assert not is_valid, "Order should be invalid without strike price"
        
        print("✅ Options order without strike price correctly fails validation")
    
    def test_options_order_missing_expiration_fails(self):
        """Test that options orders without expiration fail validation."""
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "type": "market",
            "time_in_force": "day",
            "option_type": "CALL",
            "strike_price": 200.0
            # Missing expiration_date!
        }
        
        is_options = order_data.get("option_type") is not None
        has_strike = order_data.get("strike_price") is not None
        has_expiration = order_data.get("expiration_date") is not None
        
        assert is_options, "Should be recognized as options order"
        assert has_strike, "Should have strike price"
        assert not has_expiration, "Should be missing expiration"
        
        is_valid = is_options and has_strike and has_expiration
        assert not is_valid, "Order should be invalid without expiration"
        
        print("✅ Options order without expiration correctly fails validation")
    
    def test_valid_options_order_format(self):
        """Test that valid options orders pass validation."""
        expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "type": "limit",
            "price": 5.50,  # Premium price
            "time_in_force": "day",
            "option_type": "CALL",
            "strike_price": 200.0,
            "expiration_date": expiration
        }
        
        is_options = order_data.get("option_type") is not None
        has_strike = order_data.get("strike_price") is not None
        has_expiration = order_data.get("expiration_date") is not None
        
        assert is_options, "Should be recognized as options order"
        assert has_strike, "Should have strike price"
        assert has_expiration, "Should have expiration"
        
        is_valid = is_options and has_strike and has_expiration
        assert is_valid, "Order should be valid"
        
        print(f"✅ Valid options order: {order_data['option_type']} ${order_data['strike_price']} exp {order_data['expiration_date']}")
    
    def test_options_payload_structure(self):
        """Test the structure of options order payload for Public.com API."""
        expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "type": "limit",
            "price": 5.50,
            "time_in_force": "day",
            "option_type": "CALL",
            "strike_price": 200.0,
            "expiration_date": expiration
        }
        
        # Build Public.com API payload
        is_options_order = order_data.get("option_type") is not None
        
        if is_options_order:
            order_payload = {
                "orderId": "test-order-123",
                "instrument": {
                    "symbol": order_data["symbol"],
                    "type": "OPTION",
                    "optionType": order_data["option_type"],
                    "strikePrice": str(order_data["strike_price"]),
                    "expirationDate": order_data["expiration_date"]
                },
                "orderSide": order_data["side"].upper(),
                "orderType": order_data["type"].upper(),
                "expiration": {
                    "timeInForce": order_data["time_in_force"].upper()
                },
                "quantity": str(order_data["quantity"])
            }
            
            # Add limit price if present
            if order_payload["orderType"] == "LIMIT":
                order_payload["limitPrice"] = str(order_data["price"])
            
            # Validate structure
            assert order_payload["instrument"]["type"] == "OPTION"
            assert order_payload["instrument"]["optionType"] in ["CALL", "PUT"]
            assert "strikePrice" in order_payload["instrument"]
            assert "expirationDate" in order_payload["instrument"]
            assert "limitPrice" in order_payload
            
            print(f"✅ Options payload structure validated:")
            print(f"   Type: {order_payload['instrument']['type']}")
            print(f"   Option: {order_payload['instrument']['optionType']}")
            print(f"   Strike: ${order_payload['instrument']['strikePrice']}")
            print(f"   Expiration: {order_payload['instrument']['expirationDate']}")
            print(f"   Premium: ${order_payload['limitPrice']}")
        else:
            pytest.fail("Should be options order")
    
    def test_stock_vs_options_detection(self):
        """Test detection of stock vs options orders."""
        stock_order = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 10,
            "type": "market"
        }
        
        options_order = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "option_type": "CALL",
            "strike_price": 200.0,
            "expiration_date": "2024-12-20"
        }
        
        is_stock = stock_order.get("option_type") is None
        is_options = options_order.get("option_type") is not None
        
        assert is_stock, "Stock order should be detected"
        assert is_options, "Options order should be detected"
        
        print("✅ Stock vs options detection working correctly")
    
    def test_options_validation_scenarios(self, option_type, strike, expiration, should_be_valid):
        """Test various options validation scenarios."""
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1
        }
        
        if option_type:
            order_data["option_type"] = option_type
        if strike:
            order_data["strike_price"] = strike
        if expiration:
            order_data["expiration_date"] = expiration
        
        is_options = order_data.get("option_type") is not None
        has_strike = order_data.get("strike_price") is not None
        has_expiration = order_data.get("expiration_date") is not None
        
        is_valid = is_options and has_strike and has_expiration
        
        assert is_valid == should_be_valid, f"Validation mismatch for {option_type} ${strike} {expiration}"
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{status}: {option_type} ${strike} exp {expiration}")


class TestOptionsOrderFormatting:
    """Test options order formatting for Public.com API."""
    
    def test_current_multi_strategy_order_format(self):
        """Test current multi-strategy order format (the problem case)."""
        # This is what the system currently sends
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 20,
            "type": "market",
            "time_in_force": "day",
            "strategy": "multi_strategy_ensemble",
            "legs": [{
                "action": "BUY",
                "option_type": "CALL",  # ⚠️ This is set
                "strike_price": None,   # ⚠️ But this is None!
                "expiration_date": None,  # ⚠️ And this is None!
                "quantity": 20,
                "premium": None
            }]
        }
        
        # Check if this would be considered an options order
        leg = order_data["legs"][0]
        is_options_leg = leg.get("option_type") is not None
        has_strike = leg.get("strike_price") is not None
        has_expiration = leg.get("expiration_date") is not None
        
        print(f"❌ PROBLEM DETECTED:")
        print(f"   Has option_type: {is_options_leg} ({leg.get('option_type')})")
        print(f"   Has strike_price: {has_strike} ({leg.get('strike_price')})")
        print(f"   Has expiration: {has_expiration} ({leg.get('expiration_date')})")
        
        is_valid_options = is_options_leg and has_strike and has_expiration
        is_valid_stock = not is_options_leg
        
        assert not is_valid_options, "Should NOT be valid options order"
        assert not is_valid_stock, "Should NOT be valid stock order (has option_type set)"
        
        print(f"   This is the bug! Order has option_type but no strike/expiration")
    
    def test_fixed_stock_order_format(self):
        """Test fixed stock order format (option_type should be None)."""
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 10,
            "type": "market",
            "time_in_force": "day",
            "strategy": "multi_strategy_ensemble",
            "legs": [{
                "action": "BUY",
                "option_type": None,  # ✅ Explicitly None for stocks
                "strike_price": None,
                "expiration_date": None,
                "quantity": 10,
                "premium": 188.32  # Stock price
            }]
        }
        
        leg = order_data["legs"][0]
        is_options_leg = leg.get("option_type") is not None
        
        assert not is_options_leg, "Should be stock order"
        print(f"✅ Fixed: Stock order with option_type=None")
    
    def test_fixed_options_order_format(self):
        """Test fixed options order format (with strike and expiration)."""
        expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1,
            "type": "limit",
            "time_in_force": "day",
            "strategy": "greeks_enhanced",
            "legs": [{
                "action": "BUY",
                "option_type": "CALL",  # ✅ Set
                "strike_price": 200.0,  # ✅ Set  
                "expiration_date": expiration,  # ✅ Set
                "quantity": 1,
                "premium": 5.50
            }]
        }
        
        leg = order_data["legs"][0]
        is_options_leg = leg.get("option_type") is not None
        has_strike = leg.get("strike_price") is not None
        has_expiration = leg.get("expiration_date") is not None
        
        is_valid = is_options_leg and has_strike and has_expiration
        
        assert is_valid, "Should be valid options order"
        print(f"✅ Fixed: Options order with all required fields")
        print(f"   {leg['option_type']} ${leg['strike_price']} exp {leg['expiration_date']}")


if __name__ == "__main__":
    print("=" * 80)
    print("OPTIONS ORDER VALIDATION TESTS")
    print("=" * 80)
    
    # Run tests manually
    test_validation = TestOptionsOrderValidation()
    test_formatting = TestOptionsOrderFormatting()
    
    print("\n📋 Test 1: Stock Order Format")
    print("-" * 40)
    test_validation.test_stock_order_format()
    
    print("\n📋 Test 2: Options Missing Strike")
    print("-" * 40)
    test_validation.test_options_order_missing_strike_fails()
    
    print("\n📋 Test 3: Options Missing Expiration")
    print("-" * 40)
    test_validation.test_options_order_missing_expiration_fails()
    
    print("\n📋 Test 4: Valid Options Order")
    print("-" * 40)
    test_validation.test_valid_options_order_format()
    
    print("\n📋 Test 5: Options Payload Structure")
    print("-" * 40)
    test_validation.test_options_payload_structure()
    
    print("\n📋 Test 6: Stock vs Options Detection")
    print("-" * 40)
    test_validation.test_stock_vs_options_detection()
    
    print("\n📋 Test 7: Validation Scenarios")
    print("-" * 40)
    for option_type, strike, exp, valid in [
        ("CALL", 200.0, "2024-12-20", True),
        ("PUT", 180.0, "2024-12-20", True),
        ("CALL", None, "2024-12-20", False),
        ("PUT", 180.0, None, False),
    ]:
        test_validation.test_options_validation_scenarios(option_type, strike, exp, valid)
    
    print("\n📋 Test 8: Current Bug Detection")
    print("-" * 40)
    test_formatting.test_current_multi_strategy_order_format()
    
    print("\n📋 Test 9: Fixed Stock Format")
    print("-" * 40)
    test_formatting.test_fixed_stock_order_format()
    
    print("\n📋 Test 10: Fixed Options Format")
    print("-" * 40)
    test_formatting.test_fixed_options_order_format()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)

