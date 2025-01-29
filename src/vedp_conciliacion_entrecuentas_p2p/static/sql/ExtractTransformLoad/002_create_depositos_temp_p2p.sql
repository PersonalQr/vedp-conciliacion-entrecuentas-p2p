-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `tabla_temp_depositos_p2p`.
--              Esta tabla almacena datos relacionados con las transacciones
--              de depósitos, incluyendo clasificaciones, validaciones, y cruces.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `tabla_temp_depositos_p2p` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.{tabla_temp_depositos_p2p} PURGE;

-- Creación y llenado de la tabla temporal `tabla_temp_depositos_p2p`
-- Esta tabla utiliza los datos de depósitos, filtra por fecha específica,
-- y genera valores calculados necesarios para el procesamiento.
-- Creación de la tabla temporal
CREATE TABLE {zonap}.{tabla_temp_depositos_p2p} STORED AS PARQUET AS
SELECT
    f_efectiva_trn AS fecha_efectiva,
    cod_trn AS codigo_de_transaccion,
    cod_apli_prod AS codigo_aplicacion,
    num_cta AS numero_de_cuenta,
    cod_db_cr AS naturaleza_transaccion,
    mnt_trn AS monto_de_la_transaccion,
    substr((regexp_extract(descripcion_detalle_1, '(HUB[^ ]{{12}})', 1)),4,12) AS numero_de_rastreo_depo,
    CASE
        WHEN cod_trn IN (3078, 2599, 3106, 2603, 3163, 2645, 3192, 2649, 1161, 990, 1167, 1000) THEN 'Exitoso'
        ELSE 'Rechazada'
    END AS estado,
    substr((regexp_extract(descripcion_detalle_1, '(HUB[^ ]{{12}})', 1)),4,12) AS numero_de_rastreo,
    CONCAT(CAST(f_efectiva_trn AS STRING), '|', substr((regexp_extract(descripcion_detalle_1, '(HUB[^ ]{{12}})', 1)),4,12)) AS llave_2,
    CASE
        WHEN hub.llave_2 IS NOT NULL THEN '1'
        ELSE '0'
    END AS check_hub
FROM
    {zona_depositos}.{tabla_depositos} AS depo
LEFT JOIN {zonap}.temp_{tabla_hub_p2p} AS hub
ON CONCAT(CAST(depo.f_efectiva_trn AS STRING), '|', substr((regexp_extract(descripcion_detalle_1, '(HUB[^ ]{{12}})', 1)),4,12)) = hub.llave_2
WHERE
    depo.f_efectiva_trn = {start_date}
    AND depo.year = CAST(SUBSTR(CAST({start_date} AS STRING), 1, 4) AS INT)
    AND depo.month = CAST(SUBSTR(CAST({start_date} AS STRING), 5, 2) AS INT)
    AND CAST(depo.cod_trn AS INT) IN (
        3078, 3081, 2599, 2600, 3106, 3108, 2603, 2634, 3163, 3168, 2645, 2646, 3192, 3197, 2649, 2650
    );
