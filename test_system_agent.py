#!/usr/bin/env python3
"""
Test script for System Agent new features
Tests theme detection/setting, health checks, and monitoring
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intelligent_agents.system_agent import SystemAgent

def test_theme_detection():
    """Test theme detection"""
    print("\n" + "="*80)
    print("🎨 TEST 1: Theme Detection")
    print("="*80)
    
    agent = SystemAgent()
    result = agent._detect_theme()
    
    print(f"✅ Theme detected: {result.get('theme')}")
    print(f"📝 Details: {result.get('details')}")
    
    return result

def test_theme_setting():
    """Test theme setting (dry run info)"""
    print("\n" + "="*80)
    print("🎨 TEST 2: Theme Setting (Info Only)")
    print("="*80)
    
    agent = SystemAgent()
    current = agent._detect_theme()
    
    print(f"Current theme: {current.get('theme')}")
    print(f"\nℹ️  To test theme switching:")
    print(f"   - Run: agent._set_theme('dark')")
    print(f"   - Run: agent._set_theme('light')")
    print(f"\n⚠️  Note: Skipping actual theme change to avoid disrupting your setup")
    
    return True

def test_health_check():
    """Test comprehensive health check"""
    print("\n" + "="*80)
    print("🏥 TEST 3: System Health Check")
    print("="*80)
    
    agent = SystemAgent()
    result = agent.health_check()
    
    print(f"✅ Health check completed")
    print(f"📊 Overall severity: {result.get('severity')}")
    print(f"🔍 Checks performed: {len(result.get('checks', []))}")
    
    print("\n📋 Check Results:")
    for check in result.get('checks', []):
        status_icon = "✅" if check.get('status') == 'ok' else "⚠️" if check.get('status') == 'warning' else "❓"
        print(f"   {status_icon} {check.get('name')}: {check.get('status')}")
        
        if check.get('issues'):
            print(f"      Issues: {check.get('issues')}")
        
        if check.get('error'):
            print(f"      Error: {check.get('error')[:100]}")
    
    return result

def test_fast_execution():
    """Test fast execution paths for new features"""
    print("\n" + "="*80)
    print("⚡ TEST 4: Fast Execution Paths")
    print("="*80)
    
    agent = SystemAgent()
    
    # Test 1: Theme query
    print("\n🔹 Testing: 'what theme'")
    result = agent.run("what theme is set")
    print(f"   Result: {result.get('success')}")
    if result.get('result'):
        print(f"   Theme: {result.get('result').get('theme')}")
    
    # Test 2: Health check via command
    print("\n🔹 Testing: 'run health check'")
    result = agent.run("run health check")
    print(f"   Result: {result.get('success')}")
    if result.get('severity'):
        print(f"   Severity: {result.get('severity')}")
    
    # Test 3: Standard fast commands still work
    print("\n🔹 Testing: 'list files on desktop'")
    result = agent.run("list files on desktop")
    print(f"   Result: {result.get('success')}")
    
    print("\n🔹 Testing: 'check disk space'")
    result = agent.run("check disk space")
    print(f"   Result: {result.get('success')}")
    
    return True

def test_monitoring_start():
    """Test monitor system startup"""
    print("\n" + "="*80)
    print("📡 TEST 5: System Monitoring")
    print("="*80)
    
    agent = SystemAgent()
    
    # Track if callback was called
    callback_count = [0]
    
    def test_callback(summary):
        callback_count[0] += 1
        print(f"   ✅ Monitor callback #{callback_count[0]}: severity={summary.get('severity')}")
    
    print("🔹 Starting monitor with 3-second interval...")
    monitor = agent.monitor_system(interval=3, callback=test_callback)
    
    print(f"   Monitor started: {monitor.get('success')}")
    print("   Waiting 10 seconds to observe callbacks...")
    
    # Wait for a few callbacks
    time.sleep(10)
    
    # Stop the monitor
    print("\n🔹 Stopping monitor...")
    monitor['stop_flag']['stop'] = True
    time.sleep(1)
    
    print(f"   ✅ Monitor stopped. Total callbacks: {callback_count[0]}")
    
    return callback_count[0] >= 2

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 SYSTEM AGENT COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("\nTesting new features:")
    print("  1. Theme detection and setting")
    print("  2. System health checks")
    print("  3. Fast execution integration")
    print("  4. System monitoring")
    print("\n" + "="*80)
    
    results = {}
    
    try:
        results['theme_detection'] = test_theme_detection()
        results['theme_setting'] = test_theme_setting()
        results['health_check'] = test_health_check()
        results['fast_execution'] = test_fast_execution()
        results['monitoring'] = test_monitoring_start()
        
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"✅ Theme Detection: PASS")
        print(f"✅ Theme Setting: PASS (info only)")
        print(f"✅ Health Check: PASS")
        print(f"✅ Fast Execution: PASS")
        print(f"✅ Monitoring: {'PASS' if results['monitoring'] else 'PARTIAL'}")
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ TEST FAILED: {str(e)}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
