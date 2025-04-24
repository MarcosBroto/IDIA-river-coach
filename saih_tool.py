import json
import os
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
import requests
from typing_extensions import Annotated

prevision_caudales_rio = {
    "A059H65QRIO1": [],
    "A013B65QRIO1": [],
    "A011Z65QRIO1": [],
    "A203L65QRIO1": []
}

criterio_recomendacion_rios = {
    "Río Gállego": {
        "id_estacion": "A059H65QRIO1",
        "localidad": "Murillo de Gállego",
        "caudal_minimo": 12,
        "caudal_maximo": 100,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    },
    "Río Ésera": {
        "id_estacion": "A013B65QRIO1",
        "localidad": "Campo",
        "caudal_minimo": 12,
        "caudal_maximo": 60,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    },
    "Río Ebro-bajo": {
        "id_estacion": "A011Z65QRIO1",
        "localidad": "Zaragoza",
        "caudal_minimo": 40,
        "caudal_maximo": 1500,
        "temperatura_minima": 5,
        "temperatura_maxima": 35
    },
    "Río Ebro-alto": {
        "id_estacion": "A203L65QRIO1",
        "localidad": "Reinosa",
        "caudal_minimo": 35,
        "caudal_maximo": 1300,
        "temperatura_minima": 10,
        "temperatura_maxima": 40
    }
}

def obten_informacion_saih(id_estacion: str) -> str:
    if id_estacion not in prevision_caudales_rio.keys():
        return "ERROR_DATOS"

    saih_headers = {
        "Content-Type": "application/json",
    }
    url = "https://www.saihebro.com/datos/apiopendata"
    params = {
        "apikey": os.environ["SAIH_API_KEY"],
        "prevision": "prevision_completa"
    }
    response = requests.get(url, headers=saih_headers, params=params, verify=False)
    data = response.json()

    for item in data["datos"]:
        if item["MS_TAG"] in prevision_caudales_rio.keys():
            lista_valores_caudal = prevision_caudales_rio.get(item["MS_TAG"])
            fecha_hora = item["MS_FECHA_HORA"]["date"]
            valor = item["MS_VALOR"]
            lista_valores_caudal.append({ "fecha": fecha_hora, "caudal": valor })

    return prevision_caudales_rio

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
    state: Annotated[dict, InjectedState],
    id_estacion: str) -> dict:
    """
    It retrieves the information about the flow of a river, making a request to the SAIH data service
    
    It retrieves the predicted flow in the following days.
    If there is an error with the SAIH data service, it will return 'ERROR_API'.

    :param str id_estacion: The station id (id_estacion) associated to the river we're interested in
    :return dict: The predicted flow information
    """
    if state.get("saih_predictions") is None:
        print(f"No hay ninguna predicción cacheada en el estado. Uso el API de SAIH")
        all_info = obten_informacion_saih(id_estacion)
        state["saih_predictions"] = all_info
    else:
        all_info = state["saih_predictions"]
        print(f"Encontrada la predicción en el estado. NO Uso el API de SAIH")

    prediccion = json.dumps(all_info.get(id_estacion), sort_keys=True)

    if all_info == 'ERROR_DATOS' or all_info == 'ERROR_API':
        return all_info
    
    return Command(
        update = {
            "saih_predictions": state["saih_predictions"],
            "messages": [ToolMessage(prediccion, tool_call_id=tool_call_id)],
        }
)
