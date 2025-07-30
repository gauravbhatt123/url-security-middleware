#!/usr/bin/env python3
"""
Simple test script to verify GUI functionality
"""

import os
import sys
import subprocess
import time

def test_proxy_executable():
    """Test if proxy executable exists and can be started"""
    proxy_path = os.path.abspath("../proxy/proxy_server")
    
    print(f"Checking proxy executable: {proxy_path}")
    
    if not os.path.exists(proxy_path):
        print("❌ Proxy executable not found!")
        print("Please compile the proxy first:")
        print("cd ../proxy && gcc EntryClient.c FetchServer.c Cache.c CallDns.c ClientToServer.c CacheData.c MitmCert.c -o proxy_server -lssl -lcrypto -lpthread")
        return False
    
    print("✅ Proxy executable found")
    
    # Test if it can be started
    try:
        process = subprocess.Popen(
            [proxy_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(proxy_path)
        )
        
        # Wait a moment for startup
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Proxy can be started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            print("❌ Proxy failed to start")
            output = process.stdout.read()
            print(f"Output: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting proxy: {e}")
        return False

def test_gui_imports():
    """Test if GUI dependencies are available"""
    print("\nTesting GUI dependencies...")
    
    try:
        import tkinter
        print("✅ tkinter available")
    except ImportError:
        print("❌ tkinter not available")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib available")
    except ImportError:
        print("❌ matplotlib not available")
        return False
    
    try:
        import requests
        print("✅ requests available")
    except ImportError:
        print("⚠️  requests not available (optional)")
    
    return True

def main():
    print("🔍 Testing GUI Setup...\n")
    
    # Test proxy executable
    proxy_ok = test_proxy_executable()
    
    # Test GUI dependencies
    gui_ok = test_gui_imports()
    
    print("\n" + "="*50)
    if proxy_ok and gui_ok:
        print("✅ All tests passed! GUI should work correctly.")
        print("\nTo start the GUI:")
        print("cd gui && python gui.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    print("\nGUI Features:")
    print("- Start/Stop proxy server")
    print("- Real-time log monitoring")
    print("- Cache state visualization")
    print("- Send test requests")
    print("- Latency plotting")

if __name__ == "__main__":
    main() 