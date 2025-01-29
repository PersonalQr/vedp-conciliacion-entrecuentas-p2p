-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_escenario_offus`.
--              Esta tabla calcula el escenario de cruce de información para
--              transacciones OFFUS, basado en estados de POS y depósitos.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_escenario_offus` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_escenario_offus PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_escenario_offus`
-- Esta tabla evalúa las combinaciones de estados entre POS y depósitos,
-- generando un código de escenario de cruce que clasifica cada transacción.
CREATE TABLE {zonap}.temp_hub_escenario_offus AS
SELECT
    tipotrx,
    nattrx,
    nrorastreo,
    montototal,
    llave_1,
    llave_2,
    check_pos,
    valor_monto_pos,
    estados_pos,
    check_depositos,
    valor_monto_depositos,
    estados_depositos,
    CASE
        WHEN estados_pos = 'Exitoso' AND estados_depositos = 'Exitoso' THEN
            CASE
                WHEN nattrx = 'D' THEN '100'
                ELSE '200'
            END
        WHEN estados_pos = 'Exitoso' AND (estados_depositos = 'Rechazada' OR estados_depositos IS NULL) THEN
            CASE
                WHEN nattrx = 'D' THEN '109'
                ELSE '209'
            END
        WHEN (estados_pos = 'Rechazada' OR estados_depositos IS NULL) AND estados_depositos = "Exitoso" THEN
            CASE
                WHEN nattrx = 'D' THEN '190'
                ELSE '290'
            END
        WHEN (estados_pos = 'Rechazada' OR estados_pos IS NULL) AND (estados_depositos = 'Rechazada' OR estados_depositos IS NULL) THEN
            '999'
        ELSE
            '0'
    END AS escenario_cruce
FROM
    {zonap}.temp_hub_pos_data_offus
WHERE
    tipotrx IN ('P2P-SPBVI-OFFUS');