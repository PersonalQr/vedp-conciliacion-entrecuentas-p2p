import os
import zipfile
import pandas as pd

from vedp_conciliacion_entrecuentas_p2p.utils import solicitar_fecha
from vedp_conciliacion_entrecuentas_p2p.utils import (
    ajustando_num_rastreo,
    clasificacion_cod_tipo_tranx_pos,
    clasificacion_estado_pos,
    clasificacion_tipo_ajuste_pos,
    convertir_a_dia_fecha,
    generador_llave_hub_depositos,
    generador_llave_hub_pos,
)


class ConciliacionP2P:
    def __init__(self, spk, hp, params_lz, getGlobalConfiguration, getSQLPath):
        self.hp = hp
        self.spk = spk
        self.fecha = ""
        self.getSQLPath = getSQLPath
        self.params_lz = params_lz
        self.getGlobalConfiguration = getGlobalConfiguration

    def cargar_hub_p2p(self):
        """Carga los archivos desde la carpeta especificada y valida su existencia."""
        print("********** Inicio Carga de Archivos HUB **********")

        self.hp.ejecutar_archivo(
            self.getSQLPath + "ExtractTransformLoad/000_create_temp_hub_sin_fecha.sql",
            self.params_lz,
        )

        carpeta_completa = self._obtener_ruta_completa()

        # Validar si la carpeta existe
        if not os.path.exists(carpeta_completa):
            print(f"La carpeta no existe: {carpeta_completa}")
            return

        self._obtener_fecha_y_validar_hub()

        self._procesar_archivos(carpeta_completa)
        self.cargar_pos_p2p()

    def _obtener_ruta_completa(self):
        """Obtiene la ruta completa de la carpeta para la carga de archivos."""
        ruta_carpeta_compartida = self.getGlobalConfiguration["ruta_carpeta_compartida"]
        nombre_carpeta = self.getGlobalConfiguration["rutas_nas"].get(
            "ruta_hub_p2p", ""
        )
        return os.path.normpath(f"{ruta_carpeta_compartida}/{nombre_carpeta}")

    def _obtener_fecha_y_validar_hub(self):
        """Solicita la fecha de compensación y valida si el hub ya está cargado."""
        fecha_compensacion = solicitar_fecha(
            "Ingresa la fecha de compensacion (YYYY-MM-DD): "
        )
        self.fecha = fecha_compensacion.strftime("%Y%m%d")
        self.params_lz.update({"start_date": self.fecha})

        # TODO: Analizar cargado del día
        hub_cargado = False
        try:
            count_date = self.hp.obtener_dataframe_archivo(
                self.getSQLPath + "ExtractTransformLoad/990_select_hub_day.sql",
                self.params_lz,
            )
        except Exception:
            count_date = pd.DataFrame()

        if not count_date.empty:
            total_count = count_date.iloc[0, 0]
            if total_count > 0:
                hub_cargado = True

    def _procesar_archivos(self, carpeta_completa):
        """Procesa los archivos disponibles para una fecha específica."""
        archivo_encontrado = False
        version = 1

        while True:
            nombre_archivo = f"hub_spbvi_{self.fecha}_{version}.csv"
            ruta_archivo = os.path.join(carpeta_completa, nombre_archivo)

            if os.path.isfile(ruta_archivo):
                print(f"Archivo encontrado: {ruta_archivo}. Procesando...")
                df_upload, df_sin_fecha = self._procesar_dataframe(ruta_archivo)

                self.spk.subir_df(
                    df_upload,
                    f"{self.params_lz['zonap']}.temp_{self.params_lz['tabla_hub_p2p']}",
                    modo="append",
                )

                if not df_sin_fecha.empty:
                    self.spk.subir_df(
                        df_sin_fecha,
                        f"{self.params_lz['zonap']}.{self.params_lz['tabla_temp_hub_p2p_sin_fecha']}",
                        modo="append",
                    )

                archivo_encontrado = True
            else:
                break

            version += 1

        if not archivo_encontrado:
            print(
                f"No se encontraron archivos para la fecha {self.fecha} en la carpeta {carpeta_completa}."
            )
        else:
            print("Proceso de carga completado para todos los archivos disponibles.")

    def _procesar_dataframe(self, ruta_archivo):
        """Procesa un archivo CSV y aplica las transformaciones necesarias."""
        df_upload = pd.read_csv(ruta_archivo, dtype=str)
        df_upload.columns = [col.lower() for col in df_upload.columns]

        # Validar existencia de la columna 'fechatrx'
        if "fechatrx" not in df_upload.columns:
            raise ValueError(
                "La columna 'fechatrx' no existe en el archivo proporcionado."
            )

        # Filtrar filas sin fecha (NaN o cadenas vacías)
        df_sin_fecha = df_upload[
            df_upload["fechatrx"].isna() | (df_upload["fechatrx"] == "")
        ].copy()

        # Eliminar filas sin fecha en df_upload
        df_upload = df_upload.dropna(subset=["fechatrx"])
        df_upload = df_upload[df_upload["fechatrx"] != ""]

        print(f"Filas sin 'fechatrx': {len(df_sin_fecha)}")  # Debugging

        # Aplicar transformaciones a df_upload
        df_upload["numreversoajustado"] = df_upload.apply(
            lambda row: ajustando_num_rastreo(
                row["indicadordepositosrev"],
                row["nrorastreo"],
                row["nrorastreorev"],
            ),
            axis=1,
        )

        df_upload["llave_1"] = df_upload.apply(
            lambda row: generador_llave_hub_pos(
                convertir_a_dia_fecha(str(row["fechatrx"])),
                str(row["operationidpainrbm"]),
            ),
            axis=1,
        )

        df_upload["llave_2"] = df_upload.apply(
            lambda row: generador_llave_hub_depositos(
                convertir_a_dia_fecha(str(row["fechatrx"])),
                str(row["numreversoajustado"]),
            ),
            axis=1,
        )

        if "fechatrx" in df_upload.columns:
            df_upload["fechatrx_dt"] = pd.to_datetime(
                df_upload["fechatrx"].str.split("T").str[0],
                format="%Y-%m-%d",
                errors="coerce",
            )

            df_upload["year"] = df_upload["fechatrx_dt"].dt.year
            df_upload["month"] = df_upload["fechatrx_dt"].dt.month
            df_upload["day"] = df_upload["fechatrx_dt"].dt.day

            df_upload["fechatrx"] = df_upload["fechatrx"].apply(
                lambda x: x.replace("T", " ") if pd.notnull(x) else x
            )
            df_upload["fecha_trx"] = df_upload["fechatrx"].apply(
                lambda x: x.split(" ")[0].replace("-", "") if pd.notnull(x) else x
            )
            df_upload["hora_trax"] = df_upload["fechatrx"].apply(
                lambda x: x.split()[1] if pd.notnull(x) else x
            )

        df_upload.drop(columns=["fechatrx_dt"], inplace=True)

        return df_upload, df_sin_fecha

    def cargar_pos_p2p(self):
        """Carga los archivos desde la carpeta especificada y valida su existencia."""
        print("********** Inicio Carga de Archivos desde Carpeta **********")

        # Obtener la ruta completa de la carpeta
        ruta_carpeta_compartida = self.getGlobalConfiguration["ruta_carpeta_compartida"]
        nombre_carpeta = self.getGlobalConfiguration["rutas_nas"].get(
            "ruta_pos_p2p", ""
        )

        carpeta_completa = os.path.normpath(
            f"{ruta_carpeta_compartida}/{nombre_carpeta}"
        )

        # Validar si la carpeta existe
        if not os.path.exists(carpeta_completa):
            print(f"La carpeta no existe: {carpeta_completa}")
            return

        # Construir el nombre del archivo para la versión actual
        nombre_archivo = f"P2P0807{self.fecha}.zip"
        ruta_archivo = os.path.join(carpeta_completa, nombre_archivo)

        if os.path.isfile(ruta_archivo):
            print(f"Archivo encontrado: {ruta_archivo}. Procesando...")

            with zipfile.ZipFile(ruta_archivo, "r") as zip_ref:
                for archivo in zip_ref.namelist():
                    if "." not in archivo:
                        nuevo_nombre = (
                            f"{archivo}.txt"  # Asignar extensión .txt si no tiene
                        )
                    else:
                        nuevo_nombre = archivo

                    ruta_archivo_extraido = os.path.join(carpeta_completa, nuevo_nombre)

                    with zip_ref.open(archivo) as archivo_origen:
                        with open(ruta_archivo_extraido, "wb") as archivo_destino:
                            archivo_destino.write(archivo_origen.read())

                print(f"Procesando archivo extraído: {ruta_archivo_extraido}")

                # Definir las posiciones de las columnas
                columnas = {
                    "tipo_reg": (1, 2),
                    "fiid_autorizadora": (7, 10),
                    "tipo_mensaje": (73, 76),
                    "fecha_log_transaccion": (79, 86),
                    "cod_tipo_trans": (179, 180),
                    "codigo_resp": (203, 205),
                    "monto_2": (206, 216),
                    "codigo_reverso": (288, 289),
                    "identificador_unico_pi": (599, 633),
                    "indicador_tipo_transicion_token": (651, 651),
                }

                # Convertir el diccionario de columnas en posiciones de inicio y longitud
                colspecs = [(v[0] - 1, v[1]) for v in columnas.values()]
                nombres_columnas = list(columnas.keys())

                # Leer el archivo plano ignorando la primera línea
                df_upload = pd.read_fwf(
                    ruta_archivo_extraido,
                    colspecs=colspecs,
                    header=None,
                    skiprows=1,
                    skipfooter=1,
                    names=nombres_columnas,
                )
                df_upload["estado"] = df_upload["codigo_resp"].apply(
                    clasificacion_estado_pos
                )

                df_upload["tipo_trans"] = df_upload["cod_tipo_trans"].apply(
                    clasificacion_cod_tipo_tranx_pos
                )

                df_upload["tipo_ajuste"] = df_upload["tipo_reg"].apply(
                    clasificacion_tipo_ajuste_pos
                )
                df_upload["llave_1"] = df_upload.apply(
                    lambda row: generador_llave_hub_pos(
                        str(row["fecha_log_transaccion"]),
                        str(row["identificador_unico_pi"]),
                        str(row["tipo_ajuste"]),
                    ),
                    axis=1,
                )
                df_upload["fecha_log_transaccion_dt"] = pd.to_datetime(
                    df_upload["fecha_log_transaccion"], format="%Y%m%d", errors="coerce"
                )
                df_upload["year"] = df_upload["fecha_log_transaccion_dt"].dt.year
                df_upload["month"] = df_upload["fecha_log_transaccion_dt"].dt.month
                df_upload["day"] = df_upload["fecha_log_transaccion_dt"].dt.day

                df_upload.drop(columns=["fecha_log_transaccion_dt"], inplace=True)

                # Cargar el DataFrame en el sistema
                self.spk.subir_df(
                    df_upload,
                    f"{self.params_lz['zona']}.temp_{self.params_lz['tabla_pos_p2p']}",
                    modo="append",
                )
                print(f"Archivo {archivo} procesado y cargado con éxito.")

        else:
            print(
                f"No se encontraron archivos para la fecha {self.fecha} en la carpeta {carpeta_completa}."
            )
