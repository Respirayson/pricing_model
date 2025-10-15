#!/usr/bin/env python3
"""
Complete environment setup script for the pricing agent.
This script sets up everything needed to run the pricing agent.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_environment():
    """Set up the complete environment."""
    print("🚀 Setting up Pricing Agent Environment")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Not in a virtual environment - consider using one")
    
    python_cmd = sys.executable
    
    # Install/upgrade pip
    if not run_command(f"{python_cmd} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{python_cmd} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Install the package in development mode
    if not run_command(f"{python_cmd} -m pip install -e .", "Installing pricing-agent package"):
        return False
    
    # Test imports
    print("\n🧪 Testing imports...")
    try:
        import pricing_agent
        import openai
        import requests
        from bs4 import BeautifulSoup
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Check API key
    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        print(f"✅ API key found: {api_key[:10]}...")
    else:
        print("⚠️  No API key found - set LLM_API_KEY environment variable")
        print("   export LLM_API_KEY='your-openai-api-key'")
    
    # Test CLI
    print("\n🧪 Testing CLI...")
    try:
        from pricing_agent.cli import cli
        print("✅ CLI import successful")
    except Exception as e:
        print(f"❌ CLI import failed: {e}")
        return False
    
    # Check repo_docs
    repo_docs = Path("repo_docs")
    if repo_docs.exists():
        files = list(repo_docs.glob("*.md"))
        print(f"✅ Found {len(files)} documents in repo_docs/")
    else:
        print("⚠️  repo_docs directory not found")
    
    print("\n🎉 Environment setup complete!")
    print("\nNext steps:")
    print("1. Set your API key: export LLM_API_KEY='your-key'")
    print("2. Scrape more data: python -m pricing_agent.cli scrape-web")
    print("3. Run pipeline: python -m pricing_agent.cli run-pipeline ./repo_docs evidence.json bench.json")
    print("4. Estimate prices: python -m pricing_agent.cli rule-estimate bench.json")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)
