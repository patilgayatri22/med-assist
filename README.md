# med-assist

Monitoring dashboard for the MedAssist agent (vision → checks → dispense / flags).

## Frontend (dashboard)

The dashboard lives in `frontend/`. Run it:

```bash
cd frontend
npm install
npm run dev
```

Then open the URL shown (e.g. http://localhost:5173). Use **Run demo** to cycle through scripted states (all pass + arm phases, or halt on allergy); use **Live** when connected to the agent/backend.