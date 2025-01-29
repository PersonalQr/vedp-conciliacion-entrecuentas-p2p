-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Consulta para generar un resumen de las transacciones en
--              `temp_hub_final_data_onus`, agrupadas por descripción y
--              mostrando la suma total y el conteo de transacciones.
-- -----------------------------------------------------------------------------

SELECT
    tipotrx,
    cast(SUM(montototal) as STRING) AS suma_total,
    COUNT(*) AS cantidad_transacciones
FROM {zonap}.{tabla_temp_hub_p2p_sin_fecha}
GROUP BY tipotrx
ORDER BY tipotrx;