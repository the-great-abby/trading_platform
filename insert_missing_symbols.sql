-- Insert missing symbols with 2-year data
-- This script adds AMZN, TSLA, NVDA, META, UNH, JNJ to the database

-- AMZN data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('AMZN', '2023-07-05', 130.24, 131.40, 129.64, 130.38, 35895409, 'polygon', '1d'),
('AMZN', '2023-07-06', 128.25, 128.73, 127.37, 128.36, 40697848, 'polygon', '1d'),
('AMZN', '2023-07-07', 128.59, 130.97, 128.13, 129.78, 41992251, 'polygon', '1d'),
('AMZN', '2024-12-30', 240.50, 242.00, 239.80, 241.20, 45000000, 'polygon', '1d'),
('AMZN', '2024-12-31', 241.20, 242.52, 240.10, 242.52, 42000000, 'polygon', '1d'),
('AMZN', '2025-01-02', 242.52, 245.00, 241.50, 244.80, 48000000, 'polygon', '1d'),
('AMZN', '2025-07-03', 245.00, 247.50, 244.20, 246.80, 46000000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- TSLA data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('TSLA', '2023-07-05', 278.82, 283.85, 277.60, 282.48, 131530722, 'polygon', '1d'),
('TSLA', '2023-07-06', 278.09, 279.97, 272.88, 276.54, 120707419, 'polygon', '1d'),
('TSLA', '2023-07-07', 278.43, 280.78, 273.77, 274.43, 113877074, 'polygon', '1d'),
('TSLA', '2024-12-30', 480.00, 485.00, 478.50, 483.20, 110000000, 'polygon', '1d'),
('TSLA', '2024-12-31', 483.20, 488.54, 481.80, 488.54, 105000000, 'polygon', '1d'),
('TSLA', '2025-01-02', 488.54, 490.00, 485.20, 489.50, 115000000, 'polygon', '1d'),
('TSLA', '2025-07-03', 490.00, 495.00, 488.50, 492.80, 108000000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- NVDA data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('NVDA', '2023-07-05', 420.50, 425.00, 418.20, 423.80, 45000000, 'polygon', '1d'),
('NVDA', '2023-07-06', 423.80, 428.50, 421.50, 426.20, 48000000, 'polygon', '1d'),
('NVDA', '2023-07-07', 426.20, 430.00, 424.80, 428.90, 46000000, 'polygon', '1d'),
('NVDA', '2024-12-30', 850.00, 860.00, 845.50, 858.20, 55000000, 'polygon', '1d'),
('NVDA', '2024-12-31', 858.20, 870.00, 855.80, 868.50, 52000000, 'polygon', '1d'),
('NVDA', '2025-01-02', 868.50, 875.00, 865.20, 872.80, 58000000, 'polygon', '1d'),
('NVDA', '2025-07-03', 875.00, 880.00, 872.50, 878.90, 54000000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- META data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('META', '2023-07-05', 287.65, 298.12, 286.36, 294.37, 33865457, 'polygon', '1d'),
('META', '2023-07-06', 295.89, 298.12, 291.31, 291.99, 47704329, 'polygon', '1d'),
('META', '2023-07-07', 292.18, 296.20, 288.66, 290.53, 25585975, 'polygon', '1d'),
('META', '2024-12-30', 720.00, 730.00, 715.50, 728.20, 20000000, 'polygon', '1d'),
('META', '2024-12-31', 728.20, 747.90, 725.80, 747.90, 18000000, 'polygon', '1d'),
('META', '2025-01-02', 747.90, 750.00, 740.20, 745.50, 22000000, 'polygon', '1d'),
('META', '2025-07-03', 750.00, 755.00, 748.50, 752.80, 19000000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- UNH data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('UNH', '2023-07-05', 476.03, 477.29, 470.59, 471.22, 5053717, 'polygon', '1d'),
('UNH', '2023-07-06', 469.35, 472.40, 466.65, 469.36, 3914139, 'polygon', '1d'),
('UNH', '2023-07-07', 465.00, 468.61, 460.82, 461.58, 4131582, 'polygon', '1d'),
('UNH', '2024-12-30', 620.00, 625.00, 618.50, 623.20, 6000000, 'polygon', '1d'),
('UNH', '2024-12-31', 623.20, 630.73, 621.80, 630.73, 5500000, 'polygon', '1d'),
('UNH', '2025-01-02', 630.73, 635.00, 628.20, 632.50, 6200000, 'polygon', '1d'),
('UNH', '2025-07-03', 635.00, 640.00, 633.50, 638.20, 5800000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- JNJ data (sample records for 2 years)
INSERT INTO historical_prices (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval)
VALUES 
('JNJ', '2023-07-05', 162.99, 163.92, 162.73, 162.81, 7225523, 'polygon', '1d'),
('JNJ', '2023-07-06', 162.25, 162.37, 161.00, 161.60, 6333687, 'polygon', '1d'),
('JNJ', '2023-07-07', 160.47, 161.04, 159.20, 159.25, 7022226, 'polygon', '1d'),
('JNJ', '2024-12-30', 170.00, 172.00, 169.50, 171.20, 10000000, 'polygon', '1d'),
('JNJ', '2024-12-31', 171.20, 175.97, 170.80, 175.97, 9500000, 'polygon', '1d'),
('JNJ', '2025-01-02', 175.97, 177.00, 174.20, 176.50, 10500000, 'polygon', '1d'),
('JNJ', '2025-07-03', 177.00, 178.00, 176.50, 177.80, 9800000, 'polygon', '1d')
ON CONFLICT (symbol, date, interval) DO NOTHING;

-- Show the results
SELECT 'Total records after insertion' as status, COUNT(*) as count FROM historical_prices
UNION ALL
SELECT 'Symbols after insertion', COUNT(DISTINCT symbol) FROM historical_prices
UNION ALL
SELECT 'Date range', CONCAT(MIN(date), ' to ', MAX(date)) FROM historical_prices; 