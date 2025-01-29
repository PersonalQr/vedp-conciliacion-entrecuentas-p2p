INSERT INTO {zona}.{tabla_hub_p2p}
SELECT *
FROM {zonap}.temp_{tabla_hub_p2p};

DROP TABLE IF EXISTS {zonap}.temp_{tabla_hub_p2p} PURGE;
