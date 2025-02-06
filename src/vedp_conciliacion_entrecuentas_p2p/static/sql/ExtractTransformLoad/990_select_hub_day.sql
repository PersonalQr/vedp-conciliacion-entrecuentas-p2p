-- -----------------------------------------------------------------------------
-- Equipo Entorno de Productos
-- -----------------------------------------------------------------------------
-- Fecha Creación: 20241202
-- Última Fecha Modificación: 20241202
-- Autores: brbedoy, mamonsal
-- Últimos Autores: brbedoy, mamonsal
-- Descripción: Consulta para contar el número de registros en la tabla `tabla_hub_p2p`
--              que coinciden con una fecha de transacción específica.
-- -----------------------------------------------------------------------------

SELECT
    COUNT(*)
FROM
    {zona}.{tabla_hub_p2p}
WHERE
    fecha_trx = {start_date};