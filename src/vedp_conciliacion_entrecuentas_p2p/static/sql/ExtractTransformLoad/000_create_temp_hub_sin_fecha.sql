DROP TABLE IF EXISTS {zonap}.temp_{tabla_hub_p2p} PURGE;
DROP TABLE IF EXISTS {zonap}.{tabla_temp_hub_p2p_sin_fecha} PURGE;

CREATE TABLE {zonap}.{tabla_temp_hub_p2p_sin_fecha} (    
    tipotrx STRING,
    operationidpainrbm STRING,
    nombrepagador STRING,
    tipodocumentopagador STRING,
    numerodocpagador INT,
    tipocuentapagador STRING,
    numerocuentapagador BIGINT,
    merchanidcomercio STRING,
    nombrecomercio BIGINT,
    tipoidreprecomercio BIGINT,
    numeroidreprecomercio STRING,
    propositotrx STRING,
    montototal DOUBLE,
    nrorastreo STRING,
    fechatrx STRING,
    numeroctacomercio STRING,
    tipocuentacomercio STRING,
    nattrx STRING,
    nrorastreorev STRING,
    indicadordepositosrev STRING,
    descripcionestado STRING,
    estadotrx STRING,
    sourcechannel STRING,
    idtrxbanco STRING,
    identidadbancariapagador STRING,
    identidadbancariacomercio STRING
)