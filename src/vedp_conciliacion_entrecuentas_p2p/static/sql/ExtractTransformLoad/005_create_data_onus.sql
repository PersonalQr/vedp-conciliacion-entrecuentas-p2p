-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_dep_data_onus`.
--              Esta tabla almacena información combinada de transacciones
--              de HUB, POS y depósitos, validando las relaciones entre estas
--              fuentes y generando indicadores adicionales.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_dep_data_onus` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_dep_data_onus PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_dep_data_onus`
-- Esta tabla combina datos de transacciones de HUB, POS y depósitos,
-- validando relaciones a través de llaves únicas y calculando valores
-- agregados como estados, montos y conteos.
CREATE TABLE {zonap}.temp_hub_dep_data_onus AS
SELECT
    tem_hub.tipotrx,
    tem_hub.nattrx,
    tem_hub.nrorastreo,
    tem_hub.montototal,
    tem_hub.llave_1,
    tem_hub.llave_2,
    tem_hub.check_pos,
    tem_hub.valor_monto_pos,
    tem_hub.estados_pos,
    MAX(CASE
        WHEN dep.llave_2 IS NOT NULL THEN 1
        ELSE 0
    END) AS check_depositos,
    MAX(dep.monto_de_la_transaccion) AS valor_monto_depositos,
    MAX(dep.estado) AS estados_depositos,
    MAX(CASE
        WHEN dep.cnt > 1 THEN '1'
        ELSE '0'
    END) AS check_onus
FROM
    {zonap}.temp_hub_pos_data tem_hub
LEFT JOIN
    {zonap}.temp_{tabla_hub_p2p} hub
    ON tem_hub.llave_1 = hub.llave_1 AND tem_hub.llave_2 = hub.llave_2
LEFT JOIN (
    SELECT
        numero_de_rastreo,
        llave_2,
        MAX(monto_de_la_transaccion) AS monto_de_la_transaccion,
        MAX(estado) AS estado,
        COUNT(*) AS cnt
    FROM
        {zonap}.{tabla_temp_depositos_p2p}
    GROUP BY
        numero_de_rastreo, llave_2
) dep
ON
    hub.llave_2 = dep.llave_2
    AND hub.nrorastreo = dep.numero_de_rastreo
WHERE
    hub.tipotrx = 'P2P-SPBVI-ONUS'
GROUP BY
    tem_hub.tipotrx,
    tem_hub.nattrx,
    tem_hub.nrorastreo,
    tem_hub.montototal,
    tem_hub.llave_1,
    tem_hub.llave_2,
    tem_hub.check_pos,
    tem_hub.valor_monto_pos,
    tem_hub.estados_pos;