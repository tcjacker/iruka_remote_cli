import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Snackbar } from '@mui/material';
import { useAuth } from '../context/AuthContext';

function ProjectSettings({ project, onDataChange }) {
  const [geminiToken, setGeminiToken] = useState(project.gemini_token || '');
  const [gitToken, setGitToken] = useState(project.git_token || '');
  const [gitRepo, setGitRepo] = useState(project.git_repo || '');
  const [anthropicAuthToken, setAnthropicAuthToken] = useState(project.anthropic_auth_token || '');
  const [anthropicBaseUrl, setAnthropicBaseUrl] = useState(project.anthropic_base_url || '');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const { token } = useAuth();

  const handleSave = () => {
    // Check if token exists before making authenticated requests
    if (!token) {
      console.warn('No auth token available, cannot save project settings');
      return;
    }
    
    const settings = {
        gemini_token: geminiToken,
        git_token: gitToken,
        git_repo: gitRepo,
        anthropic_auth_token: anthropicAuthToken,
        anthropic_base_url: anthropicBaseUrl
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
        Project Configuration
      </Typography>
      <TextField
        label="Git Repository URL"
        type="text"
        fullWidth
        margin="normal"
        variant="outlined"
        value={gitRepo}
        onChange={(e) => setGitRepo(e.target.value)}
        helperText="Git repository URL (e.g., github.com/user/repo). Used for creating environments."
        sx={{ input: { color: 'white' }, label: { color: 'gray' } }}
      />
      <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
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
        label="Anthropic Auth Token"
        type="password"
        fullWidth
        margin="normal"
        variant="outlined"
        value={anthropicAuthToken}
        onChange={(e) => setAnthropicAuthToken(e.target.value)}
        helperText="This token will be injected into new Claude environments as ANTHROPIC_AUTH_TOKEN."
        sx={{ input: { color: 'white' }, label: { color: 'gray' } }}
      />
      <TextField
        label="Anthropic Base URL"
        type="text"
        fullWidth
        margin="normal"
        variant="outlined"
        value={anthropicBaseUrl}
        onChange={(e) => setAnthropicBaseUrl(e.target.value)}
        helperText="Optional. Custom base URL for Claude API. Leave empty to use default."
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
        helperText="Used for accessing private repositories. Required if the Git repository is private."
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
