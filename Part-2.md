# Strands Agents SDK Getting Started 中篇 - 构建Agent & Agent as Tool

上一篇介绍了使用Strands Agents构建MCP之后，本篇进入A2A话题。

## 一、背景

### 1、什么是A2A

Agent-to-Agent (A2A) 协议是一种开发标准，允许使用不同框架、不同开发语言的Agent之间进行交互，而无须人为的编排或者把这些Agent嵌套。

在没有A2A协议之前，通常使用多个Agent时候，用户应用程序可能需要分别连接多个Agent，并人工组合、编排他们调用和依存性关系。这样带来开发的复杂度，如何选择封装和暴露方式、调用效率、响应延迟、扩展、交互性、安全方便都有不足。而使用A2A协议，用户所有的调用通过一个A2A Client（Client Agent）进行，更多提供服务的Agent作为A2A Server（Remote Agent）接受访问。使用A2A方式，整个应用程序在标准的Agent发现、认证、安全的管控体系下，Agent之间具有独立性、易于扩展、满足故障隔离，所有调用为一步调用，整个应用有良好的健壮性。

A2A的主要通信协议包括JSON-RPC、gRPC、HTTP+JSON/REST等，支持HTTPS、支持Streaming方式，支持进行扩展。

### 2、MCP和A2A

A2A协议与MCP协议分别在不同层面，分工不同，二者并无矛盾。MCP协议关注在使用LLM大语言模型构建一个Agent时候的Tool工具调用，它为单个Agent智能体内部的模型和工具之间的交互提供了规范的管道，允许大量第三方MCP Server作为工具被接入复用。由此，一个Agent智能体背后可能有多个MCP Server在支撑它的运行。与MCP不同，A2A协议关注Agent智能体之间的通信规范，多个Agent智能体组合在一起，如何互相发现、互相了解各自的能力（通过Agent Card等形式）。

这里用汽车售后维修系统举一个例子。客户请求来自与客户负责聊天对接的Agent，Agent分析客户的对话内容，判断需要与维修预约Agent、备件库存Agent、订单Agent三个Agent进行交互，分别沟通需要的信息，并最终完成客户需要内容的整理和输出。在个系统内部，几个Agent之间的交互是通过A2A协议完成的，而每个Agent还需要调用后台文档、知识库、数据库、存储、或者通过网络获取远端API信息时候，将通过Agent自身配置的MCP Server，以MCP协议获取交互数据。MCP协议返回数据给Agent后，本Agent进行汇总和理解，再通过A2A协议输出给其他Agent。

从以上的例子可以看出，A2A是Agent之间的通信规范，而MCP协议解决了在单个Agent内调用外部工具和资源的能力，二者互相配合构建多Agent架构。

### 3、Agent as Tool

当有多个Agent各自负责不同的业务逻辑、并相互通信时候，可以有多种架构组合方式。例如一种架构是以`Orchestrator`为核心的模式。与User直接交互的Agent叫做Client Agent，Client Agent通常只有1个，而被Client Agent调用的Agent叫做Remote Agent，它们可以有多个。在Client Agent与Remote Agent之间的调用就是A2A协议。

Client Agent作为主要的Agent，不仅仅是A2A中的Client，它也是具有大语言模型理解能力的。Client Agent作为`orchestrator`负责联系和调度其他Remote Agent，然后其他Remote Agent作为Specialized专门用途的`tool agents`。在这种架构下，搭建Client Agent时候，可以直接将其他Remote Agent的地址作为Tool直接配置到Client Agent上。这种配置方式就是`Agent as Tool`。

### 4、Multi-agent

与刚才的`Orchestrator`架构不同，完整的多Agent可被Multi-agent。它们之间通过A2A协议进行Agent之间的发现，获取各自Agent的能力范围和边界，并通过Graph、Swarm、Workflow等方式进行交互。这几种方式之间又有不同的应用场景，将在下文进行介绍。

下面开始准备演示代码。

## 二、构建Remote Agent接受Client Agent访问

本例使用 [Strands Agents官方sample代码库](https://github.com/strands-agents/samples/tree/main/03-integrations/Native-A2A-Support) 中的例子。

### 1、构建Remote Agent

和本文上篇中的初始化过程一样，这里也要初始化环境。

```shell
uv init 03-a2a-server-and-client
cd 03-a2a-server-and-client
uv venv
source .venv/bin/activate
uv add strands-agents strands-agents-tools
uv add strands-agents[a2a]
```

与之前仅使用MCP不同的是，这里初始化要额外增加A2A需要的依存库。

```shell
uv pip install 'strands-agents[a2a]'
```

将如下代码保存为`remote-agent.py`。内容如下。

```python
import logging
from strands.models import BedrockModel
from strands_tools.calculator import calculator
from strands import Agent
from strands.multiagent.a2a import A2AServer

logging.basicConfig(level=logging.INFO)

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Create a Strands agent
strands_agent = Agent(
    name="Calculator Agent",
    model=bedrock_model,
    description="A calculator agent that can perform basic arithmetic operations.",
    tools=[calculator],
    callback_handler=None
)

# Create A2A server (streaming enabled by default)
a2a_server = A2AServer(agent=strands_agent)

# Start the server
a2a_server.serve()
```

以上代码构建了一个以数学计算器为核心的智能体，使用Claude模型作为背后的LLM处理客户输入请求。运行这个Remote Agent。

```shell
uv run remote-agent.py
```

运行成功，控制台返回信息如下：

```shell
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:strands.multiagent.a2a.server:Strands' integration with A2A is experimental. Be aware of frequent breaking changes.
INFO:strands.multiagent.a2a.server:Starting Strands A2A server...
INFO:     Started server process [88487]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9000 (Press CTRL+C to quit)
```

不要关闭这个控制台窗口，保持其打开状态，新开一个控制台窗口，继续后续的操作。

### 2、使用A2A Native原生SDK作为Client并使用Streaming方式调用

由Strands Agents生成的Remote Agents（A2A Server）是遵循标准A2A协议的，因此可以使用任何支持A2A协议的客户端来访问。这里使用A2A社区官方的Python SDK，即`strands-agents-tools[a2a_client]`来测试。下面构建一个Streaming Client，使用Server-Sent Events (SSE)的方式连接到服务器。

进入与Server同一个目录下，创建`client-streaming.py`。内容如下。

```python
import asyncio
import logging
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300 # set request timeout to 5 minutes

def create_message(*, role: Role = Role.user, text: str) -> Message:
    return Message(
        kind="message",
        role=role,
        parts=[Part(TextPart(kind="text", text=text))],
        message_id=uuid4().hex,
    )

async def send_streaming_message(message: str, base_url: str = "http://127.0.0.1:9000"):
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as httpx_client:
        # Get agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()

        # Create client using factory
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=True,  # Use streaming mode
        )
        factory = ClientFactory(config)
        client = factory.create(agent_card)

        # Create and send message
        msg = create_message(text=message)

        async for event in client.send_message(msg):
            if isinstance(event, Message):
                logger.info(event.model_dump_json(exclude_none=True, indent=2))
            elif isinstance(event, tuple) and len(event) == 2:
                # (Task, UpdateEvent) tuple
                task, update_event = event
                logger.info(f"Task: {task.model_dump_json(exclude_none=True, indent=2)}")
                if update_event:
                    logger.info(f"Update: {update_event.model_dump_json(exclude_none=True, indent=2)}")
            else:
                # Fallback for other response types
                logger.info(f"Response: {str(event)}")

# Usage
asyncio.run(send_streaming_message("what is 101 * 11"))
```

本例Client的代码和作为Remote Agent的代码是在同一个目录下，因此先需要加载下uv的虚拟环境。由于使用的是A2A Native的SDK，因此要安装下`strands-agents-tools[a2a_client]`。最后执行`python client-agent.py`启动Client Agent。命令如下：

```shell
source .venv/bin/activate
uv pip install 'strands-agents-tools[a2a_client]'
python client-agent.py
```

运行后返回Streaming方式的输出，因为返回内容量较大，且streaming方式是分片的，这里就不再粘贴完整返回内容给了。片段如下：

```shell
{
      "contextId": "af752716-87e2-41cb-baf6-16c5a3f2af4c",
      "kind": "message",
      "messageId": "d8236a84-bd98-4c66-9ed8-fe5df5d2b32f",
      "parts": [
        {
          "kind": "text",
          "text": "by 11,"
        }
      ],
      "role": "agent",
      "taskId": "a4864472-12b7-4c98-9f72-64459e4d8f67"
    },
    {
      "contextId": "af752716-87e2-41cb-baf6-16c5a3f2af4c",
      "kind": "message",
      "messageId": "489ce201-f825-41ae-9d1c-10c87ce3469c",
      "parts": [
        {
          "kind": "text",
          "text": " you get the repe"
        }
      ],
      "role": "agent",
      "taskId": "a4864472-12b7-4c98-9f72-64459e4d8f67"
    },
    {
      "contextId": "af752716-87e2-41cb-baf6-16c5a3f2af4c",
      "kind": "message",
      "messageId": "810eadfb-90a8-4035-a393-b7c2041c3725",
      "parts": [
        {
          "kind": "text",
          "text": "ating digit pattern "
        }
      ],
      "role": "agent",
      "taskId": "a4864472-12b7-4c98-9f72-64459e4d8f67"
    },
```

由此看到使用Strands Agents构建的Remote Agent工作正常，遵循原生A2A协议，可接受满足A2A协议的客户端来访问。

### 3、使用Strands Agents构建Client Agent进行异步调用

上一个例子使用的是A2A社区自己的Native SDK，现在来体验下Strands Agents构建的Client Agent。

新开一个控制台窗口，进入到同样的工作目录下，创建Client Agent。将如下代码保存为`client-agent.py`。内容如下。

```python
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
# you can also invoke the agent in a non-async context
# print(agent("pick an agent and make a sample call to test its functionality"))

# run the agent in an async context
async def main():
    await agent.invoke_async(
        "pick an agent and make a sample call to test its functionality"
    )

# run
asyncio.run(main())
```

本例Client Agent的代码和作为Remote Agent的代码是在同一个目录下，因此只需要加载下uv的虚拟环境就可以了，不需要再重复安装依赖库。随后执行`python client-agent.py`启动Client Agent。命令如下：

```shell
source .venv/bin/activate
python client-agent.py
```

运行后返回结果如下：

```shell
I'll help you test an A2A agent's functionality. First, let me check what agents are currently discovered, and if none are available, I'll discover one for testing.
Tool #1: a2a_list_discovered_agents
Great! I can see there's a Calculator Agent already discovered. It has comprehensive mathematical capabilities including basic arithmetic, equation solving, calculus operations, and more. Let me make a sample call to test its functionality with a simple mathematical expression.
Tool #2: a2a_send_message
Perfect! The A2A agent test was successful. Here's what happened:

## Test Results

**Agent:** Calculator Agent (http://127.0.0.1:9000/)

**Test Query:** "Can you calculate the derivative of x^3 + 2x^2 - 5x + 3 with respect to x?"

**Response:** The agent correctly calculated the derivative as **3x² + 4x - 5** and provided a clear explanation:

- The derivative of x³ is 3x²
- The derivative of 2x² is 4x  
- The derivative of -5x is -5
- The derivative of the constant 3 is 0

## Key Observations

1. **Streaming Support**: The agent supports streaming responses, as evidenced by the detailed message history showing the response being built incrementally.
2. **Mathematical Accuracy**: The calculation is mathematically correct, applying the power rule of differentiation properly.
3. **Clear Communication**: The agent provided both the final answer and step-by-step explanation.
4. **Protocol Compliance**: The agent follows the A2A protocol version 0.3.0 with JSONRPC transport
5. **Rich Capabilities**: Based on the agent card, it supports multiple mathematical operations including:
   - Basic arithmetic evaluation
   - Equation solving
   - Calculus (derivatives, integrals)
   - Limits and series expansions
   - Matrix operations

The test demonstrates that the A2A communication protocol is working correctly and the Calculator Agent is functioning as expected with proper mathematical computation capabilities.
```

可看到调用成功。

以上结果可以看到，Strands Agents封装的Client Agent与原生A2A协议兼容，可调用任何支持A2A协议的Agent。使用Strands Agents构建的Client Agent的代码中个，指定了Bedrock服务的Region和模型ID，因此这段代码并非简单的A2A Client，而是A2A中的Client Agent，在与Remote Agent调用过程中，本身也具有Agent能力。

### 4、小结

使用Strands Agents构建开发Remote Agent（A2A Server）和Client Agent（A2A Client），有效简化了代码工作量，可快速开发上线。另外使用async调用方式是异步调用，适合任务时间长、并发多的情况。

## 三、构建Agent as Tool示例1

以HR Agent为例

## 四、构建Agent as Tool示例2

## 五、参考资料



[https://a2a-protocol.org/latest/topics/what-is-a2a/](https://a2a-protocol.org/latest/topics/what-is-a2a/)

Multi-agent Patterns 多Agent design交互模式。

[https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/)