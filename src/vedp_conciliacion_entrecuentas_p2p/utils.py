from datetime import datetime
from typing import Optional


def _solicitar_y_formatear_fecha(
    self, prompt="Ingresa la fecha de compensacion (YYYY-MM-DD): "
):
    """
    Solicita la fecha al usuario y la formatea para actualizar los parámetros.
    ------
    Parámetros:
    prompt : str
        Mensaje para solicitar la fecha al usuario.

    Retorna:
    --------
    fecha : str
        Fecha formateada en formato 'YYYYMMDD'.
    """
    fecha_compensacion = self.solicitar_fecha(prompt)
    fecha = fecha_compensacion.strftime("%Y%m%d")
    self.params_lz.update({"start_date": fecha})
    return fecha


def ajustando_num_rastreo(
    indicador_rev: str, num_rastreo: str, num_rev_rastreo: str
) -> str:
    """
    Devuelve el num de rastreo que corresponde al código si hay reverso o no

    Parametros:
    @indicador_rev(str) : Indicador S o N es un registro con reverso
    @num_rastreo(str) : Número de rastreo
    @num_rev_rastreo(str): Número de reverso rastreo

    Returns:
    @num_ajustado_reverso(bool): Número de rastreo ajustado si tiene o no rastreo
    """
    if indicador_rev == "S":
        return num_rev_rastreo
    return num_rastreo


def generador_llave_hub_pos(
    la_fecha: str, identificador_pi: str, tipo_ajuste: Optional[str] = ""
) -> str:  # el_monto:str,el_estado:str
    """
    Creación de llave entre HUB y POST , que empela la fecha de la transacción y
     el identificador_pi

    Parametros:
    @la_fecha(str) : Fecha de la transacción
    @identificador_pi(str) : Número de identificador PI suministrado}
    @tipo_ajuste(Optional[str]): Tipo de ajuste de transacciones.Nota: Aplica solo a POS

    Returns:
    @llave1(str): Llave entre las tablas HUB y POST
    """
    if tipo_ajuste in ("", "-"):
        return "|".join([la_fecha, identificador_pi])
    return "|".join([la_fecha, identificador_pi, tipo_ajuste])


def generador_llave_hub_depositos(
    la_fecha: str, num_trastreo: str, tipo_ajust: Optional[str] = "-"
):  # el_estado:str
    """
    Creación de llave entre HUB y DEPOSITOS , que empela la fecha de la transacción
     y el num_trastreo

    Parametros:
    @la_fecha(str) : Fecha de la transacción
    @num_trastreo(str) : Número de rastreo
    @tipo_ajust(Optional[str]): Me brinda el tipo de ajuste del registro

    Returns:
    @llave2(str): Llave entre las tablas HUB y DEPOSITOS
    """
    if tipo_ajust != "-":
        return "|".join([la_fecha, num_trastreo])
    return "|".join([la_fecha, num_trastreo])


def convertir_a_dia_fecha(
    la_fecha: str, formato_fecha: str = "%Y-%m-%dT%H:%M:%S"
) -> str:
    """
    Convertir la fecha suministrada al formato oficial YYYYMMDD o %Y%m%d
    empleado para la lógica de comparación y ajuste si es POST (posterior a las 11:00 pm)

    Parámetros:
    @la_fecha(str) : Fecha de la transacción
    @formato_fecha(str) : Formato de la fecha suministrada para su conversión

    Returns:
    @fecha_dia_ajustado(str): Fecha en formato %Y%m%d ajustado
    """
    fecha_respuesta = datetime.strptime(la_fecha, formato_fecha)
    return fecha_respuesta.strftime("%Y%m%d")


def clasificacion_estado_pos(codigo_resp: str) -> str:
    """
    Permite clasificar el código de estado a partir del código de respuesta (CODIGO-RESP)
    dando respuesta 'Exitosas' ó 'Rechazada'

    Parametros:
    @codigo_resp(str) : Código de respuesta suministrado

    Returns:
    @clasificacion(str): Clasificación suministrada a partir del código de respuesta suministrada
    """
    listado_resp_exitosas = [
        "000",
        "001",
        "002",
        "003",
        "004",
        "005",
        "006",
        "007",
        "008",
        "009",
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
    ]
    if codigo_resp in listado_resp_exitosas:
        return "Exitoso"
    return "Rechazada"


def clasificacion_cod_tipo_tranx_pos(codigo_tranx: str) -> str:
    """
    Permite clasificar entre emisor y pagador a partir del código de tipo transx (COD_TIPO_TRANS)

    Parametros:
    @codigo_tranx(str) : código de tipo transx

    Returns:
    @clasificacion(str): Clasificación pagador y emisor a partir del código de tranx suministrada
    """
    if codigo_tranx in [41, "41"]:
        return "Emisor"
    elif codigo_tranx in [25, "25"]:
        return "Comercio"
    return "No Aplica"


def clasificacion_tipo_ajuste_pos(tipo_resp: str) -> str:
    """
    Permite clasificar el tipo de ajuste a partir del tipo de registro (TIPO_REG)
    dando respuesta '-' No tiene ajuste, 'D' Devolución ó 'E' Extracompensación

    Parametros:
    @tipo_resp(str) : Código de tipo de registro

    Returns:
    @clasificacion(str): Clasificación suministrada a partir del tipo de ajuste
    """
    if tipo_resp in ["80", 80]:
        return "D"  # Devolución
    if tipo_resp in ["81", 81]:
        return "E"  # Extracompensación
    return "-"  # No Aplica
