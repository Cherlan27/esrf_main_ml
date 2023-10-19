#!/bin/bash
source /home/lukas05/mambaforge/bin/activate mlreflect

python -u -m closed_loop_xrr.tango_servers.mlreflectmodelevaluator mlreflect
