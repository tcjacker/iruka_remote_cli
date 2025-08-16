import React, { useState, useContext, useEffect } from 'react';

// 1. Create the context
const AuthContext = React.createContext(null);

// 2. Create a custom hook for easy access to the context
export function useAuth() {
  return useContext(AuthContext);
}

// 3. Create the provider component that will wrap our app
export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  // Load token from localStorage on initial render
  useEffect(() => {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  // Function to update the token
  const login = (newToken) => {
    setToken(newToken);
    localStorage.setItem('authToken', newToken);
  };

  // Function to clear the token
  const logout = () => {
    setToken(null);
    localStorage.removeItem('authToken');
  };

  const value = { token, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}