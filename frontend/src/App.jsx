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

// --- Protected Route ---
function ProtectedRoute() {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

// --- App Layout ---
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

// --- Main App Component ---
function App() {
  const [needsInitialization, setNeedsInitialization] = useState(false);
  const [authStatusChecked, setAuthStatusChecked] = useState(false);
  const { token, setToken } = useAuth();

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/auth/status');
        if (!response.ok) throw new Error('Could not connect to backend.');
        const data = await response.json();
        setNeedsInitialization(!data.has_users);
      } catch (error) {
        console.error('Failed to check auth status:', error);
      } finally {
        setAuthStatusChecked(true);
      }
    };
    checkAuthStatus();
  }, []);

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
    setToken(data.access_token);
  };

  if (!authStatusChecked) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Routes>
      {/* Redirect logic */}
      <Route
        path="/"
        element={
          needsInitialization ? (
            <Navigate to="/initialize" />
          ) : !token ? (
            <Navigate to="/login" />
          ) : (
            // If logged in, proceed to the main layout
            <AppLayout />
          )
        }
      >
        {/* Nested routes for the main app layout */}
        <Route index element={<NewProject />} />
        <Route path="project/:projectName" element={<Workspace />} />
      </Route>

      {/* Standalone routes */}
      <Route path="/initialize" element={<Initialize />} />
      <Route path="/login" element={<Login onLogin={handleLogin} />} />
      <Route path="/register" element={<Register />} />

      {/* Catch-all redirect */}
      <Route
        path="*"
        element={<Navigate to="/" />}
      />
    </Routes>
  );
}

// --- Root Component ---
export default function Root() {
  return (
    <Router>
      <AuthProvider>
        <CssBaseline />
        <App />
      </AuthProvider>
    </Router>
  );
}
