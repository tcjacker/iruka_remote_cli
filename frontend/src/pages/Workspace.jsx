import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Shell from '../components/Shell';
import DockerSidebar from '../components/DockerSidebar';
import ProjectSettings from '../components/ProjectSettings';
import { Box, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ExpandMore } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

function Workspace() {
  const { projectName } = useParams();
  const [project, setProject] = useState(null);
  const [selectedEnvId, setSelectedEnvId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { token } = useAuth();

  const fetchProjectData = () => {
    // No need to check for token here, ProtectedRoute already did it.
    setIsLoading(true);
    fetch('http://localhost:8000/api/projects', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch project data');
        return res.json();
      })
      .then(projects => {
        const currentProject = projects.find(p => p.name === projectName);
        setProject(currentProject);
        if (currentProject && !currentProject.environments.some(e => e.id === selectedEnvId)) {
          setSelectedEnvId(null);
        }
      })
      .catch(error => {
        console.error('Error fetching project:', error.message);
        setProject(null); // Clear project on error
      })
      .finally(() => setIsLoading(false));
  };

  // This useEffect now safely relies on ProtectedRoute ensuring the token exists.
  useEffect(() => {
    if (projectName) {
      fetchProjectData();
    }
  }, [projectName, token]); // Keep token dependency to refetch if it ever changes

  const handleEnvSelect = (envId) => {
    const env = project?.environments.find(e => e.id === envId);
    if (env?.status === 'running') {
      setSelectedEnvId(envId);
    } else {
      setSelectedEnvId(null);
    }
  };

  if (isLoading) {
    return <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>;
  }

  if (!project) {
    return <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Typography sx={{ color: 'gray' }}>Project not found or access denied.</Typography></Box>;
  }

  return (
    <>
      <DockerSidebar 
        project={project} 
        onEnvSelect={handleEnvSelect} 
        selectedEnvId={selectedEnvId} 
        onDataChange={fetchProjectData} 
      />
      <Box component="main" sx={{ flexGrow: 1, p: 3, width: `calc(100% - 280px)` }}>
        <Accordion sx={{ bgcolor: '#2d2d2d', color: 'white', mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
            <Typography>Project Settings</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ProjectSettings project={project} onDataChange={fetchProjectData} />
          </AccordionDetails>
        </Accordion>

        <Box sx={{ height: 'calc(100vh - 64px - 48px - 80px)', position: 'relative', bgcolor: '#1e1e1e' }}>
          {selectedEnvId ? (
            <Shell key={selectedEnvId} projectName={projectName} dockerId={selectedEnvId} />
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ color: 'gray' }}>Select a running environment to open the shell.</Typography>
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
}

export default Workspace;
