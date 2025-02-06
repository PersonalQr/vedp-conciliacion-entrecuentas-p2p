DROP TABLE IF EXISTS {zonap}.temp_diferencia_valor_hub_dep_pos PURGE;

CREATE TABLE {zonap}.temp_diferencia_valor_hub_dep_pos
STORED AS PARQUET
AS
SELECT
    tipotrx,
    descripcion,
    CAST(
        CASE 
            WHEN montototal <> CAST(valor_monto_depositos AS DECIMAL(15,2)) 
            THEN montototal - CAST(valor_monto_depositos AS DECIMAL(15,2))
            ELSE 0
        END AS DECIMAL(15,2)
    ) AS check_dep,
    CAST(
        CASE 
            WHEN montototal <> (CAST(valor_monto_pos AS DECIMAL(15,2)) / 100) 
            THEN montototal - (CAST(valor_monto_pos AS DECIMAL(15,2)) / 100)
            ELSE 0
        END AS DECIMAL(15,2)
    ) AS check_pos
FROM {zonap}.temp_hub_final_data_offus
WHERE 
    montototal <> CAST(valor_monto_depositos AS DECIMAL(15,2))
    OR montototal <> (CAST(valor_monto_pos AS DECIMAL(15,2)) / 100);