from langchain_core.tools import tool
from datetime import datetime, date, time

def delta_days(hoy, input):
    hoy_sin_hora = datetime.combine(hoy, time.min)
    input_sin_hora = datetime.combine(input, time.min)
    delta = input_sin_hora - hoy_sin_hora
    return delta.days

# Validación de que la función funciona como espero, simulo que la comprobación es hace el lunes, 24 de marzo de 2025 al comienzo de la clase
# Si se piden los datos del miércoles, 26 de marzo de 2025, debería devolver 2  (tercer elemento del array devuelto por aemet)
def test_delta_days():
  ret = delta_days(datetime.strptime("2025-03-24 15:30:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2025-03-26", "%Y-%m-%d"))
  expected_ret = 2
  assert ret == expected_ret, f"Error al obtener la diferencia de días, debería ser {expected_ret} y ha sido {ret}"

@tool
def delta_days_tool(input: datetime) -> int:
    """
    It checks if the given date is in the range of suitable dates. This is calculated in this tool, which must return a value between 0 and 3.
    If the returned value is not in that range, the agent won't be able to provide the weather and river flow prediction.

    :param datetime hoy: The current date.
    :param datetime input: The date to check.
    :return: The timedelta in days between the input date and today, which should be a value between 0 and 3. If the value is not in this range, the agent won't be able to provide the weather and river flow prediction.
    """
    return delta_days(date.today(), input)
