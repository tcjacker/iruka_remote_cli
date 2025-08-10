import React, { useState, useEffect } from 'react';
import { 
    Modal, Box, Typography, TextField, Button, Select, MenuItem, FormControl, 
    InputLabel, RadioGroup, FormControlLabel, Radio, CircularProgress 
} from '@mui/material';

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

function NewEnvironmentModal({ open, handleClose, project, onCreated }) {
  const [envName, setEnvName] = useState('');
  const [baseImage, setBaseImage] = useState('');
  const [images, setImages] = useState([]);
  const [branchMode, setBranchMode] = useState('new'); // 'new' or 'existing'
  const [existingBranch, setExistingBranch] = useState('');
  const [remoteBranches, setRemoteBranches] = useState([]);
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);

  useEffect(() => {
    if (open) {
      // Reset fields
      setEnvName('');
      setBaseImage('');
      setBranchMode('new');
      setExistingBranch('');
      setRemoteBranches([]);
      
      // Fetch docker images
      fetch('http://localhost:8000/api/docker-images')
        .then(res => res.json())
        .then(data => setImages(data))
        .catch(err => console.error("Failed to fetch images:", err));
    }
  }, [open]);

  useEffect(() => {
    if (branchMode === 'existing' && open) {
      setIsLoadingBranches(true);
      const repoUrl = encodeURIComponent(project.git_repo);
      const token = project.git_token || '';
      fetch(`http://localhost:8000/api/git/branches?repo_url=${repoUrl}&token=${token}`)
        .then(res => {
            if (!res.ok) throw new Error('Failed to fetch branches. Check repo URL and token.');
            return res.json();
        })
        .then(data => {
            setRemoteBranches(data);
            if (data.length > 0) {
                setExistingBranch(data[0]); // Default to the first branch
            }
        })
        .catch(err => {
            alert(`Error: ${err.message}`);
            console.error("Failed to fetch branches:", err)
        })
        .finally(() => setIsLoadingBranches(false));
    }
  }, [branchMode, open, project]);

  const handleCreate = () => {
    if (!envName || !baseImage || (branchMode === 'existing' && !existingBranch)) {
      alert('Please fill all required fields.');
      return;
    }
    
    const body = { 
      name: envName, 
      base_image: baseImage,
      branch_mode: branchMode,
      existing_branch: branchMode === 'existing' ? existingBranch : null
    };

    fetch(`http://localhost:8000/api/projects/${project.name}/environments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    .then(res => {
      if (!res.ok) throw new Error('Failed to create environment');
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