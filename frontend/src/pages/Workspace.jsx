import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Shell from '../components/Shell';
import DockerSidebar from '../components/DockerSidebar';
import ProjectSettings from '../components/ProjectSettings';
import { Box, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ExpandMore } from '@mui/icons-material';

function Workspace() {
  const { projectName } = useParams();
  const [project, setProject] = useState(null);
  const [selectedEnvId, setSelectedEnvId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProjectData = () => {
    if (!projectName) return;
    setIsLoading(true);
    fetch('http://localhost:8000/api/projects')
      .then(res => res.json())
      .then(projects => {
        const currentProject = projects.find(p => p.name === projectName);
        setProject(currentProject);
        if (currentProject && !currentProject.environments.some(e => e.id === selectedEnvId)) {
          setSelectedEnvId(null);
        }
      })
      .catch(error => console.error('Error fetching project:', error))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchProjectData();
  }, [projectName]);

  const handleEnvSelect = (envId) => {
    const env = project?.environments.find(e => e.id === envId);
    if (env?.status === 'running') {
      setSelectedEnvId(envId);
    } else {
      setSelectedEnvId(null);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!project) {
    return (
      <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography sx={{ color: 'gray' }}>Select a project from the top menu.</Typography>
      </Box>
    );
  }

  return (
    <>
      {/* Pass the selectedEnvId to the sidebar */}
      <DockerSidebar 
        project={project} 
        onEnvSelect={handleEnvSelect} 
        selectedEnvId={selectedEnvId} 
        onDataChange={fetchProjectData} 
      />
      <Box 
        component="main"
        sx={{ flexGrow: 1, p: 3, width: `calc(100% - 280px)` }}
      >
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
            <Shell 
              key={selectedEnvId}
              projectName={projectName} 
              dockerId={selectedEnvId}
            />
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ color: 'gray' }}>Select a running environment from the left to open the shell.</Typography>
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
}

export default Workspace;
