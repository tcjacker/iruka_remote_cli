import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { useAuth } from '../context/AuthContext';
import apiConfig from '../config/api';

// This is a simplified and robust implementation inspired by the reference project.
function Shell({ projectName, dockerId }) {
  const terminalRef = useRef(null);
  const isInitialized = useRef(false);
  const [isEnvironmentReady, setIsEnvironmentReady] = useState(false);
  const { token } = useAuth();

  useEffect(() => {
    if (isInitialized.current || !terminalRef.current) {
      return;
    }
    isInitialized.current = true;

    const term = new Terminal({
      cursorBlink: true,
      convertEol: true, // This is critical for the Enter key
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
      },
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);

    // Display initialization message
    term.write("[Environment Initializing] Please wait while the environment is being set up...\r\n");
    term.write("[This may take a few minutes as we install Node.js, AI tools, and clone your repository.]\r\n\r\n");

    // Check if token exists before establishing WebSocket connection
    if (!token) {
      console.error("No auth token available for WebSocket connection");
      term.write("[Authentication Error] No auth token available. Please log in again.\r\n");
      return;
    }
    
    const wsUrl = apiConfig.buildWsUrl(`/ws/shell/${projectName}/${dockerId}?token=${token}`);
    const ws = new WebSocket(wsUrl);

    const sendJson = (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    };
    
    const fitAndResize = () => {
        fitAddon.fit();
        sendJson({ type: 'resize', cols: term.cols, rows: term.rows });
    };

    ws.onopen = () => {
      fitAndResize();
    };

    ws.onmessage = (event) => {
      // The backend now sends raw strings, not JSON
      term.write(event.data);
    };

    ws.onerror = (error) => {
        term.write("\r\n[WebSocket Error] See browser console for details.\r\n");
        console.error("WebSocket Error:", error);
    };

    ws.onclose = (event) => {
      term.write(`\r\n[Connection Closed] Code: ${event.code}\r\n`);
    };

    // The core logic: send all terminal data wrapped in a simple JSON object.
    term.onData((data) => {
      sendJson({ type: 'input', data: data });
    });
    
    const resizeObserver = new ResizeObserver(fitAndResize);
    resizeObserver.observe(terminalRef.current);

    fitAndResize();

    return () => {
      resizeObserver.disconnect();
      ws.close();
      term.dispose();
      isInitialized.current = false;
    };
  }, [projectName, dockerId]);

  return <div ref={terminalRef} style={{ height: '100%', width: '100%' }} />;
}

export default Shell;