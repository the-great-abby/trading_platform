from datetime import datetime
from src.core.types import TradeSignal

# Test the timestamp comparison logic
signal1 = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
signal_id = f"{signal1.symbol}_{signal1.timestamp}"

print(f"Signal ID: {signal_id}")
print(f"Signal timestamp: {signal1.timestamp}")
print(f"Signal timestamp strftime (old): {signal1.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Signal timestamp strftime (new): {signal1.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}")

# Test the comparison
timestamp_str_old = signal1.timestamp.strftime('%Y-%m-%d %H:%M:%S')
timestamp_str_new = signal1.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
parts = signal_id.split('_')
print(f"Parts: {parts}")
print(f"Symbol match: {signal1.symbol == parts[0]}")
print(f"Timestamp match (old): {timestamp_str_old == parts[1]}")
print(f"Timestamp match (new): {timestamp_str_new == parts[1]}") 