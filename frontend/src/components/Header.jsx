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

function Header() {
  const [projects, setProjects] = useState([]);
  const [selectedValue, setSelectedValue] = useState("");
  const { projectName } = useParams();
  const navigate = useNavigate();

  // Effect 1: Fetch projects once on component mount
  useEffect(() => {
    fetch("http://localhost:8000/api/projects")
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
      })
      .catch((err) => console.error("Failed to fetch projects:", err));
  }, []);

  // Effect 2: 同步 URL 参数和选择状态
  useEffect(() => {
    if (projectName && projects.length > 0) {
      // 检查 URL 中的项目名是否在项目列表中存在
      const projectExists = projects.some((p) => p.name === projectName);
      if (projectExists) {
        setSelectedValue(projectName);
      } else {
        setSelectedValue("");
      }
    } else if (!projectName) {
      // 如果不在项目页面，重置选择
      setSelectedValue("");
    }
  }, [projectName, projects]);

  const handleProjectChange = (event) => {
    const newProjectName = event.target.value;
    setSelectedValue(newProjectName); // 立即更新本地状态

    if (newProjectName) {
      navigate(`/project/${newProjectName}`);
    } else {
      navigate("/");
    }
  };

  const handleOpen = () => {
    // Fetch projects every time the dropdown is opened
    fetch("http://localhost:8000/api/projects")
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
      })
      .catch((err) => console.error("Failed to fetch projects:", err));
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
            value={selectedValue} // The Select's value is now reliably controlled by our state
            onChange={handleProjectChange}
            onOpen={handleOpen} // <-- This is the fix
            displayEmpty
            renderValue={(selected) => {
              if (!selected) {
                return <em>Select a Project</em>;
              }
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
      </Toolbar>
    </AppBar>
  );
}

export default Header;
