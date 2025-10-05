# Strands Agents Getting Started 上篇 - Tool use & 构建MCP Server

## 一、背景

### 1、LLM互动模式的发展

大模型交互方式的发展经历了多个阶段，从2022年大模型推出，到本文编写的2025年下半年，已经有了数次技术迭代。最早的输入补全到多次会话聊天方式已经不能满足需求，模型需要与外部工具交互。于是，Tool use工具调用的技术诞生了，在调用模型的时候，可以直接指定可用的Tool，模型将会判断是否要调用Tool，如果判定需要调用Tool的话，模型会等待Tool的调用，并整合结果。

模型Tool use调用需要大量外部工具配合，这个时候的外部工具都来自于自行研发、没有统一规范，于是MCP协议诞生了。MCP协议规定了标准的输入、输出，可通过stdio、streamable http、sse等方式进行外部工具调用。由于协议是标准的，因此开发者可以使用社区内第三方开发者的MCP Server为我所用，从而不需要重复开发轮子。在使用MCP的过程中，还有着数据安全的需求，例如访问外部API获取文件，拉取回来的数据可能有安全隐患，需要在沙箱环境中封闭运行，由此沙箱技术、E2B诞生了。

使用了以上的技术，模型可以与多种工具进行多次交互，一次交互获取的信息不足，模型会反复访问获取数据，直到获得用户满意的结果。这种交互方式，也就是所谓的智能体Agent。

在没有Agent之前，数据访问一般是通过标准SQL，访问者需要知道表结构，并且自行编写SQL并输入查询条件，SQL语句和数据库负责取回数据。在走向微服务架构后，获取数据的方式从SQL变化为API方式，API接口提供增、删、查、改的交互方式，并且在API上允许输入约束条件，用于获取特定数据集。由此需要经常变更接口，增加多种交互接口，例如分别针对每天的、每周的、每月的、每季度的、每年的都开发对应接口，用于暴露数据。在转向智能体Agent后，这一切都被大语言模型的理解能力所取代，只需要用人类语言输入需求，即可获得所需要的数据。

在数据交互API这个特定领域中使用智能体也就是使用Agent，与传统方式、包括与大模型对话方式的主要区别是：1）人类语言输入；2）外部工具集成；3）人类与模型、其他工具多次反复多轮交互，调用多种tool，而不是一锤子买卖输入数据等模型返回。本文后续演示环境将演示Agent构建过程，并且演示Agent之间的通信过程。

### 2、Strands Agents简介

Strands Agents是一个开源的Python SDK，提供了构建智能体Agent的能力。Strands Agents提供了丰富的内置工具，并且支持调用外部MCP Server，从而大大降低了智能体Agent的开发难度。Strands Agents支持多种大模型，包括AWS Bedrock、OpenAI、Azure OpenAI、Anthropic等。

不使用Strands Agents也可以开发实现完整的智能体，不过需要自行构建MCP Server所需要的网络端口监听、客户端调用、智能体相关的模型对话、外部工具判定、历史记录、RAG召回、多次交互等。使用Strands Agents将以上许多过程封装在一个SDK中，由此将开发难度降低到之前的几分之一、甚至几十分之一，仅需简单的几行代码，即可实现一个支持外部工具调用的智能体。

本文后续所有例子都使用Strands Agents构建。

### 3、循序渐进的代码样例

本文提供从入门开始，分别构建如下几个应用：

- 使用Strands Agent内置Tool、外部Tool的调用
- 使用Strands Agent构建自己的MCP Server，分别通过stdio和http方式进行交互
- A2A协议交互演示
- 构建Agent之间的交互

### 4、Python环境管理

安装uv工具，uv是强力推荐替代pip的功能，运行速度是pip的N倍，并且提供虚拟环境管理的功能。在MacOS和Linux系统上执行如下命令安装uv。如果您是别的操作系统，请查询uv的[官网](https://github.com/astral-sh/uv)有关安装方法。

```shell
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 二、Strands Agent使用内置工具

演示代码位于`01-tool-use`目录。

### 1、初始化

安装完毕后，开始初始化运行环境，并安装Strands Agents的python库。

```shell
uv init 01-internal-tool-use
cd 01-internal-tool-use
uv venv 
source .venv/bin/activate
uv add strands-agents strands-agents-tools
```

以上步骤重点是激活虚拟环境，然后将运行代码所需要的Strands Agent依赖包安装到虚拟环境中。注意，这个虚拟环境中安装的依赖库对于OS内其他位置的Python是不可见的。如果不启动虚拟环境、只是用OS默认的Python直接运行代码，则将会看到找不到Strands库文件的报错。

使用虚拟环境的好处是运行当前代码所需要的各种依赖库版本的安装和配置将完全不会影响其他代码，避免了当前测试安装升级依赖库后，其他现有Python代码无法运行的问题。因此如果在本机上开发多个Python代码，使用虚拟环境是最佳实践。

### 2、调用Strands Agent内置Tool的代码

编辑如下一段代码，保存为`internal-tool.py`，稍后运行之。

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# 指定使用工具
agent = Agent(
    model=bedrock_model,
    tools=[calculator]
    )

# 向Agent提问！
agent("What is the square root of 1764")
```

这段代码使用Strands Agents开发，将调用区域为`us-west-2`的AWS Bedrock服务上的模型`us.anthropic.claude-sonnet-4-20250514-v1:0`。另外由于这个模型ID是一个cross-region的推理ID，因此在流量发送往`us-west-2`区域后，还会自动路由到另外的区域。为了正常调用，需要将这个cross-region对应的三个区域`us-east-1`、`us-east-2`、`us-west-1`都开启Anthropic Claude Sonnet 4的模型访问权限。

在功能上，代码中的Strands Agents调用了内置的计算器`calculator`工具，实现精确的数学计算，而不是在依靠大模型的文字推理来猜测数学题。

运行代码：

```shell
python internal-tool.py
```

获得结果如下：

```shell
I'll calculate the square root of 1764 for you.
Tool #1: calculator
The square root of 1764 is **42**.

This is a perfect square since 42 × 42 = 1764.
```

以上运行结果可以看到，Strands Agent识别出了数学计算问题需要使用Tool，然后调用了Tool计算器实现精确计算能力，最后计算结果返回给LLM大模型，给出最终答案。

### 3、Strands Agents内置Tool说明

Strands Agents内置了一系列现成的Tool，可开箱即用。他们包括：

- RAG & Memory：RAG召回等
- File Operations：读写文件等
- Shell & System：执行shell命令等
- Code Interpretation：运行Python代码等
- Web & Network：发起外部网络请求、浏览器交互等
- Multi-modal：多模态相关，生成视频、音频等
- AWS Services：与AWS云服务交互
- Utilities：工具类，如计算器、日期时间等
- Agents & Workflows¶：用于Agent编排和工作流相关

详细说明：

[https://github.com/strands-agents/tools](https://github.com/strands-agents/tools)

如果以上Tool不能满足需求，则可以自行开发更多工具。

### 4、调用外部Tool的代码

编写`external-tool.py`，代码如下。

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters

# System prompt
NAMING_SYSTEM_PROMPT = """
你是一个域名起名和查询助手。我现在计划使用.com或者.net的域名。

现在为我选择5个和AI智能化相关的域名，用你的工具查询域名是否可用，如果可用的域名请告诉我，否则继续帮我想新的域名，直到找到5个可用的域名为止。
"""

# 定义外部的MCP Server（通过uv包管理工具自动下载，并使用stdio方式加载）
domain_name_tools = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["fastdomaincheck-mcp-server"])
))

# 指定使用Amazon Bedrock上的特定模型版本、使用特定AWS Region
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# 启动Agent
with domain_name_tools:
    tools = domain_name_tools.list_tools_sync()
    naming_agent = Agent(
        model=bedrock_model,
        system_prompt=NAMING_SYSTEM_PROMPT,
        tools=tools
    )

    # 输入要Agent解决的问题
    naming_agent("I need to name an open source project for building AI agents.")
```

运行这段代码`python external-tool.py`，这个AI Agent将会为您选择5个域名，然后查询其是否被注册（fastdomaincheck-mcp-server这个MCP Server是通过whois查询），然后再查找下一批。如此Agent会多次调用MCP Server和LLM模型，直到满足5个可用的条件位置。

由此案例可以看到，Strands Agents大大降低了开发难度，Agent可快速与模型和外部工具交互，满足业务要求。

### 5、注意事项

使用uv管理环境需要注意的是，如果退出了当前终端会导致虚拟环境失效，需要再次进入代码所在环境，然后执行命令开启虚拟环境：

```shell
source .venv/bin/activate
```

由此才可以正确加载已经安装的Strands Agents的库文件用于运行程序。如果不再次执行这个命令加载Python虚拟环境的话，程序将会调用系统默认的Python、并且提示找不到Strands依赖库文件。因为这些依赖文件安装时候仅针对本虚拟环境，位于本OS上其他路径的Python都无法加载这些库。

## 三、调用MCP CLient访问MCP Server并构建AI Agent

演示代码位于`02-mcp-client`目录。

### 1、使用stdio访问本地MCP Server

此处使用了一个查询天气的MCP Server，代码位于目录`02-mcp-client`的`mcp-server-stdio.py`。首先初始化环境。

```shell
uv init 02-mcp-client
cd 02-mcp-client
uv venv 
source .venv/bin/activate
uv add strands-agents strands-agents-tools
```

环境初始化完成后，将`02-mcp-client`的`mcp-server-stdio.py`保存在当前目录中，这个文件是MCP Server。由于是stdio本地方式调用，因此这个MCP Server是不需要监听网络端口的，也就不需要事先启动进程。

接下来使用Strands Agents构建一个MCP Client客户端。将以下代码保存为`mcp-client-stdio.py`，内容如下。

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel

stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uv", 
        args=["run", "mcp-server-stdio.py"],
        transport="stdio",
        wait=True
    )
))

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2"
)

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(
        model=bedrock_model,
        tools=tools
        )
    
    agent("西雅图天气怎么样？")  # Example query about Seattle weather
```

在以上命令中，可以看到使用Strands Agents构建MCP Client，使得开发编程大为简化，只需要简单几行代码，即可构建一个AI Agent，这个AI Agent会使用stdio方式加载本地的MCP Server，并完成与MCP Server的通信。

执行如下命令运行：

```shell
python mcp-client-stdio.py
```

运行后，代码返回：

```shell
[09/15/25 14:34:46] INFO     Processing request of type ListToolsRequest                                                                                                                    server.py:623
我来为您查询西雅图的天气预报。西雅图的地理坐标大约是北纬47.6062度，西经122.3321度。
Tool #1: get_forecast
[09/15/25 14:34:49] INFO     Processing request of type CallToolRequest                                                                                                                     server.py:623
[09/15/25 14:34:50] INFO     HTTP Request: GET https://api.weather.gov/points/47.6062,-122.3321 "HTTP/1.1 200 OK"                                                                         _client.py:1740
                    INFO     HTTP Request: GET https://api.weather.gov/gridpoints/SEW/125,68/forecast "HTTP/1.1 200 OK"                                                                   _client.py:1740
西雅图近期天气情况如下：

**今晚**：
- 温度：54°F（约12°C）
- 风力：东南风2-6英里/小时
- 天气：多云，晚上10点前有轻微降雨可能（降雨概率20%）

**周一**：
- 高温：69°F（约20°C）
- 风力：东北偏北风2-7英里/小时
- 天气：晴朗

**周一夜间**：
- 低温：55°F（约13°C）
- 风力：北风6英里/小时
- 天气：基本晴朗

**周二**：
- 高温：83°F（约28°C）
- 风力：东北偏东风6英里/小时
- 天气：晴朗

**周二夜间**：
- 低温：60°F（约16°C）
- 风力：东南风6英里/小时
- 天气：晴朗

总体来说，西雅图未来几天天气不错，从周一开始将是连续的晴天，温度逐渐升高，非常适合户外活动！
```

以上可看到Strands Agent构建的MCP Server工作正常。

### 2、使用SSE访问网络MCP Server

以上例子是通过stdio方式加载的应用，现在我们将相同的代码修改为使用Streamable HTTP协议方式。代码位于目录`02-mcp-client`的`mcp-server-http.py`。由于上一个步骤已经初始化了uv环境并且加载了虚拟环境了，这里就不需要重复加载。

执行如下命令运行代码：

```shell
python mcp-server-http.py
```

此时可看到程序监听在本机的8002端口。

```shell
INFO:     Started server process [30789]
INFO:     Waiting for application startup.
[09/15/25 23:15:17] INFO     StreamableHTTP session manager started                  streamable_http_manager.py:110
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

现在使用Strands Agents编写一个调用HTTP协议的Client。将如下代码保存为`mcp-client-http.py`。内容如下。

```python
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
```

以上这段代码与之前调用stdio的代码相比，可看到仅在初始化MCP Client的位置稍有不同，其他业务逻辑一样。

然后打开另一个终端，进入`02-mcp-client`目录。首先加载uv的venv环境，然后执行代码。

```shell
source .venv/bin/activate
python mcp-client-http.py
```

即可看到本Agent正常访问了MCP Server，完成了交互逻辑。如果将控制台窗口切换到刚才启动MCP Server的命令行窗口中，还可以看到如下日志：

```shell
INFO:     127.0.0.1:61740 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:61740 - "POST /mcp HTTP/1.1" 200 OK
[09/15/25 23:22:30] INFO     Terminating session: None                                                                     streamable_http.py:630
INFO:     127.0.0.1:61742 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:61742 - "POST /mcp HTTP/1.1" 202 Accepted
                    INFO     Terminating session: None                                                                     streamable_http.py:630
INFO:     127.0.0.1:61744 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:61744 - "POST /mcp HTTP/1.1" 200 OK
                    INFO     Processing request of type ListToolsRequest                                                            server.py:625
                    INFO     Terminating session: None                                                                     streamable_http.py:630
INFO:     127.0.0.1:61764 - "POST /mcp/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:61764 - "POST /mcp HTTP/1.1" 200 OK
[09/15/25 23:22:34] INFO     Processing request of type CallToolRequest                                                             server.py:625
                    INFO     HTTP Request: GET https://api.weather.gov/points/47.6062,-122.3321 "HTTP/1.1 200 OK"                 _client.py:1740
[09/15/25 23:22:35] INFO     HTTP Request: GET https://api.weather.gov/gridpoints/SEW/125,68/forecast "HTTP/1.1 200 OK"           _client.py:1740
                    INFO     Terminating session: None                                                                     streamable_http.py:630
```

通过日志可以看到，由Strands Agents构建的MCP Client正常链接到了MCP Server，并且完成了调用。

以上例子展示了构建Agent与MCP Server交互的过程。

第一部分完。

## 四、参考资料

[https://strandsagents.com/1.x/documentation/docs/user-guide/concepts/tools/mcp-tools/](https://strandsagents.com/1.x/documentation/docs/user-guide/concepts/tools/mcp-tools/)