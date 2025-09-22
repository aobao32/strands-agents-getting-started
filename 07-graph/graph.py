import logging
from strands import Agent
from strands.multiagent import GraphBuilder
from strands.models import BedrockModel

# Enable debug logs and print them to stderr
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Create specialized agents
researcher = Agent(name="researcher", model=bedrock_model, system_prompt="You are a research specialist...")
analyst = Agent(name="analyst", model=bedrock_model, system_prompt="You are a data analysis specialist...")
fact_checker = Agent(name="fact_checker", model=bedrock_model, system_prompt="You are a fact checking specialist...")
report_writer = Agent(name="report_writer", model=bedrock_model, system_prompt="You are a report writing specialist...")

# Build the graph
builder = GraphBuilder()

# 添加所有Agent节点
builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(fact_checker, "fact_check")
builder.add_node(report_writer, "report")

# 设置两两之间的关系
# entry point是research agent，然后分别交给analysis和fact_check
builder.add_edge("research", "analysis")
builder.add_edge("research", "fact_check")

# 在analysis和fact_check分别执行完毕后，结果汇总到report
builder.add_edge("analysis", "report")
builder.add_edge("fact_check", "report")

# Set entry points (optional - will be auto-detected if not specified)
builder.set_entry_point("research")

# Optional: Configure execution limits for safety
builder.set_execution_timeout(900)   # 10 minute timeout
builder.set_node_timeout(600)

# Build the graph
graph = builder.build()

# Execute the graph on a task
result = graph("Research the impact of AI on healthcare and create a comprehensive report")

# Access the results
print(f"\nStatus: {result.status}")
print(f"Execution order: {[node.node_id for node in result.execution_order]}")