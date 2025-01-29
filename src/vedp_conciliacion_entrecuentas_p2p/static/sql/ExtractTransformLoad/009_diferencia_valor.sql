DROP TABLE IF EXISTS {zonap}.temp_diferencia_valor_hub_dep_pos PURGE;

CREATE TABLE {zonap}.temp_diferencia_valor_hub_dep_pos
STORED AS PARQUET
AS
SELECT
    tipotrx,
    descripcion,
    CAST(
        CASE 
            WHEN montototal <> valor_monto_depositos THEN montototal - valor_monto_depositos
            ELSE 0
        END
    AS BIGINT) AS check_dep,
    CAST(
        CASE 
            WHEN montototal <> valor_monto_pos THEN montototal - valor_monto_pos
            ELSE 0
        END
    AS BIGINT) AS check_pos
FROM {zonap}.temp_hub_final_data_offus
WHERE montototal <> valor_monto_depositos
OR montototal <> valor_monto_pos;