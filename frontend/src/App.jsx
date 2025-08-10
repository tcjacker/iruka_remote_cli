import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';
import Header from './components/Header';
import Workspace from './pages/Workspace';
import NewProject from './pages/NewProject';

function App() {
  return (
    <Router>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header />
        <Box component="main" sx={{ flexGrow: 1, bgcolor: '#121212', display: 'flex' }}>
          {/* The Workspace route will now handle the sidebar and content */}
          <Routes>
            <Route path="/" element={<NewProject />} />
            <Route path="/project/:projectName" element={<Workspace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

export default App;
