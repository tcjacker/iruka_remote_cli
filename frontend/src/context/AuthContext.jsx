import React, { useState, useContext } from 'react';

// Create the context
const AuthContext = React.createContext(null);

// Create a custom hook to use the auth context
export function useAuth() {
  return useContext(AuthContext);
}

// Create the provider component
export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('authToken'));

  const handleLogin = (newToken) => {
    if (newToken) {
      localStorage.setItem('authToken', newToken);
    } else {
      localStorage.removeItem('authToken');
    }
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
  };

  // The value passed to the provider
  const value = {
    token,
    setToken: handleLogin, // Provide a consistent function name
    logout: handleLogout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
