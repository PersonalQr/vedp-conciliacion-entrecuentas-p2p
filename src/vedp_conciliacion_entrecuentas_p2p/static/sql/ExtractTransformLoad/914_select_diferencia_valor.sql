SELECT
    descripcion,
    cast(SUM(check_dep) as STRING) AS hub_vs_dep,
    cast(SUM(check_pos) as STRING) AS hub_vs_pos,
    COUNT(*) AS cantidad_transacciones
FROM {zonap}.temp_diferencia_valor_hub_dep_pos
GROUP BY descripcion
ORDER BY descripcion;