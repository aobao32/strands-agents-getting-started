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