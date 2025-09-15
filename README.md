# Strands Agents SDK Getting Started

## 一、背景

### 1、LLM互动模式的发展

### 2、Strands Agents 简介

### 3、循序渐进的代码样例

本文提供从入门开始，分别构建如下几个应用：

- 使用Strands Agent内置Tool来完成数学计算
- 使用Strands Agent构建自己的MCP Server，并进行交互
- 实现A2A、完成Agent之间的交互

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

### 2、演示代码

编辑如下一段代码，保存为`internal-tool.py`，稍后运行之。

```python
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

### 4、调用外部Tool



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

stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uv", 
        args=["run", "mcp-server-stdio.py"],
        transport="stdio",
        wait=True
    )
))

with stdio_mcp_client:
    tools = stdio_mcp_client.list_tools_sync()

    agent = Agent(tools=tools)
    agent("西雅图天气怎么样？")  
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



## 四、构建Agent-to-Agent（A2A）

### 1、Agent-to-Agent 协议

#### (1) Agent as MCP Server

### 2、构建示例应用（HR Agent）

### 3、

## 五、参考资料

[https://strandsagents.com/1.x/documentation/docs/user-guide/concepts/tools/mcp-tools/](https://strandsagents.com/1.x/documentation/docs/user-guide/concepts/tools/mcp-tools/)