"""
Cloud Runner for GitHub Actions
===============================
This script is optimized for running the video pipeline in a headless
environment (GitHub Actions). It handles paths, logging, and error reporting.
"""

import sys
import os
import asyncio
import traceback

# Ensure the 'src' directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# Import the pipeline
from app import run_full_pipeline

async def run_bot():
    print("=" * 50)
    print("  🚀 WEBORAX CLOUD BOT RUNNER")
    print("=" * 50)
    
    # Check for critical files
    required_files = ["Client_secret.json", "youtube_token.pickle", ".env"]
    for f in required_files:
        if os.path.exists(f):
            print(f"[OK] Found {f}")
        else:
            print(f"[ERROR] Missing {f}! Did you add all GitHub Secrets?")
            # We don't exit here to let the pipeline handle specific missing config errors
            
    try:
        print("\nStarting video pipeline...")
        result = await run_full_pipeline(script_text=None, auto_upload=True)
        if isinstance(result, dict) and result.get("error"):
            print("\n" + "!" * 50)
            print("  ❌ PIPELINE COMPLETED WITH ERRORS")
            print("!" * 50)
            print(f"Error: {result.get('error')}")
            sys.exit(1)
        print("\n[SUCCESS] Pipeline completed successfully!")
    except Exception as e:
        print("\n" + "!" * 50)
        print("  ❌ PIPELINE FAILED")
        print("!" * 50)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("\nFull Traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_bot())
