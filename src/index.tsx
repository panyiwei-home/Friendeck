import {
  PanelSection,
  ProgressBar,
  ButtonItem,
  PanelSectionRow,
  ToggleField,
  Navigation,
  Router,
  TextField,
  Tabs,
  gamepadTabbedPageClasses
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster,
  routerHook,
  openFilePicker,
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
const getPendingNotifications = callable<[], { status: string; notifications?: { title: string; body?: string; urgency?: string; timestamp?: number }[] }>("get_pending_notifications");
const getDownloadDir = callable<[], { status: string; path?: string; message?: string }>("get_download_dir");
const setDownloadDir = callable<[path: string], { status: string; path?: string; message?: string }>("set_download_dir");
const getAutoCopyText = callable<[], { status: string; enabled?: boolean; message?: string }>("get_auto_copy_text");
const setAutoCopyText = callable<[enabled: boolean], { status: string; enabled?: boolean; message?: string }>("set_auto_copy_text");
const getPromptUploadPath = callable<[], { status: string; enabled?: boolean; message?: string }>("get_prompt_upload_path");
const setPromptUploadPath = callable<[enabled: boolean], { status: string; enabled?: boolean; message?: string }>("set_prompt_upload_path");
const setServerPort = callable<[port: number], { status: string; port?: number; message?: string }>("set_server_port");


// =============================================================================
// Global State Cache (similar to ToMoon pattern)
// =============================================================================
// These global variables cache the server status so that when the component
// renders, it can immediately show the correct state without flashing.
// The state is pre-fetched in definePlugin() before the component mounts.

const DEFAULT_PORT = 59271;
const FILE_SELECTION_FOLDER = 1;

let serverRunningGlobal = false;
let serverUrlGlobal = '';
let serverIpGlobal = '';
let serverPortGlobal = DEFAULT_PORT;
let pluginReady = false;  // Set to true after initial status fetch

const SETTINGS_ROUTE = "/decky-send-settings";
const UI_SETTINGS_KEY = "decky_send_ui_settings";
const DEFAULT_UI_SETTINGS = {
  showQRCode: true,
  showUrlText: true,
  showTransferHistory: true,
};

type SettingsTab = { id: string; title: string; content: any };

type UiSettings = {
  showQRCode: boolean;
  showUrlText: boolean;
  showTransferHistory: boolean;
};

const loadUiSettings = (): UiSettings => {
  try {
    const raw = localStorage.getItem(UI_SETTINGS_KEY);
    if (!raw) return { ...DEFAULT_UI_SETTINGS };
    const parsed = JSON.parse(raw);
    return {
      showQRCode: typeof parsed.showQRCode === "boolean" ? parsed.showQRCode : DEFAULT_UI_SETTINGS.showQRCode,
      showUrlText: typeof parsed.showUrlText === "boolean" ? parsed.showUrlText : DEFAULT_UI_SETTINGS.showUrlText,
      showTransferHistory: typeof parsed.showTransferHistory === "boolean" ? parsed.showTransferHistory : DEFAULT_UI_SETTINGS.showTransferHistory,
    };
  } catch {
    return { ...DEFAULT_UI_SETTINGS };
  }
};

const saveUiSettings = (settings: UiSettings) => {
  localStorage.setItem(UI_SETTINGS_KEY, JSON.stringify(settings));
  window.dispatchEvent(new Event("decky-send-settings-updated"));
};

// Background toast polling so notifications appear even when UI is closed
let toastPoller: ReturnType<typeof setInterval> | null = null;

function startToastPolling() {
  if (toastPoller) return;
  toastPoller = setInterval(async () => {
    try {
      const response = await getPendingNotifications();
      if (response.status === "success" && response.notifications && response.notifications.length > 0) {
        response.notifications.forEach((toast) => {
          toaster.toast({
            title: toast.title,
            body: toast.body
          });
        });
      }
    } catch (error) {
      console.error("Toast polling failed:", error);
    }
  }, 2500);
}

function stopToastPolling() {
  if (!toastPoller) return;
  clearInterval(toastPoller);
  toastPoller = null;
}

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

  const [autoCopyEnabled, setAutoCopyEnabledState] = useState(false);
  const autoCopyEnabledRef = useRef(autoCopyEnabled);
  useEffect(() => {
    autoCopyEnabledRef.current = autoCopyEnabled;
  }, [autoCopyEnabled]);

  const [uiSettings, setUiSettings] = useState<UiSettings>(() => loadUiSettings());
  useEffect(() => {
    const handler = () => setUiSettings(loadUiSettings());
    window.addEventListener("decky-send-settings-updated", handler);
    return () => window.removeEventListener("decky-send-settings-updated", handler);
  }, []);

  useEffect(() => {
    let active = true;
    const loadAutoCopy = async () => {
      try {
        const response = await getAutoCopyText();
        if (active && response.status === "success") {
          setAutoCopyEnabledState(Boolean(response.enabled));
        }
      } catch (error) {
        console.error("Failed to load auto copy setting:", error);
      }
    };
    loadAutoCopy();
    const handler = () => loadAutoCopy();
    window.addEventListener("decky-send-auto-copy-updated", handler);
    return () => {
      active = false;
      window.removeEventListener("decky-send-auto-copy-updated", handler);
    };
  }, []);
  

  
  // State for copy button
  const [isCopying, setIsCopying] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  const normalizeText = (value: unknown): string => {
    if (typeof value === "string") return value;
    if (value && typeof value === "object") {
      const candidate = (value as { text?: unknown; content?: unknown; value?: unknown }).text
        ?? (value as { text?: unknown; content?: unknown; value?: unknown }).content
        ?? (value as { text?: unknown; content?: unknown; value?: unknown }).value;
      if (typeof candidate === "string") return candidate;
    }
    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
    try {
      return JSON.stringify(value ?? "");
    } catch {
      return "";
    }
  };
  
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
  const copyToClipboard = async (overrideText?: unknown, force = false) => {
    if (isCopying || (!force && copySuccess)) return;

    const resolvedText = typeof overrideText === "undefined"
      ? textStatus.content
      : normalizeText(overrideText);

    const text = typeof resolvedText === "string" ? resolvedText : String(resolvedText ?? "");
    if (!text) return;

    setIsCopying(true);
    
    try {
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
      } finally {
        document.body.removeChild(tempInput);
      }
    } catch (err) {
      console.error('Copy failed:', err);
      toaster.toast({
        title: "复制失败",
        body: "无法复制文本到剪贴板，请手动复制"
      });
    } finally {
      setIsCopying(false);
    }
  };

  const copyViaSteamClient = async (text: string): Promise<boolean> => {
    try {
      const steamClient = (window as any).SteamClient;
      if (!steamClient) return false;

      const candidates: Array<(value: string) => any> = [
        steamClient.System?.SetClipboardText,
        steamClient.System?.CopyToClipboard,
        steamClient.System?.SetClipboard,
        steamClient.Utils?.SetClipboardText,
        steamClient.Utils?.CopyToClipboard,
        steamClient.Browser?.SetClipboardText,
        steamClient.FriendsUI?.SetClipboardText,
      ].filter(Boolean);

      for (const fn of candidates) {
        try {
          const result = fn.call(steamClient.System || steamClient.Utils || steamClient, text);
          if (result && typeof result.then === "function") {
            await result;
          }
          return true;
        } catch (error) {
          console.error("SteamClient clipboard method failed:", error);
        }
      }
    } catch (error) {
      console.error("SteamClient clipboard error:", error);
    }
    return false;
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
        const targetPort = serverStatus.port || serverPortGlobal || DEFAULT_PORT;
        const response = await startServer(targetPort);
        
        if (response.status === 'success' || response.message === '服务器已在运行') {
          // Update global cache
          serverRunningGlobal = true;
          serverIpGlobal = response.ip_address || serverIpGlobal;
          serverPortGlobal = response.port || DEFAULT_PORT;
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
      serverPortGlobal = statusResponse.port || DEFAULT_PORT;
      
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
            port: statusResponse.port || DEFAULT_PORT,
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
        serverPortGlobal = status.port || DEFAULT_PORT;
        
        if (status.running) {
          // Server is running, update URL info
          const ipAddress = status.ip_address || '127.0.0.1';
          serverIpGlobal = ipAddress;
          serverUrlGlobal = `http://${ipAddress}:${status.port}`;
          
          setServerStatus({
            running: true,
            url: serverUrlGlobal,
            ip_address: ipAddress,
            port: status.port || DEFAULT_PORT,
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

    const handlePortUpdate = () => {
      syncServerStatus();
    };
    window.addEventListener("decky-send-port-updated", handlePortUpdate);
    
    // Set up interval to periodically sync server status (every 5 seconds)
    const statusInterval = setInterval(() => {
      checkServerStatus();
    }, 5000);
    
    return () => {
      clearInterval(statusInterval);
      window.removeEventListener("decky-send-port-updated", handlePortUpdate);
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
    const textReceivedListener = addEventListener<[text: unknown]>("text_received", ([text]) => {
      const normalizedText = normalizeText(text);
      if (normalizedText) {
        setTextStatus({
          received: true,
          content: normalizedText
        });
        if (autoCopyEnabledRef.current) {
          void (async () => {
            const steamSuccess = await copyViaSteamClient(normalizedText);
            if (!steamSuccess) {
              await copyToClipboard(normalizedText, true);
            }
          })();
        }
        return;
      }
      void (async () => {
        try {
          const textResponse = await getTextContent();
          if (textResponse.status === "success") {
            const content = textResponse.content || "";
            setTextStatus({
              received: content.trim() !== "",
              content
            });
            if (autoCopyEnabledRef.current && content) {
              const steamSuccess = await copyViaSteamClient(content);
              if (!steamSuccess) {
                await copyToClipboard(content, true);
              }
            }
          }
        } catch (error) {
          console.error("Failed to load text content after event:", error);
        }
      })();
    });
    
    return () => {
      removeEventListener("transfer_status", transferListener);
      removeEventListener("transfer_complete", transferCompleteListener);
      removeEventListener("text_received", textReceivedListener);
    };
  }, []);
  
  return (
    <div
      style={{
        paddingTop: 16,
        paddingBottom: 24,
        minHeight: "100%",
        boxSizing: "border-box",
        backgroundColor: "var(--gpBackground-color, #1b1b1b)"
      }}
    >
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
      {serverStatus.running && serverStatus.url && (uiSettings.showQRCode || uiSettings.showUrlText) && (
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
            {uiSettings.showQRCode && (
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
            )}
            
            {/* URL Display */}
            {uiSettings.showUrlText && (
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
            )}
            

          </div>
        </PanelSection>
      )}
      
      {/* Transfer Status - Only show when server is running */}
      {serverStatus.running && uiSettings.showTransferHistory && (
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
                onClick={() => copyToClipboard()}
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

      <PanelSection title="设置">
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={() => {
              Router.CloseSideMenus?.();
              Router.Navigate(SETTINGS_ROUTE);
            }}
          >
            设置
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      

    </div>
  );
};

const SettingsPage = () => {
  const [settings, setSettings] = useState<UiSettings>(() => loadUiSettings());
  const [downloadDir, setDownloadDirState] = useState<string>("");
  const [autoCopyEnabled, setAutoCopyEnabled] = useState(false);
  const [promptUploadPathEnabled, setPromptUploadPathEnabled] = useState(false);
  const [portInput, setPortInput] = useState<string>("");
  const [portSaving, setPortSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("ui");
  const containerRef = useRef<any>(null);

  useEffect(() => {
    const classMap = gamepadTabbedPageClasses as Record<string, string> | undefined;
    if (!classMap) return;
    const styleId = "decky-send-tabs-no-jitter";
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    const rules: string[] = [];
    if (classMap.TabsRowScroll) {
      rules.push(`.${classMap.TabsRowScroll}{scroll-behavior:auto !important;}`);
    }
    if (classMap.TabRowTabs) {
      rules.push(`.${classMap.TabRowTabs}{transition:none !important;}`);
      rules.push(`.${classMap.TabRowTabs}{scroll-snap-type:none !important;}`);
    }
    if (classMap.Tab) {
      rules.push(`.${classMap.Tab}{transition:none !important;}`);
    }
    style.textContent = rules.join("\n");
    document.head.appendChild(style);
  }, []);

  useEffect(() => {
    const classMap = gamepadTabbedPageClasses as Record<string, string> | undefined;
    if (!classMap) return;
    const rowClass = classMap.TabsRowScroll || classMap.TabRowTabs;
    if (!rowClass) return;
    const handle = window.requestAnimationFrame(() => {
      const row = document.querySelector(`.${rowClass}`) as HTMLElement | null;
      if (row) {
        row.style.scrollBehavior = "auto";
        row.scrollLeft = 0;
      }
    });
    return () => window.cancelAnimationFrame(handle);
  }, [activeTab]);

  const focusTabRow = (tabId?: string) => {
    const classMap = gamepadTabbedPageClasses as Record<string, string> | undefined;
    if (!classMap || !containerRef.current) return;
    const tabClass = classMap.Tab;
    if (!tabClass) return;

    let target: HTMLElement | null = null;
    if (tabId) {
      const tabTitle = tabDefs.find((tab) => tab.id === tabId)?.title;
      if (tabTitle) {
        const tabs = containerRef.current.querySelectorAll(`.${tabClass}`);
        for (const tab of Array.from(tabs)) {
          const el = tab as HTMLElement;
          if (el.textContent?.trim() === tabTitle) {
            target = el;
            break;
          }
        }
      }
    }

    if (!target) {
      const activeClass = classMap.Active || classMap.Selected;
      const selector = activeClass ? `.${tabClass}.${activeClass}` : `.${tabClass}`;
      target = containerRef.current.querySelector(selector) as HTMLElement | null;
    }

    target?.focus?.();
  };

  const updateSetting = (key: keyof UiSettings, value: boolean) => {
    const next = { ...settings, [key]: value };
    setSettings(next);
    saveUiSettings(next);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const status = await getServerStatus();
        if (active && status) {
          const initialPort = String(status.port || DEFAULT_PORT);
          setPortInput(initialPort);
        }
        const response = await getDownloadDir();
        if (active && response.status === "success") {
          setDownloadDirState(response.path || "");
        }
        const autoCopyResponse = await getAutoCopyText();
        if (active && autoCopyResponse.status === "success") {
          setAutoCopyEnabled(Boolean(autoCopyResponse.enabled));
        }
        const promptPathResponse = await getPromptUploadPath();
        if (active && promptPathResponse.status === "success") {
          setPromptUploadPathEnabled(Boolean(promptPathResponse.enabled));
        }
      } catch (error) {
        console.error("Failed to load download directory:", error);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleAutoCopyToggle = async (value: boolean) => {
    try {
      const response = await setAutoCopyText(value);
      if (response.status === "success") {
        setAutoCopyEnabled(Boolean(response.enabled));
        window.dispatchEvent(new Event("decky-send-auto-copy-updated"));
        return;
      }
      toaster.toast({
        title: "设置失败",
        body: response.message || "无法更新自动复制设置"
      });
    } catch (error) {
      console.error("Failed to set auto copy:", error);
      toaster.toast({
        title: "设置失败",
        body: "无法更新自动复制设置"
      });
    }
  };

  const handlePromptUploadPathToggle = async (value: boolean) => {
    try {
      const response = await setPromptUploadPath(value);
      if (response.status === "success") {
        setPromptUploadPathEnabled(Boolean(response.enabled));
        return;
      }
      toaster.toast({
        title: "设置失败",
        body: response.message || "无法更新上传路径设置"
      });
    } catch (error) {
      console.error("Failed to set prompt upload path:", error);
      toaster.toast({
        title: "设置失败",
        body: "无法更新上传路径设置"
      });
    }
  };

  const handlePickDownloadDir = async () => {
    try {
      const startPath = downloadDir || "/home/deck";
      const result = await openFilePicker(
        FILE_SELECTION_FOLDER,
        startPath,
        false,
        true
      );
      const selectedPath = result?.realpath || result?.path;
      if (!selectedPath) {
        return;
      }
      const saveResult = await setDownloadDir(selectedPath);
      if (saveResult.status === "success") {
        const nextPath = saveResult.path || selectedPath;
        setDownloadDirState(nextPath);
        toaster.toast({
          title: "下载目录已更新",
          body: nextPath
        });
      } else {
        toaster.toast({
          title: "设置失败",
          body: saveResult.message || "无法更新下载目录"
        });
      }
    } catch (error) {
      console.error("Failed to pick download directory:", error);
      toaster.toast({
        title: "设置失败",
        body: "无法打开文件选择器"
      });
    }
  };

  const handlePortSave = async () => {
    if (portSaving) return;
    const parsed = Number(portInput);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) {
      toaster.toast({
        title: "端口无效",
        body: "请输入 1-65535 之间的整数端口"
      });
      return;
    }
    setPortSaving(true);
    try {
      const response = await setServerPort(parsed);
      if (response.status === "success") {
        const nextPort = String(response.port ?? parsed);
        setPortInput(nextPort);
        window.dispatchEvent(new Event("decky-send-port-updated"));
        toaster.toast({
          title: "端口已更新",
          body: `当前端口: ${nextPort}`
        });
      } else {
        toaster.toast({
          title: "设置失败",
          body: response.message || "无法更新端口"
        });
      }
    } catch (error) {
      console.error("Failed to set port:", error);
      toaster.toast({
        title: "设置失败",
        body: "无法更新端口"
      });
    } finally {
      setPortSaving(false);
    }
  };

  const tabDefs: SettingsTab[] = [
    {
      id: "ui",
      title: "界面设置",
      content: (
        <PanelSection>
          <PanelSectionRow>
            <ToggleField
              label="显示二维码"
              description="在主页展示二维码"
              checked={settings.showQRCode}
              onChange={(value: boolean) => updateSetting("showQRCode", value)}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ToggleField
              label="显示访问地址"
              description="在主页展示访问链接"
              checked={settings.showUrlText}
              onChange={(value: boolean) => updateSetting("showUrlText", value)}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ToggleField
              label="显示传输记录"
              description="在主页展示传输状态"
              checked={settings.showTransferHistory}
              onChange={(value: boolean) => updateSetting("showTransferHistory", value)}
            />
          </PanelSectionRow>
        </PanelSection>
      )
    },
    {
      id: "transfer",
      title: "传输设置",
      content: (
        <>
          <PanelSection title="文本传输">
            <PanelSectionRow>
              <ToggleField
                label="自动复制文本"
                description="收到文本后自动复制到剪贴板"
                checked={autoCopyEnabled}
                onChange={handleAutoCopyToggle}
              />
            </PanelSectionRow>
          </PanelSection>
          <PanelSection title="文件传输">
            <PanelSectionRow>
              <ToggleField
                label="上传前选择路径"
                description="每次上传前手动选择保存目录"
                checked={promptUploadPathEnabled}
                onChange={handlePromptUploadPathToggle}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <div style={{ fontSize: "12px", color: "#9aa0a6", lineHeight: 1.4 }}>
                当前下载目录：{downloadDir || "未设置"}
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={handlePickDownloadDir}
              >
                选择下载目录
              </ButtonItem>
            </PanelSectionRow>
          </PanelSection>
        </>
      )
    },
    {
      id: "port",
      title: "端口设置",
      content: (
        <PanelSection>
          <PanelSectionRow>
            <TextField
              label="端口号"
              type="number"
              min={1}
              max={65535}
              inputMode="numeric"
              value={portInput}
              onChange={(event: { currentTarget: { value: string } }) => setPortInput(event.currentTarget.value)}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={handlePortSave}
              disabled={portSaving}
            >
              {portSaving ? "保存中..." : "保存端口"}
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )
    }
  ];

  return (
    <div
      ref={containerRef}
      style={{
        paddingTop: 48,
        paddingBottom: 24,
        minHeight: "100%",
        boxSizing: "border-box",
        backgroundColor: "var(--gpBackground-color, #1b1b1b)",
        overflowX: "hidden"
      }}
    >
      <Tabs
        tabs={tabDefs}
        activeTab={activeTab}
        onShowTab={(tabId: string) => {
          focusTabRow();
          setActiveTab(tabId);
          window.requestAnimationFrame(() => focusTabRow(tabId));
        }}
        autoFocusContents={false}
      />
    </div>
  );
};

export default definePlugin(() => {
  console.log("decky-send plugin initializing");
  startToastPolling();
  routerHook.addRoute(SETTINGS_ROUTE, SettingsPage);

  // Pre-fetch server status before component renders (like ToMoon pattern)
  // This prevents the "flash" effect where toggle shows OFF then switches to ON
  // IMPORTANT: Use immediately-invoked async function to pre-fetch, then set pluginReady
  (async function () {
    try {
      console.log("Pre-fetching server status...");
      const status = await getServerStatus();
      
      serverRunningGlobal = status.running;
      serverPortGlobal = status.port || DEFAULT_PORT;
      
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
    name: "Decky-send",
    // The content of your plugin's menu
    content: <Content />,
    alwaysRender: true,
    // The icon displayed in the plugin list
    icon: <FaUpload />,
    // The function triggered when your plugin unloads
    onDismount() {
      console.log("Unloading decky-send plugin");
      stopToastPolling();
      routerHook.removeRoute(SETTINGS_ROUTE);
    }
  };
});
