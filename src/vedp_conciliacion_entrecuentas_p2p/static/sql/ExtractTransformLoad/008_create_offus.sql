-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_final_data_offus`.
--              Esta tabla consolida información de cruce de transacciones OFFUS,
--              verificando diferencias de cantidad y generando descripciones
--              detalladas para el estado final de cada transacción.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_final_data_offus` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_final_data_offus PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_final_data_offus`
-- Esta tabla utiliza información de `temp_hub_escenario_offus` para consolidar
-- datos de transacciones OFFUS, validando montos, escenarios de cruce y estados
-- de conciliación.
CREATE TABLE {zonap}.temp_hub_final_data_offus AS
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
    hub.escenario_cruce,
    CASE
        WHEN hub.valor_monto_depositos = hub.montototal
             AND hub.valor_monto_pos = hub.montototal THEN 1
        ELSE 0
    END AS check_dif_cant,
    CASE
        WHEN hub.escenario_cruce in ('100', '200') THEN 1
        ELSE 0
    END AS check_conciliada,
    CASE
        WHEN hub.escenario_cruce = '100' THEN "Conciliado DB Originador" 
        WHEN hub.escenario_cruce = '109' THEN "No Db originador Bancol - Cr exitoso RBM"
        WHEN hub.escenario_cruce = '190' THEN "Db originador Bancol - No Cr RBM"
        WHEN hub.escenario_cruce = '200' THEN "Conciliado CR Receptor"
        WHEN hub.escenario_cruce = '209' THEN "No Cr receptor Bancol - Db exitoso RBM"
        WHEN hub.escenario_cruce = '290' THEN "Cr exitoso receptor - Bancol_No Db RBM"
        WHEN hub.escenario_cruce = '900' THEN "Proceso"
        WHEN hub.escenario_cruce = '999' THEN "Rechazado"
        ELSE "Sin reportar"
    END AS Descripcion
FROM
    {zonap}.temp_hub_escenario_offus hub;
