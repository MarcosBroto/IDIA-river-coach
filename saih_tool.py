import json
import os
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import Annotated

datos_tramos_rio = {
    "Gállego": {
        "id_estacion": "A059",
        "localidad": "Murillo de Gállego",
        "caudal_minimo": 12,
        "caudal_maximo": 100,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    },
    "Ésera": {
        "id_estacion": "A013",
        "localidad": "Campo",
        "caudal_minimo": 12,
        "caudal_maximo": 60,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    },
    "Ebro-bajo": {
        "id_estacion": "A011",
        "localidad": "Zaragoza",
        "caudal_minimo": 40,
        "caudal_maximo": 1500,
        "temperatura_minima": 5,
        "temperatura_maxima": 35
    },
    "Ebro-alto": {
        "id_estacion": "A203",
        "localidad": "Reinosa",
        "caudal_minimo": 35,
        "caudal_maximo": 1300,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    }
}

def obten_informacion_saih(codigo_estacion: str) -> str:
    saih_headers = {
        "accept": "application/json",
        'api_key': os.environ['SAIH_API_KEY']
    }

    if codigo_estacion not in datos_tramos_rio:
        return "ERROR_DATOS"
    
    # 1. Chequear si la localidad existe y encontrar el código
    # municipios_info = requests.get("https://opendata.aemet.es/opendata/api/maestro/municipios", headers=aemet_headers)
    # if municipios_info.status_code != 200:
    #     return 'ERROR_API'
        
    # datos = municipios_info.json().get("datos")
    datos = "1 2"
    return datos

def test_obten_informacion_saih():
  # Validación de que la función funciona como espero
  sin_datos_ret = obten_informacion_saih("NoExiste")
  expected_sin_datos_ret = 'ERROR_DATOS'
  assert sin_datos_ret == expected_sin_datos_ret, f"Error al obtener la información SAIH de una estación inexistente, debería ser {expected_sin_datos_ret} y ha sido {sin_datos_ret}"
  prediccion_ret = obten_informacion_saih("Ebro-bajo")
  expected_con_datos_ret = "1 2"
  assert prediccion_ret == expected_con_datos_ret, f"Error al obtener las predicciones de Zaragoza, el resultado debería ser {expected_con_datos_ret} y ha sido {prediccion_ret}"

@tool
def obten_informacion_saih_tool(
    tool_call_id: Annotated[str, InjectedToolCallId], 
    state: Annotated[dict, InjectedState]) -> dict:
    """
    It retrieves the information about the flow of a river, maing a request to the SAIH data service
    
    It retrieves the predicted flow in the following days.
    If there is an error with the SAIH data service, it will return 'ERROR_API'.

    :return str: The predicted flow information
    """
    if state.get("saih_predictions") is None:
        print(f"No hay ninguna predicción cacheada en el estado. Uso el API de SAIH")
        all_info = obten_informacion_saih()
    else:
        all_info = state["saih_predictions"]
        print(f"Encontrada la predicción de SAIH en el estado. NO Uso el API de SAIH")

    prediccion = json.dumps(all_info, sort_keys=True)

    if all_info == 'ERROR_DATOS' or all_info == 'ERROR_API':
        return all_info
    
    return Command(
        update = {
            "aemet_predictions": { state.get("saih_predictions")},
            "saih_predictions": { state.get("saih_predictions")}, 
            "messages": [ToolMessage(prediccion, tool_call_id=tool_call_id)],
        }
    )