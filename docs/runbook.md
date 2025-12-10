# AgentX Runbook

## Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Run backend: `cd backend && python main.py`
3. Run frontend: `cd frontend && streamlit run app.py`
4. Run demo: `./run_demo.sh`

## Development

- Agent code in `agent/` directory
- Add new tools in `agent/tools.py`
- Update SQL templates in `sql/` directory
