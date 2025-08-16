class WebSocketManager {
  constructor() {
    this.connections = new Map(); // envId -> { ws, terminal, isActive }
    this.activeEnvId = null;
    this.activeConnection = null;
    this.activeTerminal = null;
    this.heartbeatInterval = 30000; // 30 seconds
    this.reconnectDelay = 5000; // 5 seconds
    this.maxReconnectAttempts = 3;
  }

  getConnection(projectName, envId, token) {
    return this.createConnection(projectName, envId, token);
  }

  setActiveConnection(projectName, envId) {
    const connectionKey = `${projectName}-${envId}`;
    this.activeConnection = connectionKey;
    
    if (this.connections.has(connectionKey)) {
      const connection = this.connections.get(connectionKey);
      connection.isActive = true;
    }
  }

  createConnection(projectName, envId, token, terminal = null) {
    const connectionKey = `${projectName}-${envId}`;
    
    // Check if connection already exists
    if (this.connections.has(connectionKey)) {
      const connection = this.connections.get(connectionKey);
      if (terminal) {
        connection.terminal = terminal;
        connection.isActive = true;
        this.attachTerminalEvents(connection);
      }
      return connection.ws;
    }

    // Create new WebSocket connection
    const wsUrl = `ws://localhost:8000/ws/shell/${projectName}/${envId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    const connection = {
      ws,
      status: 'connecting',
      isActive: false,
      terminal: terminal,
      tuiInitialized: false,
      projectName,
      envId,
      heartbeatTimer: null,
      reconnectAttempts: 0,
      lastActivity: Date.now()
    };

    this.connections.set(connectionKey, connection);
    this.activeConnection = connectionKey;

    // Setup WebSocket event handlers
    ws.onopen = () => {
      console.log(`WebSocket connected for ${connectionKey}`);
      connection.status = 'connected';
      connection.reconnectAttempts = 0;
      connection.lastActivity = Date.now();
      
      // Start heartbeat
      this.startHeartbeat(connection);
      
      if (connection.isActive && connection.terminal) {
        this.sendResize(connection);
        // Don't write connection messages that could interfere with TUI
      }
    };

    ws.onmessage = (event) => {
      connection.lastActivity = Date.now();
      
      // Handle heartbeat and control messages
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'heartbeat') {
          // Send pong response
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
          }
          return;
        } else if (message.type === 'pong') {
          // Heartbeat acknowledged
          return;
        }
      } catch (e) {
        // Not a JSON message, treat as terminal data
      }
      
      if (this.activeConnection === connectionKey && this.activeTerminal) {
        const data = event.data;
        
        // 检测到 Claude Code 启动时，强制使用替代屏幕
        if (data.includes('Welcome to Claude Code')) {
          // 清空当前内容并强制启用替代屏幕缓冲区
          this.activeTerminal.clear();
          this.activeTerminal.reset();
          this.activeTerminal.write('\x1b[?1049h\x1b[2J\x1b[H');
          this.activeTerminal.write(data);
          setTimeout(() => {
            this.activeTerminal.focus();
          }, 100);
          return; // 不要重复写入数据
        }
        
        this.activeTerminal.write(data);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error for ${connectionKey}:`, error);
      if (connection.isActive && connection.terminal) {
        connection.terminal.write("\r\n[WebSocket Error] See browser console for details.\r\n");
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed for ${connectionKey}, code: ${event.code}`);
      
      // Stop heartbeat
      this.stopHeartbeat(connection);
      
      if (connection.isActive && connection.terminal) {
        connection.terminal.write(`\r\n[Connection Closed] Code: ${event.code}\r\n`);
        
        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && connection.reconnectAttempts < this.maxReconnectAttempts) {
          connection.terminal.write(`\r\n[Reconnecting...] Attempt ${connection.reconnectAttempts + 1}/${this.maxReconnectAttempts}\r\n`);
          setTimeout(() => {
            this.reconnectConnection(connectionKey, token);
          }, this.reconnectDelay);
          return;
        }
      }
      
      this.connections.delete(connectionKey);
    };

    this.attachTerminalEvents(connection);
    return ws;
  }

  attachTerminalEvents(connection) {
    if (!connection.terminal) return;

    // Remove existing data handler if any
    if (connection.dataHandler) {
      connection.terminal.onData(null);
    }

    // Add new data handler
    connection.dataHandler = (data) => {
      if (connection.ws.readyState === WebSocket.OPEN) {
        connection.ws.send(JSON.stringify({ type: 'input', data }));
      }
    };

    connection.terminal.onData(connection.dataHandler);
  }

  switchToEnvironment(projectName, envId, terminal) {
    // Deactivate current connection
    if (this.activeConnection) {
      const currentConnection = this.connections.get(this.activeConnection);
      if (currentConnection) {
        currentConnection.isActive = false;
        if (currentConnection.dataHandler) {
          currentConnection.terminal?.onData(null);
        }
        currentConnection.terminal = null;
      }
    }

    // Activate new connection
    const connectionKey = `${projectName}-${envId}`;
    const connection = this.connections.get(connectionKey);
    
    if (connection) {
      connection.isActive = true;
      connection.terminal = terminal;
      this.activeConnection = connectionKey;
      this.activeTerminal = terminal;
      
      // Focus the terminal to ensure it can receive input
      terminal.focus();
      
      // Reattach terminal events for this connection
      this.attachTerminalEvents(connection);
      
      // Send resize to ensure proper dimensions
      this.sendResize(connection);
    }
  }

  sendResize(connection) {
    if (connection.ws.readyState === WebSocket.OPEN && connection.terminal) {
      connection.ws.send(JSON.stringify({ 
        type: 'resize', 
        cols: connection.terminal.cols, 
        rows: connection.terminal.rows 
      }));
    }
  }

  findConnectionKey(envId) {
    for (const [key, connection] of this.connections) {
      if (connection.envId === envId) {
        return key;
      }
    }
    return null;
  }

  startHeartbeat(connection) {
    this.stopHeartbeat(connection);
    connection.heartbeatTimer = setInterval(() => {
      if (connection.ws.readyState === WebSocket.OPEN) {
        // Check if connection has been idle too long
        const idleTime = Date.now() - connection.lastActivity;
        if (idleTime > 600000) { // 10 minutes
          console.log('Connection idle too long, closing');
          connection.ws.close();
          return;
        }
        
        // Send heartbeat
        connection.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, this.heartbeatInterval);
  }

  stopHeartbeat(connection) {
    if (connection.heartbeatTimer) {
      clearInterval(connection.heartbeatTimer);
      connection.heartbeatTimer = null;
    }
  }

  reconnectConnection(connectionKey, token) {
    const connection = this.connections.get(connectionKey);
    if (!connection) return;
    
    connection.reconnectAttempts++;
    const [projectName, envId] = connectionKey.split('-');
    
    // Create new WebSocket connection
    const wsUrl = `ws://localhost:8000/ws/shell/${projectName}/${envId}?token=${token}`;
    const newWs = new WebSocket(wsUrl);
    
    // Replace the old WebSocket
    connection.ws = newWs;
    
    // Re-setup event handlers (reuse existing logic)
    this.setupWebSocketHandlers(connection, connectionKey, token);
  }

  setupWebSocketHandlers(connection, connectionKey, token) {
    const ws = connection.ws;
    
    ws.onopen = () => {
      console.log(`WebSocket reconnected for ${connectionKey}`);
      connection.status = 'connected';
      connection.reconnectAttempts = 0;
      connection.lastActivity = Date.now();
      
      this.startHeartbeat(connection);
      
      if (connection.isActive && connection.terminal) {
        connection.terminal.write(`\r\n[Reconnected]\r\n`);
        this.sendResize(connection);
      }
    };
    
    // Reuse the existing onmessage, onerror, onclose handlers
    // (This would need the existing logic moved to a separate method)
  }

  closeConnection(projectName, envId) {
    const connectionKey = `${projectName}-${envId}`;
    const connection = this.connections.get(connectionKey);
    
    if (connection) {
      this.stopHeartbeat(connection);
      connection.ws.close(1000); // Normal closure
      this.connections.delete(connectionKey);
      
      if (this.activeEnvId === envId) {
        this.activeEnvId = null;
      }
    }
  }

  closeAllConnections() {
    for (const [key, connection] of this.connections) {
      this.stopHeartbeat(connection);
      connection.ws.close(1000); // Normal closure
    }
    this.connections.clear();
    this.activeEnvId = null;
  }

  getConnectionStatus(projectName, envId) {
    const connectionKey = `${projectName}-${envId}`;
    const connection = this.connections.get(connectionKey);
    
    if (!connection) return 'disconnected';
    
    switch (connection.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  getAllConnections() {
    const status = {};
    for (const [key, connection] of this.connections) {
      status[key] = {
        envId: connection.envId,
        projectName: connection.projectName,
        isActive: connection.isActive,
        status: this.getConnectionStatus(connection.projectName, connection.envId)
      };
    }
    return status;
  }
}

// Export singleton instance
export default new WebSocketManager();
