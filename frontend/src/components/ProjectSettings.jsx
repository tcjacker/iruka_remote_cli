import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Snackbar } from '@mui/material';
import { useAuth } from '../context/AuthContext';

function ProjectSettings({ project, onDataChange }) {
  const [geminiToken, setGeminiToken] = useState(project.gemini_token || '');
  const [gitToken, setGitToken] = useState(project.git_token || '');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const { token } = useAuth();

  const handleSave = () => {
    const settings = {
        gemini_token: geminiToken,
        git_token: gitToken
    };

    fetch(`http://localhost:8000/api/projects/${project.name}/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(settings),
    })
    .then(res => {
      if (!res.ok) throw new Error('Failed to save settings');
      setSnackbarOpen(true);
      onDataChange();
    })
    .catch(err => console.error("Save failed:", err));
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>
        Authentication Tokens
      </Typography>
      <TextField
        label="Gemini API Key"
        type="password"
        fullWidth
        margin="normal"
        variant="outlined"
        value={geminiToken}
        onChange={(e) => setGeminiToken(e.target.value)}
        helperText="This key will be injected into new environments as GEMINI_API_KEY."
        sx={{ input: { color: 'white' }, label: { color: 'gray' } }}
      />
      <TextField
        label="Git Personal Access Token"
        type="password"
        fullWidth
        margin="normal"
        variant="outlined"
        value={gitToken}
        onChange={(e) => setGitToken(e.target.value)}
        helperText="Used for cloning private repositories. Injected as GIT_TOKEN."
        sx={{ input: { color: 'white' }, label: { color: 'gray' } }}
      />
      <Button variant="contained" onClick={handleSave}>
        Save Settings
      </Button>
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message="Settings saved successfully!"
      />
    </Box>
  );
}

export default ProjectSettings;
