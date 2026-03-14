# MedAssist Monitor (frontend)

Dashboard for the MedAssist agent.

- **Backend (recommended, no Supabase):** Set `VITE_API_URL` (e.g. `http://localhost:8000`) in `.env.local`. Run state and dispense log come from the backend. In the header, choose **Logs: Backend**. Start the backend with `cd ../backend && uvicorn api_server:app --reload --port 8000`.
- **Run demo:** Use scripted flows; **Logs: Demo** uses mock data only.
- **Logs:** **Demo** (mock), **Backend** (requires `VITE_API_URL`), or **Supabase** (optional; requires `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`).

## Deploy on Vercel

1. **From this repo (monorepo):** In the Vercel project, set **Root Directory** to `med-assist/frontend` so the app builds from this folder.
2. **Build:** Vercel will use `npm run build` and output `dist` (see `vercel.json`).
3. **Environment variables:** In Vercel → Project → Settings → Environment Variables, add:
   - `VITE_API_URL` – backend API URL (e.g. your deployed backend) for **Logs: Backend** and run state.
   - `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` – optional; only needed for **Logs: Supabase**.

You can run with backend only (no Supabase): set `VITE_API_URL` and use **Logs: Backend**.

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
