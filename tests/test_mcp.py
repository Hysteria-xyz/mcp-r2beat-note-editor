import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=str(r"C:\Users\Hysteria\OneDrive\Desktop\mcp r2beat\.venv\Scripts\python.exe"),
        args=["server.py"],
        cwd=r"C:\Users\Hysteria\OneDrive\Desktop\mcp r2beat",
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


asyncio.run(main())