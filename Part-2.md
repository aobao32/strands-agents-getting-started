# Strands Agents SDK Getting Started 中篇 - 构建Agent & Agent as Tool

上一篇介绍了使用Strands Agents构建MCP之后，本篇进入A2A话题。

## 一、背景

### 1、什么是A2A

Agent-to-Agent (A2A) 协议是一种开发标准，允许使用不同框架、不同开发语言的Agent之间进行交互，而无须人为的编排或者把这些Agent嵌套。

在没有A2A协议之前，通常使用多个Agent时候，用户应用程序可能需要分别连接多个Agent，并人工组合、编排他们调用和依存性关系。这样带来开发的复杂度，如何选择封装和暴露方式、调用效率、响应延迟、扩展、交互性、安全方便都有不足。而使用A2A协议，用户所有的调用通过一个A2A Client（Client Agent）进行，更多提供服务的Agent作为A2A Server（Remote Agent）接受访问。使用A2A方式，整个应用程序在标准的Agent发现、认证、安全的管控体系下，Agent之间具有独立性、易于扩展、满足故障隔离，所有调用为一步调用，整个应用有良好的健壮性。

A2A的主要通信协议包括JSON-RPC、gRPC、HTTP+JSON/REST等，支持HTTPS、支持Streaming方式，支持进行扩展。

### 2、MCP和A2A

A2A协议与MCP协议分别在不同层面，分工不同，二者并无矛盾。MCP协议关注在使用LLM大语言模型构建一个Agent时候的Tool工具调用，它为单个Agent智能体内部的模型和工具之间的交互提供了规范的管道，允许大量第三方MCP Server作为工具被接入复用。由此，一个Agent智能体背后可能有多个MCP Server在支撑它的运行。与MCP不同，A2A协议关注Agent智能体之间的通信规范，多个Agent智能体组合在一起，如何互相发现、互相了解各自的能力（通过Agent Card等形式）。

这里用汽车售后维修系统举一个例子。客户请求来自与客户负责聊天对接的Agent，Agent分析客户的对话内容，判断需要与维修预约Agent、备件库存Agent、订单Agent三个Agent进行交互，分别沟通需要的信息，并最终完成客户需要内容的整理和输出。在这个系统内部，几个Agent之间的交互是通过A2A协议完成的，而每个Agent还需要调用后台文档、知识库、数据库、存储、或者通过网络获取远端API信息时候，将通过Agent自身配置的MCP Server，以MCP协议获取交互数据。MCP协议返回数据给Agent后，本Agent进行汇总和理解，再通过A2A协议输出给其他Agent。

从以上的例子可以看出，A2A是Agent之间的通信规范，而MCP协议解决了在单个Agent内调用外部工具和资源的能力，二者互相配合构建多Agent架构。

### 3、Agent as Tool

当有多个Agent各自负责不同的业务逻辑、并相互通信时候，可以有多种架构组合方式。例如一种架构是以`Orchestrator`为核心的模式。与User直接交互的Agent叫做Client Agent，Client Agent通常只有1个，而被Client Agent调用的Agent叫做Remote Agent，它们可以有多个。在Client Agent与Remote Agent之间的调用就是A2A协议。

Client Agent作为主要的Agent，不仅仅是A2A中的Client，它也是具有大语言模型理解能力的。Client Agent作为`orchestrator`负责联系和调度其他Remote Agent，然后其他Remote Agent作为Specialized专门用途的`tool agents`。在这种架构下，搭建Client Agent时候，可以直接将其他Remote Agent的地址作为Tool直接配置到Client Agent上。这种配置方式就是`Agent as Tool`。

### 4、Multi-agent

与刚才的`Orchestrator`架构依赖单个Agent居中调度所不同，多Agent架构在它们之间通过A2A协议进行发现，获取各自Agent的能力范围和边界，并通过Graph、Swarm、Workflow等方式进行交互。这几种方式之间又有不同的应用场景，将在下文进行介绍。

下面开始准备演示代码。

## 二、构建Remote Agent接受Client Agent访问

本例使用 [Strands Agents官方sample代码库](https://github.com/strands-agents/samples/tree/main/03-integrations/Native-A2A-Support) 中的例子。

### 1、使用Strands Agents的Python SDK构建Remote Agent

和本文上篇中的初始化过程一样，这里也要初始化环境。

```shell
uv init 03-a2a-server-and-client
cd 03-a2a-server-and-client
uv venv
source .venv/bin/activate
uv add strands-agents strands-agents-tools
uv add strands-agents[a2a]
```

与之前仅使用MCP不同的是，这里初始化要额外增加A2A需要的依存库。因此增加一步，执行如下命令：

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

### 3、使用Strands Agents构建Client Agent进行异步调用（Agent as Tool）

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

## 三、构建Agent as Tool示例 - HR Agent

本文以Github上AWS官方Sample代码仓库中的[HR Agent](https://github.com/aws-samples/sample-agentic-ai-demos/tree/main/modules/strands-a2a-inter-agent)为例。这个例子是一个HR Agent查询员工信息和技能。HR Agent作为Client Agent接受用户提问，背后是一个Employee Agent负责查询用户信息。Employee Agent的数据来自MCP Server，MCP Server以数组方式预先储存了一组员工数据。

### 1、构建Employee Agent背后的MCP Server

初始化环境。执行如下shell脚本。

```shell
uv init 04-agent-as-tool
cd 04-agent-as-tool
uv venv
source .venv/bin/activate
uv add strands-agents strands-agents-tools
```

员工信息如下。将如下代码保存为`employee_data.py`。

```python
import random

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

SKILLS = {
    "Kotlin", "Java", "Python", "JavaScript", "TypeScript",
    "React", "Angular", "Spring Boot", "AWS", "Docker",
    "Kubernetes", "SQL", "MongoDB", "Git", "CI/CD",
    "Machine Learning", "DevOps", "Node.js", "REST API", "GraphQL"
}

EMPLOYEES = list({emp["name"]: emp for emp in [
    {
        "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "skills": random.sample(list(SKILLS), random.randint(2, 5))
    }
    for i in range(100)
]}.values())
```

提供员工信息的MCP Server代码如下。将如下代码保存为`MCP-Server-for-Employee-agent.py`。

```python
from mcp.server.fastmcp import FastMCP

from employee_data import SKILLS, EMPLOYEES

mcp = FastMCP("employee-server", stateless_http=True, host="0.0.0.0", port=8002)

@mcp.tool()
def get_skills() -> set[str]:
    """all of the skills that employees may have - use this list to figure out related skills"""
    print("get_skills")
    return SKILLS

@mcp.tool()
def get_employees_with_skill(skill: str) -> list[dict]:
    """employees that have a specified skill - output includes fullname (First Last) and their skills"""
    print(f"get_employees_with_skill({skill})")
    skill_lower = skill.lower()
    employees_with_skill = [employee for employee in EMPLOYEES if any(s.lower() == skill_lower for s in employee["skills"])]
    if not employees_with_skill:
        raise ValueError(f"No employees have the {skill} skill")
    return employees_with_skill

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

启动负责提供数据的MCP Server。

```shell
uv run MCP-Server-for-Employee-agent.py
```

可看到MCP Server启动成功。

```shell
INFO:     Started server process [88133]
INFO:     Waiting for application startup.
[09/19/25 16:37:22] INFO     StreamableHTTP session manager started                                                                       streamable_http_manager.py:110
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

保持上述控制台的Shell窗口运行中不要关闭。再新开新的Shell执行后续操作。

### 2、构建Employee Agent作为Remote Agent提供服务

构建Employee Agent的Python代码如下。将如下代码保存为`employee-agent.py`。

```python
import os

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from strands.multiagent.a2a import A2AServer
from urllib.parse import urlparse

EMPLOYEE_INFO_URL = os.environ.get("EMPLOYEE_INFO_URL", "http://localhost:8002/mcp/")
EMPLOYEE_AGENT_URL = os.environ.get("EMPLOYEE_AGENT_URL", "http://localhost:8001/")

employee_mcp_client = MCPClient(lambda: streamablehttp_client(EMPLOYEE_INFO_URL))

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

with employee_mcp_client:
    tools = employee_mcp_client.list_tools_sync()

    employee_agent = Agent(
        model=bedrock_model,
        name="Employee Agent",
        description="Answers questions about employees",
        tools=tools,
        system_prompt="when listing employees, abbreviate employee first names and list all their skills"
    )

    a2a_server = A2AServer(
        agent=employee_agent, 
        host=urlparse(EMPLOYEE_AGENT_URL).hostname, 
        port=urlparse(EMPLOYEE_AGENT_URL).port
        )

    if __name__ == "__main__":
        a2a_server.serve(host="0.0.0.0", port=8001)
```

将文件保存在同一个目录下，然后加载uv的虚拟环境，再安装A2A的SDK，最后启动Agent。

```shell
source .venv/bin/activate
uv add mcp "strands-agents[a2a]" "strands-agents-tools[a2a_client]" uvicorn
uv run employee-agent.py
```

可看到Employee Agent启动成功。

```shell
INFO:     Started server process [90618]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

保持上述控制台的Shell窗口运行中不要关闭。再新开新的Shell执行后续操作。

### 3、构建与用户/人类交互的Client Agent、并以Agent as Tool方式连接到Employee Agent

构建HR Agent的Python代码如下。将如下代码保存为`HR-agent.py`。

```python
import os

import uvicorn
from strands import Agent
from strands.models import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

EMPLOYEE_AGENT_URL = os.environ.get("EMPLOYEE_AGENT_URL", "http://localhost:8001/")

app = FastAPI(title="HR Agent API")

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

provider = A2AClientToolProvider(known_agent_urls=[EMPLOYEE_AGENT_URL])

agent = Agent(
    model=bedrock_model, 
    tools=provider.tools, 
    system_prompt="Use a2a agents to access information you don't otherwise have access to."
    )

@app.post("/inquire")
async def ask_agent(request: QuestionRequest):
    async def generate():
        stream_response = agent.stream_async(request.question)

        async for event in stream_response:
            if "data" in event:
                yield event["data"]

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

将文件保存在同一个目录下，然后加载uv的虚拟环境，再安装A2A的SDK，最后启动Agent。

```shell
source .venv/bin/activate
uv run HR-agent.py
```

启动成功。

```shell
INFO:     Started server process [92699]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4、模拟用户（人类）向HR Agent提问

HR Agent是以匿名方式启动并监听在0.0.0.0:8000的，因此在本机上可以通过CURL直接访问。构建如下CURL，包含人类语言提问给HR Agent。

```shell
curl -X POST --location "http://localhost:8000/inquire" \
    -H "Content-Type: application/json" \
    -d '{"question": "list employees that have skills related to AI programming"}'
```

现在观察几个处于运行状态的Server。

在MCP Server的控制台上可以看到查询MCP Server的日志：

```shell
INFO:     127.0.0.1:60510 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:60510 - "POST /mcp HTTP/1.1" 200 OK
[09/19/25 16:44:33] INFO     Terminating session: None                                                                                                                 streamable_http.py:630
INFO:     127.0.0.1:60512 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:60512 - "POST /mcp HTTP/1.1" 202 Accepted
                    INFO     Terminating session: None                      
```

在Employee Agent的控制台上可以看到打出了如下交互日志：

```shell
Tool #1: get_skills
Here are all the available skills that employees may have:

- TypeScript
- Kotlin
- Git
- JavaScript
- AWS
- Node.js
- Kubernetes
- GraphQL
- CI/CD
- SQL
- Angular
- React
- Python
- DevOps
- Java
- Docker
- MongoDB
- REST API
- Machine Learning
- Spring BootINFO:     127.0.0.1:61672 - "POST / HTTP/1.1" 200 OK

Tool #2: get_employees_with_skill
Here are the employees with Machine Learning skills:

- **J. Jones** - Angular, Machine Learning, Python, Java
- **M. Brown** - Kotlin, Machine Learning, CI/CD, REST API, AWS
- **W. Brown** - Python, SQL, Machine Learning
- **E. Jones** - REST API, Machine Learning, Spring Boot
- **J. Johnson** - Machine Learning, JavaScript, Python, TypeScript
- **J. Jones** - Angular, Machine Learning, Docker
- **P. Smith** - CI/CD, JavaScript, Machine Learning, Kotlin, Git
- **M. Brown** - Java, TypeScript, Machine Learning
- **J. Johnson** - Machine Learning, SQL, Git
- **J. Williams** - Spring Boot, Machine Learning, GraphQL, SQL, Git
- **M. Garcia** - Java, GraphQL, Machine Learning
- **L. Johnson** - SQL, Machine Learning, Kubernetes, GraphQL, Python
- **L. Rodriguez** - JavaScript, Angular, Machine Learning, Kotlin, MongoDB
- **E. Smith** - Machine Learning, CI/CD, DevOps, Java, REST API

In total, 14 employees have Machine Learning skills.INFO:     127.0.0.1:61712 - "POST / HTTP/1.1" 200 OK

Tool #3: get_employees_with_skill
Here are the employees with Python skills:

- **J. Jones** - Angular, Machine Learning, Python, Java
- **M. Miller** - Node.js, Docker, Kubernetes, Python
- **W. Williams** - Kotlin, Python, GraphQL, SQL
- **M. Williams** - CI/CD, Node.js, Python
- **R. Rodriguez** - Python, GraphQL, Docker, Spring Boot, Java
- **W. Brown** - Python, SQL, Machine Learning
- **J. Rodriguez** - Kotlin, Python, React, Node.js
- **J. Johnson** - Machine Learning, JavaScript, Python, TypeScript
- **R. Miller** - Kubernetes, Python
- **R. Martinez** - SQL, Kotlin, Angular, Python
- **E. Williams** - Python, CI/CD, REST API, React, DevOps
- **J. Smith** - Kubernetes, TypeScript, Python, AWS
- **W. Miller** - React, Python
- **M. Williams** - Docker, React, Kubernetes, Python, AWS
- **L. Johnson** - SQL, Machine Learning, Kubernetes, GraphQL, Python
- **M. Rodriguez** - Kubernetes, MongoDB, GraphQL, TypeScript, Python
- **J. Garcia** - Python, TypeScript

In total, 17 employees have Python skills.INFO:     127.0.0.1:61712 - "POST / HTTP/1.1" 200 OK
```

在这部分日志中，可以看到Employee Agent调用了3次Tool，分别获取技能、人员、并组合合适的技能到查询结果中。由此可以看到Employee Agent与MCP Server的多轮交互，这是Agent智能体具备的多次交互的能力。

最后来看HR Agent的控制台输出日志。

```shell
I'll help you find employees with AI programming skills. First, let me check what A2A agents are available that might have access to employee data.
Tool #1: a2a_list_discovered_agents
Great! I found an Employee Agent that can help with this. It has skills to get employee information and skills data. Let me first get the list of available skills to identify which ones are related to AI programming.
Tool #2: a2a_send_message
Perfect! I can see the available skills. For AI programming, the most relevant skills would be:
- **Machine Learning** (directly AI-related)
- **Python** (commonly used for AI/ML development)

Let me query for employees with these skills. I'll start with Machine Learning since it's most directly related to AI.
Tool #3: a2a_send_message
Now let me also check for employees with Python skills, as Python is commonly used for AI programming:
Tool #4: a2a_send_message
Based on my query to the Employee Agent, here are the employees that have skills related to AI programming:

## **Employees with AI Programming Skills**

### **Machine Learning Skills (14 employees)**
These employees have direct AI/ML expertise:

1. **J. Jones** - Angular, Machine Learning, Python, Java
2. **M. Brown** - Kotlin, Machine Learning, CI/CD, REST API, AWS
3. **W. Brown** - Python, SQL, Machine Learning

# 日志较长，以上为部分节选...
```

由此可以看到HR Agent与Employee Agent二者之间通过A2A协议进行了交互。

最后我们来看用户即人类与HR Agent交互的信息，由HR Agent整理并重写之后的最终结果：

```shell
I'll help you find employees with AI programming skills. First, let me check what A2A agents are available that might have access to employee data.Great! I found an Employee Agent that can help with this. It has skills to get employee information and skills data. Let me first get the list of available skills to identify which ones are related to AI programming.Perfect! I can see the available skills. For AI programming, the most relevant skills would be:
- **Machine Learning** (directly AI-related)
- **Python** (commonly used for AI/ML development)

Let me query for employees with these skills. I'll start with Machine Learning since it's most directly related to AI.Now let me also check for employees with Python skills, as Python is commonly used for AI programming:Based on my query to the Employee Agent, here are the employees that have skills related to AI programming:

## **Employees with AI Programming Skills**

### **Machine Learning Skills (14 employees)**
These employees have direct AI/ML expertise:

1. **J. Jones** - Angular, Machine Learning, Python, Java
2. **M. Brown** - Kotlin, Machine Learning, CI/CD, REST API, AWS
3. **W. Brown** - Python, SQL, Machine Learning
4. **E. Jones** - REST API, Machine Learning, Spring Boot
5. **J. Johnson** - Machine Learning, JavaScript, Python, TypeScript
6. **J. Jones** - Angular, Machine Learning, Docker
7. **P. Smith** - CI/CD, JavaScript, Machine Learning, Kotlin, Git
8. **M. Brown** - Java, TypeScript, Machine Learning
9. **J. Johnson** - Machine Learning, SQL, Git
10. **J. Williams** - Spring Boot, Machine Learning, GraphQL, SQL, Git
11. **M. Garcia** - Java, GraphQL, Machine Learning
12. **L. Johnson** - SQL, Machine Learning, Kubernetes, GraphQL, Python
13. **L. Rodriguez** - JavaScript, Angular, Machine Learning, Kotlin, MongoDB
14. **E. Smith** - Machine Learning, CI/CD, DevOps, Java, REST API

### **Python Skills (17 employees total)**
These employees have Python programming skills, which is commonly used for AI development. Some overlap with the ML list above:

**Additional Python developers (not already listed above):**
- **M. Miller** - Node.js, Docker, Kubernetes, Python
- **W. Williams** - Kotlin, Python, GraphQL, SQL
- **M. Williams** - CI/CD, Node.js, Python
- **R. Rodriguez** - Python, GraphQL, Docker, Spring Boot, Java
- **J. Rodriguez** - Kotlin, Python, React, Node.js
- **R. Miller** - Kubernetes, Python
- **R. Martinez** - SQL, Kotlin, Angular, Python
- **E. Williams** - Python, CI/CD, REST API, React, DevOps
- **J. Smith** - Kubernetes, TypeScript, Python, AWS
- **W. Miller** - React, Python
- **M. Williams** - Docker, React, Kubernetes, Python, AWS
- **M. Rodriguez** - Kubernetes, MongoDB, GraphQL, TypeScript, Python
- **J. Garcia** - Python, TypeScript

### **Summary**
- **14 employees** have direct **Machine Learning** skills
- **17 employees** have **Python** programming skills
- Several employees have both ML and Python skills, making them particularly strong candidates for AI programming roles
- The employees with **both Machine Learning and Python** skills are the most qualified for AI programming work

These employees would be your best candidates for AI programming projects, with those having both Machine Learning and Python skills being the most qualified.
```

Agent输出到此结束。以上过程可以看到，HR Agent和Employee Agent完成了交互，并且每个Agent都在自己的技能范围内进行了有效的信息汇总和输出，最终由负责与用户对接的Client Agent向用户返回结果。

## 四、构建Agent as Tool示例 - 

## 五、参考资料

什么是A2A。

[https://a2a-protocol.org/latest/topics/what-is-a2a/](https://a2a-protocol.org/latest/topics/what-is-a2a/)

Strands A2A Inter-Agent Sample

[https://github.com/aws-samples/sample-agentic-ai-demos/tree/main/modules/strands-a2a-inter-agent](https://github.com/aws-samples/sample-agentic-ai-demos/tree/main/modules/strands-a2a-inter-agent)

Multi-agent Patterns 多Agent design交互模式。

[https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/)