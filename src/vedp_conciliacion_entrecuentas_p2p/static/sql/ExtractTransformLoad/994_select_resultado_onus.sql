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
    escenario_cruce,
    check_dif_cant,
    check_conciliada,
    descripcion
FROM {zonap}.temp_hub_final_data_onus;
