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
from orquestador2.step import Step
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import json
import pandas as pd
import pkg_resources

from vedp_conciliacion_entrecuentas_p2p.compensacion import DataFrameProcessor
from vedp_conciliacion_entrecuentas_p2p.conciliacion import ConciliacionP2P
from vedp_conciliacion_entrecuentas_p2p.correo import EnviarCorreo


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

    def conciliacion_p2p(self):
        self.params_lz = self.obtener_params()
        self.hp = self.getHelper()
        conciliacion = ConciliacionP2P(
            self.getSparky(),
            self.hp,
            self.params_lz,
            self.getGlobalConfiguration(),
            self.getSQLPath(),
        )

        conciliacion.cargar_hub_p2p()
        conciliacion.cargar_pos_p2p()

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
                    f"${'{:,}'.format(int(x)).replace(',', '.')}"
                    if pd.notnull(x) and str(x).isdigit()
                    else x
                )
            )
            extra = f"""<p>Diferencia Valor.</p>
            <p>{df_sin_valor.to_html(index=False)}</p>"""
            df_diferencia_valor = self.hp.obtener_dataframe_archivo(
                self.getSQLPath()
                + "ExtractTransformLoad/996_select_diferencia_valor.sql",
                self.params_lz,
            )
            df_diferencia_valor.to_csv(
                os.path.join(
                    os.path.normpath(f"{ruta_carpeta_compartida}/{nombre_carpeta}"),
                    f"resultado_diferencia_valor_{params['start_date']}.csv",
                ),
                index=False,
                encoding="utf-8",
            )

        correo = EnviarCorreo(params["start_date"], self.getGlobalConfiguration())
        correo.estructura_correo(df_offus, df_onus, df_rechazadas, extra)
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
        spk = self.getSparky()
        params = self.obtener_params()
        ruta_carpeta_compartida = self.getGlobalConfiguration()[
            "ruta_carpeta_compartida"
        ]
        nombre_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_pmd_p2p", ""
        )

        carpeta_completa = os.path.normpath(
            f"{ruta_carpeta_compartida}/{nombre_carpeta}"
        )
        archivo_excel = f"P2PPMD0807{params['start_date']}.xlsx"
        ruta_archivo = os.path.join(carpeta_completa, archivo_excel)
        processor = DataFrameProcessor(ruta_archivo)

        processor.procesar()
        df_resultado, pmd_neto = processor.obtener_resultado()

        spk.subir_df(
            df_resultado,
            f"{self.params_lz['zona']}.{self.params_lz['tabla_pmd_p2p']}",
            modo="append",
        )

        df_pmd = self.hp.obtener_dataframe_archivo(
            self.getSQLPath() + "ExtractTransformLoad/912_select_compensacion.sql",
            self.params_lz,
        )

        # Verificar y calcular total_suma
        total_suma = df_pmd["suma_total"].fillna(0).sum()
        pmd_neto = 0 if pd.isna(pmd_neto) else pmd_neto
        df_pmd["suma_total"] = df_pmd["suma_total"].apply(
            lambda x: (
                f"${'{:,}'.format(int(x)).replace(',', '.')}"
                if pd.notnull(x) and str(x).lstrip("-").isdigit()
                else x
            )
        )
        # Depuración
        print(f"Total suma: {total_suma}")
        print(f"PMD neto: {pmd_neto}")

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
        df_extra_data = pd.DataFrame(extra_data)
        df_actualizado = pd.concat([df_pmd, df_extra_data], ignore_index=True)

        self.estructura_correo_pmd(df_actualizado)

        # Evidencia de conciliación
        df_evidencia_conciliacion = self.hp.obtener_dataframe_archivo(
            self.getSQLPath()
            + "ExtractTransformLoad/913_select_evidencia_conciliación.sql",
            self.params_lz,
        )
        # Guardar evidencia como CSV
        evidencia_carpeta = self.getGlobalConfiguration()["rutas_nas"].get(
            "ruta_evidencia_conciliacion", ""
        )
        evidencia_ruta = os.path.join(
            os.path.normpath(f"{ruta_carpeta_compartida}/{evidencia_carpeta}"),
            f"resultado_evidencia_conciliacion_{params['start_date']}.csv",
        )
        df_evidencia_conciliacion.to_csv(evidencia_ruta, index=False, encoding="utf-8")

        # Ejecutar SQL final
        self.helper.ejecutar_archivo(
            self.getSQLPath() + "ExtractTransformLoad/999_insert_hub_data.sql",
            self.params_lz,
        )
