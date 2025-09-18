
import asyncio

from strands.models import BedrockModel
from strands import Agent
from strands_tools.a2a_client import A2AClientToolProvider

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# initialize collection of A2A tools for the agent
provider = A2AClientToolProvider(known_agent_urls=["http://localhost:9000"])

# initialize agent with tools
agent = Agent(
    model=bedrock_model,
    tools=provider.tools
    )

# run the agent in an async context
async def main():
    await agent.invoke_async(
        "pick an agent and make a sample call to test its functionality"
    )

if __name__ == "__main__":
    asyncio.run(main())