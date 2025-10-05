"""
Tax Optimization API endpoints
Exposes tax-loss harvesting and tax-aware portfolio management through REST APIs
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tax", tags=["tax"])

# Pydantic models for tax optimization requests
class TaxLossHarvestingRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    max_harvest_amount: Optional[float] = Field(None, description="Maximum amount to harvest")
    wash_sale_threshold: int = Field(30, description="Wash sale period in days")
    tax_rate: float = Field(0.20, description="Capital gains tax rate")
    include_similar_assets: bool = Field(True, description="Include similar assets in wash sale check")

class TaxOptimizedRebalancingRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio ID")
    target_weights: Dict[str, float] = Field(..., description="Target portfolio weights")
    tax_rate: float = Field(0.20, description="Capital gains tax rate")
    max_tax_cost: Optional[float] = Field(None, description="Maximum acceptable tax cost")
    optimization_horizon: int = Field(365, description="Optimization horizon in days")

class TaxLotRequest(BaseModel):
    position_id: str = Field(..., description="Position ID")
    tax_lot_id: str = Field(..., description="Tax lot ID")
    quantity: float = Field(..., description="Quantity to sell")
    lot_method: str = Field("FIFO", description="Lot selection method: FIFO, LIFO, SPECIFIC_ID, TAX_OPTIMIZED")

# Tax optimization endpoints
@router.post("/harvest-losses", response_model=Dict[str, Any])
async def harvest_tax_losses(request: TaxLossHarvestingRequest):
    """Identify and execute tax-loss harvesting opportunities"""
    try:
        # Mock implementation for now
        tax_loss_harvesting = {
            "harvesting_id": f"harvest-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "harvesting_date": datetime.now().isoformat(),
            "tax_rate": request.tax_rate,
            "wash_sale_threshold": request.wash_sale_threshold,
            "harvesting_opportunities": [
                {
                    "opportunity_id": f"opp-1-{datetime.now().timestamp()}",
                    "asset_id": "PYPL",
                    "position_id": "pos-pypl-123",
                    "current_price": 85.0,
                    "average_cost": 120.0,
                    "unrealized_loss": -3500.0,
                    "quantity_to_sell": 100,
                    "tax_benefit": 700.0,  # 20% of 3500
                    "harvest_reason": "Significant unrealized loss",
                    "wash_sale_risk": "LOW",
                    "replacement_candidate": "V"
                },
                {
                    "opportunity_id": f"opp-2-{datetime.now().timestamp()}",
                    "asset_id": "NFLX",
                    "position_id": "pos-nflx-456",
                    "current_price": 280.0,
                    "average_cost": 350.0,
                    "unrealized_loss": -2100.0,
                    "quantity_to_sell": 30,
                    "tax_benefit": 420.0,  # 20% of 2100
                    "harvest_reason": "Medium-term loss",
                    "wash_sale_risk": "MEDIUM",
                    "replacement_candidate": "DIS"
                }
            ],
            "harvesting_summary": {
                "total_opportunities": 2,
                "total_unrealized_loss": -5600.0,
                "total_tax_benefit": 1120.0,
                "max_harvestable_amount": 5600.0,
                "recommended_harvest_amount": 5600.0,
                "wash_sale_warnings": [
                    {
                        "asset_id": "NFLX",
                        "warning": "Similar asset DIS purchased within 30 days",
                        "recommendation": "Wait 31 days or choose different replacement"
                    }
                ]
            },
            "replacement_recommendations": [
                {
                    "original_asset": "PYPL",
                    "replacement_asset": "V",
                    "correlation": 0.85,
                    "sector_match": "Financial Services",
                    "tax_efficiency": "HIGH",
                    "expected_tracking_error": 0.02
                },
                {
                    "original_asset": "NFLX",
                    "replacement_asset": "DIS",
                    "correlation": 0.78,
                    "sector_match": "Communication Services",
                    "tax_efficiency": "MEDIUM",
                    "expected_tracking_error": 0.05
                }
            ],
            "execution_strategy": {
                "recommended_timing": "IMMEDIATE",
                "execution_order": ["PYPL", "NFLX"],
                "estimated_execution_time": "1_DAY",
                "market_impact_consideration": True,
                "liquidity_check": "PASSED"
            }
        }
        
        return {
            "success": True,
            "tax_loss_harvesting": tax_loss_harvesting,
            "message": "Tax-loss harvesting opportunities identified successfully"
        }
    except Exception as e:
        logger.error(f"Error in tax-loss harvesting: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/optimize-rebalancing", response_model=Dict[str, Any])
async def optimize_rebalancing_tax_aware(request: TaxOptimizedRebalancingRequest):
    """Generate tax-optimized rebalancing recommendations"""
    try:
        # Mock implementation for now
        tax_optimized_rebalancing = {
            "optimization_id": f"tax-rebal-{request.portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": request.portfolio_id,
            "optimization_date": datetime.now().isoformat(),
            "tax_rate": request.tax_rate,
            "optimization_horizon": request.optimization_horizon,
            "target_weights": request.target_weights,
            "current_weights": {
                "AAPL": 0.28,
                "MSFT": 0.22,
                "GOOGL": 0.16,
                "TSLA": 0.12,
                "NVDA": 0.10,
                "AMZN": 0.08,
                "META": 0.04
            },
            "tax_optimized_trades": [
                {
                    "trade_id": f"tax-trade-1-{datetime.now().timestamp()}",
                    "asset_id": "AAPL",
                    "action": "SELL",
                    "quantity": 100,
                    "current_price": 150.0,
                    "average_cost": 140.0,
                    "capital_gain": 1000.0,
                    "tax_cost": 200.0,
                    "lot_method": "TAX_OPTIMIZED",
                    "selected_lots": [
                        {
                            "lot_id": "lot-1",
                            "quantity": 60,
                            "cost_basis": 135.0,
                            "capital_gain": 900.0
                        },
                        {
                            "lot_id": "lot-2",
                            "quantity": 40,
                            "cost_basis": 150.0,
                            "capital_gain": 0.0
                        }
                    ]
                },
                {
                    "trade_id": f"tax-trade-2-{datetime.now().timestamp()}",
                    "asset_id": "META",
                    "action": "BUY",
                    "quantity": 50,
                    "current_price": 200.0,
                    "average_cost": 0.0,
                    "capital_gain": 0.0,
                    "tax_cost": 0.0,
                    "lot_method": "NEW_POSITION"
                }
            ],
            "tax_optimization_metrics": {
                "total_tax_cost": 200.0,
                "tax_cost_reduction": 150.0,  # Compared to naive approach
                "tax_efficiency_score": 0.85,
                "deferred_tax_liability": 500.0,
                "immediate_tax_benefit": 200.0,
                "net_tax_impact": -50.0  # Negative means tax benefit
            },
            "alternative_scenarios": [
                {
                    "scenario_name": "AGGRESSIVE_HARVESTING",
                    "total_tax_cost": 50.0,
                    "tax_cost_reduction": 300.0,
                    "additional_harvesting": 1500.0,
                    "risk_adjustment": 0.02
                },
                {
                    "scenario_name": "CONSERVATIVE_APPROACH",
                    "total_tax_cost": 300.0,
                    "tax_cost_reduction": 50.0,
                    "minimal_harvesting": 500.0,
                    "risk_adjustment": 0.01
                }
            ],
            "wash_sale_analysis": {
                "wash_sale_risks": [],
                "safe_harvesting_period": "IMMEDIATE",
                "replacement_timing": "SIMULTANEOUS"
            },
            "execution_recommendations": {
                "optimal_execution_order": ["META_BUY", "AAPL_SELL"],
                "timing_strategy": "SAME_DAY",
                "estimated_slippage": 0.001,
                "liquidity_assessment": "HIGH"
            }
        }
        
        return {
            "success": True,
            "tax_optimized_rebalancing": tax_optimized_rebalancing,
            "message": "Tax-optimized rebalancing generated successfully"
        }
    except Exception as e:
        logger.error(f"Error in tax-optimized rebalancing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/select-tax-lots", response_model=Dict[str, Any])
async def select_optimal_tax_lots(request: TaxLotRequest):
    """Select optimal tax lots for selling"""
    try:
        # Mock implementation for now
        tax_lot_selection = {
            "selection_id": f"lot-select-{request.position_id}-{datetime.now().timestamp()}",
            "position_id": request.position_id,
            "tax_lot_id": request.tax_lot_id,
            "selection_date": datetime.now().isoformat(),
            "lot_method": request.lot_method,
            "requested_quantity": request.quantity,
            "available_lots": [
                {
                    "lot_id": "lot-1",
                    "purchase_date": "2023-01-15",
                    "cost_basis": 135.0,
                    "quantity": 100,
                    "current_price": 150.0,
                    "unrealized_gain": 1500.0,
                    "holding_period": 365,  # days
                    "tax_rate": 0.15  # Long-term capital gains
                },
                {
                    "lot_id": "lot-2",
                    "purchase_date": "2024-01-15",
                    "cost_basis": 145.0,
                    "quantity": 50,
                    "current_price": 150.0,
                    "unrealized_gain": 250.0,
                    "holding_period": 180,  # days
                    "tax_rate": 0.20  # Short-term capital gains
                },
                {
                    "lot_id": "lot-3",
                    "purchase_date": "2024-06-01",
                    "cost_basis": 155.0,
                    "quantity": 75,
                    "current_price": 150.0,
                    "unrealized_loss": -375.0,
                    "holding_period": 30,  # days
                    "tax_rate": 0.20
                }
            ],
            "selected_lots": [
                {
                    "lot_id": "lot-3",
                    "quantity": 75,
                    "cost_basis": 155.0,
                    "unrealized_loss": -375.0,
                    "tax_benefit": 75.0,
                    "selection_reason": "Tax loss harvesting"
                },
                {
                    "lot_id": "lot-2",
                    "quantity": 25,  # Remaining quantity needed
                    "cost_basis": 145.0,
                    "unrealized_gain": 125.0,
                    "tax_cost": 25.0,
                    "selection_reason": "Minimize tax impact"
                }
            ],
            "selection_summary": {
                "total_quantity_selected": 100,
                "total_cost_basis": 14750.0,
                "net_tax_impact": -50.0,  # Net tax benefit
                "average_cost_basis": 147.5,
                "tax_efficiency": 0.95
            },
            "alternative_selections": [
                {
                    "method": "FIFO",
                    "total_tax_cost": 300.0,
                    "average_cost_basis": 135.0
                },
                {
                    "method": "LIFO",
                    "total_tax_cost": 400.0,
                    "average_cost_basis": 155.0
                }
            ]
        }
        
        return {
            "success": True,
            "tax_lot_selection": tax_lot_selection,
            "message": "Optimal tax lots selected successfully"
        }
    except Exception as e:
        logger.error(f"Error selecting tax lots: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{portfolio_id}/wash-sale-analysis", response_model=Dict[str, Any])
async def analyze_wash_sales(portfolio_id: str, days_back: int = 60):
    """Analyze potential wash sale violations"""
    try:
        # Mock implementation
        wash_sale_analysis = {
            "analysis_id": f"wash-sale-{portfolio_id}-{datetime.now().timestamp()}",
            "portfolio_id": portfolio_id,
            "analysis_date": datetime.now().isoformat(),
            "lookback_period": days_back,
            "wash_sale_violations": [],
            "potential_violations": [
                {
                    "violation_id": f"violation-1-{datetime.now().timestamp()}",
                    "asset_sold": "NFLX",
                    "asset_purchased": "DIS",
                    "sale_date": "2024-08-15",
                    "purchase_date": "2024-08-20",
                    "days_between": 5,
                    "similarity_score": 0.78,
                    "violation_type": "SUBSTANTIALLY_IDENTICAL",
                    "recommended_action": "AVOID_PURCHASE"
                }
            ],
            "safe_harvesting_periods": [
                {
                    "asset_id": "PYPL",
                    "last_sale_date": "2024-07-01",
                    "safe_harvest_date": "2024-08-01",
                    "days_remaining": 0
                },
                {
                    "asset_id": "TSLA",
                    "last_sale_date": "2024-08-10",
                    "safe_harvest_date": "2024-09-10",
                    "days_remaining": 20
                }
            ],
            "replacement_recommendations": [
                {
                    "original_asset": "NFLX",
                    "recommended_replacements": [
                        {
                            "asset_id": "DIS",
                            "correlation": 0.78,
                            "wash_sale_risk": "HIGH",
                            "alternative": "CMCSA"
                        },
                        {
                            "asset_id": "CMCSA",
                            "correlation": 0.65,
                            "wash_sale_risk": "LOW",
                            "alternative": "VIAC"
                        }
                    ]
                }
            ],
            "compliance_summary": {
                "total_violations": 0,
                "potential_violations": 1,
                "compliance_score": 0.95,
                "recommended_actions": [
                    "Avoid purchasing DIS within 30 days of selling NFLX",
                    "Consider CMCSA as alternative to NFLX"
                ]
            }
        }
        
        return {
            "success": True,
            "wash_sale_analysis": wash_sale_analysis,
            "message": "Wash sale analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Error analyzing wash sales: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{portfolio_id}/tax-efficiency", response_model=Dict[str, Any])
async def calculate_tax_efficiency(portfolio_id: str):
    """Calculate portfolio tax efficiency metrics"""
    try:
        # Mock implementation
        tax_efficiency = {
            "portfolio_id": portfolio_id,
            "calculation_date": datetime.now().isoformat(),
            "tax_efficiency_score": 0.82,
            "tax_metrics": {
                "total_unrealized_gains": 15000.0,
                "total_unrealized_losses": -5000.0,
                "net_unrealized_gains": 10000.0,
                "deferred_tax_liability": 2000.0,
                "immediate_tax_benefits": 1000.0,
                "tax_loss_harvesting_potential": 5000.0
            },
            "tax_optimization_opportunities": [
                {
                    "opportunity_type": "TAX_LOSS_HARVESTING",
                    "asset_id": "PYPL",
                    "unrealized_loss": -3500.0,
                    "tax_benefit": 700.0,
                    "priority": "HIGH"
                },
                {
                    "opportunity_type": "LOT_OPTIMIZATION",
                    "asset_id": "AAPL",
                    "potential_savings": 200.0,
                    "priority": "MEDIUM"
                }
            ],
            "historical_tax_performance": {
                "ytd_tax_cost": 2500.0,
                "ytd_tax_benefits": 1200.0,
                "net_tax_impact": -1300.0,
                "tax_efficiency_trend": "IMPROVING"
            },
            "recommendations": [
                "Harvest losses in PYPL position",
                "Optimize tax lot selection for AAPL sales",
                "Consider tax-efficient fund alternatives"
            ]
        }
        
        return {
            "success": True,
            "tax_efficiency": tax_efficiency,
            "message": "Tax efficiency analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating tax efficiency: {e}")
        raise HTTPException(status_code=500, detail=str(e))












