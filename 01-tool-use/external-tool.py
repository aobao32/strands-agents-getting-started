from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters

# Define a naming-focused system prompt
NAMING_SYSTEM_PROMPT = """
你是一个域名起名和查询助手。我现在计划使用.com或者.net的域名。

现在为我选择5个和AI智能化相关的域名，用你的工具查询域名是否可用，如果可用的域名请告诉我，否则继续帮我想新的域名，直到找到5个可用的域名为止。
"""

# Load an MCP server that can determine if a domain name is available
domain_name_tools = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["fastdomaincheck-mcp-server"])
))

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

with domain_name_tools:
    # Define the naming agent with tools and a system prompt
    tools = domain_name_tools.list_tools_sync()
    naming_agent = Agent(
        model=bedrock_model,
        system_prompt=NAMING_SYSTEM_PROMPT,
        tools=tools
    )

    # Run the naming agent with the end user's prompt
    naming_agent("I need to name an open source project for building AI agents.")