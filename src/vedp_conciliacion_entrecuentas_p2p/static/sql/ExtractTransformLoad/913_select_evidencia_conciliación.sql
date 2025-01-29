SELECT 
    hub.fechatrx AS FECHA,
    CASE 
        WHEN hub.nattrx = "C" THEN numeroidreprecomercio
        ELSE numerodocpagador
    END AS NIT,
    CASE 
        WHEN offus.escenario_cruce IN ('100', '209') THEN -offus.montototal
        ELSE offus.montototal
    END AS VALOR,
    hub.nrorastreo AS ID_TRN,
    CASE 
        WHEN hub.nattrx = "C" THEN numeroctacomercio
        ELSE numerocuentapagador
    END AS CUENTA
FROM {zonap}.temp_hub_final_data_offus offus
INNER JOIN {zonap}.temp_{tabla_hub_p2p} hub
ON offus.llave_1 = hub.llave_1 AND offus.llave_2 = hub.llave_2
WHERE escenario_cruce IN ('100', '200', '209', '109');
