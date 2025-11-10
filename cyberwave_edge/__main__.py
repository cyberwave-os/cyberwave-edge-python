"""
Entry point for running cyberwave_edge as a module
"""

import asyncio

from .service import main

if __name__ == "__main__":
    asyncio.run(main())
