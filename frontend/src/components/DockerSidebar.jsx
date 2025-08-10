import React, { useState } from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemText, Typography, Box, Button, IconButton } from '@mui/material';
import { Add, Stop, Delete } from '@mui/icons-material';
import NewEnvironmentModal from './NewEnvironmentModal';

const DRAWER_WIDTH = 280;

function DockerSidebar({ project, onEnvSelect, selectedEnvId, onDataChange }) { // Receive selectedEnvId
  const [modalOpen, setModalOpen] = useState(false);

  if (!project) {
    return null;
  }

  const handleStop = (envId, e) => {
    e.stopPropagation();
    fetch(`http://localhost:8000/api/projects/${project.name}/environments/${envId}/stop`, { method: 'POST' })
      .then(() => onDataChange());
  };

  const handleDelete = (envId, e) => {
    e.stopPropagation();
    fetch(`http://localhost:8000/api/projects/${project.name}/environments/${envId}`, { method: 'DELETE' })
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
              {/* This is the critical fix */}
              <ListItemButton 
                onClick={() => onEnvSelect(env.id)} 
                selected={selectedEnvId === env.id} // Apply selected state
                sx={{
                    // Custom styles for the selected item
                    '&.Mui-selected': {
                        backgroundColor: 'rgba(0, 123, 255, 0.24)', // A pleasant blue highlight
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
