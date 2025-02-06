SELECT
    hub.fecha_trx as fecha_trx,
    offus.montototal as monto_trx,
    hub.estadotrx as estado_trx,
    hub.operationidpainrbm as numero_unico,
    hub.numerocuentapagador as nro_cuenta_pagador,
    hub.tipocuentapagador as tipo_cuenta_pagador,
    hub.nombrepagador as nombre_pagador,
    hub.numerodocpagador as identificacion_pagador,
    hub.tipodocumentopagador as tipo_doc_pragador,
    hub.numeroctacomercio as nro_cuenta_comercio,
    hub.tipocuentacomercio as tipo_cuenta_comercio,
    hub.nombrecomercio as nombre_comercio,
    hub.numeroidreprecomercio as identificacion_comercio,
    hub.tipoidreprecomercio as tipo_doc_comercio,
    offus.nrorastreo as nro_rastreo,
    offus.descripcion
FROM {zonap}.temp_hub_final_data_offus offus
INNER JOIN {zonap}.temp_{tabla_hub_p2p} hub
ON offus.llave_2 = hub.llave_2;
