from strands import Agent, tool
from strands.models import BedrockModel

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Define a specialized system prompt
RESEARCH_ASSISTANT_PROMPT = """
你是个专业的研究助理，由于这是演示程序，我们不会连接到外部数据库或API，所以请基于你已有的知识进行回答。
"""

PRODUCT_RECOMMENDATION_PROMPT ="""
你是个专业的产品推荐助理。由于这是演示程序，我们不会连接到外部数据库或API，所以请基于你已有的知识进行回答。
"""

TRIP_PLANNING_PROMPT ="""
你是个专业的旅行规划助理。由于这是演示程序，我们不会连接到外部数据库或API，所以请基于你已有的知识进行回答。
"""

@tool
def research_assistant(query: str) -> str:
    """
    Process and respond to research-related queries.

    Args:
        query: A research question requiring factual information

    Returns:
        A detailed research answer with citations
    """
    try:
        # Strands Agents SDK makes it easy to create a specialized agent
        research_agent = Agent(
            model=bedrock_model,
            system_prompt=RESEARCH_ASSISTANT_PROMPT
        )
        response = research_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in research assistant: {str(e)}"

@tool
def product_recommendation_assistant(query: str) -> str:
    """
    Handle product recommendation queries by suggesting appropriate products.

    Args:
        query: A product inquiry with user preferences

    Returns:
        Personalized product recommendations with reasoning
    """
    try:
        product_agent = Agent(
            system_prompt=PRODUCT_RECOMMENDATION_PROMPT,
            model=bedrock_model
        )
        response = product_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in product recommendation: {str(e)}"

@tool
def trip_planning_assistant(query: str) -> str:
    """
    Create travel itineraries and provide travel advice.

    Args:
        query: A travel planning request with destination and preferences

    Returns:
        A detailed travel itinerary or travel advice
    """
    try:
        travel_agent = Agent(
            system_prompt=TRIP_PLANNING_PROMPT,
            model=bedrock_model
        )
        response = travel_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in trip planning: {str(e)}"