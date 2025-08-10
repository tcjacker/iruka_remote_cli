import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Select, MenuItem, FormControl, Box, Button } from '@mui/material';

function Header() {
  const [projects, setProjects] = useState([]);
  const [selectedValue, setSelectedValue] = useState(''); // Dedicated state for the dropdown's value
  const { projectName } = useParams();
  const navigate = useNavigate();

  // Effect 1: Fetch projects once on component mount
  useEffect(() => {
    fetch('http://localhost:8000/api/projects')
      .then(res => res.json())
      .then(data => {
        setProjects(data);
      })
      .catch(err => console.error("Failed to fetch projects:", err));
  }, []);

  // Effect 2: This is the key fix. It synchronizes the dropdown's value
  // with the URL, but only after the project list is available.
  useEffect(() => {
    // Check if the project from the URL exists in our fetched list
    if (projectName && projects.some(p => p.name === projectName)) {
      setSelectedValue(projectName);
    } else {
      // If it doesn't exist (e.g., on the '/' page or a bad URL), reset the selection
      setSelectedValue('');
    }
  }, [projectName, projects]); // This effect re-runs if the URL changes OR the project list loads

  const handleProjectChange = (event) => {
    const newProjectName = event.target.value;
    // We don't need to manually set the state here. The `useEffect` above will
    // automatically handle it once the navigation completes and `projectName` updates.
    navigate(newProjectName ? `/project/${newProjectName}` : '/');
  };

  return (
    <AppBar position="static" sx={{ bgcolor: '#2d2d2d', zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Iruka Remote
        </Typography>
        
        <FormControl sx={{ m: 1, minWidth: 200 }} size="small">
          <Select
            value={selectedValue} // The Select's value is now reliably controlled by our state
            onChange={handleProjectChange}
            displayEmpty
            inputProps={{ 'aria-label': 'Without label' }}
            sx={{ color: 'white', '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' }, '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'white' }, '.MuiSvgIcon-root': { color: 'white' } }}
          >
            <MenuItem value="">
              <em>Select a Project</em>
            </MenuItem>
            {projects.map((p) => (
              <MenuItem key={p.name} value={p.name}>{p.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button color="inherit" onClick={() => navigate('/')}>New Project</Button>
      </Toolbar>
    </AppBar>
  );
}

export default Header;