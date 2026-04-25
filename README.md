# DisasterGuard AI

Smart Multi-Hazard Prediction & Alert System

## Features

- Firebase email/password authentication
- Protected routes for dashboard, alerts, map, mitigation, live data, and predictor
- India-focused hazard zonation dashboard
- Live data to map interaction
- OTP-style simulated phone alert setup with browser notifications
- Deployment-ready Flask backend and Vite frontend

## Firebase Setup

1. Create a Firebase project in the Firebase console.
2. Enable `Authentication`.
3. Turn on the `Email/Password` sign-in provider.
4. Copy your Firebase web app config values.
5. Create a local `.env` file for the frontend from `.env.example`.
6. Fill in the `VITE_FIREBASE_*` variables.

## Frontend Environment Variables

- `VITE_API_URL`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

Legacy `REACT_APP_*` fallbacks are also supported for compatibility, but this project runs on Vite and prefers `VITE_*`.

## Backend Local Run

```bash
cd backend
pip install -r requirements.txt
python app.py
```

## Frontend Local Run

```bash
cd frontend
npm install
npm run dev
```

## Render Backend Deployment

1. Push the repository to GitHub.
2. Create a new Render Web Service.
3. Use the root `render.yaml` file.
4. Set any required backend environment variables in Render.
5. Deploy the service.

The backend starts with:

```bash
cd backend && python app.py
```

## Vercel Frontend Deployment

1. Import the repository into Vercel.
2. Set the frontend environment variables from `.env.example`.
3. Add `VITE_API_URL` pointing to your Render backend URL.
4. Deploy the frontend.

## Build Check

```bash
cd frontend
npm run build
```

## Authentication Flow

- Users sign up with Firebase email/password auth.
- `onAuthStateChanged` keeps auth state synced globally.
- Protected routes redirect unauthenticated users to `/login`.
- Logout is available from the top navbar.

## Notes

- OTP phone alerts are simulated for demo purposes.
- Browser notifications are triggered when permission is granted.
- Existing prediction and API functionality remains unchanged.
