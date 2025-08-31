#!/usr/bin/env python3
"""
Simple script to export all tools from flo_ai_tools to JSON format for Flo AI Studio.

This script automatically discovers all tools from __init__.py without requiring manual updates.
"""

from scripts.export_tools_dynamic import main

if __name__ == '__main__':
    main()
