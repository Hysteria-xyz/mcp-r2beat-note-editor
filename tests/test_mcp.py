import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP_CLIENT = True
except ImportError:
    HAS_MCP_CLIENT = False


async def main():
    if not HAS_MCP_CLIENT:
        print("SKIP: 'mcp' client package not installed in current environment.")
        print("To run MCP client test: pip install mcp")
        return

    params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        cwd=str(ROOT_DIR),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("MCP OK - tools (%d):" % len(tools.tools))
            for t in tools.tools:
                print("  -", t.name)
            res = await session.call_tool(
                "create_chart",
                {"chart_id": "smoke", "name": "Smoke Test", "bpm": 175, "bgm": "x/x.mp3"},
            )
            data = res.content[0].text
            print("create_chart ->", data[:80], "...")


if __name__ == "__main__":
    asyncio.run(main())
