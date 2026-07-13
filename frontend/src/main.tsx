import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import './index.css'
import App from './App.tsx'
import { getGoogleClientId } from '@/services/auth'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* clientId may be "" in environments without Google sign-in configured;
       GoogleAuthButton itself hides the button in that case. */}
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </GoogleOAuthProvider>
  </StrictMode>,
)
