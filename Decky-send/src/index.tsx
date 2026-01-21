import {
  PanelSection,
  ProgressBar,
  ButtonItem,
  PanelSectionRow,
  ToggleField,
  Navigation
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster,
} from "@decky/api"

// Declare decky global object
declare const decky: any;
import { useState, useEffect, useRef } from "react";
import { FaUpload } from "react-icons/fa";

// Import QR code component
import { QRCodeCanvas } from "qrcode.react";

// Define callable functions to communicate with Python backend
const startServer = callable<[port: number], { status: string; message: string; url?: string; ip_address?: string; port?: number }>("start_server");
const stopServer = callable<[], { status: string; message: string }>("stop_server");
const getServerStatus = callable<[], { running: boolean; port: number; host: string; ip_address?: string }>("get_server_status");
const getIpAddressFromBackend = callable<[], { status: string; ip_address?: string; message?: string }>("get_ip_address");
const getTextContent = callable<[], { status: string; content: string }>("get_text_content");


// =============================================================================
// Global State Cache (similar to ToMoon pattern)
// =============================================================================
// These global variables cache the server status so that when the component
// renders, it can immediately show the correct state without flashing.
// The state is pre-fetched in definePlugin() before the component mounts.

let serverRunningGlobal = false;
let serverUrlGlobal = '';
let serverIpGlobal = '';
let serverPortGlobal = 8000;
let pluginReady = false;  // Set to true after initial status fetch

// Define types for server and transfer status
interface ServerStatus {
  running: boolean;
  url: string;
  ip_address: string;
  port: number;
}

interface ServerStatusState extends ServerStatus {
  loading: boolean;
}

interface TransferStatus {
  running: boolean;
  filename: string;
  size: number;
  transferred: number;
  speed: number;
  eta: number;
}

interface TextStatus {
  received: boolean;
  content: string;
}

function Content() {
  // Show loading screen while plugin is initializing (like ToMoon's "Init..." screen)
  if (!pluginReady) {
    return <PanelSection>初始化中...</PanelSection>;
  }
  
  // Initialize with cached global values - this prevents the "flash" effect
  const [serverStatus, setServerStatus] = useState<ServerStatusState>({
    running: serverRunningGlobal,
    url: serverUrlGlobal,
    ip_address: serverIpGlobal,
    port: serverPortGlobal,
    loading: false  // No loading state on initial render since we have cached values
  });
  
  // Use ref to track latest serverStatus for use in intervals/callbacks
  const serverStatusRef = useRef(serverStatus);
  useEffect(() => {
    serverStatusRef.current = serverStatus;
  }, [serverStatus]);
  
  const [transferStatus, setTransferStatus] = useState<TransferStatus>({
    running: false,
    filename: '',
    size: 0,
    transferred: 0,
    speed: 0,
    eta: 0
  });
  
  // Text transfer status
  const [textStatus, setTextStatus] = useState<TextStatus>({
    received: false,
    content: ''
  });
  

  
  // State for copy button
  const [isCopying, setIsCopying] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  
  // Reset copy success state after 2 seconds
  useEffect(() => {
    if (copySuccess) {
      const timer = setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [copySuccess]);
  
  // Copy text to clipboard with fallback methods
  const copyToClipboard = async () => {
    if (isCopying || copySuccess) return;
    
    const text = textStatus.content;
    setIsCopying(true);
    
    // Create an input element for copying (more reliable than textarea in some environments)
    const tempInput = document.createElement('input');
    tempInput.value = text;
    tempInput.style.position = 'absolute';
    tempInput.style.left = '-9999px';
    document.body.appendChild(tempInput);
    
    try {
      tempInput.focus();
      tempInput.select();
      
      let success = false;
      
      // Try execCommand first (more reliable in Decky environment)
      try {
        if (document.execCommand('copy')) {
          success = true;
        }
      } catch (e) {
        // If execCommand fails, try modern clipboard API
        try {
          await navigator.clipboard.writeText(text);
          success = true;
        } catch (clipboardError) {
          console.error('Both copy methods failed:', e, clipboardError);
        }
      }
      
      if (success) {
        setCopySuccess(true);
      } else {
        throw new Error('Both copy methods failed');
      }
    } catch (err) {
      console.error('Copy failed:', err);
      toaster.toast({
        title: "复制失败",
        body: "无法复制文本到剪贴板，请手动复制"
      });
    } finally {
      // Always clean up
      document.body.removeChild(tempInput);
      setIsCopying(false);
    }
  };
  
  // Format file size to human readable format
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };
  
  // Format time in seconds to mm:ss format
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Calculate transfer progress percentage (0-100)
  const calculateProgress = (): number => {
    if (transferStatus.size <= 0 || transferStatus.transferred < 0) return 0;
    if (transferStatus.transferred >= transferStatus.size) return 100;
    return Math.min(100, Math.round((transferStatus.transferred / transferStatus.size) * 100));
  };
  
  // Handle service toggle switch
  const handleServiceToggle = async (enabled: boolean) => {
    try {
      setServerStatus((prev: ServerStatusState) => ({ ...prev, loading: true }));
      
      if (enabled) {
        // Start server
        console.log('Starting server...');
        const response = await startServer(8000);
        
        if (response.status === 'success' || response.message === '服务器已在运行') {
          // Update global cache
          serverRunningGlobal = true;
          serverIpGlobal = response.ip_address || serverIpGlobal;
          serverPortGlobal = response.port || 8000;
          serverUrlGlobal = response.url || `http://${serverIpGlobal}:${serverPortGlobal}`;
          
          setServerStatus((prev: ServerStatusState) => ({
            ...prev,
            running: true,
            url: serverUrlGlobal,
            ip_address: serverIpGlobal,
            port: serverPortGlobal,
            loading: false
          }));
          toaster.toast({
            title: "服务已启动",
            body: "文件传输服务已成功启动"
          });
        } else {
          // Update global cache on failure
          serverRunningGlobal = false;
          
          setServerStatus((prev: ServerStatusState) => ({ ...prev, running: false, loading: false }));
          toaster.toast({
            title: "启动失败",
            body: response.message || "无法启动服务"
          });
        }
      } else {
        // Stop server
        console.log('Stopping server...');
        const response = await stopServer();
        
        if (response.status === 'success') {
          // Update global cache
          serverRunningGlobal = false;
          serverUrlGlobal = '';
          serverIpGlobal = '';
          
          // Clear transfer status when stopping server
          setTransferStatus({
            running: false,
            filename: '',
            size: 0,
            transferred: 0,
            speed: 0,
            eta: 0
          });
          
          setServerStatus((prev: ServerStatusState) => ({
            ...prev,
            running: false,
            loading: false
          }));
          toaster.toast({
            title: "服务已停止",
            body: "文件传输服务已停止"
          });
        } else {
          setServerStatus((prev: ServerStatusState) => ({ ...prev, loading: false }));
          toaster.toast({
            title: "停止失败",
            body: response.message || "无法停止服务"
          });
        }
      }
    } catch (error) {
      console.error('Service toggle error:', error);
      setServerStatus((prev: ServerStatusState) => ({ ...prev, loading: false }));
      toaster.toast({
        title: "操作失败",
        body: "切换服务状态时发生错误"
      });
    }
  };

  // Check actual server status from backend (simplified - no auto-start)
  const checkServerStatus = async () => {
    try {
      const statusResponse = await getServerStatus();
      const currentStatus = serverStatusRef.current;
      
      // Update global cache
      serverRunningGlobal = statusResponse.running;
      serverPortGlobal = statusResponse.port || 8000;
      
      // Only update UI if status actually changed
      if (statusResponse.running !== currentStatus.running) {
        if (statusResponse.running) {
          // Server is running, get URL info
          const ipAddress = statusResponse.ip_address || '127.0.0.1';
          serverIpGlobal = ipAddress;
          serverUrlGlobal = `http://${ipAddress}:${statusResponse.port}`;
          
          setServerStatus((prev: ServerStatusState) => ({
            ...prev,
            running: true,
            url: serverUrlGlobal,
            ip_address: ipAddress,
            port: statusResponse.port || 8000,
            loading: false
          }));
        } else {
          // Server stopped
          serverIpGlobal = '';
          serverUrlGlobal = '';
          
          setServerStatus((prev: ServerStatusState) => ({
            ...prev,
            running: false,
            loading: false
          }));
        }
      }
    } catch (error) {
      console.error('Failed to check server status:', error);
      // Don't change state on error, just log it
    }
  };
  

  
  // Initialize: fetch server status on component mount (runs once)
  useEffect(() => {
    const syncServerStatus = async () => {
      try {
        // Get current server status from backend
        const status = await getServerStatus();
        
        // Update global cache
        serverRunningGlobal = status.running;
        serverPortGlobal = status.port || 8000;
        
        if (status.running) {
          // Server is running, update URL info
          const ipAddress = status.ip_address || '127.0.0.1';
          serverIpGlobal = ipAddress;
          serverUrlGlobal = `http://${ipAddress}:${status.port}`;
          
          setServerStatus({
            running: true,
            url: serverUrlGlobal,
            ip_address: ipAddress,
            port: status.port || 8000,
            loading: false
          });
        } else {
          // Server not running
          serverIpGlobal = '';
          serverUrlGlobal = '';
          
          setServerStatus((prev: ServerStatusState) => ({
            ...prev,
            running: false,
            loading: false
          }));
        }
        
        // Load text content from file
        try {
          const textResponse = await getTextContent();
          if (textResponse.status === 'success') {
            setTextStatus({
              received: textResponse.content.trim() !== '',
              content: textResponse.content
            });
          }
        } catch (error) {
          console.error('Failed to load text content:', error);
        }
      } catch (error) {
        console.error('Failed to sync server status:', error);
      }
    };
    
    // Sync status on mount (in case it changed since plugin init)
    syncServerStatus();
    
    // Set up interval to periodically sync server status (every 5 seconds)
    const statusInterval = setInterval(() => {
      checkServerStatus();
    }, 5000);
    
    return () => {
      clearInterval(statusInterval);
    };
  }, []); // Empty dependency array - only run on mount
  
  // Listen for transfer status updates from backend
  useEffect(() => {
    const transferListener = addEventListener<[
      filename: string,
      size: number,
      transferred: number,
      speed: number,
      eta: number
    ]>("transfer_status", ([filename, size, transferred, speed, eta]) => {
      const transferState = {
        running: true,
        filename,
        size,
        transferred,
        speed,
        eta
      };
      setTransferStatus(transferState);
    });
    
    const transferCompleteListener = addEventListener<[filename: string]>("transfer_complete", ([filename]) => {
      toaster.toast({
        title: "Transfer Complete",
        body: `${filename} has been successfully transferred.`
      });
      // Reset transfer status after a delay
      setTimeout(() => {
        setTransferStatus({
          running: false,
          filename: '',
          size: 0,
          transferred: 0,
          speed: 0,
          eta: 0
        });
      }, 2000);
      
      // Reset text status since text file was cleared
      setTextStatus({
        received: false,
        content: ''
      });
    });
    
    // Listen for text received event
    const textReceivedListener = addEventListener<[text: string]>("text_received", ([text]) => {
      toaster.toast({
        title: "文本传输完成",
        body: "已接收到新的文本内容"
      });
      
      // Update text status
      const textState = {
        received: true,
        content: text
      };
      setTextStatus(textState);
    });
    
    return () => {
      removeEventListener("transfer_status", transferListener);
      removeEventListener("transfer_complete", transferCompleteListener);
      removeEventListener("text_received", textReceivedListener);
    };
  }, []);
  
  return (
    <>
      {/* Title Bar */}
      <PanelSection>
        {/* Service Toggle */}
        <PanelSectionRow>
          <ToggleField
            label="文件传输服务"
            description={serverStatus.loading ? '正在切换...' : (serverStatus.running ? '服务运行中' : '服务已停止')}
            checked={serverStatus.running}
            disabled={serverStatus.loading}
            onChange={handleServiceToggle}
          />
        </PanelSectionRow>
      </PanelSection>
      
      {/* QR Code Section */}
      {serverStatus.running && serverStatus.url && (
        <PanelSection title="访问方式">
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            padding: '10px 20px 10px 20px', 
            gap: '15px',
            marginBottom: '-10px'
          }}>
            {/* QR Code Image */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              padding: '10px',
              backgroundColor: 'white',
              borderRadius: '8px',
              outline: 'none',
              cursor: 'default',
              userSelect: 'auto',
              transition: 'outline 0.2s ease'
            }} 
            tabIndex={0} 
            role="img" 
            aria-label={`QR码: ${serverStatus.url}`} 
            onFocus={(e: React.FocusEvent<HTMLElement>) => e.currentTarget.style.outline = '3px solid #1b73e8'}
            onBlur={(e: React.FocusEvent<HTMLElement>) => e.currentTarget.style.outline = 'none'}
            onClick={(e: React.MouseEvent<HTMLElement>) => e.preventDefault()}
            onKeyDown={(e: React.KeyboardEvent<HTMLElement>) => {
              // Prevent default keyboard actions that might interfere with navigation
              if (['Enter', 'Space'].includes(e.key)) {
                e.preventDefault();
              }
            }}>
              <QRCodeCanvas 
                value={serverStatus.url} 
                size={100} 
                level="M" 
                includeMargin={false} 
                aria-hidden="true"
              />
            </div>
            
            {/* URL Display */}
            <div style={{ 
              textAlign: 'center',
              maxWidth: '100%',
              wordBreak: 'break-all'
            }}>
              <p style={{ 
                margin: '5px 0', 
                fontSize: '16px', 
                fontWeight: 'bold',
                color: '#1b73e8',
                outline: 'none',
                cursor: 'default',
                userSelect: 'text',
                transition: 'outline 0.2s ease'
              }} 
              tabIndex={0} 
              role="text"
              aria-label="服务器URL地址" 
              onFocus={(e: React.FocusEvent<HTMLElement>) => e.currentTarget.style.outline = '3px solid #1b73e8'}
              onBlur={(e: React.FocusEvent<HTMLElement>) => e.currentTarget.style.outline = 'none'}
              onClick={(e: React.MouseEvent<HTMLElement>) => e.preventDefault()}
              onKeyDown={(e: React.KeyboardEvent<HTMLElement>) => {
                // Prevent default keyboard actions that might interfere with navigation
                if (['Enter', 'Space'].includes(e.key)) {
                  e.preventDefault();
                }
              }}>
                {serverStatus.url}
              </p>
            </div>
            

          </div>
        </PanelSection>
      )}
      
      {/* Transfer Status - Only show when server is running */}
      {serverStatus.running && (
        <PanelSection title="传输记录">
          {/* Show file transfer if it's running or the latest transfer is file */}
          {(transferStatus.running || (transferStatus.filename !== '' && transferStatus.size > 0)) ? (
            // File transfer in progress or recent transfer
            <div style={{ padding: '10px 0' }}>
              {/* Filename and Size */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{ fontSize: '14px', fontWeight: 'bold' }}>
                  {transferStatus.filename}
                </span>
                <span style={{ fontSize: '13px', color: '#666' }}>
                  {formatFileSize(transferStatus.size)}
                </span>
              </div>
              
              {/* Progress Bar */}
              <ProgressBar 
                nProgress={calculateProgress()} 
              />
              
              {/* Progress Details */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{ fontSize: '13px', color: '#666' }}>
                  已传输: {formatFileSize(transferStatus.transferred)}
                </span>
                <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#1b73e8' }}>
                  {calculateProgress()}%
                </span>
              </div>
              
              {/* Transfer Speed and ETA */}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
                <span>速度: {formatFileSize(transferStatus.speed)}/s</span>
                <span>剩余: {formatTime(transferStatus.eta)}</span>
              </div>
            </div>
          ) : textStatus.received ? (
            // Text received
            <div style={{ padding: '10px 0' }}>
              {/* Text Content */}
              <div style={{ 
                marginBottom: '15px', 
                padding: '15px', 
                backgroundColor: 'rgba(0, 0, 0, 0.1)', 
                borderRadius: '8px', 
                maxHeight: '200px', 
                overflowY: 'auto'
              }}>
                <pre style={{ 
                  margin: 0, 
                  fontSize: '14px', 
                  whiteSpace: 'pre-wrap', 
                  wordBreak: 'break-word'
                }}>
                  {textStatus.content}
              </pre>
            </div>
            
            {/* Copy Button */}
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={copyToClipboard}
                disabled={isCopying || copySuccess}
              >
                <div style={{ 
                  color: copySuccess ? "#4CAF50" : "inherit",
                  fontWeight: copySuccess ? "bold" : "normal"
                }}>
                  {copySuccess ? "复制成功" : isCopying ? "复制中..." : "复制到剪贴板"}
                </div>
              </ButtonItem>
            </PanelSectionRow>
          </div>
        ) : (
          // No transfer in progress
          <div style={{ 
            textAlign: 'center', 
            padding: '20px', 
            color: '#666', 
            fontSize: '14px' 
          }}>
            当前无传输任务
          </div>
        )}
      </PanelSection>
      )}
      

    </>
  );
};

export default definePlugin(() => {
  console.log("decky-send plugin initializing");

  // Pre-fetch server status before component renders (like ToMoon pattern)
  // This prevents the "flash" effect where toggle shows OFF then switches to ON
  // IMPORTANT: Use immediately-invoked async function to pre-fetch, then set pluginReady
  (async function () {
    try {
      console.log("Pre-fetching server status...");
      const status = await getServerStatus();
      
      serverRunningGlobal = status.running;
      serverPortGlobal = status.port || 8000;
      
      if (status.running) {
        serverIpGlobal = status.ip_address || '127.0.0.1';
        serverUrlGlobal = `http://${serverIpGlobal}:${serverPortGlobal}`;
        console.log(`Server is running at ${serverUrlGlobal}`);
      } else {
        serverIpGlobal = '';
        serverUrlGlobal = '';
        console.log("Server is not running");
      }
    } catch (error) {
      console.error("Failed to pre-fetch server status:", error);
      // Keep default values (server not running)
      serverRunningGlobal = false;
      serverIpGlobal = '';
      serverUrlGlobal = '';
    } finally {
      // Always mark plugin as ready, even if fetch failed
      // This ensures UI renders (with default values if needed)
      pluginReady = true;
      console.log("Plugin initialization complete");
    }
  })();

  return {
    // The name shown in various decky menus
    name: "", // Removed plugin name as requested
    // The content of your plugin's menu
    content: <Content />,
    // The icon displayed in the plugin list
    icon: <FaUpload />,
    // The function triggered when your plugin unloads
    onDismount() {
      console.log("Unloading decky-send plugin");
    }
  };
});
