import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Select,
  MenuItem,
  FormControl,
  Box,
  Button,
} from "@mui/material";
import { useAuth } from '../context/AuthContext';

function Header({ onLogout }) {
  const [projects, setProjects] = useState([]);
  const [selectedValue, setSelectedValue] = useState("");
  const { projectName } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  
  console.log('Header component rendered, token:', token ? token.substring(0, 20) + '...' : 'null');

  // This function is now ONLY called when the user interacts with the dropdown.
  const fetchProjects = () => {
    // Check if token exists before making the request
    if (!token) {
      console.warn('No auth token available, skipping projects fetch');
      return;
    }
    
    console.log('Fetching projects with token:', token.substring(0, 20) + '...'); // Log first 20 chars of token for debugging
    
    fetch("http://localhost:8000/api/projects", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        console.log('Projects fetch response status:', res.status);
        if (!res.ok) throw new Error("Failed to fetch projects");
        return res.json();
      })
      .then((data) => {
        console.log('Projects fetch successful, data:', data);
        setProjects(data);
        // After fetching, ensure the selected value is still valid
        if (projectName && !data.some(p => p.name === projectName)) {
            navigate('/');
        }
      })
      .catch((err) => console.error('Projects fetch error:', err));
  };

  // This effect now ONLY syncs the URL parameter to the dropdown's display value.
  // It no longer fetches data.
  useEffect(() => {
    if (projectName) {
        setSelectedValue(projectName);
    } else {
        setSelectedValue("");
    }
  }, [projectName]);

  const handleProjectChange = (event) => {
    const newProjectName = event.target.value;
    setSelectedValue(newProjectName);
    navigate(newProjectName ? `/project/${newProjectName}` : "/");
  };

  return (
    <AppBar
      position="static"
      sx={{ bgcolor: "#2d2d2d", zIndex: (theme) => theme.zIndex.drawer + 1 }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Iruka Remote
        </Typography>

        <FormControl sx={{ m: 1, minWidth: 200 }} size="small">
          <Select
            value={selectedValue}
            onChange={handleProjectChange}
            onOpen={fetchProjects} // <-- This is now the ONLY place projects are fetched from.
            displayEmpty
            renderValue={(selected) => {
              if (!selected) return <em>Select a Project</em>;
              return selected;
            }}
            inputProps={{ "aria-label": "Without label" }}
            sx={{
              color: "white",
              ".MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(255, 255, 255, 0.23)",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "white",
              },
              ".MuiSvgIcon-root": { color: "white" },
            }}
          >
            {projects.map((p) => (
              <MenuItem key={p.name} value={p.name}>
                {p.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button color="inherit" onClick={() => navigate("/")}>
          New Project
        </Button>
        <Button color="inherit" onClick={onLogout}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  );
}

export default Header;