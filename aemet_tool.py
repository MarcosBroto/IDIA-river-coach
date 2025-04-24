import requests
import os
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import Annotated

with open('./aemet_api_key', 'r') as f:
    os.environ['AEMET_API_KEY'] = f.read().strip()
    f.close()

# Datos de prueba para simular la respuesta de la API de AEMET, para probar que la tool funciona bien
test_data = {
    "temperatura": {
        "maxima": 18,
        "minima": 12,
        "dato": [
            { "value": 0, "hora": 6 },
            { "value": 15, "hora": 12 },
            { "value": 16, "hora": 18 },
            { "value": 14, "hora": 24 }
        ]
    },
    "probPrecipitacion": [
        { "value": 0, "periodo": "00-24" },
        { "value": 0, "periodo": "00-12" },
        { "value": 55, "periodo": "12-24" },
        { "value": 0, "periodo": "00-06" },
        { "value": 0, "periodo": "06-12" },
        { "value": 5, "periodo": "12-18" },
        { "value": 45, "periodo": "18-24" }
    ]
}

def obten_predicciones_aemet(localidad: str, day_index: int, use_test_data=False) -> str:
    if use_test_data:
        return test_data

    aemet_headers = {
        "accept": "application/json",
        'api_key': os.environ['AEMET_API_KEY']
    }

    # 1. Chequear si la localidad existe y encontrar el código
    municipios_info = requests.get("https://opendata.aemet.es/opendata/api/maestro/municipios", headers=aemet_headers)
    if municipios_info.status_code != 200:
        return 'ERROR_API'
        
    data_url = municipios_info.json().get("datos")
    if data_url is None:
        return 'ERROR_API'

    municipios_request = requests.get(data_url, headers=aemet_headers)
    if municipios_request.status_code != 200:
        return 'ERROR_API'

    municipios_json = municipios_request.json()
    id = None
    for mun in municipios_json:
        if mun['nombre'].upper() == localidad.upper():
            id = mun['id'].replace('id','')
            break
    if id is None:
        return 'ERROR_DATOS'
    
    # 2. Obtener la predicción del tiempo
    predicciones_url = f"https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/{id}"
    predicciones_info = requests.get(predicciones_url, headers=aemet_headers)
    if predicciones_info.status_code != 200:
        return 'ERROR_API'

    data_url = predicciones_info.json()["datos"]
    predicciones_request = requests.get(data_url, headers=aemet_headers)
    if predicciones_request.status_code != 200:
        return 'ERROR_API'
    
    return predicciones_request.json()[0]['prediccion']['dia'][day_index]

# Validación de que la función funciona como espero
def test_obten_predicciones_aemet():
    sin_datos_ret = obten_predicciones_aemet("NoExiste", 2)
    expected_sin_datos_ret = 'ERROR_DATOS'
    assert sin_datos_ret == expected_sin_datos_ret, f"Error al obtener las predicciones de un sitio inexistente, debería ser {expected_sin_datos_ret} y ha sido {sin_datos_ret}"
    prediccion_ret = obten_predicciones_aemet("Zaragoza", 3, use_test_data=True)
    assert type(prediccion_ret) == dict and type(prediccion_ret["probPrecipitacion"]) == list, f"Error al obtener las predicciones de Zaragoza, el resultado NO es un diccionario correcto"

def temperatura_por_hora(prediction_data: dict, hora: str, forzar_dia_sin_rangos=False) -> str:
    # Podemos tener datos por rangos de horas o no
    prediction_data = prediction_data["temperatura"]
    if forzar_dia_sin_rangos or len(prediction_data["dato"]) == 0:
        return f"Temperature will be between {prediction_data['minima']} and {prediction_data['maxima']} degrees. "
    
    hour = int(hora.split(":")[0])
    for data in prediction_data["dato"]:
        if data["hora"] >= hour:
            return f"Temperature will be {data['value']} degrees. "
        
    return "No data found"

def test_temperatura_por_hora():
    # Validación de que la función funciona como espero, tanto para los días que tienen rangos de horas independientes
    #   como para los días que sólo tienen temperatura mínima y máxima, sin más detalles
    temp_ret = temperatura_por_hora(test_data, "23:00", forzar_dia_sin_rangos=False)
    expected_temp_ret = "Temperature will be 14 degrees. "
    assert temp_ret == expected_temp_ret, f"Error al parsear los datos de temperatura por hora, debería ser {expected_temp_ret} y ha sido {temp_ret}"
    temperatura_sin_rango = temperatura_por_hora(test_data, "23:00", forzar_dia_sin_rangos=True)
    expected_temperatura_sin_rango = "Temperature will be between 12 and 18 degrees. "
    assert temperatura_sin_rango == expected_temperatura_sin_rango, f"Error al parsear los datos de temperatura por hora, debería ser {expected_temperatura_sin_rango} y ha sido {temperatura_sin_rango}"

def precipitaciones_por_hora(prediction_data: dict, hora: str, forzar_dia_sin_rangos=False) -> int:
    prediction_data = prediction_data["probPrecipitacion"]
    if forzar_dia_sin_rangos or len(prediction_data) == 1:
        return f"Rain probability is {prediction_data[0]['value']}%. "
    
    hour = int(hora.split(":")[0])
    more_accurate_value = 0
    for data in prediction_data:
        rango_periodo = data["periodo"].split("-")
        if hour >= int(rango_periodo[0]) and hour <= int(rango_periodo[1]):
            more_accurate_value = data["value"]
        
    return f"Rain probability is {more_accurate_value}%. "

# Validación de que la función funciona como espero
def test_precipitaciones_por_hora():
    rain = precipitaciones_por_hora(test_data, "23:00", forzar_dia_sin_rangos=False)
    expected_rain = "Rain probability is 45%. "
    assert rain == expected_rain, f"Error al parsear los datos de prob de lluvia por hora, debería ser {expected_rain} y es {rain}"
    rain_sin_rango = precipitaciones_por_hora(test_data, "23:00", forzar_dia_sin_rangos=True)
    expected_rain_sin_rango = "Rain probability is 0%. "
    assert rain_sin_rango == expected_rain_sin_rango, f"Error al parsear los datos de prob de lluvia por hora, debería ser {expected_rain_sin_rango} y es {rain_sin_rango}"

@tool
def obten_predicciones_aemet_integradas_con_estado_tool(
    tool_call_id: Annotated[str, InjectedToolCallId], 
    state: Annotated[dict, InjectedState],                                                         
    localidad: str, day_index: int, hora: str) -> dict:
    """
    It retrieves the weather prediction information for a given location.
    
    It will validate that the location exists in the AEMET database.
    If the location doesn't exist, it will return 'ERROR_DATOS'. If there is an error with the AEMET API, it will return 'ERROR_API'.

    :param str localidad: The name of the location to get the weather prediction for.
    :param int day_index: The number of days between today and the input date. It should be a value between 0 and 6.
    :return str: The weather prediction for the given location for that day and that hour

    """
    if state.get("aemet_predictions") is None:
        print(f"No hay ninguna predicción cacheada en el estado. Uso el API de AEMET")
        all_info = obten_predicciones_aemet(localidad, day_index)
    else:
        all_info = state["aemet_predictions"].get(localidad)
        if all_info is None:
            print(f"Hay alguna predicción cacheada en el estado, pero no la de {localidad}. Uso el API de AEMET")
            all_info = obten_predicciones_aemet(localidad, day_index)
        print(f"Encontrada la predicción de {localidad} en el estado. NO Uso el API de AEMET")

    if all_info == 'ERROR_DATOS' or all_info == 'ERROR_API':
        return all_info
    
    temperatura = temperatura_por_hora(all_info, hora)
    precipitaciones = precipitaciones_por_hora(all_info, hora)
    prediccion = f"{temperatura} {precipitaciones}"    
    return Command(
        update = {
            "aemet_predictions": { localidad: all_info },
            "saih_predictions": { state.get("saih_predictions")}, 
            "messages": [ToolMessage(prediccion, tool_call_id=tool_call_id)],
        }
    )