-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(100) PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')),
    time_in_force VARCHAR(10) DEFAULT 'DAY' CHECK (time_in_force IN ('DAY', 'GTC', 'IOC', 'FOK')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'cancelled', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP,
    filled_price DECIMAL(10,2),
    filled_quantity INTEGER,
    notes TEXT
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Insert some sample orders for testing
INSERT INTO orders (order_id, symbol, side, quantity, price, order_type, status, created_at) VALUES
('order_1754329000_AAPL', 'AAPL', 'BUY', 100, 150.00, 'LIMIT', 'filled', NOW() - INTERVAL '1 hour'),
('order_1754329001_MSFT', 'MSFT', 'SELL', 50, 300.00, 'MARKET', 'pending', NOW() - INTERVAL '30 minutes'),
('order_1754329002_GOOGL', 'GOOGL', 'BUY', 25, 2800.00, 'LIMIT', 'pending', NOW() - INTERVAL '15 minutes')
ON CONFLICT (order_id) DO NOTHING; 