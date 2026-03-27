"""python -m autoauthor — 기본 파이프라인 실행"""
import asyncio
from .pipeline import _cli_main

if __name__ == "__main__":
    asyncio.run(_cli_main())
