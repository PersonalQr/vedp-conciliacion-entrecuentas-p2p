DROP TABLE IF EXISTS {zona}.{tabla_hub_p2p} PURGE;

CREATE TABLE IF NOT EXISTS {zona}.{tabla_hub_p2p} AS
SELECT *
FROM {zonap}.temp_{tabla_hub_p2p};
