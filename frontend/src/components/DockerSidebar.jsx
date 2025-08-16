import React, { useState, useEffect } from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemText, Typography, Box, Button, IconButton } from '@mui/material';
import { Add, Stop, Delete, PlayArrow } from '@mui/icons-material';
import NewEnvironmentModal from './NewEnvironmentModal';
import { useAuth } from '../context/AuthContext';

const DRAWER_WIDTH = 280;

function DockerSidebar({ project, onEnvSelect, selectedEnvId, onDataChange }) {
  const [modalOpen, setModalOpen] = useState(false);
  const { token } = useAuth();
  
  // Check environment status periodically for pending environments
  useEffect(() => {
    if (!project || !project.environments || project.environments.length === 0) return;
    
    const pendingEnvs = project.environments.filter(env => env.status === 'pending');
    if (pendingEnvs.length === 0 || !token) return; // Don't check if no token
    
    const interval = setInterval(() => {
      pendingEnvs.forEach(env => {
        fetch(`http://localhost:8000/api/projects/${project.name}/environments/${env.id}/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'running') {
            // Update the environment status
            onDataChange();
          }
        })
        .catch(err => {
          console.error("Failed to check environment status:", err);
          // Handle authentication or other errors appropriately
        });
      });
    }, 5000); // Check every 5 seconds
    
    return () => clearInterval(interval);
  }, [project, token, onDataChange]);

  if (!project) {
    return null;
  }

  const makeAuthenticatedRequest = (url, options = {}) => {
    // Check if token exists before making authenticated requests
    if (!token) {
      console.warn('No auth token available, cannot make authenticated request to:', url);
      return Promise.reject(new Error('No authentication token available'));
    }
    
    const defaultOptions = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };
    return fetch(url, { ...defaultOptions, ...options });
  };

  const handleStop = (envId, e) => {
    e.stopPropagation();
    makeAuthenticatedRequest(`http://localhost:8000/api/projects/${project.name}/environments/${envId}/stop`, { method: 'POST' })
      .then(() => onDataChange())
      .catch(err => {
        console.error('Failed to stop environment:', err);
        // Handle authentication or other errors appropriately
      });
  };

  const handleStart = (envId, e) => {
    e.stopPropagation();
    makeAuthenticatedRequest(`http://localhost:8000/api/projects/${project.name}/environments/${envId}/start`, { method: 'POST' })
      .then(() => onDataChange())
      .catch(err => {
        console.error('Failed to start environment:', err);
        // Handle authentication or other errors appropriately
      });
  };

  const handleDelete = (envId, e) => {
    e.stopPropagation();
    makeAuthenticatedRequest(`http://localhost:8000/api/projects/${project.name}/environments/${envId}`, { method: 'DELETE' })
      .then(() => onDataChange())
      .catch(err => {
        console.error('Failed to delete environment:', err);
        // Handle authentication or other errors appropriately
      });
  };

  return (
    <>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            bgcolor: '#1e1e1e',
            color: 'white',
            top: '64px',
            height: 'calc(100% - 64px)',
          },
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="div">Environments</Typography>
          <Button
            variant="contained"
            size="small"
            startIcon={<Add />}
            onClick={() => setModalOpen(true)}
          >
            New
          </Button>
        </Box>
        <List>
          {project.environments.map((env) => (
            <ListItem key={env.id} disablePadding
              secondaryAction={
                <>
                  {env.status === 'running' ? (
                    <IconButton size="small" onClick={(e) => handleStop(env.id, e)} title="Stop">
                      <Stop fontSize="small" sx={{ color: 'red' }} />
                    </IconButton>
                  ) : (
                    <IconButton size="small" onClick={(e) => handleStart(env.id, e)} title="Start">
                      <PlayArrow fontSize="small" sx={{ color: '#4caf50' }} />
                    </IconButton>
                  )}
                  <IconButton size="small" onClick={(e) => handleDelete(env.id, e)} title="Delete">
                    <Delete fontSize="small" />
                  </IconButton>
                </>
              }
            >
              <ListItemButton 
                onClick={() => onEnvSelect(env.id)} 
                selected={selectedEnvId === env.id}
                sx={{
                    '&.Mui-selected': {
                        backgroundColor: 'rgba(0, 123, 255, 0.24)',
                        '&:hover': {
                            backgroundColor: 'rgba(0, 123, 255, 0.3)',
                        }
                    },
                }}
              >
                <ListItemText 
                  primary={env.id} 
                  primaryTypographyProps={{ style: { color: 'white' } }}
                  secondary={`Status: ${env.status}`}
                  secondaryTypographyProps={{ style: { color: env.status === 'running' ? '#4caf50' : env.status === 'pending' ? '#ff9800' : 'gray' } }}
                />
              </ListItemButton>
            </ListItem>
          ))}
          {project.environments.length === 0 && (
              <ListItem>
                  <ListItemText primary="No environments created." primaryTypographyProps={{ style: { color: 'gray' } }} />
              </ListItem>
          )}
        </List>
      </Drawer>
      <NewEnvironmentModal 
        open={modalOpen}
        handleClose={() => setModalOpen(false)}
        project={project}
        onCreated={onDataChange}
      />
    </>
  );
}

export default DockerSidebar;