import React, { useState, useEffect } from 'react';
import { 
    Modal, Box, Typography, TextField, Button, Select, MenuItem, FormControl, 
    InputLabel, RadioGroup, FormControlLabel, Radio, CircularProgress, Checkbox 
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import apiConfig from '../config/api';

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 500,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

// Cache for branch data to avoid repeated API calls
const branchCache = new Map();

function NewEnvironmentModal({ open, handleClose, project, onCreated }) {
  const [envName, setEnvName] = useState('');
  const [baseImage, setBaseImage] = useState('');
  const [images, setImages] = useState([]);
  const [branchMode, setBranchMode] = useState('new');
  const [existingBranch, setExistingBranch] = useState('');
  const [remoteBranches, setRemoteBranches] = useState([]);
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);
  const [aiTool, setAiTool] = useState('gemini'); // "gemini" or "claude"
  const [geminiUseGoogleLogin, setGeminiUseGoogleLogin] = useState(false); // Whether to use Google login for Gemini
  const { token } = useAuth(); // Get the auth token

  useEffect(() => {
    if (open && token) {
      // Reset fields
      setEnvName('');
      setBaseImage('');
      setBranchMode('new');
      setExistingBranch('');
      setRemoteBranches([]);
      setAiTool('gemini');
      setGeminiUseGoogleLogin(false);
      
      // Fetch docker images with auth
      fetch(apiConfig.buildApiUrl('/api/docker-images'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => setImages(data))
        .catch(err => console.error("Failed to fetch images:", err));
    }
  }, [open, token]);

  useEffect(() => {
    if (branchMode === 'existing' && open && token) {
      const repoUrl = encodeURIComponent(project.git_repo);
      const gitApiToken = project.git_token || '';
      const cacheKey = `${project.git_repo}:${gitApiToken}`;
      
      // Check cache first
      if (branchCache.has(cacheKey)) {
        const cachedBranches = branchCache.get(cacheKey);
        setRemoteBranches(cachedBranches);
        if (cachedBranches.length > 0) setExistingBranch(cachedBranches[0]);
        return;
      }
      
      setIsLoadingBranches(true);
      
      // Add timeout to the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15-second timeout
      
      // Fetch remote branches with auth and timeout - using project_name instead of token for security
      fetch(apiConfig.buildApiUrl(`/api/git/branches?repo_url=${repoUrl}&project_name=${encodeURIComponent(project.name)}`), {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: controller.signal
      })
        .then(res => {
            clearTimeout(timeoutId);
            if (!res.ok) throw new Error('Failed to fetch branches. Check repo URL and token.');
            return res.json();
        })
        .then(data => {
            // Cache the result for 5 minutes
            branchCache.set(cacheKey, data);
            setTimeout(() => branchCache.delete(cacheKey), 5 * 60 * 1000);
            
            setRemoteBranches(data);
            if (data.length > 0) setExistingBranch(data[0]);
        })
        .catch(err => {
            clearTimeout(timeoutId);
            console.error("Failed to fetch branches:", err);
            
            if (err.name === 'AbortError') {
              alert('Request timed out. Please check your network connection and try again.');
            } else {
              // Show the actual error message from backend
              alert(`Error fetching branches: ${err.message}\n\nPlease check:\n- Git repository URL is correct\n- Git token has proper permissions\n- Repository is accessible`);
            }
            
            // Only set default branches as a last resort
            const defaultBranches = ['main', 'master'];
            setRemoteBranches(defaultBranches);
            setExistingBranch(defaultBranches[0]);
        })
        .finally(() => setIsLoadingBranches(false));
    }
  }, [branchMode, open, project, token]);

  const handleCreate = () => {
    if (!envName || !baseImage || (branchMode === 'existing' && !existingBranch)) {
      alert('Please fill all required fields.');
      return;
    }
    
    const body = { 
      name: envName, 
      base_image: baseImage,
      branch_mode: branchMode,
      existing_branch: branchMode === 'existing' ? existingBranch : null,
      ai_tool: aiTool,
      gemini_use_google_login: aiTool === 'gemini' ? geminiUseGoogleLogin : false
    };

    // Create environment with auth
    fetch(apiConfig.buildApiUrl(`/api/projects/${project.name}/environments`), {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(body),
    })
    .then(async res => {
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to create environment');
      }
      return res.json();
    })
    .then(() => {
      onCreated();
      handleClose();
    })
    .catch(err => {
      alert(`Error: ${err.message}`);
    });
  };

  return (
    <Modal open={open} onClose={handleClose}>
      <Box sx={style}>
        <Typography variant="h6" component="h2">Create New Environment</Typography>
        <TextField label="Environment Name" fullWidth required margin="normal" value={envName} onChange={(e) => setEnvName(e.target.value)} />
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Base Image</InputLabel>
          <Select value={baseImage} label="Base Image" onChange={(e) => setBaseImage(e.target.value)}>
            {images.map(img => <MenuItem key={img} value={img}>{img}</MenuItem>)}
          </Select>
        </FormControl>
        
        <FormControl component="fieldset" margin="normal">
          <RadioGroup row value={branchMode} onChange={(e) => setBranchMode(e.target.value)}>
            <FormControlLabel value="new" control={<Radio />} label="Create new branch" />
            <FormControlLabel value="existing" control={<Radio />} label="Use existing branch" />
          </RadioGroup>
        </FormControl>
        
        <FormControl component="fieldset" margin="normal">
          <RadioGroup row value={aiTool} onChange={(e) => setAiTool(e.target.value)}>
            <FormControlLabel value="gemini" control={<Radio />} label="Gemini CLI" />
            <FormControlLabel value="claude" control={<Radio />} label="Claude Code" />
          </RadioGroup>
        </FormControl>
        
        {aiTool === 'gemini' && (
          <FormControlLabel
            control={
              <Checkbox
                checked={geminiUseGoogleLogin}
                onChange={(e) => setGeminiUseGoogleLogin(e.target.checked)}
              />
            }
            label="Use Google Login for Gemini CLI (instead of API Key)"
          />
        )}

        {branchMode === 'existing' && (
          <FormControl fullWidth margin="normal" required disabled={isLoadingBranches}>
            <InputLabel>Remote Branch</InputLabel>
            {isLoadingBranches ? (
              <Box sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
                <CircularProgress size={20} sx={{ mr: 2 }} />
                <Typography>Loading branches...</Typography>
              </Box>
            ) : (
              <Select value={existingBranch} label="Remote Branch" onChange={(e) => setExistingBranch(e.target.value)}>
                {remoteBranches.map(branch => <MenuItem key={branch} value={branch}>{branch}</MenuItem>)}
              </Select>
            )}
          </FormControl>
        )}

        <Button variant="contained" onClick={handleCreate} sx={{ mt: 2 }}>Create</Button>
      </Box>
    </Modal>
  );
}

export default NewEnvironmentModal;
