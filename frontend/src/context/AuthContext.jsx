import React, { useState, useContext } from 'react';

// 1. Create the context
const AuthContext = React.createContext(null);

// 2. Create a custom hook for easy access to the context
export function useAuth() {
  return useContext(AuthContext);
}

// 3. Create the provider component that will wrap our app
export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  // Function to update the token
  const login = (newToken) => {
    setToken(newToken);
  };

  // Function to clear the token
  const logout = () => {
    setToken(null);
  };

  const value = { token, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}