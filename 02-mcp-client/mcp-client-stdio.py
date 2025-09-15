from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uv", 
        args=["run", "mcp-server-stdio.py"],
        transport="stdio",
        wait=True
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
    agent("西雅图天气怎么样？")  # Example query about Seattle weather