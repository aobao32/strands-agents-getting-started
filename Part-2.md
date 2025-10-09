# Strands Agents Getting Started 中篇 - 构建 Agent & Agent as Tool

上一篇介绍了使用Strands Agents构建MCP之后，本篇进入A2A话题。

## 一、背景

### 1、什么是A2A

Agent-to-Agent (A2A) 协议是一种开发标准，允许使用不同框架、不同开发语言的Agent之间进行交互。

在没有A2A协议之前，通常使用多个Agent时候，用户应用程序可能需要分别连接多个Agent，并人工组合、编排他们调用和依存性关系。这样带来开发的复杂度，如何选择封装和暴露方式、调用效率、响应延迟、扩展、交互性、安全方便都有不足。而使用A2A协议，用户所有的调用通过一个A2A Client（Client Agent）进行，更多提供服务的Agent作为A2A Server（Remote Agent）接受访问。使用A2A方式，整个应用程序在标准的Agent发现、认证、安全的管控体系下，Agent之间具有独立性、易于扩展、满足故障隔离，所有调用为一步调用，整个应用有良好的健壮性。

A2A的主要通信协议包括JSON-RPC、gRPC、HTTP+JSON/REST等，支持HTTPS、支持Streaming方式，支持进行扩展。

### 2、MCP和A2A

A2A协议与MCP协议分别在不同层面，分工不同，二者并无矛盾。MCP协议关注在使用LLM大语言模型构建一个Agent时候的Tool工具调用，它为单个Agent智能体内部的模型和工具之间的交互提供了规范的管道，允许大量第三方MCP Server作为工具被接入复用。由此，一个Agent智能体背后可能有多个MCP Server在支撑它的运行。与MCP不同，A2A协议关注Agent智能体之间的通信规范，多个Agent智能体组合在一起，如何互相发现、互相了解各自的能力（通过Agent Card等形式）。

这里用汽车售后维修系统举一个例子。客户请求来自与客户负责聊天对接的Agent，Agent分析客户的对话内容，判断需要与维修预约Agent、备件库存Agent、订单Agent三个Agent进行交互，分别沟通需要的信息，并最终完成客户需要内容的整理和输出。在这个系统内部，几个Agent之间的交互是通过A2A协议完成的，而每个Agent还需要调用后台文档、知识库、数据库、存储、或者通过网络获取远端API信息时候，将通过Agent自身配置的MCP Server，以MCP协议获取交互数据。MCP协议返回数据给Agent后，本Agent进行汇总和理解，再通过A2A协议输出给其他Agent。

从以上的例子可以看出，A2A是Agent之间的通信规范，而MCP协议解决了在单个Agent内调用外部工具和资源的能力，二者互相配合构建多Agent架构。

### 3、Multi-agent

当有多个Agent各自负责不同的业务逻辑、并相互通信时候，可以有多种架构组合方式。与User直接交互的Agent可被称作Client Agent，Client Agent通常只有1个，而被Client Agent调用的Agent叫做Remote Agent，它们可以有多个。在Client Agent与Remote Agent之间的调用就是A2A协议。Client Agent作为主要的Agent，不仅仅是A2A中的Client，它也是具有大语言模型理解能力的。Remote Agent之间其实没有交互，都依赖Client Agent与它们交互和汇总。

另外的架构是Remote Agent之间可以交互，这与存在单个Client Agent居中调度所不同，多Agent架构在它们之间通过A2A协议进行发现，获取各自Agent的能力范围和边界，并通过Graph、Swarm、Workflow等方式进行交互。这几种方式之间又有不同的应用场景，将在下一篇中进行过介绍。

### 4、Agent as Tool

刚才介绍的Multi-agent架构中的Client Agent和Remote Agent是通过A2A协议在网络上交互的，它们可能位于不同的环境（不同的容器），监听不同的端口各自独立工作。除此之外，还有一种更简单的实现方式，就是把所有Remote Agent和Client Agent都部署在一起，通过Client Agent作为`Orchestrator`的角色来启动。在启动作为`Orchestrator`的Agent时候，将其他Agent作为`Specialized Tool`的方式直接配置到Tooluse部分。在此场景下，这些`Specialized Agent`是不能独立运行，也没有对外暴露，而是都缩进了一层，完全藏在`Orchestrator Agent`的背后。这种实现方式，对外只暴露单一Agent也就是`Orchestrator Agent`。这种方式被称为`Agent as Tool`。

下面分别准备演示代码。

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
uv run client-agent.py
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
uv run client-agent.py
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

## 三、A2A Server & Client 例子 - HR Agent

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

### 3、构建与用户/人类交互的Client Agent、并连接到Employee Agent

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

## 四、Agent as Tool示例2个

### 1、旅行顾问示例（英文版）

初始化环境。执行如下shell脚本。

```shell
uv init 05-agent-as-tool/sample-1
cd init 05-agent-as-tool/sample-1
uv venv
source .venv/bin/activate
uv add strands-agents strands-agents-tools
```

将如下内容保存为`specialized_agent_as_tool.py`。

```python
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
```

将如下内容保存为`orchestrator-agent.py`。

```python
from strands import Agent
from specialized_agent_as_tool import research_assistant, product_recommendation_assistant, trip_planning_assistant
from strands.models import BedrockModel

# Define the orchestrator system prompt with clear tool selection guidance
MAIN_SYSTEM_PROMPT = """
You are an assistant that routes queries to specialized agents:
- For research questions and factual information → Use the research_assistant tool
- For product recommendations and shopping advice → Use the product_recommendation_assistant tool
- For travel planning and itineraries → Use the trip_planning_assistant tool
- For simple questions not requiring specialized knowledge → Answer directly

Always select the most appropriate tool based on the user's query.

如果你使用某个一个工具失败，请把那个tool直接的报错信息返回给用户，而不是尝试用其他工具回答。
"""

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Strands Agents SDK allows easy integration of agent tools
orchestrator = Agent(
    model=bedrock_model,
    system_prompt=MAIN_SYSTEM_PROMPT,
    callback_handler=None,
    tools=[research_assistant, product_recommendation_assistant, trip_planning_assistant]
)

# Example: E-commerce Customer Service System
customer_query = "I'm looking for hiking boots for a trip to Patagonia next month"

# The orchestrator automatically determines that this requires multiple specialized agents
response = orchestrator(customer_query)
print(response)

# Behind the scenes, the orchestrator will:
# 1. First call the trip_planning_assistant to understand travel requirements for Patagonia
#    - Weather conditions in the region next month
#    - Typical terrain and hiking conditions
# 2. Then call product_recommendation_assistant with this context to suggest appropriate boots
#    - Waterproof options for potential rain
#    - Proper ankle support for uneven terrain
#    - Brands known for durability in harsh conditions
# 3. Combine these specialized responses into a cohesive answer that addresses both the
#    travel planning and product recommendation aspects of the query
```

保存完毕后，执行作为入口的`Orchestrator Agent`。命令如下：

```shell
python3 orchestrator-agent.py
```

如果所有作为Tool的agent工作正常，则会返回类似信息。由于在`Orchestrator Agent`的`System Prompt`提示词部分，写明了如果某个作为Tool的Agent报错，则要求抛出错误信息。因此执行后如果返回结果没有包含任何Tool错误说明，那就是所有Tool工作正常。

```shell
Great choice for an adventure in Patagonia! Here are my top recommendations for hiking boots that will handle those challenging conditions:

## **Top Recommendations:**

### **1. Salomon Quest 4D 3 GTX**
- **Best for:** All-around performance in Patagonia's varied terrain
- **Features:** GORE-TEX waterproofing, excellent ankle support, Contagrip outsole for traction
- **Why it's ideal:** Handles rocky terrain and stream crossings well

### **2. La Sportiva Nucleo High GTX**
- **Best for:** Technical terrain and durability
- **Features:** Vibram sole, reinforced toe/heel, excellent waterproofing
- **Why it's ideal:** Built for rugged Patagonian granite and scree

### **3. Scarpa Zodiac Plus GTX**
- **Best for:** Long-distance comfort with technical capability
- **Features:** Superior ankle support, GORE-TEX Extended Comfort, Vibram Pentax Precision sole
- **Why it's ideal:** Excellent for multi-day treks with heavy packs

## **Key Features for Patagonia:**
- **Waterproofing:** Essential for sudden weather changes
- **Ankle support:** Critical for uneven terrain and loose rock
- **Aggressive tread:** For traction on wet rocks and muddy trails
- **Durability:** To withstand sharp granite and thorny vegetation

## **Sizing Tip:**
Get fitted in the afternoon when your feet are naturally swollen, and consider going up half a size to accommodate thicker socks and foot swelling during long hikes.

Would you like specific advice based on which region of Patagonia you're visiting or your experience level?These are excellent recommendations for your Patagonia adventure! The boots I've suggested are all designed to handle Patagonia's unique challenges - from the unpredictable weather and stream crossings to the rugged granite terrain and scree fields.

The **Salomon Quest 4D 3 GTX** is particularly popular among Patagonia hikers for its versatility, while the **La Sportiva Nucleo High GTX** offers exceptional durability for the harsh conditions. The **Scarpa Zodiac Plus GTX** is ideal if you're planning longer multi-day treks.

A few additional considerations for your Patagonia trip:
- Make sure to break in your boots well before the trip
- Pack extra socks and consider bringing gaiters for added protection
- The waterproofing will be crucial given Patagonia's notorious weather changes

Which area of Patagonia are you planning to visit? Torres del Paine, Fitz Roy area, or somewhere else? This could help narrow down the best choice for your specific route and conditions.
```

请注意：在以上例子中，所有Tool都是模拟的，由扮演Tool的Agent直接输出，没有调用外部MCP工具去查询真实信息。因此以上代码仅供学习理解Agent as Tool的架构。实际生产环节，需要自行增加MCP Server的调用，了解到真正的数据源。

### 2、旅行顾问示例（中文版+聊天UI）

上一个例子是在命令行终端下执行的Python文件的例子。这里还有一个例子是使用了Streamlit图形界面交互的例子，并且使用中文Prompt以更直观的交互。

初始化环境。执行如下shell脚本。

```shell
uv init 05-agent-as-tool/sample-2
cd init 05-agent-as-tool/sample-2
uv venv
source .venv/bin/activate
uv add strands-agents strands-agents-tools streamlit dotenv
```

将如下内容保存为`chat.py`。

```python
import os
import streamlit as st
from dotenv import load_dotenv
from strands import Agent, tool
from strands_tools import file_write
import time
from strands.models import BedrockModel

# Load environment variables
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="研究助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
        border-bottom: 2px solid #4c8bf5;
    }
    .agent-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# 为不同智能体定义系统提示
RESEARCH_ASSISTANT_PROMPT = """你是一个专业的研究助手。专注于提供对研究问题的事实性、来源可靠的信息。
尽可能引用你的信息来源。请用中文回答用户的问题。"""

PRODUCT_RECOMMENDATION_PROMPT = """你是一个专业的产品推荐助手。
根据用户偏好提供个性化的产品建议。尽可能引用你的信息来源。请用中文回答用户的问题。"""

TRIP_PLANNING_PROMPT = """你是一个专业的旅行规划助手。
根据用户偏好创建详细的旅行行程。请用中文回答用户的问题。"""

# 定义协调器系统提示
MAIN_SYSTEM_PROMPT = """
你是一个将查询路由到专业智能体的助手：
- 对于研究问题和事实信息 → 使用 research_assistant 工具
- 对于产品推荐和购物建议 → 使用 product_recommendation_assistant 工具
- 对于旅行规划和行程 → 使用 trip_planning_assistant 工具
- 对于不需要专业知识的简单问题 → 直接回答

始终根据用户的查询选择最合适的工具。请用中文回答用户的问题。
"""

# Define agent tools
@tool
def research_assistant(query: str) -> str:
    """
    处理和响应研究性问题，提供有事实依据的信息。

    参数:
        query: 需要解答的研究问题

    返回:
        包含引证的详细研究答案
    """
    try:
        research_agent = Agent(
            system_prompt=RESEARCH_ASSISTANT_PROMPT,
            model=bedrock_model
        )
        response = research_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in research assistant: {str(e)}"

@tool
def product_recommendation_assistant(query: str) -> str:
    """
    处理产品推荐和购物建议相关的查询，根据用户偏好提出合适的产品建议。

    参数:
        query: 用户有关产品的询问

    返回:
        带有理由的个性化产品推荐
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
    创建旅行计划和建议

    参数:
        query: 包含目的地和偏好的旅行计划请求

    返回:
        详细的旅行行程或旅行建议
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

@tool
def summarize_content(content: str) -> str:
    """
    将提供的内容总结为简明的格式。

    参数:
        content: 需要总结的文本内容

    返回:
        内容的简洁摘要
    """
    try:
        summary_agent = Agent(
            system_prompt="""
            你是擅长总结复杂信息的专业人士，能够将其提炼为清晰简洁的摘要。
            你的主要目标是从详尽的信息中提取关键点、主要论据和核心数据。
            你应该在保持原始内容准确性的同时，使其更易于理解。
            注重清晰、简洁，并突出信息中最重要方面。
            """,
            model=bedrock_model
        )
        response = summary_agent(f"请为这段内容创建一个简洁的摘要: {content}")
        return str(response)
    except Exception as e:
        return f"Error in summarization: {str(e)}"

# Create the orchestrator agent
@st.cache_resource
def get_orchestrator():
    return Agent(
        system_prompt=MAIN_SYSTEM_PROMPT,
        tools=[
            research_assistant,
            product_recommendation_assistant,
            trip_planning_assistant,
            file_write,
            summarize_content,
        ],
    )

# Streamlit UI
st.title("🔍 多智能体研究助手")
st.markdown("""
本应用展示了使用Strands Agents的"智能体即工具"模式。
专业AI智能体协同工作，帮助您进行研究、产品推荐和旅行规划。
""")

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "research_history" not in st.session_state:
    st.session_state.research_history = []
if "product_history" not in st.session_state:
    st.session_state.product_history = []
if "travel_history" not in st.session_state:
    st.session_state.travel_history = []
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Chat"

# 创建不同功能的标签页
tab1, tab2, tab3, tab4 = st.tabs(["💬 聊天", "🔍 研究", "🛒 产品", "✈️ 旅行"])

with tab1:
    st.header("与多智能体助手聊天")
    
    # 聊天标签页的侧边栏选项
    st.sidebar.title("聊天选项")
    agent_mode = st.sidebar.radio(
        "选择交互模式:",
        ["直接查询", "顺序处理", "保存结果"]
    )
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 获取用户输入
    query = st.chat_input("请输入您的问题...")

with tab2:
    st.header("研究助手")
    st.markdown("""
    这个专业智能体专注于提供有事实依据、来源可靠的信息，以回应研究问题。
    """)
    
    research_query = st.text_area("输入您的研究问题:", height=100, key="research_query")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("开始研究", key="research_button"):
            if research_query:
                with st.spinner("正在研究中..."):
                    try:
                        # 调用研究智能体
                        result = research_assistant(research_query)
                        # 添加到历史记录
                        st.session_state.research_history.append({
                            "query": research_query,
                            "result": result,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception as e:
                        st.error(f"错误: {str(e)}")
    with col2:
        if st.button("研究并总结", key="research_summarize_button"):
            if research_query:
                with st.spinner("正在研究并总结..."):
                    try:
                        # 调用研究智能体
                        research_result = research_assistant(research_query)
                        # 总结结果
                        summary = summarize_content(research_result)
                        # 添加到历史记录
                        st.session_state.research_history.append({
                            "query": research_query,
                            "result": f"**摘要:**\n\n{summary}\n\n**完整研究:**\n\n{research_result}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception as e:
                        st.error(f"错误: {str(e)}")
    
    # 显示研究历史
    if st.session_state.research_history:
        st.subheader("研究历史")
        for i, item in enumerate(reversed(st.session_state.research_history)):
            with st.expander(f"研究 {i+1}: {item['query'][:50]}... ({item['timestamp']})"):
                st.markdown(item["result"])
                if st.button("保存到文件", key=f"save_research_{i}"):
                    file_name = f"research_results_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(file_name, "w") as f:
                        f.write(f"问题: {item['query']}\n\n{item['result']}")
                    st.success(f"已保存到 {file_name}")

with tab3:
    st.header("产品推荐助手")
    st.markdown("""
    这个专业智能体根据您的偏好提供个性化的产品建议。
    """)
    
    product_query = st.text_area("描述您要寻找的产品:", 
                                height=100, 
                                placeholder="例如：我需要适合初学者的舒适登山鞋，价格在100美元以下",
                                key="product_query")
    
    if st.button("获取推荐", key="product_button"):
        if product_query:
            with st.spinner("正在查找产品推荐..."):
                try:
                    # 调用产品推荐智能体
                    result = product_recommendation_assistant(product_query)
                    # 显示结果
                    st.markdown("### 推荐产品")
                    st.markdown(result)
                    # 添加到历史记录
                    st.session_state.product_history.append({
                        "query": product_query,
                        "result": result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    st.error(f"错误: {str(e)}")
    
    # 显示产品推荐历史
    if st.session_state.product_history:
        st.subheader("历史推荐")
        for i, item in enumerate(reversed(st.session_state.product_history)):
            with st.expander(f"查询 {i+1}: {item['query'][:50]}... ({item['timestamp']})"):
                st.markdown(item["result"])

with tab4:
    st.header("旅行规划助手")
    st.markdown("""
    这个专业智能体根据您的偏好创建详细的旅行行程。
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("目的地:", placeholder="例如：东京，日本")
    with col2:
        duration = st.number_input("行程天数:", min_value=1, max_value=30, value=7)
    
    interests = st.multiselect("兴趣爱好:", 
                              ["文化", "历史", "自然", "冒险", "美食", "购物", "休闲"],
                              ["文化", "美食"])
    
    budget = st.select_slider("预算:", options=["经济", "适中", "豪华"], value="适中")
    
    additional_info = st.text_area("其他偏好或要求:", 
                                  placeholder="例如：携带儿童旅行，无障碍需求等",
                                  height=100)
    
    if st.button("创建行程", key="travel_button"):
        if destination:
            with st.spinner("正在创建旅行行程..."):
                try:
                    # 构建查询
                    travel_query = f"为{destination}创建{duration}天的行程。"
                    travel_query += f"兴趣：{', '.join(interests)}。预算：{budget}。"
                    if additional_info:
                        travel_query += f"附加信息：{additional_info}"
                    
                    # 调用旅行规划智能体
                    result = trip_planning_assistant(travel_query)
                    
                    # 显示结果
                    st.markdown("### 您的旅行行程")
                    st.markdown(result)
                    
                    # 添加到历史记录
                    st.session_state.travel_history.append({
                        "query": travel_query,
                        "result": result,
                        "destination": destination,
                        "duration": duration,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    st.error(f"错误: {str(e)}")
    
    # 显示旅行规划历史
    if st.session_state.travel_history:
        st.subheader("历史行程")
        for i, item in enumerate(reversed(st.session_state.travel_history)):
            with st.expander(f"行程 {i+1}: {item['destination']} ({item['duration']} 天) - {item['timestamp']}"):
                st.markdown(item["result"])
                if st.button("保存行程", key=f"save_itinerary_{i}"):
                    file_name = f"{item['destination'].replace(' ', '_')}_itinerary_{time.strftime('%Y%m%d')}.txt"
                    with open(file_name, "w") as f:
                        f.write(f"目的地: {item['destination']} ({item['duration']} 天)\n\n{item['result']}")
                    st.success(f"已保存到 {file_name}")

if query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(query)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        orchestrator = get_orchestrator()
        
        try:
            # Set environment variable to bypass tool consent
            os.environ["BYPASS_TOOL_CONSENT"] = "true"
            
            start_time = time.time()
            
            if agent_mode == "直接查询":
                # 使用协调器处理查询
                response = orchestrator(query)
                result = str(response)
                
            elif agent_mode == "顺序处理":
                # 首先进行研究
                research_response = research_assistant(query)
                
                # 然后总结研究结果
                result = summarize_content(research_response)
                result = f"**研究摘要:**\n\n{result}\n\n**详细研究:**\n\n{research_response}"
                
            elif agent_mode == "保存结果":
                # 处理查询并保存结果
                response = orchestrator(query)
                result = str(response)
                
                # 保存到文件
                file_name = f"research_results_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                with open(file_name, "w") as f:
                    f.write(result)
                result += f"\n\n结果已保存到 {file_name}"
            
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            
            # Update placeholder with result
            message_placeholder.markdown(f"{result}\n\n*Processed in {processing_time} seconds*")
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": f"{result}\n\n*Processed in {processing_time} seconds*"})
            
            # If the query is related to research, also add to research history
            if "research" in query.lower() or "information" in query.lower() or "facts" in query.lower():
                st.session_state.research_history.append({
                    "query": query,
                    "result": result,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # If the query is related to products, also add to product history
            if "product" in query.lower() or "recommend" in query.lower() or "buy" in query.lower():
                st.session_state.product_history.append({
                    "query": query,
                    "result": result,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # If the query is related to travel, also add to travel history
            if "travel" in query.lower() or "trip" in query.lower() or "vacation" in query.lower():
                st.session_state.travel_history.append({
                    "query": query,
                    "result": result,
                    "destination": query.split("to ")[-1].split(" ")[0] if "to " in query else "Unknown",
                    "duration": "7",  # Default duration
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# 添加侧边栏信息
with st.sidebar:
    st.title("研究助手")
    
    st.markdown("## 智能体能力")
    st.markdown("""
    - **研究助手**: 提供有事实依据、来源可靠的信息
    - **产品推荐**: 根据用户偏好推荐产品
    - **旅行规划**: 创建旅行行程并提供建议
    - **内容总结**: 将复杂信息提炼为简洁摘要
    """)
    
    st.markdown("## 使用说明")
    st.markdown("""
    1. 在聊天输入框中输入您的问题，或使用专业标签页
    2. 从侧边栏选择交互模式
    3. 查看来自相应专业智能体的回应
    """)
    
    st.markdown("## 关于")
    st.markdown("""
    本应用展示了使用Strands Agents的"智能体即工具"模式。
    
    每个专业智能体都被封装为可调用的函数（工具），可供协调器智能体使用。
    
    这创建了一个层次结构，其中协调器处理用户交互并决定调用哪个专业智能体。
    """)
    
    # 添加清除按钮以重置聊天
    if st.button("清除聊天历史"):
        st.session_state.messages = []
        st.experimental_rerun()
```

使用Streamlit启动运行这个脚本。

```shell
streamlit run chat.py
```

命令行返回如下：

```shell

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.238.92:8501

```

现在用浏览器访问本机的`http://localhost:8501`，比提出问题，例如`历史上1860年发生了什么`。现在查看控制台，即可看到有调用Tool的记录。

### 3、小结

通过以上例子可以看出，Agent as Tool的方式只需要启动单一的服务、对外只暴露单一的Agent，而其他Agent在内部作为Tool完成Agent的机能，最终满足整个Agent对外输出的需求。

## 五、参考资料

什么是A2A。

[https://a2a-protocol.org/latest/topics/what-is-a2a/](https://a2a-protocol.org/latest/topics/what-is-a2a/)

Strands A2A Inter-Agent Sample

[https://github.com/aws-samples/sample-agentic-ai-demos/tree/main/modules/strands-a2a-inter-agent](https://github.com/aws-samples/sample-agentic-ai-demos/tree/main/modules/strands-a2a-inter-agent)

Multi-agent Patterns 多Agent design交互模式。

[https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/)

Strands in 5 minnutes - agent-as-tool

[https://github.com/aws-samples/sample-strands-in-5-minutes/tree/main/05_strands_multi_agent/agent-as-tool](https://github.com/aws-samples/sample-strands-in-5-minutes/tree/main/05_strands_multi_agent/agent-as-tool)