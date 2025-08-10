import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';

function NewProject() {
  const [name, setName] = useState('');
  const [gitRepo, setGitRepo] = useState('');
  const [gitToken, setGitToken] = useState('');
  const [geminiToken, setGeminiToken] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();
    const projectData = { name, git_repo: gitRepo, git_token: gitToken, gemini_token: geminiToken };

    fetch('http://localhost:8000/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(projectData),
    })
      .then(response => response.json())
      .then(data => {
        if (data.name) {
          navigate(`/project/${data.name}`);
        } else {
          // Handle error
          console.error('Error creating project:', data);
        }
      })
      .catch(error => console.error('Error creating project:', error));
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
