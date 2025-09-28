"""
Stress Tester Service

Provides stress testing capabilities for portfolio risk assessment in the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass

from ..models.stress_test_result import StressTestResult, ScenarioType, TestStatus, PositionImpact, SectorImpact


logger = logging.getLogger(__name__)


@dataclass
class StressTestScenario:
    """Configuration for a stress test scenario."""
    name: str
    scenario_type: ScenarioType
    parameters: Dict[str, Any]
    description: str = ""


class StressTester:
    """
    Portfolio stress testing service.
    
    Provides stress testing capabilities using predefined and custom scenarios
    to assess portfolio performance under adverse market conditions.
    """
    
    def __init__(self, market_data_provider=None):
        """
        Initialize stress tester.
        
        Args:
            market_data_provider: Provider for market data (optional)
        """
        self.market_data_provider = market_data_provider
        self.scenario_cache = {}
        
        # Initialize standard scenarios
        self._initialize_standard_scenarios()
    
    def _initialize_standard_scenarios(self) -> None:
        """Initialize standard stress test scenarios."""
        self.standard_scenarios = {
            "market_crash": StressTestScenario(
                name="Market Crash",
                scenario_type=ScenarioType.MARKET_CRASH,
                parameters={
                    "market_decline": -0.30,
                    "duration_days": 5,
                    "volatility_spike": 0.50
                },
                description="Simulates a 30% market decline over 5 days with increased volatility"
            ),
            "rate_shock": StressTestScenario(
                name="Interest Rate Shock",
                scenario_type=ScenarioType.RATE_SHOCK,
                parameters={
                    "rate_increase": 0.02,  # 2% increase
                    "bond_duration_impact": -0.15,
                    "equity_impact": -0.05
                },
                description="Simulates a 2% interest rate increase and its impact on bonds and equities"
            ),
            "volatility_spike": StressTestScenario(
                name="Volatility Spike",
                scenario_type=ScenarioType.VOLATILITY_SPIKE,
                parameters={
                    "volatility_increase": 0.50,  # 50% increase
                    "correlation_increase": 0.30,
                    "duration_days": 10
                },
                description="Simulates a 50% increase in market volatility with higher correlations"
            ),
            "sector_rotation": StressTestScenario(
                name="Sector Rotation",
                scenario_type=ScenarioType.SECTOR_ROTATION,
                parameters={
                    "technology_decline": -0.25,
                    "energy_increase": 0.15,
                    "financial_decline": -0.10
                },
                description="Simulates sector rotation with technology decline and energy increase"
            ),
            "options_decay": StressTestScenario(
                name="Options Time Decay",
                scenario_type=ScenarioType.OPTIONS_DECAY,
                parameters={
                    "time_decay_acceleration": 0.30,
                    "volatility_decrease": -0.20,
                    "duration_days": 7
                },
                description="Simulates accelerated time decay for options positions"
            )
        }
    
    def run_stress_tests(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        scenarios: List[str] = None,
        custom_scenarios: List[Dict[str, Any]] = None,
        include_position_impacts: bool = True,
        include_sector_impacts: bool = True,
        portfolio_value: float = 100000.0
    ) -> List[StressTestResult]:
        """
        Run stress tests on a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            portfolio_positions: List of portfolio positions
            scenarios: List of standard scenario names to run
            custom_scenarios: List of custom scenario configurations
            include_position_impacts: Whether to calculate position-level impacts
            include_sector_impacts: Whether to calculate sector-level impacts
            portfolio_value: Total portfolio value
            
        Returns:
            List of StressTestResult objects
        """
        logger.info(f"Running stress tests for portfolio {portfolio_id}")
        
        # Validate inputs
        self._validate_inputs(portfolio_id, portfolio_positions, scenarios, custom_scenarios)
        
        results = []
        
        # Run standard scenarios
        if scenarios:
            for scenario_name in scenarios:
                if scenario_name in self.standard_scenarios:
                    scenario = self.standard_scenarios[scenario_name]
                    result = self._run_single_stress_test(
                        portfolio_id, portfolio_positions, scenario, portfolio_value,
                        include_position_impacts, include_sector_impacts
                    )
                    results.append(result)
                else:
                    logger.warning(f"Unknown scenario: {scenario_name}")
        
        # Run custom scenarios
        if custom_scenarios:
            for custom_scenario_data in custom_scenarios:
                scenario = self._create_custom_scenario(custom_scenario_data)
                result = self._run_single_stress_test(
                    portfolio_id, portfolio_positions, scenario, portfolio_value,
                    include_position_impacts, include_sector_impacts
                )
                results.append(result)
        
        return results
    
    def _validate_inputs(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        scenarios: List[str],
        custom_scenarios: List[Dict[str, Any]]
    ) -> None:
        """Validate stress test inputs."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not portfolio_positions:
            raise ValueError("Portfolio positions are required")
        
        if not scenarios and not custom_scenarios:
            raise ValueError("At least one scenario must be specified")
        
        # Validate portfolio positions
        for position in portfolio_positions:
            if "symbol" not in position or "weight" not in position:
                raise ValueError("Each position must have 'symbol' and 'weight'")
            
            if not (0 <= position["weight"] <= 1):
                raise ValueError(f"Position weight for {position['symbol']} must be between 0 and 1")
        
        # Validate scenarios
        if scenarios:
            for scenario_name in scenarios:
                if scenario_name not in self.standard_scenarios:
                    raise ValueError(f"Unknown standard scenario: {scenario_name}")
        
        # Validate custom scenarios
        if custom_scenarios:
            for scenario_data in custom_scenarios:
                if "name" not in scenario_data or "type" not in scenario_data:
                    raise ValueError("Custom scenario must have 'name' and 'type'")
                
                if scenario_data["type"] not in [t.value for t in ScenarioType]:
                    raise ValueError(f"Invalid scenario type: {scenario_data['type']}")
    
    def _create_custom_scenario(self, scenario_data: Dict[str, Any]) -> StressTestScenario:
        """Create a custom scenario from configuration data."""
        return StressTestScenario(
            name=scenario_data["name"],
            scenario_type=ScenarioType(scenario_data["type"]),
            parameters=scenario_data.get("parameters", {}),
            description=scenario_data.get("description", "")
        )
    
    def _run_single_stress_test(
        self,
        portfolio_id: str,
        portfolio_positions: List[Dict[str, Any]],
        scenario: StressTestScenario,
        portfolio_value: float,
        include_position_impacts: bool,
        include_sector_impacts: bool
    ) -> StressTestResult:
        """Run a single stress test scenario."""
        start_time = datetime.utcnow()
        
        try:
            # Calculate initial portfolio value
            initial_value = portfolio_value
            
            # Apply stress scenario
            stressed_positions = self._apply_stress_scenario(portfolio_positions, scenario)
            
            # Calculate stressed portfolio value
            stressed_value = self._calculate_stressed_portfolio_value(stressed_positions, portfolio_value)
            
            # Calculate portfolio change
            portfolio_change = stressed_value - initial_value
            portfolio_change_pct = portfolio_change / initial_value if initial_value > 0 else 0.0
            
            # Calculate position impacts if requested
            position_impacts = []
            if include_position_impacts:
                position_impacts = self._calculate_position_impacts(
                    portfolio_positions, stressed_positions, portfolio_value
                )
            
            # Calculate sector impacts if requested
            sector_impacts = []
            if include_sector_impacts:
                sector_impacts = self._calculate_sector_impacts(
                    portfolio_positions, stressed_positions, portfolio_value
                )
            
            # Calculate risk impacts
            risk_impacts = self._calculate_risk_impacts(
                portfolio_positions, stressed_positions, scenario
            )
            
            # Calculate test duration
            end_time = datetime.utcnow()
            test_duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Create stress test result
            result = StressTestResult(
                portfolio_id=portfolio_id,
                scenario_name=scenario.name,
                scenario_type=scenario.scenario_type,
                initial_portfolio_value=initial_value,
                stressed_portfolio_value=stressed_value,
                portfolio_value_change=portfolio_change,
                portfolio_value_change_pct=portfolio_change_pct,
                var_impact=risk_impacts.get("var_impact", 0.0),
                volatility_impact=risk_impacts.get("volatility_impact", 0.0),
                max_drawdown_impact=risk_impacts.get("max_drawdown_impact", 0.0),
                position_impacts=position_impacts,
                sector_impacts=sector_impacts,
                scenario_parameters=scenario.parameters,
                test_duration_ms=test_duration_ms,
                status=TestStatus.COMPLETED
            )
            
            logger.info(f"Completed stress test '{scenario.name}' for portfolio {portfolio_id}")
            return result
            
        except Exception as e:
            logger.error(f"Stress test '{scenario.name}' failed: {str(e)}")
            
            # Create failed result
            end_time = datetime.utcnow()
            test_duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return StressTestResult(
                portfolio_id=portfolio_id,
                scenario_name=scenario.name,
                scenario_type=scenario.scenario_type,
                initial_portfolio_value=portfolio_value,
                stressed_portfolio_value=portfolio_value,  # No change on failure
                portfolio_value_change=0.0,
                portfolio_value_change_pct=0.0,
                scenario_parameters=scenario.parameters,
                test_duration_ms=test_duration_ms,
                status=TestStatus.FAILED,
                error_message=str(e)
            )
    
    def _apply_stress_scenario(
        self,
        portfolio_positions: List[Dict[str, Any]],
        scenario: StressTestScenario
    ) -> List[Dict[str, Any]]:
        """Apply stress scenario to portfolio positions."""
        stressed_positions = []
        
        for position in portfolio_positions:
            stressed_position = position.copy()
            
            # Apply scenario-specific stress
            if scenario.scenario_type == ScenarioType.MARKET_CRASH:
                stressed_position = self._apply_market_crash_stress(position, scenario.parameters)
            elif scenario.scenario_type == ScenarioType.RATE_SHOCK:
                stressed_position = self._apply_rate_shock_stress(position, scenario.parameters)
            elif scenario.scenario_type == ScenarioType.VOLATILITY_SPIKE:
                stressed_position = self._apply_volatility_spike_stress(position, scenario.parameters)
            elif scenario.scenario_type == ScenarioType.SECTOR_ROTATION:
                stressed_position = self._apply_sector_rotation_stress(position, scenario.parameters)
            elif scenario.scenario_type == ScenarioType.OPTIONS_DECAY:
                stressed_position = self._apply_options_decay_stress(position, scenario.parameters)
            elif scenario.scenario_type == ScenarioType.CUSTOM:
                stressed_position = self._apply_custom_stress(position, scenario.parameters)
            
            stressed_positions.append(stressed_position)
        
        return stressed_positions
    
    def _apply_market_crash_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply market crash stress to a position."""
        stressed_position = position.copy()
        
        # Get market decline parameter
        market_decline = parameters.get("market_decline", -0.30)
        
        # Apply stress based on asset type
        asset_type = position.get("asset_type", "stock")
        
        if asset_type in ["stock", "equity"]:
            # Stocks are directly affected by market crash
            stress_factor = 1 + market_decline
        elif asset_type in ["bond", "fixed_income"]:
            # Bonds may benefit from flight to quality
            stress_factor = 1 + (market_decline * 0.3)  # Less impact on bonds
        elif asset_type in ["option", "derivative"]:
            # Options are more sensitive to market moves
            stress_factor = 1 + (market_decline * 1.5)
        else:
            # Default stress for other asset types
            stress_factor = 1 + (market_decline * 0.5)
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _apply_rate_shock_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply interest rate shock stress to a position."""
        stressed_position = position.copy()
        
        rate_increase = parameters.get("rate_increase", 0.02)
        bond_duration_impact = parameters.get("bond_duration_impact", -0.15)
        equity_impact = parameters.get("equity_impact", -0.05)
        
        asset_type = position.get("asset_type", "stock")
        
        if asset_type in ["bond", "fixed_income"]:
            # Bonds are negatively affected by rate increases
            stress_factor = 1 + bond_duration_impact
        elif asset_type in ["stock", "equity"]:
            # Equities are moderately affected
            stress_factor = 1 + equity_impact
        else:
            # Other assets less affected
            stress_factor = 1 + (equity_impact * 0.5)
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _apply_volatility_spike_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply volatility spike stress to a position."""
        stressed_position = position.copy()
        
        volatility_increase = parameters.get("volatility_increase", 0.50)
        
        asset_type = position.get("asset_type", "stock")
        
        if asset_type in ["option", "derivative"]:
            # Options benefit from volatility increases
            stress_factor = 1 + (volatility_increase * 0.3)
        elif asset_type in ["stock", "equity"]:
            # Stocks are negatively affected by volatility
            stress_factor = 1 - (volatility_increase * 0.2)
        else:
            # Other assets less affected
            stress_factor = 1 + (volatility_increase * 0.1)
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _apply_sector_rotation_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply sector rotation stress to a position."""
        stressed_position = position.copy()
        
        # Get sector from position
        sector = position.get("sector", "unknown")
        
        # Apply sector-specific stress
        if sector.lower() in ["technology", "tech"]:
            stress_factor = 1 + parameters.get("technology_decline", -0.25)
        elif sector.lower() in ["energy", "oil", "gas"]:
            stress_factor = 1 + parameters.get("energy_increase", 0.15)
        elif sector.lower() in ["financial", "finance", "banking"]:
            stress_factor = 1 + parameters.get("financial_decline", -0.10)
        else:
            # Default impact for other sectors
            stress_factor = 1 + parameters.get("other_sector_impact", -0.05)
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _apply_options_decay_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply options time decay stress to a position."""
        stressed_position = position.copy()
        
        time_decay_acceleration = parameters.get("time_decay_acceleration", 0.30)
        volatility_decrease = parameters.get("volatility_decrease", -0.20)
        
        asset_type = position.get("asset_type", "option")
        
        if asset_type in ["option", "derivative"]:
            # Options lose value due to time decay and volatility decrease
            stress_factor = 1 - time_decay_acceleration - abs(volatility_decrease)
        else:
            # Other assets not affected
            stress_factor = 1.0
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _apply_custom_stress(
        self,
        position: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom stress scenario to a position."""
        stressed_position = position.copy()
        
        # Apply custom stress factor if provided
        stress_factor = parameters.get("stress_factor", 1.0)
        
        # Apply stress to position value
        if "current_value" in stressed_position:
            stressed_position["current_value"] *= stress_factor
        
        return stressed_position
    
    def _calculate_stressed_portfolio_value(
        self,
        stressed_positions: List[Dict[str, Any]],
        initial_portfolio_value: float
    ) -> float:
        """Calculate the total value of stressed portfolio."""
        total_value = 0.0
        
        for position in stressed_positions:
            if "current_value" in position:
                total_value += position["current_value"]
            else:
                # Fallback to weight-based calculation
                weight = position.get("weight", 0.0)
                total_value += weight * initial_portfolio_value
        
        return total_value
    
    def _calculate_position_impacts(
        self,
        original_positions: List[Dict[str, Any]],
        stressed_positions: List[Dict[str, Any]],
        portfolio_value: float
    ) -> List[PositionImpact]:
        """Calculate position-level impacts from stress testing."""
        impacts = []
        
        for i, (original, stressed) in enumerate(zip(original_positions, stressed_positions)):
            original_value = original.get("current_value", original.get("weight", 0.0) * portfolio_value)
            stressed_value = stressed.get("current_value", original_value)
            
            position_change = stressed_value - original_value
            position_change_pct = position_change / original_value if original_value > 0 else 0.0
            
            # Calculate contribution to portfolio change
            portfolio_change = sum(
                stressed.get("current_value", pos.get("weight", 0.0) * portfolio_value) -
                original.get("current_value", pos.get("weight", 0.0) * portfolio_value)
                for pos in original_positions
            )
            
            contribution_to_portfolio_change = position_change / portfolio_change if portfolio_change != 0 else 0.0
            
            impact = PositionImpact(
                asset_id=original.get("symbol", f"asset_{i}"),
                asset_type=original.get("asset_type", "stock"),
                initial_value=original_value,
                stressed_value=stressed_value,
                position_value_change=position_change,
                position_value_change_pct=position_change_pct,
                contribution_to_portfolio_change=contribution_to_portfolio_change
            )
            
            impacts.append(impact)
        
        return impacts
    
    def _calculate_sector_impacts(
        self,
        original_positions: List[Dict[str, Any]],
        stressed_positions: List[Dict[str, Any]],
        portfolio_value: float
    ) -> List[SectorImpact]:
        """Calculate sector-level impacts from stress testing."""
        # Group positions by sector
        sector_data = {}
        
        for i, (original, stressed) in enumerate(zip(original_positions, stressed_positions)):
            sector = original.get("sector", "unknown")
            
            if sector not in sector_data:
                sector_data[sector] = {
                    "original_value": 0.0,
                    "stressed_value": 0.0,
                    "weight": 0.0
                }
            
            original_value = original.get("current_value", original.get("weight", 0.0) * portfolio_value)
            stressed_value = stressed.get("current_value", original_value)
            weight = original.get("weight", 0.0)
            
            sector_data[sector]["original_value"] += original_value
            sector_data[sector]["stressed_value"] += stressed_value
            sector_data[sector]["weight"] += weight
        
        # Calculate sector impacts
        impacts = []
        total_portfolio_change = sum(
            stressed.get("current_value", pos.get("weight", 0.0) * portfolio_value) -
            original.get("current_value", pos.get("weight", 0.0) * portfolio_value)
            for pos in original_positions
        )
        
        for sector, data in sector_data.items():
            sector_change = data["stressed_value"] - data["original_value"]
            sector_change_pct = sector_change / data["original_value"] if data["original_value"] > 0 else 0.0
            contribution_to_portfolio_change = sector_change / total_portfolio_change if total_portfolio_change != 0 else 0.0
            
            impact = SectorImpact(
                sector=sector,
                initial_value=data["original_value"],
                stressed_value=data["stressed_value"],
                sector_value_change=sector_change,
                sector_value_change_pct=sector_change_pct,
                weight_in_portfolio=data["weight"],
                contribution_to_portfolio_change=contribution_to_portfolio_change
            )
            
            impacts.append(impact)
        
        return impacts
    
    def _calculate_risk_impacts(
        self,
        original_positions: List[Dict[str, Any]],
        stressed_positions: List[Dict[str, Any]],
        scenario: StressTestScenario
    ) -> Dict[str, float]:
        """Calculate risk metric impacts from stress testing."""
        # This is a simplified implementation
        # In a real system, this would involve recalculating VaR, volatility, etc.
        
        portfolio_change_pct = sum(
            (stressed.get("weight", 0.0) - original.get("weight", 0.0))
            for original, stressed in zip(original_positions, stressed_positions)
        )
        
        return {
            "var_impact": portfolio_change_pct * 0.8,  # Simplified VaR impact
            "volatility_impact": portfolio_change_pct * 0.6,  # Simplified volatility impact
            "max_drawdown_impact": portfolio_change_pct * 0.9  # Simplified drawdown impact
        }
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of available stress test scenarios."""
        scenarios = []
        
        for scenario_name, scenario in self.standard_scenarios.items():
            scenarios.append({
                "name": scenario_name,
                "type": scenario.scenario_type.value,
                "description": scenario.description,
                "default_parameters": scenario.parameters,
                "customizable": True
            })
        
        return scenarios
    
    def get_scenario_parameters(self, scenario_name: str) -> Dict[str, Any]:
        """Get parameters for a specific scenario."""
        if scenario_name in self.standard_scenarios:
            return self.standard_scenarios[scenario_name].parameters
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")
    
    def validate_scenario_parameters(
        self,
        scenario_type: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Validate scenario parameters."""
        try:
            scenario_type_enum = ScenarioType(scenario_type)
            
            # Basic validation - in a real system, this would be more comprehensive
            if scenario_type_enum == ScenarioType.MARKET_CRASH:
                required_params = ["market_decline"]
                return all(param in parameters for param in required_params)
            elif scenario_type_enum == ScenarioType.RATE_SHOCK:
                required_params = ["rate_increase"]
                return all(param in parameters for param in required_params)
            
            return True
            
        except ValueError:
            return False



