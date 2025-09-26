# Data Model: Elliott Wave Analysis Service

**Feature**: Elliott Wave Analysis Service  
**Date**: 2025-01-27  
**Status**: Complete

## Entity Definitions

### ElliottWavePattern
**Purpose**: Represents a complete Elliott Wave pattern with all analysis results
**Fields**:
- `symbol: str` - Trading symbol (e.g., "SPY", "QQQ", "AAPL")
- `timeframe: str` - Analysis timeframe ("15m")
- `pattern_type: WaveType` - Pattern type (impulse, corrective, extension, diagonal, triangle, flat, zigzag)
- `waves: List[WavePoint]` - Individual wave points in the pattern
- `start_time: datetime` - Pattern start timestamp
- `end_time: datetime` - Pattern end timestamp
- `confidence: float` - Pattern reliability score (0.0-1.0)
- `fibonacci_levels: Dict[str, float]` - Fibonacci retracement and extension levels
- `target_price: Optional[float]` - Predicted completion price
- `invalidation_level: Optional[float]` - Pattern invalidation price level
- `enhanced_analysis: Dict[str, Any]` - Advanced analysis results

**Validation Rules**:
- Confidence must be between 0.0 and 1.0
- Start time must be before end time
- Minimum 3 waves for corrective patterns, 5 for impulse patterns
- Target price must be reasonable (within 50% of current price)

**State Transitions**:
- `detected` → `validated` → `completed` → `invalidated`
- `detected` → `extended` → `completed`

### WavePoint
**Purpose**: Individual wave high or low point in the pattern
**Fields**:
- `timestamp: datetime` - Wave point timestamp
- `price: float` - Wave point price
- `wave_number: Optional[int]` - Wave number (1-5 for impulse, A-C for corrective)
- `wave_type: Optional[WaveType]` - Wave type classification
- `direction: Optional[WaveDirection]` - Wave direction (up, down)
- `confidence: float` - Point reliability score (0.0-1.0)

**Validation Rules**:
- Price must be positive
- Wave number must be valid for pattern type
- Direction must be consistent with wave sequence
- Confidence must be between 0.0 and 1.0

**Relationships**:
- Belongs to one ElliottWavePattern
- Precedes/follows other WavePoints in sequence

### FibonacciLevel
**Purpose**: Fibonacci retracement and extension levels for pattern analysis
**Fields**:
- `level_name: str` - Level identifier (e.g., "fib_0.618_retracement")
- `price: float` - Fibonacci level price
- `ratio: float` - Fibonacci ratio (0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618)
- `level_type: str` - Type (retracement, extension)
- `confidence: float` - Level reliability score (0.0-1.0)

**Validation Rules**:
- Ratio must be valid Fibonacci number
- Price must be reasonable for symbol
- Level type must be valid
- Confidence must be between 0.0 and 1.0

**Relationships**:
- Belongs to one ElliottWavePattern
- Used by TradingSignal for target levels

### TradingSignal
**Purpose**: Generated trading signal based on Elliott Wave analysis
**Fields**:
- `symbol: str` - Trading symbol
- `signal_type: str` - Signal type (pattern_completion, fibonacci_retracement, volatility_expansion, pattern_invalidation)
- `wave_pattern: str` - Associated wave pattern
- `confidence: float` - Signal confidence (0.0-1.0)
- `recommended_strategy: str` - Suggested options strategy
- `strike_selection: Dict[str, float]` - Recommended strike prices
- `expiration_preference: str` - Preferred expiration timeframe
- `risk_level: str` - Risk level (high, medium, low)
- `profit_target: Optional[float]` - Profit target price
- `stop_loss: Optional[float]` - Stop loss price
- `description: str` - Signal description
- `timestamp: datetime` - Signal generation time

**Validation Rules**:
- Confidence must be >= 0.6 for signal generation
- Risk level must be valid
- Profit target must be reasonable
- Stop loss must be reasonable
- Strike selection must be valid for strategy

**Relationships**:
- Generated from ElliottWavePattern
- References FibonacciLevel for targets
- Maps to options strategies

### PatternAnalysis
**Purpose**: Complete analysis including extensions, relationships, and strength
**Fields**:
- `pattern_id: str` - Unique pattern identifier
- `wave_extensions: Dict[str, Any]` - Wave extension analysis
- `fibonacci_relationships: List[WaveRelationship]` - Wave-to-wave relationships
- `pattern_subtype: Optional[str]` - Specific pattern subtype
- `pattern_completion_prediction: Dict[str, Any]` - Completion predictions
- `pattern_strength: float` - Overall pattern strength (0.0-1.0)
- `trading_signals: List[TradingSignal]` - Generated trading signals

**Validation Rules**:
- Pattern strength must be between 0.0 and 1.0
- Completion prediction must be reasonable
- Trading signals must be valid

**Relationships**:
- Belongs to one ElliottWavePattern
- Contains multiple WaveRelationship objects
- Generates multiple TradingSignal objects

### WaveRelationship
**Purpose**: Relationship between two waves with Fibonacci analysis
**Fields**:
- `wave1_number: int` - First wave number
- `wave2_number: int` - Second wave number
- `ratio: float` - Length ratio between waves
- `fibonacci_level: Optional[float]` - Closest Fibonacci ratio
- `confidence: float` - Relationship confidence (0.0-1.0)

**Validation Rules**:
- Wave numbers must be valid
- Ratio must be positive
- Fibonacci level must be valid if present
- Confidence must be between 0.0 and 1.0

**Relationships**:
- Belongs to one PatternAnalysis
- References two WavePoints

## Data Flow

### Pattern Detection Flow
1. **Market Data Input** → Swing Point Detection → Wave Counting → Pattern Validation
2. **Pattern Validation** → Fibonacci Analysis → Confidence Scoring → Signal Generation
3. **Signal Generation** → Options Strategy Mapping → Risk Assessment → Trading Signal

### Real-Time Update Flow
1. **New Price Data** → Swing Point Update → Pattern Re-evaluation → Signal Update
2. **Pattern Completion** → Alert Generation → Options Signal → Risk Management

## Storage Requirements

### Pattern Storage
- **ElliottWavePattern**: TimescaleDB table with time-series optimization
- **WavePoint**: Related table with foreign key to pattern
- **FibonacciLevel**: Related table with foreign key to pattern
- **TradingSignal**: Related table with foreign key to pattern

### Caching Strategy
- **Swing Points**: Redis cache for recent swing points
- **Active Patterns**: Redis cache for current patterns
- **Fibonacci Levels**: Redis cache for calculated levels
- **Trading Signals**: Redis cache for recent signals

### Data Retention
- **Patterns**: 30 days of historical patterns
- **Signals**: 7 days of trading signals
- **Cache**: 1 hour TTL for swing points, 15 minutes for patterns

## Validation Rules

### Pattern Validation
- Minimum 20 data points required
- Maximum 50 data points per wave
- Elliott Wave rules compliance
- Fibonacci relationship validation

### Signal Validation
- Confidence threshold >= 0.6
- Risk level appropriateness
- Strike price validity
- Expiration timeframe validity

### Data Validation
- Price data completeness
- Timestamp consistency
- Symbol validity
- Timeframe consistency

## Performance Considerations

### Query Optimization
- Indexed by symbol and timestamp
- Partitioned by date for historical data
- Cached frequently accessed patterns

### Memory Management
- Efficient data structures for wave storage
- Periodic cleanup of old patterns
- Memory limits for analysis buffers

### Scalability
- Horizontal scaling for multiple symbols
- Load balancing for analysis requests
- Caching for performance optimization
