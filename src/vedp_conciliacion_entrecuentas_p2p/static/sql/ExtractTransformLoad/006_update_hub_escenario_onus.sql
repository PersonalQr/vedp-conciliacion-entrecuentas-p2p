-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_escenario_onus`.
--              Esta tabla calcula el escenario de cruce de información para
--              transacciones ONUS, considerando los estados de depósitos y
--              la naturaleza de las transacciones.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_escenario_onus` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_escenario_onus PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_escenario_onus`
-- Esta tabla evalúa las combinaciones de estados entre los datos de HUB y
-- depósitos, generando un código de escenario de cruce específico para ONUS.
CREATE TABLE {zonap}.temp_hub_escenario_onus AS
SELECT
    hub.tipotrx,
    hub.nattrx,
    hub.nrorastreo,
    hub.montototal,
    hub.llave_1,
    hub.llave_2,
    hub.check_pos,
    hub.valor_monto_pos,
    hub.estados_pos,
    hub.check_depositos,
    hub.valor_monto_depositos,
    hub.estados_depositos,
    CASE
        WHEN hub.estados_depositos = 'Exitoso' AND cast(hub.check_onus as string) = '1' THEN '300'
        WHEN hub.estados_depositos = 'Exitoso' AND cast(hub.check_onus as string) = '0' AND dep.naturaleza_transaccion = 'D' THEN '500'
        WHEN hub.estados_depositos = 'Exitoso' AND cast(hub.check_onus as string) = '0' AND dep.naturaleza_transaccion = 'C' THEN '600'
        WHEN hub.estados_depositos = 'Rechazada' OR hub.estados_depositos IS NULL THEN '400'
        ELSE '400'
    END AS escenario_cruce,
    hub.check_onus
FROM
    {zonap}.temp_hub_dep_data_onus hub
LEFT JOIN (
    SELECT
        llave_2,
        MAX(naturaleza_transaccion) AS naturaleza_transaccion
    FROM
        {zonap}.{tabla_temp_depositos_p2p}
    GROUP BY
        llave_2
) dep
ON
    hub.llave_2 = dep.llave_2
WHERE
    hub.tipotrx = 'P2P-SPBVI-ONUS';
