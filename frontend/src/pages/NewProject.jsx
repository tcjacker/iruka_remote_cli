import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';
import { useAuth } from '../context/AuthContext';
import apiConfig from '../config/api';

function NewProject() {
  const [name, setName] = useState('');
  const [gitRepo, setGitRepo] = useState('');
  const [gitToken, setGitToken] = useState('');
  const [geminiToken, setGeminiToken] = useState('');
  const navigate = useNavigate();
  const { token } = useAuth(); // Get the auth token

  const handleSubmit = (event) => {
    event.preventDefault();
    const projectData = { name, git_repo: gitRepo, git_token: gitToken, gemini_token: geminiToken };

    fetch(apiConfig.buildApiUrl('/api/projects'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`, // Add the Authorization header
      },
      body: JSON.stringify(projectData),
    })
      .then(response => {
        if (!response.ok) {
          // Handle non-2xx responses
          return response.json().then(err => { throw new Error(err.detail || 'Failed to create project') });
        }
        return response.json();
      })
      .then(data => {
        if (data.name) {
          navigate(`/project/${data.name}`);
        }
      })
      .catch(error => console.error('Error creating project:', error.message));
  };

  return (
    <Paper sx={{ p: 4, maxWidth: 600, margin: 'auto', bgcolor: '#2d2d2d', color: 'white' }}>
      <Typography variant="h5" mb={3}>Create New Project</Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label="Project Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          required
          margin="normal"
          InputLabelProps={{ style: { color: 'white' } }}
          inputProps={{ style: { color: 'white' } }}
        />
        <TextField
          label="Git Repository URL"
          value={gitRepo}
          onChange={(e) => setGitRepo(e.target.value)}
          fullWidth
          required
          margin="normal"
          InputLabelProps={{ style: { color: 'white' } }}
          inputProps={{ style: { color: 'white' } }}
        />
        <TextField
          label="Git Token (Optional)"
          value={gitToken}
          onChange={(e) => setGitToken(e.target.value)}
          fullWidth
          margin="normal"
          type="password"
          InputLabelProps={{ style: { color: 'white' } }}
          inputProps={{ style: { color: 'white' } }}
        />
        <TextField
          label="Gemini Token (Optional)"
          value={geminiToken}
          onChange={(e) => setGeminiToken(e.target.value)}
          fullWidth
          margin="normal"
          type="password"
          InputLabelProps={{ style: { color: 'white' } }}
          inputProps={{ style: { color: 'white' } }}
        />
        <Button type="submit" variant="contained" sx={{ mt: 3 }}>
          Create Project
        </Button>
      </form>
    </Paper>
  );
}

export default NewProject;
