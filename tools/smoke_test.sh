#!/usr/bin/env bash
# tools/smoke_test.sh
# Full local smoke test for AgentX
set -e

echo "========================================="
echo "AgentX Smoke Test"
echo "========================================="

PORT=8080
if [ -f .backend_port ]; then
    PORT=$(cat .backend_port)
fi
echo "Using Backend Port: $PORT"

echo ""
echo "1) Config loader check"
python tools/verify_config.py

echo ""
echo "2) Health check"
curl -s http://localhost:$PORT/ | python -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))"

echo ""
echo "3) Metrics check"
curl -s http://localhost:$PORT/metrics | python -c "import sys,json; d=json.load(sys.stdin); print('DOB Completeness:', d.get('result',{}).get('dob_completeness',0)*100, '%')"

echo ""
echo "4) Run identifier (sample)"
curl -s -X POST http://localhost:$PORT/run-identifier \
  -H "Content-Type: application/json" \
  -d '{"table":"dev_dataset.customers"}' | python -c "import sys,json; d=json.load(sys.stdin); print('Found', d.get('result',{}).get('count',0), 'issues')"

echo ""
echo "========================================="
echo "SMOKE TEST COMPLETE"
echo "========================================="
