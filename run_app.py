#!/usr/bin/env python3
"""
Launcher script for the Streamlit GPU Deal Finder app
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app"""
    print("🚀 Starting NaNo PC Parts - GPU Deal Finder Web App...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("streamlit_app.py"):
        print("❌ Error: streamlit_app.py not found!")
        print("Please run this script from the project directory.")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected!")
        print("It's recommended to activate your virtual environment first:")
        print("  source venv/bin/activate")
        print()
    
    try:
        # Launch Streamlit
        print("🌐 Launching web interface...")
        print("📱 The app will open in your default browser")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Streamlit is installed: pip install streamlit")
        print("2. Check if port 8501 is available")
        print("3. Try running: streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()
