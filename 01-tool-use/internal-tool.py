from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

agent = Agent(
    model=bedrock_model,
    tools=[calculator]
    )

agent("What is the square root of 1764")