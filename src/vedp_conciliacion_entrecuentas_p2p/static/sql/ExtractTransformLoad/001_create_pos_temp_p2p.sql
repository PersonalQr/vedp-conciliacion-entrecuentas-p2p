-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `tabla_temp_pos_p2p`.
--              Esta tabla almacena resultados relacionados con el cruce de
--              información entre datos provenientes de POS y HUB.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `tabla_temp_pos_p2p` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.{tabla_temp_pos_p2p} PURGE;

-- Creación y llenado de la tabla temporal `tabla_temp_pos_p2p`
-- Esta tabla utiliza como base los datos de `tabla_hub_p2p` y calcula
-- si una llave (`llave_1`) tiene relación con los datos en POS.
CREATE TABLE {zonap}.{tabla_temp_pos_p2p} STORED AS PARQUET AS
SELECT 
    pos.llave_1,
    CASE
        WHEN hub.llave_1 IS NOT NULL THEN 1
        ELSE 0
    END AS check_HUB
FROM
    {zonap}.temp_{tabla_pos_p2p} AS pos
LEFT JOIN
    {zonap}.temp_{tabla_hub_p2p} AS hub
    ON pos.llave_1 = hub.llave_1
WHERE
    pos.fecha_log_transaccion = '{start_date}';