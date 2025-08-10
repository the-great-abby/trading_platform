#!/usr/bin/env python3
"""
Test script to verify new strategies are accessible in the dashboard
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_dashboard_strategies():
    """Test if new strategies are accessible in the dashboard"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🌐 Navigating to trading dashboard...")
            await page.goto("http://localhost:11115/")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            print("✅ Page loaded successfully")
            
            # Click on Backtesting tab
            print("📊 Clicking Backtesting tab...")
            await page.click('text=Backtesting')
            
            # Wait for backtesting content to load
            await page.wait_for_selector('#backtesting', timeout=10000)
            print("✅ Backtesting tab loaded")
            
            # Test different strategy categories
            categories_to_test = [
                ("🚀 Advanced Strategies", "advanced"),
                ("🌟 All Strategies", "all"),
                ("📊 Basic Strategies", "basic")
            ]
            
            new_strategies = [
                "RiskFirstStrategy",
                "MarketRegimeAdaptiveStrategy", 
                "MultiTimeframeStrategy"
            ]
            
            for button_text, category in categories_to_test:
                print(f"\n🔍 Testing {button_text}...")
                
                try:
                    # Click the category button
                    await page.click(f'text="{button_text}"')
                    await page.wait_for_timeout(1000)
                    
                    # Check if new strategies are visible
                    found_strategies = []
                    for strategy in new_strategies:
                        try:
                            # Look for the strategy in the page
                            element = await page.wait_for_selector(f'text="{strategy}"', timeout=3000)
                            if element:
                                found_strategies.append(strategy)
                                print(f"  ✅ Found: {strategy}")
                        except:
                            print(f"  ❌ Not found: {strategy}")
                    
                    if found_strategies:
                        print(f"🎉 Success! Found {len(found_strategies)} new strategies in {category}")
                        return True
                    else:
                        print(f"⚠️ No new strategies found in {category}")
                        
                except Exception as e:
                    print(f"❌ Error testing {category}: {e}")
            
            # Try browser console method
            print("\n🔧 Testing browser console method...")
            try:
                await page.evaluate("selectCategory('new')")
                await page.wait_for_timeout(1000)
                
                # Check if new strategies appeared
                for strategy in new_strategies:
                    try:
                        element = await page.wait_for_selector(f'text="{strategy}"', timeout=3000)
                        if element:
                            print(f"  ✅ Console method found: {strategy}")
                    except:
                        print(f"  ❌ Console method failed for: {strategy}")
                        
            except Exception as e:
                print(f"❌ Console method error: {e}")
            
            return False
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            return False
        finally:
            await browser.close()

async def main():
    """Main test function"""
    print("🚀 Starting Playwright strategy test...")
    
    result = await test_dashboard_strategies()
    
    if result:
        print("\n🎉 SUCCESS: New strategies are accessible!")
    else:
        print("\n❌ FAILURE: New strategies are not accessible")
    
    print("\n📋 Summary:")
    print("- Visit: http://localhost:11115/")
    print("- Click: Backtesting tab")
    print("- Try: Advanced Strategies or All Strategies buttons")
    print("- Or use browser console: selectCategory('new')")

if __name__ == "__main__":
    asyncio.run(main()) 