#!/bin/bash
# run in repo root
if [ "$1" == "sandbox" ]; then
  cp config/prod.sandbox.json config.json
  export AGENTX_CONFIG_MODE=sandbox
else
  cp config/dev.local.json config.json
  export AGENTX_CONFIG_MODE=dev
fi
echo "Using config:"
cat config.json
