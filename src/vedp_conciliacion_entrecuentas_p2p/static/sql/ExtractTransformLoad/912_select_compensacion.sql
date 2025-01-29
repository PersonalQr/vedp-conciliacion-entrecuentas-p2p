SELECT 
    descripcion,
    CAST(SUM(
        CASE 
            WHEN escenario_cruce IN ('100', '209') THEN -montototal
            ELSE montototal
        END
    ) AS BIGINT) AS suma_total
FROM {zonap}.temp_hub_final_data_offus
WHERE escenario_cruce IN ('100', '200', '209', '109')
GROUP BY descripcion
ORDER BY descripcion;



