import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import './index.css'
import App from './App.tsx'

// VITE_GOOGLE_CLIENT_ID must equal the client ID configured in Google Cloud
// Console → APIs & Services → Credentials → OAuth 2.0 Client IDs.
// For local dev, add http://localhost:5173 to "Authorized JavaScript origins"
// in that same client ID config, then save and wait ~5 minutes to propagate.
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* clientId may be "" in environments without Google sign-in configured;
       GoogleAuthButton itself hides the button in that case. */}
    <GoogleOAuthProvider
      clientId={googleClientId}
      onScriptLoadError={() => {
        console.warn(
          '[CareerVerse] Google Identity Services script failed to load. ' +
          'Check that http://localhost:5173 is in the "Authorized JavaScript origins" ' +
          'list for client ID ' + googleClientId + ' in Google Cloud Console.'
        )
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </GoogleOAuthProvider>
  </StrictMode>,
)
