import os

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel

MCP_SERVER_URL = os.environ.get("MY_MCP_SERVER_URL", "http://localhost:8002/mcp/")

myhttp_mcp_client = MCPClient(lambda: streamablehttp_client(MCP_SERVER_URL))

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Create an agent with MCP tools
with myhttp_mcp_client:
    # Get the tools from the MCP server
    tools = myhttp_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(
        model=bedrock_model,
        tools=tools
        )
    
    agent("西雅图天气怎么样？")  # Example query about Seattle weather