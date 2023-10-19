#!/bin/bash
source /home/lukas05/mambaforge/bin/activate bliss_env

beacon-server --db-path=demo_configuration --tango-port=10000 --redis-port=25001 --redis-data-port=25002 --port=25000
