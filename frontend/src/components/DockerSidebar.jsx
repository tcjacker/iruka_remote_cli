import React, { useState } from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemText, Typography, Box, Button, IconButton } from '@mui/material';
import { Add, Stop, Delete } from '@mui/icons-material';
import NewEnvironmentModal from './NewEnvironmentModal';
import { useAuth } from '../context/AuthContext';

const DRAWER_WIDTH = 280;

function DockerSidebar({ project, onEnvSelect, selectedEnvId, onDataChange }) {
  const [modalOpen, setModalOpen] = useState(false);
  const { token } = useAuth();

  if (!project) {
    return null;
  }

  // Define the authenticated request helper function ONCE.
  const makeAuthenticatedRequest = (url, options = {}) => {
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
      .then(() => onDataChange());
  };

  const handleDelete = (envId, e) => {
    e.stopPropagation();
    makeAuthenticatedRequest(`http://localhost:8000/api/projects/${project.name}/environments/${envId}`, { method: 'DELETE' })
      .then(() => onDataChange());
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
                  <IconButton size="small" onClick={(e) => handleStop(env.id, e)} disabled={env.status !== 'running'} title="Stop">
                    <Stop fontSize="small" sx={{ color: env.status !== 'running' ? 'gray' : 'red' }} />
                  </IconButton>
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
                  secondaryTypographyProps={{ style: { color: env.status === 'running' ? '#4caf50' : 'gray' } }}
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