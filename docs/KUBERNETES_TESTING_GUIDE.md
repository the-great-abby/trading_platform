# Kubernetes Testing Guide

This guide covers the comprehensive testing suite for your Kubernetes configuration and services in the trading system.

## 🎯 Overview

The Kubernetes testing suite provides three main categories of tests:

1. **Configuration Tests** - Validate Kubernetes resource configurations
2. **YAML Validation Tests** - Check YAML syntax and best practices
3. **Service Health Tests** - Test service connectivity and health endpoints

## 🚀 Quick Start

### Prerequisites

- `kubectl` configured and connected to your cluster
- `pytest` installed (`pip install -r requirements-kubernetes-tests.txt`)
- Access to the `trading-system` namespace

### Run All Tests

```bash
make k8s-test
```

### Run Specific Test Categories

```bash
# Configuration tests only
make k8s-test-config

# YAML validation tests only
make k8s-test-yaml

# Service health tests only
make k8s-test-health
```

### Run Tests Directly

```bash
# Run all tests
./scripts/run_kubernetes_tests.sh

# Run specific test type
./scripts/run_kubernetes_tests.sh config
./scripts/run_kubernetes_tests.sh yaml
./scripts/run_kubernetes_tests.sh health
```

## 📋 Test Categories

### 1. Configuration Tests (`test_kubernetes_configuration.py`)

Tests the actual Kubernetes cluster configuration:

- **Namespace Validation**: Ensures `trading-system` namespace exists
- **Secrets Validation**: Checks required secrets exist and have proper keys
- **ConfigMaps Validation**: Verifies required configmaps are present
- **Deployment Validation**: Tests deployment configurations
- **Service Validation**: Validates service configurations
- **Resource Limits**: Ensures proper resource requests/limits
- **Health Checks**: Validates liveness and readiness probes
- **Environment Variables**: Checks environment variable configuration

### 2. YAML Validation Tests (`test_kubernetes_yaml_validation.py`)

Tests Kubernetes YAML files for syntax and best practices:

- **YAML Syntax**: Validates YAML syntax and structure
- **Resource Definitions**: Ensures proper Kubernetes resource definitions
- **Best Practices**: Checks for resource limits, health checks, selectors
- **Consistency**: Validates namespace and label consistency
- **Port Configuration**: Ensures proper port ranges and protocols
- **Resource Validation**: Validates CPU and memory specifications

### 3. Service Health Tests (`test_kubernetes_service_health.py`)

Tests actual service connectivity and health:

- **Pod Status**: Verifies all pods are running and ready
- **Deployment Status**: Checks deployment availability and updates
- **Service Connectivity**: Tests service health endpoints
- **Port Forwarding**: Sets up port forwards for testing
- **Health Endpoints**: Tests `/health` and `/ready` endpoints
- **Dependency Access**: Validates secret and configmap access

## 🔧 Test Configuration

### Test Environment

Tests run against your local Kubernetes cluster (Docker Desktop, minikube, etc.) and validate:

- **Namespace**: `trading-system`
- **Services**: All deployed services in the namespace
- **Port Ranges**: Uses project-specific port ranges (11000-11999)
- **Registry**: Validates localhost:32000 image usage

### Test Reports

All tests generate HTML reports in the `test_reports/` directory:

- `kubernetes_config_YYYYMMDD_HHMMSS.html`
- `kubernetes_yaml_YYYYMMDD_HHMMSS.html`
- `kubernetes_health_YYYYMMDD_HHMMSS.html`
- `kubernetes_all_YYYYMMDD_HHMMSS.html`

## 📊 Test Coverage

### What Gets Tested

✅ **Kubernetes Resources**
- Deployments, Services, ConfigMaps, Secrets
- Pod templates and container specifications
- Resource limits and requests
- Health checks and probes

✅ **Configuration Validation**
- YAML syntax and structure
- Required fields and metadata
- Label and annotation consistency
- Namespace validation

✅ **Service Health**
- Pod status and readiness
- Service connectivity
- Health endpoint responses
- Resource utilization

✅ **Best Practices**
- Resource limits defined
- Health checks configured
- Proper selectors
- Image pull policies

### What's NOT Tested

❌ **External Dependencies**
- Database connectivity (only validates configuration)
- External API endpoints
- Network policies and security
- Cluster-level resources

❌ **Performance Testing**
- Load testing
- Stress testing
- Performance benchmarks
- Resource scaling

## 🛠️ Customization

### Adding New Tests

1. **Create test file**: `tests/test_kubernetes_<category>.py`
2. **Follow naming convention**: `TestKubernetes<Category>`
3. **Use fixtures**: Leverage existing test fixtures
4. **Add to runner**: Update `scripts/run_kubernetes_tests.sh`

### Example Test Structure

```python
class TestKubernetesCustomFeature:
    """Test custom Kubernetes feature"""
    
    def test_custom_feature(self, k8s_tester):
        """Test custom feature functionality"""
        # Your test logic here
        assert True
```

### Custom Test Categories

To add new test categories:

1. Add test file to `tests/` directory
2. Update `scripts/run_kubernetes_tests.sh`
3. Add Makefile targets in `Makefile.simple`
4. Update this documentation

## 🚨 Troubleshooting

### Common Issues

#### kubectl not found
```bash
# Install kubectl
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

#### Cannot connect to cluster
```bash
# Check cluster status
kubectl cluster-info

# Check context
kubectl config current-context

# List contexts
kubectl config get-contexts
```

#### Tests fail with permission errors
```bash
# Check namespace access
kubectl get pods -n trading-system

# Check RBAC permissions
kubectl auth can-i get pods -n trading-system
```

#### Port forwarding fails
```bash
# Check if ports are in use
lsof -i :11113
lsof -i :11114
lsof -i :11115

# Kill existing port forwards
pkill -f "kubectl port-forward"
```

### Debug Mode

Run tests with verbose output:

```bash
# Verbose pytest output
pytest tests/test_kubernetes_configuration.py -v -s

# Debug script execution
bash -x scripts/run_kubernetes_tests.sh config
```

## 📈 Continuous Integration

### GitHub Actions Integration

Add to your `.github/workflows/kubernetes-tests.yml`:

```yaml
name: Kubernetes Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-kubernetes-tests.txt
      - name: Run tests
        run: |
          pytest tests/test_kubernetes_*.py --html=test_reports/ci_report.html
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_reports/
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: kubernetes-tests
        name: Kubernetes Tests
        entry: make k8s-test-yaml
        language: system
        pass_filenames: false
        always_run: true
```

## 🔍 Monitoring and Maintenance

### Regular Testing Schedule

- **Daily**: Run health tests during development
- **Weekly**: Run full test suite
- **Before Deployments**: Run all tests
- **After Changes**: Run relevant test categories

### Test Maintenance

- **Update Tests**: When Kubernetes resources change
- **Review Reports**: Analyze test failures and trends
- **Optimize**: Remove obsolete tests, add new coverage
- **Document**: Keep this guide updated

### Performance Monitoring

Monitor test execution time and optimize:

```bash
# Run with timing
pytest tests/test_kubernetes_*.py --durations=10

# Parallel execution
pytest tests/test_kubernetes_*.py -n auto
```

## 📚 Additional Resources

### Documentation
- [Kubernetes Testing Best Practices](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Kubernetes YAML Reference](https://kubernetes.io/docs/reference/kubernetes-api/)

### Tools
- [kubeval](https://github.com/instrumenta/kubeval) - YAML validation
- [kube-score](https://github.com/zegl/kube-score) - Best practices scoring
- [kubeconform](https://github.com/yannh/kubeconform) - Schema validation

### Community
- [Kubernetes Slack](https://slack.k8s.io/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/kubernetes)
- [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/)

## 🎉 Getting Help

### Support Channels

1. **Check this guide** for common solutions
2. **Run tests with debug** for detailed error information
3. **Review test reports** for specific failure details
4. **Check cluster status** with kubectl commands

### Contributing

To improve the testing suite:

1. **Report Issues**: Document test failures and edge cases
2. **Suggest Improvements**: Propose new test categories or validations
3. **Submit PRs**: Contribute test enhancements
4. **Update Documentation**: Keep this guide current

---

**Happy Testing! 🧪✨**

Your Kubernetes configuration is now thoroughly validated and monitored.



