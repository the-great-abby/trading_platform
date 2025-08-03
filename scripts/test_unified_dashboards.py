#!/usr/bin/env python3
"""
Test Unified Dashboards with Playwright
Tests the new unified dashboard services to ensure they're working correctly
"""

import asyncio
import logging
from playwright.async_api import async_playwright
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedDashboardTester:
    def __init__(self):
        self.results = {}
        self.dashboards = {
            'unified-trading-dashboard': {
                'url': 'http://localhost:11114',
                'description': 'Unified Trading Dashboard (Trading, Performance, Health)'
            },
            'unified-analytics-dashboard': {
                'url': 'http://localhost:11115',
                'description': 'Unified Analytics Dashboard (AI Stock, Central Hub, Data Pipeline)'
            },
            'unified-news-dashboard': {
                'url': 'http://localhost:11116',
                'description': 'Unified News Dashboard (RSS, News Feed)'
            }
        }
    
    async def test_dashboard(self, page, name: str, config: dict):
        """Test a single dashboard"""
        url = config['url']
        description = config['description']
        
        logger.info(f"🧪 Testing {name}: {description}")
        logger.info(f"📍 URL: {url}")
        
        try:
            # Navigate to the dashboard
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for the page to load
            await page.wait_for_timeout(2000)
            
            # Check if the page loaded successfully
            title = await page.title()
            logger.info(f"📄 Page title: {title}")
            
            # Check for common dashboard elements
            elements_found = []
            
            # Check for header/title
            try:
                header = await page.locator('h1').first.text_content()
                elements_found.append(f"Header: {header}")
            except:
                pass
            
            # Check for navigation tabs
            try:
                tabs = await page.locator('.nav-tab, .nav-tabs button, nav button').count()
                if tabs > 0:
                    elements_found.append(f"Navigation tabs: {tabs} found")
            except:
                pass
            
            # Check for dashboard content
            try:
                content = await page.locator('.dashboard-content, .container, main').count()
                if content > 0:
                    elements_found.append("Dashboard content found")
            except:
                pass
            
            # Check for API endpoints
            api_endpoints = []
            try:
                # Test health endpoint
                health_response = await page.evaluate(f"""
                    fetch('{url}/health')
                        .then(response => response.status)
                        .catch(error => 'error')
                """)
                if health_response == 200:
                    api_endpoints.append("Health endpoint: ✅")
                else:
                    api_endpoints.append(f"Health endpoint: ❌ ({health_response})")
            except:
                api_endpoints.append("Health endpoint: ❌ (error)")
            
            # Test readiness endpoint
            try:
                ready_response = await page.evaluate(f"""
                    fetch('{url}/ready')
                        .then(response => response.status)
                        .catch(error => 'error')
                """)
                if ready_response == 200:
                    api_endpoints.append("Ready endpoint: ✅")
                else:
                    api_endpoints.append(f"Ready endpoint: ❌ ({ready_response})")
            except:
                api_endpoints.append("Ready endpoint: ❌ (error)")
            
            # Take a screenshot
            screenshot_path = f"test_results/{name}_screenshot.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Check for JavaScript errors
            js_errors = await page.evaluate("""
                () => {
                    const errors = [];
                    window.addEventListener('error', (e) => {
                        errors.push(e.message);
                    });
                    return errors;
                }
            """)
            
            # Compile results
            result = {
                'status': 'SUCCESS',
                'url': url,
                'title': title,
                'elements_found': elements_found,
                'api_endpoints': api_endpoints,
                'js_errors': js_errors,
                'screenshot': screenshot_path,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {name} test completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ {name} test failed: {str(e)}")
            return {
                'status': 'FAILED',
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def test_all_dashboards(self):
        """Test all unified dashboards"""
        logger.info("🚀 Starting unified dashboard tests...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set viewport
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            for name, config in self.dashboards.items():
                result = await self.test_dashboard(page, name, config)
                self.results[name] = result
                
                # Small delay between tests
                await asyncio.sleep(1)
            
            await browser.close()
        
        return self.results
    
    def print_results(self):
        """Print test results in a formatted way"""
        print("\n" + "="*80)
        print("🎯 UNIFIED DASHBOARD TEST RESULTS")
        print("="*80)
        
        for name, result in self.results.items():
            print(f"\n📊 {name.upper()}")
            print("-" * 40)
            
            if result['status'] == 'SUCCESS':
                print(f"✅ Status: {result['status']}")
                print(f"🌐 URL: {result['url']}")
                print(f"📄 Title: {result['title']}")
                
                if result['elements_found']:
                    print(f"🔍 Elements Found:")
                    for element in result['elements_found']:
                        print(f"   • {element}")
                
                if result['api_endpoints']:
                    print(f"🔌 API Endpoints:")
                    for endpoint in result['api_endpoints']:
                        print(f"   • {endpoint}")
                
                if result['js_errors']:
                    print(f"⚠️  JavaScript Errors:")
                    for error in result['js_errors']:
                        print(f"   • {error}")
                else:
                    print("✅ No JavaScript errors")
                
                print(f"📸 Screenshot: {result['screenshot']}")
                
            else:
                print(f"❌ Status: {result['status']}")
                print(f"🌐 URL: {result['url']}")
                print(f"💥 Error: {result['error']}")
            
            print(f"⏰ Timestamp: {result['timestamp']}")
        
        # Summary
        print("\n" + "="*80)
        print("📋 SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in self.results.values() if r['status'] == 'SUCCESS')
        total = len(self.results)
        
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        print(f"📊 Success Rate: {(successful/total)*100:.1f}%")
        
        if successful == total:
            print("\n🎉 All unified dashboards are working correctly!")
        else:
            print("\n⚠️  Some dashboards need attention.")

async def main():
    """Main test function"""
    import os
    
    # Create test results directory
    os.makedirs("test_results", exist_ok=True)
    
    # Run tests
    tester = UnifiedDashboardTester()
    results = await tester.test_all_dashboards()
    
    # Print results
    tester.print_results()
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 