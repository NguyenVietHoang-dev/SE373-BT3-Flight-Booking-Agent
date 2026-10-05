import os
import operator
from typing import List, Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from tools import tools_list

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

try:
    llm = ChatGoogleGenerativeAI(model="model_name", temperature=0.3)
    
    # 1. ReAct Pattern (Reasoning and Acting)
    react_agent = create_react_agent(llm, tools_list)
    
    # 2. Plan-then-Execute Pattern
    class PlanExecuteState(TypedDict):
        input: str
        plan: List[str]
        past_steps: Annotated[List[str], operator.add]
        response: str
        messages: Annotated[list, operator.add]

    def planner(state: PlanExecuteState):
        prompt = f"Lập kế hoạch các bước để thực hiện yêu cầu sau, trả về danh sách các bước: {state['input']}"
        res = llm.invoke([HumanMessage(content=prompt)])
        plan = [line for line in res.content.split('\n') if line.strip()]
        return {"plan": plan, "messages": [res]}

    def executor(state: PlanExecuteState):
        step = state["plan"][0]
        res = react_agent.invoke({"messages": [HumanMessage(content=f"Thực hiện bước này: {step}. Context ban đầu: {state['input']}")]})
        return {
            "past_steps": [step], 
            "plan": state["plan"][1:], 
            "messages": [AIMessage(content=res["messages"][-1].content)]
        }

    def should_end(state: PlanExecuteState):
        if not state["plan"]:
            return END
        return "executor"

    plan_exec_graph = StateGraph(PlanExecuteState)
    plan_exec_graph.add_node("planner", planner)
    plan_exec_graph.add_node("executor", executor)
    plan_exec_graph.set_entry_point("planner")
    plan_exec_graph.add_edge("planner", "executor")
    plan_exec_graph.add_conditional_edges("executor", should_end)
    plan_exec_agent = plan_exec_graph.compile()

    class PlanExecWrapper:
        def invoke(self, input_data):
            res = plan_exec_agent.invoke({"input": input_data["messages"][0].content, "messages": []})
            return {"messages": [AIMessage(content=res["messages"][-1].content)]}

    # 3. Hybrid Pattern
    hybrid_prompt = SystemMessage(content="""Bạn là một Hybrid Booking Agent.
    Trước khi dùng tool, hãy TỰ VIẾT RA KẾ HOẠCH (Thought: My plan is...).
    Sau mỗi bước, ĐÁNH GIÁ LẠI KẾ HOẠCH và thay đổi nếu cần thiết.
    Hãy kiểm tra kỹ quyền hạn (auth_token) và ràng buộc dữ liệu trước khi đặt vé.""")
    
    _base_hybrid_agent = create_react_agent(llm, tools_list)
    
    class HybridWrapper:
        def invoke(self, input_data):
            # Prepend system prompt to the messages
            messages = [hybrid_prompt] + input_data["messages"]
            res = _base_hybrid_agent.invoke({"messages": messages})
            return {"messages": res["messages"]}
            
    hybrid_agent = HybridWrapper()
    
except Exception as e:
    print(f"Khởi tạo LLM thất bại (có thể thiếu API key). Lỗi: {e}")
    react_agent = None
    PlanExecWrapper = None
    hybrid_agent = None
