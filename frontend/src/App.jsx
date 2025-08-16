import React, { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from 'react-router-dom';
import { Box, CssBaseline, CircularProgress } from '@mui/material';
import Header from './components/Header';
import Workspace from './pages/Workspace';
import NewProject from './pages/NewProject';
import Login from './pages/Login';
import Initialize from './pages/Initialize';
import Register from './pages/Register';
import { AuthProvider, useAuth } from './context/AuthContext';

// --- Protected Route: Renders child routes if logged in, otherwise redirects to /login ---
function ProtectedRoute() {
  const { token } = useAuth();
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

// --- App Layout: The main UI for authenticated users ---
function AppLayout() {
  const { logout } = useAuth();
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header onLogout={logout} />
      <Box component="main" sx={{ flexGrow: 1, bgcolor: '#121212', display: 'flex' }}>
        <Outlet />
      </Box>
    </Box>
  );
}

// --- App Component: Defines the application's routes ---
function App() {
  const { token, login } = useAuth();

  const handleLogin = async (username, password) => {
    const response = await fetch('http://localhost:8000/api/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await response.json();
    login(data.access_token); // Use the login function from context
  };

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/initialize" element={<Initialize />} />
      
      {/* If user is logged in, /login and /register redirect to home */}
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />} />
      <Route path="/register" element={token ? <Navigate to="/" replace /> : <Register />} />

      {/* Protected routes are nested here */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<NewProject />} />
          <Route path="/project/:projectName" element={<Workspace />} />
        </Route>
      </Route>
    </Routes>
  );
}

// --- Initializer: Checks if the app needs setup before rendering the main app ---
function Initializer() {
  const [needsInitialization, setNeedsInitialization] = useState(null);

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/auth/status');
        if (!response.ok) throw new Error('Could not connect to backend.');
        const data = await response.json();
        setNeedsInitialization(!data.has_users);
      } catch (error) {
        console.error('Failed to check auth status:', error);
        setNeedsInitialization(false); // Default to normal flow if backend check fails
      }
    };
    checkAuthStatus();
  }, []);

  if (needsInitialization === null) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  // If initialization is needed, all routes should point to the initialize page.
  if (needsInitialization) {
    return (
        <Routes>
            <Route path="/initialize" element={<Initialize />} />
            <Route path="*" element={<Navigate to="/initialize" replace />} />
        </Routes>
    );
  }

  // If initialization is not needed, render the main app.
  return <App />;
}

// --- Root Component: Provides context and routing ---
export default function Root() {
  return (
    <Router>
      <AuthProvider>
        <CssBaseline />
        <Initializer />
      </AuthProvider>
    </Router>
  );
}