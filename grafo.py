from aemet_tool import obten_predicciones_aemet_integradas_con_estado_tool
from datetime import datetime
from delta_days_tool import delta_days_tool
from google.cloud import secretmanager
import json
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import START, MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
import os
from saih_tool import obten_informacion_saih_tool, criterio_recomendacion_rios

class MeteoGraphState(MessagesState):
    aemet_predictions: dict = None
    saih_predictions: dict = None

class AgenteCondicionesRios:
    def __init__(self):
        self.grafo_interno = self.genera_grafo()

    def genera_grafo(self):
        if os.environ.get('EXECUTION_ENVIRONMENT') != None:
            with open('./openai_api_key', 'r') as f:
                os.environ['OPENAI_API_KEY'] = f.read().strip()
                f.close()
            with open('./saih_key', 'r') as f:
                os.environ['SAIH_API_KEY'] = f.read().strip()
                f.close()

        else:
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(name="projects/299185326090/secrets/openai_key/versions/1")
            os.environ['OPENAI_API_KEY'] = response.payload.data.decode("UTF-8")
            response = client.access_secret_version(name="projects/299185326090/secrets/saih_key/versions/1")
            os.environ['SAIH_API_KEY'] = response.payload.data.decode("UTF-8")

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
        now = datetime.now()

        all_chunks = self.grafo_interno.stream(
            {"messages": [
                SystemMessage(content=f"Considera que el día y hora actuales son {now} "),
                SystemMessage(content=f"""
                    Sólo debes responder a preguntas relativas a alguno de los siguientes cuatro ríos de interés: Gállego, Ésera, Ebro-alto y Ebro-bajo.
                    Los criterios que has de seguir para determinar si las condiciones son adecuadas para cada uno de los ríos de interés están configurados
                        en el siguiente JSON: {json.dumps(criterio_recomendacion_rios)}
                """),
                HumanMessage(content=message)
            ]},
            config={"configurable": {"thread_id": "chat_id"}},
            stream_mode="values"
        )
        for chunk in all_chunks:
            all_messages = chunk["messages"]
            if isinstance(all_messages[-1], ToolMessage):
                for m_index in range(len(all_messages) -1, -1, -1):
                    if isinstance(all_messages[m_index], ToolMessage):
                        all_messages[m_index].pretty_print()
                    else:
                        break
            else:
                all_messages[-1].pretty_print()
                
        return all_messages[-1].content

        # messages = self.grafo_interno.invoke(
        #     {"messages": [
        #         SystemMessage(content=f"Considera que el día y hora actuales son {now} "),
        #         SystemMessage(content=f"""
        #             Sólo debes responder a preguntas relativas a alguno de los siguientes cuatro ríos de interés: Gállego, Ésera, Ebro-alto y Ebro-bajo.
        #             Los criterios que has de seguir para determinar si las condiciones son adecuadas para cada uno de los ríos de interés están configurados
        #                 en el siguiente JSON: {json.dumps(criterio_recomendacion_rios)}
        #         """),
        #         HumanMessage(content=message)
        #     ]},
        #     config={"configurable": {"thread_id": chat_id}}
        # )
        # return(messages['messages'][-1].content)