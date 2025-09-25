# Trading Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: trading strategies, market data, risk management, user interactions
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable and backtestable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Trading-Specific Guidelines
- ✅ Focus on WHAT traders need and WHY (profitability, risk management, automation)
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for trading stakeholders, not developers
- 📊 Include backtesting requirements for all strategies
- ⚠️ Include risk management requirements

### Section Requirements
- **Mandatory sections**: Must be completed for every trading feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "options strategy" without specific strategy type), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas in trading**:
   - Risk management parameters (position sizing, stop-losses)
   - Market data requirements (real-time vs historical)
   - Performance targets (profitability, drawdown limits)
   - User permissions and access controls
   - Integration requirements with existing strategies

---

## User Scenarios & Testing *(mandatory)*

### Primary Trading Scenario
[Describe the main trading workflow in plain language]

### Acceptance Scenarios
1. **Given** [market conditions], **When** [strategy triggers], **Then** [expected trade execution]
2. **Given** [portfolio state], **When** [risk limit reached], **Then** [expected risk management action]
3. **Given** [user request], **When** [feature used], **Then** [expected outcome]

### Edge Cases
- What happens when [market data unavailable]?
- How does system handle [risk limit breach]?
- What occurs during [market volatility spike]?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST [specific trading capability, e.g., "execute Iron Condor trades"]
- **FR-002**: System MUST [specific validation, e.g., "validate position sizing limits"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "view real-time P&L"]
- **FR-004**: System MUST [data requirement, e.g., "persist trade history"]
- **FR-005**: System MUST [behavior, e.g., "log all trading decisions"]

*Example of marking unclear requirements:*
- **FR-006**: System MUST handle risk management via [NEEDS CLARIFICATION: risk method not specified - stop-loss, position sizing, portfolio limits?]
- **FR-007**: System MUST process market data at [NEEDS CLARIFICATION: frequency not specified - real-time, 1-minute, daily?]

### Risk Management Requirements *(mandatory for trading features)*
- **RM-001**: System MUST [specific risk control, e.g., "limit position size to 5% of portfolio"]
- **RM-002**: System MUST [specific monitoring, e.g., "alert when drawdown exceeds 10%"]
- **RM-003**: System MUST [specific validation, e.g., "validate trade parameters before execution"]

### Backtesting Requirements *(mandatory for strategy features)*
- **BT-001**: System MUST [specific backtesting capability, e.g., "backtest strategy over 2-year period"]
- **BT-002**: System MUST [specific metrics, e.g., "calculate Sharpe ratio and max drawdown"]
- **BT-003**: System MUST [specific validation, e.g., "validate strategy performance before live trading"]

### Key Entities *(include if feature involves data)*
- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on trading value and business needs
- [ ] Written for non-technical trading stakeholders
- [ ] All mandatory sections completed
- [ ] Risk management requirements included
- [ ] Backtesting requirements included (for strategies)

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified
- [ ] Risk management parameters specified
- [ ] Performance targets defined

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Risk management requirements added
- [ ] Backtesting requirements added
- [ ] Entities identified
- [ ] Review checklist passed

---


