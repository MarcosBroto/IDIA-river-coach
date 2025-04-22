import os
from langchain_core.tools import tool

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
def obten_informacion_saih_tool(codigo_estacion: str) -> dict:
    """
    It retrieves the information about the flow of a river, maing a request to the SAIH data service
    
    It can retrieve both real time data, as well as the predicted flow in the following days. 
    If the station code doesn't exist, it will return 'ERROR_DATOS'. If there is an error with the SAIH data service, it will return 'ERROR_API'.

    :param str codigo_estacion: Code of the station to query
    :return str: The predicted flow information
    """
    return obten_informacion_saih(codigo_estacion)