from aemet_tool import obten_predicciones_aemet_integradas_con_estado_tool
from delta_days_tool import delta_days_tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langgraph.graph import START, MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
import os
from saih_tool import obten_informacion_saih_tool

class MeteoGraphState(MessagesState):
    my_predictions: dict = None


class AgenteCondicionesRios:
    def __init__(self):
        self.grafo_interno = self.genera_grafo()

    def genera_grafo(self):
        with open('./openai_api_key', 'r') as f:
            os.environ['OPENAI_API_KEY'] = f.read().strip()
            f.close()

        tools = [delta_days_tool, obten_predicciones_aemet_integradas_con_estado_tool, obten_informacion_saih_tool]
        model_with_tools = init_chat_model("gpt-4o-mini",
                                model_provider="openai",
                                temperature=0.3,
                                max_tokens=2000,
                                max_retries=1
                                ).bind_tools(tools)
        tool_node = ToolNode(tools)

        def should_continue(state: MeteoGraphState):
            messages = state["messages"]
            last_message = messages[-1]
            if last_message.tool_calls:
                return "tools"
            return END

        def call_model(state: MeteoGraphState):
            messages = state["messages"]
            response = model_with_tools.invoke(messages)
            return {"messages": [response]}

        workflow = StateGraph(MeteoGraphState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, ["tools", END])
        workflow.add_edge("tools", "agent")
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        return app

    def pregunta(self, chat_id: str, message: str):
        messages = self.grafo_interno.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": chat_id}}
        )
        return(messages['messages'][-1].content)
