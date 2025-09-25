/**
 * Portfolio Analytics Integration for Unified Analytics Dashboard
 * Advanced portfolio management analytics and visualizations
 */

// Portfolio Analytics Module
class PortfolioAnalytics {
    constructor(apiBaseUrl = 'http://localhost:11180') {
        this.apiBaseUrl = apiBaseUrl;
        this.riskApiBaseUrl = 'http://localhost:11181';
        this.charts = {};
        this.data = {};
        this.refreshInterval = null;
    }

    /**
     * Initialize portfolio analytics
     */
    async init() {
        try {
            console.log('🚀 Initializing Portfolio Analytics...');
            
            // Check if portfolio services are available
            await this.checkServicesHealth();
            
            // Load initial data
            await this.loadPortfolioData();
            
            // Initialize charts
            await this.initializeCharts();
            
            // Set up real-time updates
            this.setupRealTimeUpdates();
            
            console.log('✅ Portfolio Analytics initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing Portfolio Analytics:', error);
            this.showError('Failed to initialize portfolio analytics');
        }
    }

    /**
     * Check health of portfolio services
     */
    async checkServicesHealth() {
        try {
            const [portfolioHealth, riskHealth] = await Promise.all([
                fetch(`${this.apiBaseUrl}/health`).then(r => r.json()),
                fetch(`${this.riskApiBaseUrl}/health`).then(r => r.json())
            ]);

            if (!portfolioHealth.status || !riskHealth.status) {
                throw new Error('Portfolio services are not healthy');
            }

            console.log('✅ Portfolio services are healthy');
        } catch (error) {
            console.warn('⚠️ Portfolio services health check failed:', error);
            throw error;
        }
    }

    /**
     * Load portfolio data
     */
    async loadPortfolioData() {
        try {
            // Load portfolios
            const portfolios = await this.fetchPortfolios();
            this.data.portfolios = portfolios;

            // Load risk metrics
            const riskMetrics = await this.fetchRiskMetrics();
            this.data.riskMetrics = riskMetrics;

            // Load optimization results
            const optimizationResults = await this.fetchOptimizationResults();
            this.data.optimizationResults = optimizationResults;

            console.log('📊 Portfolio data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading portfolio data:', error);
            throw error;
        }
    }

    /**
     * Fetch portfolios from API
     */
    async fetchPortfolios() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/portfolios`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching portfolios:', error);
            return [];
        }
    }

    /**
     * Fetch risk metrics from API
     */
    async fetchRiskMetrics() {
        try {
            const response = await fetch(`${this.riskApiBaseUrl}/api/v1/risk/metrics`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching risk metrics:', error);
            return [];
        }
    }

    /**
     * Fetch optimization results from API
     */
    async fetchOptimizationResults() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/optimization/results`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching optimization results:', error);
            return [];
        }
    }

    /**
     * Initialize charts
     */
    async initializeCharts() {
        // Portfolio Performance Chart
        this.initializePortfolioPerformanceChart();
        
        // Risk Metrics Chart
        this.initializeRiskMetricsChart();
        
        // Asset Allocation Chart
        this.initializeAssetAllocationChart();
        
        // Optimization Results Chart
        this.initializeOptimizationResultsChart();
        
        // Correlation Matrix Chart
        this.initializeCorrelationMatrixChart();
    }

    /**
     * Initialize portfolio performance chart
     */
    initializePortfolioPerformanceChart() {
        const ctx = document.getElementById('portfolioPerformanceChart');
        if (!ctx) return;

        this.charts.portfolioPerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }, {
                    label: 'Benchmark (SPY)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Portfolio Performance vs Benchmark'
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Value ($)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize risk metrics chart
     */
    initializeRiskMetricsChart() {
        const ctx = document.getElementById('riskMetricsChart');
        if (!ctx) return;

        this.charts.riskMetrics = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['VaR 95%', 'VaR 99%', 'CVaR 95%', 'CVaR 99%', 'Max Drawdown', 'Volatility'],
                datasets: [{
                    label: 'Risk Metrics',
                    data: [],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)',
                        'rgb(153, 102, 255)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Risk Metrics'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Risk Value (%)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize asset allocation chart
     */
    initializeAssetAllocationChart() {
        const ctx = document.getElementById('assetAllocationChart');
        if (!ctx) return;

        this.charts.assetAllocation = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF',
                        '#FF9F40',
                        '#FF6384',
                        '#C9CBCF'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Asset Allocation'
                    },
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    /**
     * Initialize optimization results chart
     */
    initializeOptimizationResultsChart() {
        const ctx = document.getElementById('optimizationResultsChart');
        if (!ctx) return;

        this.charts.optimizationResults = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Efficient Frontier',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    pointRadius: 4
                }, {
                    label: 'Current Portfolio',
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    pointRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Portfolio Optimization - Efficient Frontier'
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Risk (Volatility)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Expected Return'
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize correlation matrix chart
     */
    initializeCorrelationMatrixChart() {
        const ctx = document.getElementById('correlationMatrixChart');
        if (!ctx) return;

        this.charts.correlationMatrix = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Correlation',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Asset Correlation Matrix'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        min: -1,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Correlation Coefficient'
                        }
                    }
                }
            }
        });
    }

    /**
     * Update charts with new data
     */
    updateCharts() {
        // Update portfolio performance chart
        this.updatePortfolioPerformanceChart();
        
        // Update risk metrics chart
        this.updateRiskMetricsChart();
        
        // Update asset allocation chart
        this.updateAssetAllocationChart();
        
        // Update optimization results chart
        this.updateOptimizationResultsChart();
        
        // Update correlation matrix chart
        this.updateCorrelationMatrixChart();
    }

    /**
     * Update portfolio performance chart
     */
    updatePortfolioPerformanceChart() {
        if (!this.charts.portfolioPerformance || !this.data.portfolios) return;

        const portfolio = this.data.portfolios[0]; // Use first portfolio for demo
        if (!portfolio || !portfolio.performance_history) return;

        const history = portfolio.performance_history;
        const labels = history.map(h => new Date(h.date).toLocaleDateString());
        const portfolioValues = history.map(h => h.total_value);
        const benchmarkValues = history.map(h => h.benchmark_value);

        this.charts.portfolioPerformance.data.labels = labels;
        this.charts.portfolioPerformance.data.datasets[0].data = portfolioValues;
        this.charts.portfolioPerformance.data.datasets[1].data = benchmarkValues;
        this.charts.portfolioPerformance.update();
    }

    /**
     * Update risk metrics chart
     */
    updateRiskMetricsChart() {
        if (!this.charts.riskMetrics || !this.data.riskMetrics) return;

        const riskMetrics = this.data.riskMetrics[0]; // Use first risk metrics for demo
        if (!riskMetrics) return;

        const data = [
            Math.abs(riskMetrics.var_95) * 100,
            Math.abs(riskMetrics.var_99) * 100,
            Math.abs(riskMetrics.cvar_95) * 100,
            Math.abs(riskMetrics.cvar_99) * 100,
            riskMetrics.max_drawdown * 100,
            riskMetrics.portfolio_volatility * 100
        ];

        this.charts.riskMetrics.data.datasets[0].data = data;
        this.charts.riskMetrics.update();
    }

    /**
     * Update asset allocation chart
     */
    updateAssetAllocationChart() {
        if (!this.charts.assetAllocation || !this.data.portfolios) return;

        const portfolio = this.data.portfolios[0]; // Use first portfolio for demo
        if (!portfolio || !portfolio.positions) return;

        const labels = portfolio.positions.map(p => p.asset_id);
        const data = portfolio.positions.map(p => p.weight * 100);

        this.charts.assetAllocation.data.labels = labels;
        this.charts.assetAllocation.data.datasets[0].data = data;
        this.charts.assetAllocation.update();
    }

    /**
     * Update optimization results chart
     */
    updateOptimizationResultsChart() {
        if (!this.charts.optimizationResults || !this.data.optimizationResults) return;

        const optimization = this.data.optimizationResults[0]; // Use first optimization for demo
        if (!optimization || !optimization.efficient_frontier) return;

        const frontier = optimization.efficient_frontier;
        const frontierData = frontier.map(point => ({
            x: point.volatility * 100,
            y: point.expected_return * 100
        }));

        const currentPortfolio = {
            x: optimization.expected_volatility * 100,
            y: optimization.expected_return * 100
        };

        this.charts.optimizationResults.data.datasets[0].data = frontierData;
        this.charts.optimizationResults.data.datasets[1].data = [currentPortfolio];
        this.charts.optimizationResults.update();
    }

    /**
     * Update correlation matrix chart
     */
    updateCorrelationMatrixChart() {
        if (!this.charts.correlationMatrix || !this.data.portfolios) return;

        const portfolio = this.data.portfolios[0]; // Use first portfolio for demo
        if (!portfolio || !portfolio.correlation_matrix) return;

        const matrix = portfolio.correlation_matrix;
        const labels = Object.keys(matrix);
        const data = Object.values(matrix);

        this.charts.correlationMatrix.data.labels = labels;
        this.charts.correlationMatrix.data.datasets[0].data = data;
        this.charts.correlationMatrix.update();
    }

    /**
     * Set up real-time updates
     */
    setupRealTimeUpdates() {
        // Update every 5 minutes
        this.refreshInterval = setInterval(async () => {
            try {
                await this.loadPortfolioData();
                this.updateCharts();
                console.log('📊 Portfolio data refreshed');
            } catch (error) {
                console.error('❌ Error refreshing portfolio data:', error);
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    /**
     * Show error message
     */
    showError(message) {
        // Create or update error message element
        let errorElement = document.getElementById('portfolioError');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'portfolioError';
            errorElement.className = 'alert alert-danger';
            errorElement.style.margin = '10px';
            document.body.insertBefore(errorElement, document.body.firstChild);
        }
        errorElement.textContent = `Portfolio Analytics Error: ${message}`;
        errorElement.style.display = 'block';
    }

    /**
     * Hide error message
     */
    hideError() {
        const errorElement = document.getElementById('portfolioError');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    /**
     * Destroy portfolio analytics
     */
    destroy() {
        // Clear refresh interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        // Clear data
        this.data = {};
        this.charts = {};

        console.log('🧹 Portfolio Analytics destroyed');
    }
}

// Export for use in other modules
window.PortfolioAnalytics = PortfolioAnalytics;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Check if we're on the analytics dashboard
    if (window.location.pathname.includes('/analytics') || 
        window.location.pathname.includes('/portfolio')) {
        
        // Initialize portfolio analytics
        const portfolioAnalytics = new PortfolioAnalytics();
        await portfolioAnalytics.init();
        
        // Make it globally available
        window.portfolioAnalytics = portfolioAnalytics;
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (window.portfolioAnalytics) {
        if (document.hidden) {
            // Page is hidden, pause updates
            if (window.portfolioAnalytics.refreshInterval) {
                clearInterval(window.portfolioAnalytics.refreshInterval);
                window.portfolioAnalytics.refreshInterval = null;
            }
        } else {
            // Page is visible, resume updates
            window.portfolioAnalytics.setupRealTimeUpdates();
        }
    }
});

