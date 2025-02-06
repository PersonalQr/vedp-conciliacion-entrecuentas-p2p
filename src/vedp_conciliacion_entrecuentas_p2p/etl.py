# -*- coding: utf-8 -*-

"""
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Script de ejecución de los ETLs
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
"""
import zipfile
from orquestador2.step import Step
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import json
import pandas as pd
import pkg_resources
import win32com.client as win32

from vedp_conciliacion_entrecuentas_p2p.compensacion import DataFrameProcessor
from vedp_conciliacion_entrecuentas_p2p.utils import (
    ajustando_num_rastreo,
    clasificacion_cod_tipo_tranx_pos,
    clasificacion_estado_pos,
    clasificacion_tipo_ajuste_pos,
    convertir_a_dia_fecha,
    generador_llave_hub_depositos,
    generador_llave_hub_pos,
)


class ExtractTransformLoad(Step):
    """
    Clase encargada de la ejecución de los ETLs
    necesarios para extraer y procesar la información
    de interés de la rutina.
    """

    @staticmethod
    def obtener_ruta():
        """
        Función encargada de identificar la
        carpeta static relacionada al paquete
        ------
        Return
        ------
        ruta_src : string
        Ruta static en el sistema o entorno de
        los recursos del paquete
        """
        return pkg_resources.resource_filename(__name__, "static")

    def obtener_params(self):
        """
        Función encargada de obtener los parámetros
        necesarios para la ejecución del paso.
        ------
        Return
        ------
        params : dictionary
        Parámetros necesarios para ejecutar el paso.
        """
        # PARAMETROS GENERALES DEL PASO
        params = self.getGlobalConfiguration()["parametros_lz"]
        now = datetime.today()
        params_default = {
            "kwargs_year": now.year,
            "kwargs_month": now.month,
            "kwargs_day": now.day,
        }
        params_default.update(self.kwa)
        now = datetime(
            params_default["kwargs_year"],
            params_default["kwargs_month"],
            params_default["kwargs_day"],
        )
        params_calc = {
            # FECHAS
            "f_corte_y": str((now + relativedelta(months=-1)).year),
            "f_corte_m": str((now + relativedelta(months=-1)).month),
            "f_corte_d": str((now + relativedelta(months=-1)).day),
            "f_actual_y": str(now.year),
            "f_actual_m": str(now.month),
            "f_actual_d": str(now.day),
        }
        params.update(params_calc)
        params.update(self.kwa)
        params.pop("password", None)
        return params

    def ejecutar(self):
        """
        Función que ejecuta el paso de la clase.
        """
        self.log.info(json.dumps(self.obtener_params(), indent=4, sort_keys=True))
        self.executeTasks()

    def consolidar_activo(self):
        """
        Funcion que ejecuta los modulos de SQL.
        """
        try:
            params = self.obtener_params()  # obtiene los parametros de la LZ
            archivos_sql = self.getStepConfig()[
                "archivos_sql"
            ]  # Retorna el diccionario del config llamado SQL
            for archivo_sql in archivos_sql:
                self.log.info("Iniciando ejecucion de {}".format(archivo_sql))
                self.helper.ejecutar_archivo(
                    str(self.getSQLPath()) + __class__.__name__ + "/" + archivo_sql,
                    params,
                )
                self.log.info("Finalizada ejecucion de {}".format(archivo_sql))
        except Exception as excep:
            self.log.error(excep)

    def ejecutar_modulos(self):
        """
        Función que ejecuta los módulos de información.
        """
        self.executeFolder(
            self.getSQLPath() + type(self).__name__, self.obtener_params()
        )

    def solicitar_fecha(
        self, prompt="Por favor, ingresa la fecha en formato YYYY-MM-DD: "
    ):
        meses = {
            "01": "Enero",
            "02": "Febrero",
            "03": "Marzo",
            "04": "Abril",
            "05": "Mayo",
            "06": "Junio",
            "07": "Julio",
            "08": "Agosto",
            "09": "Septiembre",
            "10": "Octubre",
            "11": "Noviembre",
            "12": "Diciembre",
        }
        while True:
            fecha_str = input(prompt)
            try:
                self.fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                mes = self.fecha.strftime("%m")
                self.año = self.fecha.strftime("%Y")
                self.mes_formateado = f"{mes}_{meses[mes]}"
                return self.fecha
            except ValueError:
                print(
                    "Formato invalido. Por favor, ingresa la fecha en formato YYYY-MM-DD."
                )

    def _obtener_ruta_completa(self):
        """Obtiene la ruta completa de la carpeta para la carga de archivos."""
        ruta_carpeta_compartida = self.getGlobalConfiguration()[
            "ruta_carpeta_compartida"
        ]
        nombre_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_hub_p2p", ""
        )
        return os.path.normpath(f"{ruta_carpeta_compartida}/{nombre_carpeta}")

    def _obtener_fecha_y_validar_hub(self):
        """Solicita la fecha de compensación y valida si el hub ya está cargado."""
        fecha_compensacion = self.solicitar_fecha(
            "Ingresa la fecha de compensacion (YYYY-MM-DD): "
        )
        fecha = fecha_compensacion.strftime("%Y%m%d")
        self.params_lz.update({"start_date": fecha})

        hub_cargado = False
        try:
            count_date = self.hp.obtener_dataframe_archivo(
                self.getSQLPath() + "ExtractTransformLoad/990_select_hub_day.sql",
                self.params_lz,
            )
        except Exception:
            count_date = pd.DataFrame()

        if not count_date.empty:
            total_count = count_date.iloc[0, 0]
            if total_count > 0:
                hub_cargado = True

        return fecha, hub_cargado

    def _procesar_archivos(self, carpeta_completa, fecha, spk):
        """Procesa los archivos disponibles para una fecha específica."""
        archivo_encontrado = False
        activar_pos = False
        version = 1

        while True:
            nombre_archivo = f"hub_spbvi_{fecha}_{version}.csv"
            ruta_archivo = os.path.join(carpeta_completa, nombre_archivo)

            if os.path.isfile(ruta_archivo):
                print(f"Archivo encontrado: {ruta_archivo}. Procesando...")
                df_upload, df_sin_fecha = self._procesar_dataframe(ruta_archivo)

                if (
                    "tipotrx" in df_upload.columns
                    and df_upload["tipotrx"].str.contains("P2P-SPBVI-OFFUS").any()
                ):
                    activar_pos = True
                    print("El valor 'P2P-SPBVI-OFFUS' existe en la columna 'tipotrx'.")

                spk.subir_df(
                    df_upload,
                    f"{self.params_lz['zonap']}.temp_{self.params_lz['tabla_hub_p2p']}",
                    modo="append",
                )

                if not df_sin_fecha.empty:
                    spk.subir_df(
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
                f"No se encontraron archivos para la fecha {fecha} en la carpeta {carpeta_completa}."
            )
        else:
            print("Proceso de carga completado para todos los archivos disponibles.")

        return activar_pos

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

    def cargar_hub_p2p(self):
        """Carga los archivos desde la carpeta especificada y valida su existencia."""
        spk = self.getSparky()
        self.hp = self.getHelper()
        self.params_lz = self.obtener_params()
        print("********** Inicio Carga de Archivos HUB **********")

        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/000_drop_temp_tables.sql",
            self.params_lz,
        )

        self.helper.ejecutar_archivo(
            self.getSQLPath()
            + "ExtractTransformLoad/000_create_temp_hub_sin_fecha.sql",
            self.params_lz,
        )

        carpeta_completa = self._obtener_ruta_completa()

        # Validar si la carpeta existe
        if not os.path.exists(carpeta_completa):
            print(f"La carpeta no existe: {carpeta_completa}")
            return

        fecha, hub_cargado = self._obtener_fecha_y_validar_hub()

        # if not hub_cargado:
        self._procesar_archivos(carpeta_completa, fecha, spk)
        self.cargar_pos_p2p(fecha)

    def cargar_pos_p2p(self, fecha):
        """Carga los archivos desde la carpeta especificada y valida su existencia."""
        spk = self.getSparky()
        self.params_lz = self.obtener_params()
        print("********** Inicio Carga de Archivos desde Carpeta **********")

        # Obtener la ruta completa de la carpeta
        ruta_carpeta_compartida = self.getGlobalConfiguration()[
            "ruta_carpeta_compartida"
        ]
        nombre_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
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
        nombre_archivo = f"P2P0807{fecha}.zip"
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
                    "monto_2": (206, 218),
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
                spk.subir_df(
                    df_upload,
                    f"{self.params_lz['zona']}.temp_{self.params_lz['tabla_pos_p2p']}",
                    modo="append",
                )
                print(f"Archivo {archivo} procesado y cargado con éxito.")

        else:
            print(
                f"No se encontraron archivos para la fecha {fecha} en la carpeta {carpeta_completa}."
            )

    def estructura_correo(self, df_offus, df_onus, df_rechazadas, extra: str = ""):
        params = self.obtener_params()
        try:
            email = self.getGlobalConfiguration()["email"]
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = email["to"]
            mail.CC = email["cc"]

            # ajustar la fecha:
            # mail.Subject = f'Solicitud de Información: Clientes vendidos a "REINTEGRA" Cartera vendida a R26 ({fecha dd-MM-yyyy})'
            mail.Subject = f"Conciliación interoperabilidad {params['start_date']}"

            mail.HTMLBody = f"""
            <html>
            <head></head>
            <body>
            <p>Cordial saludo,</p>
            <p>Se envia la información sobre la conciliación de interoperabilidad {params['start_date']}.</p>
            <p>Cociliado OFFUS.</p>
            <p>{df_offus.to_html(index=False)}</p>
            <p>Cociliado ONUS.</p>
            <p>{df_onus.to_html(index=False)}</p>
            <p>Rechazadas sin fecha.</p>
            <p>{df_rechazadas.to_html(index=False)}</p>
            {extra}
            </body>
            </html>
            """

            # Enviar el correo
            mail.Send()
            print("Correo enviado exitosamente.")

        except Exception as e:
            print(f"Error al enviar el correo: {e}")

    def enviar_correo(self):
        print("Enviando Correo")
        params = self.obtener_params()  # obtiene los parametros de la LZ
        """Obtiene la ruta completa de la carpeta para la carga de archivos."""
        ruta_carpeta_compartida = self.getGlobalConfiguration()[
            "ruta_carpeta_compartida"
        ]
        nombre_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_reportes", ""
        )

        df_offus = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/991_select_resumen_offus.sql",
            self.params_lz,
        )
        df_offus["suma_total"] = df_offus["suma_total"].apply(
            lambda x: (
                f"${'{:,}'.format(int(x)).replace(',', '.')}"
                if pd.notnull(x) and str(x).isdigit()
                else x
            )
        )
        df_onus = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/992_select_resumen_onus.sql",
            self.params_lz,
        )
        df_onus["suma_total"] = df_onus["suma_total"].apply(
            lambda x: (
                f"${'{:,}'.format(int(x)).replace(',', '.')}"
                if pd.notnull(x) and str(x).isdigit()
                else x
            )
        )
        df_rechazadas = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/995_select_resumen_sin_fecha.sql",
            self.params_lz,
        )
        if df_rechazadas.empty:
            default_data = {
                "tipotrx": ["P2P-SPBVI-ONUS", "P2P-SPBVI-OFFUS"],
                "suma_total": ["$0", "$0"],
                "cantidad_transacciones": ["0", "0"],
            }
            df_rechazadas = pd.DataFrame(default_data)
        else:
            df_rechazadas["suma_total"] = df_rechazadas["suma_total"].apply(
                lambda x: (
                    f"${'{:,}'.format(int(x)).replace(',', '.')}"
                    if pd.notnull(x) and str(x).isdigit()
                    else x
                )
            )
        df_sin_valor = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/914_select_diferencia_valor.sql",
            self.params_lz,
        )
        extra = ""
        if not df_sin_valor.empty:
            df_sin_valor["hub_vs_dep"] = df_sin_valor["hub_vs_dep"].apply(
                lambda x: (
                    f"${'{:,.2f}'.format(x).replace(',', '.')}"  # Formatea números con dos decimales
                    if pd.notnull(x)
                    and isinstance(x, (int, float))  # Verifica que sea numérico
                    else x  # Deja los valores no numéricos tal cual
                )
            )
            df_sin_valor["hub_vs_pos"] = df_sin_valor["hub_vs_pos"].apply(
                lambda x: (
                    f"${'{:,.2f}'.format(x).replace(',', '.')}"  # Formatea números con dos decimales
                    if pd.notnull(x)
                    and isinstance(x, (int, float))  # Verifica que sea numérico
                    else x  # Deja los valores no numéricos tal cual
                )
            )
            extra = f"""<p>Diferencia Valor.</p>
            <p>{df_sin_valor.to_html(index=False)}</p>"""
        self.estructura_correo(df_offus, df_onus, df_rechazadas, extra)
        df_offus_final = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/993_select_resultado_offus.sql",
            self.params_lz,
        )
        df_onus_final = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/994_select_resultado_onus.sql",
            self.params_lz,
        )
        # Guardar los DataFrames como archivos CSV
        df_offus_final.to_csv(
            os.path.join(
                os.path.normpath(f"{ruta_carpeta_compartida}/{nombre_carpeta}"),
                f"resultado_offus_{params['start_date']}.csv",
            ),
            index=False,
            encoding="utf-8",
        )
        df_onus_final.to_csv(
            os.path.join(
                os.path.normpath(f"{ruta_carpeta_compartida}/{nombre_carpeta}"),
                f"resultado_onus_{params['start_date']}.csv",
            ),
            index=False,
            encoding="utf-8",
        )

    def guardar_historial(self):
        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/997_create_final_hub.sql",
            self.params_lz,
        )
        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/998_create_final_pos.sql",
            self.params_lz,
        )
        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/9991_insert_pos_p2p.sql",
            self.params_lz,
        )

    def compensar_pmd(self):
        print("Iniciando el proceso de compensación PMD...")

        spk = self.getSparky()
        print("Objeto Sparky obtenido:", spk)

        params = self.obtener_params()
        print("Parámetros obtenidos:", params)

        ruta_carpeta_compartida = self.getGlobalConfiguration()[
            "ruta_carpeta_compartida"
        ]
        print("Ruta de la carpeta compartida:", ruta_carpeta_compartida)

        nombre_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_pmd_p2p", ""
        )
        print("Nombre de la carpeta:", nombre_carpeta)

        carpeta_completa = os.path.normpath(
            f"{ruta_carpeta_compartida}/{nombre_carpeta}"
        )
        print("Carpeta completa:", carpeta_completa)

        archivo_excel = f"P2PPMD0807{params['start_date']}.xlsx"
        print("Nombre del archivo Excel:", archivo_excel)

        ruta_archivo = os.path.join(carpeta_completa, archivo_excel)
        print("Ruta completa del archivo Excel:", ruta_archivo)

        processor = DataFrameProcessor(ruta_archivo)
        print("Processor inicializado con ruta:", ruta_archivo)

        processor.procesar()
        print("Procesamiento del archivo completado.")

        df_resultado, pmd_neto = processor.obtener_resultado()
        print("Resultado obtenido del procesador:")
        print("DataFrame resultado:", df_resultado)
        print("PMD neto:", pmd_neto)

        spk.subir_df(
            df_resultado,
            f"{self.params_lz['zona']}.{self.params_lz['tabla_pmd_p2p']}",
            modo="append",
        )
        print("DataFrame subido a Sparky.")

        df_pmd = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/912_select_compensacion.sql",
            self.params_lz,
        )
        print("DataFrame PMD obtenido desde SQL.")

        # Verificar y calcular total_suma
        total_suma = df_pmd["suma_total"].fillna(0).sum()
        print("Total suma calculado:", total_suma)

        pmd_neto = 0 if pd.isna(pmd_neto) else pmd_neto
        print("PMD neto ajustado:", pmd_neto)

        df_pmd["suma_total"] = df_pmd["suma_total"].apply(
            lambda x: (
                f"${'{:,}'.format(int(x)).replace(',', '.')}"
                if pd.notnull(x) and str(x).lstrip("-").isdigit()
                else x
            )
        )
        print("Formato aplicado a la columna suma_total.")

        # Crear datos extra
        extra_data = [
            {
                "descripcion": "Total Compensar Transaccional",
                "suma_total": f"${total_suma:,}".replace(",", "."),
            },
            {
                "descripcion": "PMD P2P REDEBAN",
                "suma_total": f"${pmd_neto:,}".replace(",", "."),
            },
            {
                "descripcion": "Comparacion",
                "suma_total": f"${total_suma - pmd_neto:,}".replace(",", "."),
            },
        ]
        print("Datos extra creados:", extra_data)

        df_extra_data = pd.DataFrame(extra_data)
        print("DataFrame con datos extra creado.")

        df_actualizado = pd.concat([df_pmd, df_extra_data], ignore_index=True)
        print("DataFrame actualizado concatenado.")

        self.estructura_correo_pmd(df_actualizado)
        print("Estructura de correo generada y enviada.")

        # Evidencia de conciliación
        df_evidencia_conciliacion = self.hp.obtener_dataframe_archivo(
            self.getSQLPath()
            + "ExtractTransformLoad/913_select_evidencia_conciliación.sql",
            self.params_lz,
        )
        print("Evidencia de conciliación obtenida:", df_evidencia_conciliacion)

        # Guardar evidencia como CSV
        evidencia_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_evidencia_conciliacion", ""
        )
        print("Ruta de la carpeta de evidencia:", evidencia_carpeta)

        evidencia_ruta = os.path.join(
            os.path.normpath(f"{ruta_carpeta_compartida}/{evidencia_carpeta}"),
            f"resultado_evidencia_conciliacion_{params['start_date']}.csv",
        )
        print("Ruta completa para la evidencia:", evidencia_ruta)

        df_evidencia_conciliacion.to_csv(evidencia_ruta, index=False, encoding="utf-8")
        print("Evidencia de conciliación guardada como CSV.")

        # Ejecutar SQL final
        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/999_insert_hub_data.sql",
            self.params_lz,
        )
        print("SQL final ejecutado.")
        print("Proceso de compensación PMD completado.")

    def estructura_correo_pmd(self, df_resultado):
        params = self.obtener_params()
        try:
            email = self.getGlobalConfiguration()["email"]
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = email["to"]
            mail.CC = email["cc"]

            # ajustar la fecha:
            # mail.Subject = f'Solicitud de Información: Clientes vendidos a "REINTEGRA" Cartera vendida a R26 ({fecha dd-MM-yyyy})'
            mail.Subject = f"Compensación interoperabilidad {params['start_date']}"

            mail.HTMLBody = f"""
            <html>
            <head></head>
            <body>
            <p>Cordial saludo,</p>
            <p>Se envia la información sobre la compensacion de interoperabilidad {params['start_date']}.</p>
            <p>COMPENSADO.</p>
            <p>{df_resultado.to_html(index=False)}</p>
            </body>
            </html>
            """

            # Enviar el correo
            mail.Send()
            print("Correo enviado exitosamente.")

        except Exception as e:
            print(f"Error al enviar el correo: {e}")
