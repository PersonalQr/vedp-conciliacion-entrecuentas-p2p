-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_pos_data`.
--              Esta tabla almacena información unificada de transacciones
--              provenientes de HUB y POS, validando las relaciones entre ambas.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_pos_data` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_pos_data PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_pos_data`
-- Esta tabla combina datos de transacciones de HUB y POS, utilizando
-- relaciones basadas en `llave_1` y filtrando por una fecha específica.
CREATE TABLE {zonap}.temp_hub_pos_data AS
SELECT DISTINCT
    hub.tipotrx,
    hub.nattrx,
    hub.nrorastreo,
    hub.montototal,
    hub.llave_1,
    hub.llave_2,
    CASE
        WHEN pos.llave_1 IS NOT NULL THEN '1'
        ELSE '0'
    END AS check_pos,
    pos.monto_2 AS valor_monto_pos,
    pos.estado AS estados_pos
FROM
    {zona}.temp_{tabla_hub_p2p} hub
LEFT JOIN
    {zona}.temp_{tabla_pos_p2p} pos
ON
    hub.llave_1 = pos.llave_1
WHERE hub.fecha_trx = {start_date};
