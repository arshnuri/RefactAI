#!/usr/bin/env python
"""
RefactAI Simple Git Pre-Push Hook - Minimal version that actually works
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Simple hook that just allows pushes to go through"""
    print("RefactAI Git Hook: Allowing push to proceed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
