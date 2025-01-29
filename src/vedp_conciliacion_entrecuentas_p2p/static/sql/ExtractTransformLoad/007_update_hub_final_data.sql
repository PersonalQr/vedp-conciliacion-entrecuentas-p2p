-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Creación y llenado de la tabla temporal `temp_hub_final_data_onus`.
--              Esta tabla consolida información de cruce de transacciones ONUS,
--              verificando diferencias de cantidad y generando descripciones
--              detalladas para el estado final de cada transacción.
-- -----------------------------------------------------------------------------

-- Eliminación de la tabla temporal `temp_hub_final_data_onus` si ya existe
-- Esto asegura que la tabla no contenga datos antiguos antes de ser recreada.
DROP TABLE IF EXISTS {zonap}.temp_hub_final_data_onus PURGE;

-- Creación y llenado de la tabla temporal `temp_hub_final_data_onus`
-- Esta tabla utiliza información de `temp_hub_escenario_onus` para consolidar
-- datos de transacciones ONUS, validando montos, escenarios de cruce y estados
-- de conciliación.
CREATE TABLE {zonap}.temp_hub_final_data_onus AS
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
        WHEN hub.escenario_cruce = '300' THEN 1
        ELSE 0
    END AS check_conciliada,
    hub.check_onus,
    CASE
        WHEN hub.escenario_cruce = '300' THEN "Conciliado Db y Cr" 
        WHEN hub.escenario_cruce = '400' THEN "Rechazado"
        WHEN hub.escenario_cruce = '500' THEN "Db exitoso originador - No Cr Receptor_Bancol"
        WHEN hub.escenario_cruce = '600' THEN "No DB orginador - CR exitoso Receptor_Bancol"
        ELSE "Sin reportar"
    END AS Descripcion
FROM
    {zonap}.temp_hub_escenario_onus hub;