

```powershell
.\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload --port 8080
```

**Backend will be available at**: http://127.0.0.1:8080  
**API Documentation**: http://127.0.0.1:8080/docs

### Step 3: Start Frontend (Terminal 2)

```powershell
.\.venv\Scripts\Activate.ps1; streamlit run frontend/app.py
```

**Frontend will be available at**: http://localhost:8501

---

## Complete One-Liner (if running in same terminal)

If you want to run both in sequence (frontend after backend stops):

```powershell
.\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload --port 8080
```

Then in another terminal:

```powershell
.\.venv\Scripts\Activate.ps1; streamlit run frontend/app.py
```

---

## Access the Application

- **Web Interface**: http://localhost:8501
- **API Docs**: http://127.0.0.1:8080/docs
- **API Root**: http://127.0.0.1:8080

---

## Troubleshooting

If you get a "port already in use" error:
- Backend port (8080): `netstat -ano | findstr :8080`
- Frontend port (8501): `netstat -ano | findstr :8501`

To kill a process by port:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess | Stop-Process -Force
```
