# WebSocket Persistence Implementation Guide

## Overview
This guide documents the implementation of persistent WebSocket connections across Docker environments, enabling seamless environment switching without losing terminal sessions.

## Architecture

### WebSocket Connection Management
- **WebSocketManager**: Singleton class managing multiple WebSocket connections
- **Connection Pool**: Maintains connections keyed by `${projectName}-${envId}`
- **Background Persistence**: Connections remain active when switching environments

### Components Integration
1. **Shell Component**: Uses WebSocketManager for connection creation and reuse
2. **DockerSidebar**: Displays connection status indicators
3. **Workspace**: Manages environment selection and Shell rendering

## Key Features

### 1. Persistent Connections
- WebSocket connections stay open in background when switching environments
- No reconnection required when returning to previously accessed environments
- Terminal state and history preserved across switches

### 2. Connection Status Indicators
- Visual chips in sidebar showing "Connected" status
- Color coding: Green (active), Blue (inactive), None (disconnected)
- Real-time status updates every 2 seconds

### 3. Proper Cleanup
- Connections automatically closed when environments are deleted
- Memory leak prevention through proper connection management
- Graceful handling of connection failures

## Implementation Details

### WebSocketManager API
```javascript
// Get or create connection
const ws = WebSocketManager.getConnection(projectName, envId, token);

// Switch active connection
WebSocketManager.setActiveConnection(projectName, envId);

// Close specific connection
WebSocketManager.closeConnection(projectName, envId);

// Get connection status
const status = WebSocketManager.getConnectionStatus(projectName, envId);
```

### Shell Component Integration
```javascript
// Use WebSocketManager instead of direct WebSocket creation
const ws = WebSocketManager.getConnection(projectName, selectedEnvId, token);
WebSocketManager.setActiveConnection(projectName, selectedEnvId);

// Setup message handlers
ws.onmessage = handleMessage;
ws.onerror = handleError;
```

### Connection Status Display
```javascript
// Check connection status in sidebar
const connectionStatus = getConnectionStatus(env.id);
const isActive = isConnectionActive(env.id);

// Render status indicator
{connectionStatus === 'connected' && (
  <Chip
    icon={<Wifi />}
    label="Connected"
    sx={{ bgcolor: isActive ? '#4caf50' : '#2196f3' }}
  />
)}
```

## Benefits

### User Experience
- **Seamless switching**: No interruption when changing environments
- **Preserved context**: Terminal history and state maintained
- **Visual feedback**: Clear indication of connection status
- **Reduced wait time**: No reconnection delays

### Technical Advantages
- **Resource efficiency**: Reuse existing connections
- **State preservation**: Terminal sessions persist
- **Error resilience**: Graceful handling of connection issues
- **Memory management**: Proper cleanup prevents leaks

## Usage Workflow

1. **Environment Creation**: User creates new Docker environment
2. **First Access**: Shell component creates WebSocket connection via WebSocketManager
3. **Environment Switch**: User switches to different environment
   - Previous connection remains open in background
   - New connection created if needed, or existing one reused
4. **Return to Previous**: User returns to previously accessed environment
   - Existing connection immediately activated
   - Terminal state exactly as left
5. **Environment Deletion**: Connection properly closed and cleaned up

## Configuration

### Environment Variables
No additional configuration required. The system automatically:
- Detects available environments
- Manages connection lifecycle
- Updates status indicators

### Connection Parameters
- **Reconnection**: Automatic with exponential backoff
- **Timeout**: 30 seconds for initial connection
- **Heartbeat**: Built into WebSocket protocol
- **Buffer Size**: Default browser WebSocket limits

## Troubleshooting

### Common Issues
1. **Connection Failed**: Check backend WebSocket server status
2. **Status Not Updating**: Verify timer intervals in components
3. **Memory Leaks**: Ensure proper cleanup on component unmount
4. **Multiple Connections**: Check for duplicate connection creation

### Debug Information
- Browser DevTools Network tab shows WebSocket connections
- Console logs connection events and status changes
- Backend logs show WebSocket server activity

## Future Enhancements

### Potential Improvements
- **Connection Pooling**: Limit maximum concurrent connections
- **Bandwidth Optimization**: Compress WebSocket messages
- **Reconnection Strategy**: Smarter reconnection logic
- **Session Persistence**: Save terminal state to storage
- **Multi-tab Support**: Share connections across browser tabs

### Monitoring
- **Connection Metrics**: Track connection count and duration
- **Performance Monitoring**: Measure switching speed
- **Error Tracking**: Log connection failures and recovery
- **Resource Usage**: Monitor memory and network consumption

## Security Considerations

### Authentication
- Token-based authentication for WebSocket connections
- Automatic token refresh when needed
- Secure token storage and transmission

### Access Control
- Environment-specific connection permissions
- Project-level access restrictions
- User session validation

This implementation provides a robust foundation for persistent WebSocket connections while maintaining security and performance standards.
