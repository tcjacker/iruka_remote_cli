#!/usr/bin/env python3
"""
Gemini CLI Docker Integration - Main Entry Point

This is the main entry point for the Gemini CLI Docker Integration system.
It starts the main service that manages Docker environments and routes requests.

Usage:
    python main.py [--port PORT] [--host HOST] [--debug]

Environment Variables:
    MAIN_SERVICE_PORT: Port to run the service on (default: 8081)
    MAIN_SERVICE_HOST: Host to bind to (default: 127.0.0.1)
    DEBUG: Enable debug mode (default: False)
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import load_env_file, get_config
from core.main_service import app, logger

def parse_args():
    """Parse command line arguments."""
    # Load environment variables first
    load_env_file()
    config = get_config()
    
    parser = argparse.ArgumentParser(
        description="Gemini CLI Docker Integration Main Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=config.MAIN_SERVICE_PORT,
        help=f'Port to run the service on (default: {config.MAIN_SERVICE_PORT})'
    )
    
    parser.add_argument(
        '--host', '-H',
        default=config.MAIN_SERVICE_HOST,
        help=f'Host to bind to (default: {config.MAIN_SERVICE_HOST})'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        default=config.DEBUG,
        help='Enable debug mode'
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    config = get_config()
    
    # Print startup banner
    print("🚀 Gemini CLI Docker Integration")
    print("=" * 40)
    print(f"🌐 Starting service on {args.host}:{args.port}")
    print(f"🐛 Debug mode: {'ON' if args.debug else 'OFF'}")
    print(f"📁 Project root: {project_root}")
    print("=" * 40)
    
    # Print configuration
    config.print_config()
    print("=" * 40)
    
    try:
        # Start the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
        print("\n👋 Service stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Service failed to start: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
