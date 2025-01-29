import pandas as pd
from datetime import datetime


class DataFrameProcessor:
    def __init__(self, archivo_excel):
        self.archivo_excel = archivo_excel
        self.df = None
        self.fecha_actual = datetime.now()
        self.fecha = None
        self.posicion_neta = None
        self.df_temp_debito = None
        self.df_temp_credito = None
        self.df_unificado = None

    def cargar_datos(self):
        # Leer el archivo Excel
        self.df = pd.read_excel(self.archivo_excel, sheet_name="Hoja1")
        self.df.columns = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
        ]
        self.df = self.df.drop("A", axis=1)

    def procesar_fecha_y_posicion(self):
        # Obtener la fecha y la posición neta
        self.fecha = self.df.iloc[5]["C"]
        self.posicion_neta = self.df.iloc[24]["C"]

    def crear_df_temp_debito(self):
        # Crear el DataFrame de débito
        self.df_temp_debito = self.df.copy()
        self.df_temp_debito = self.df_temp_debito.drop(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23, 24], axis=0
        )
        self.df_temp_debito = self.df_temp_debito.drop(
            ["H", "I", "J", "K", "L"], axis=1
        )
        self.df_temp_debito.columns = [
            "productos_servicios",
            "cantidad",
            "valor",
            "comision_intercambio",
            "comision_administrativa",
            "neto",
            "total",
        ]
        self.df_temp_debito["tag"] = "debito"

    def crear_df_temp_credito(self):
        # Crear el DataFrame de crédito
        self.df_temp_credito = self.df.copy()
        self.df_temp_credito = self.df_temp_credito.drop(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23, 24], axis=0
        )
        self.df_temp_credito = self.df_temp_credito.drop(
            ["C", "D", "E", "F", "G"], axis=1
        )
        self.df_temp_credito.columns = [
            "productos_servicios",
            "cantidad",
            "valor",
            "comision_intercambio",
            "comision_administrativa",
            "neto",
            "total",
        ]
        self.df_temp_credito["tag"] = "credito"

    def unificar_dataframes(self):
        # Crear el DataFrame unificado y agregar la posición neta
        posicion_neta_dict = {
            "productos_servicios": "posicion_neta",
            "cantidad": "0",
            "valor": self.posicion_neta,
            "comision_intercambio": 0,
            "comision_administrativa": 0,
            "neto": self.posicion_neta,
            "total": self.posicion_neta,
            "tag": "general",
        }

        self.df_unificado = pd.concat(
            [self.df_temp_debito, self.df_temp_credito], ignore_index=True
        )
        self.df_unificado.loc[len(self.df_unificado)] = posicion_neta_dict

    def agregar_columnas_fecha(self):
        # Agregar columnas de fecha
        self.df_unificado["fecha"] = self.fecha
        self.df_unificado["year"] = self.fecha_actual.year
        self.df_unificado["month"] = self.fecha_actual.month
        self.df_unificado["day"] = self.fecha_actual.day

    def procesar(self):
        self.cargar_datos()
        self.procesar_fecha_y_posicion()
        self.crear_df_temp_debito()
        self.crear_df_temp_credito()
        self.unificar_dataframes()
        self.agregar_columnas_fecha()

    def obtener_resultado(self):
        return self.df_unificado, self.posicion_neta
