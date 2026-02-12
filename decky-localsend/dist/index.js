const manifest = {"name":"Decky Localsend"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const addEventListener = api.addEventListener;
const removeEventListener = api.removeEventListener;
const routerHook = api.routerHook;
const toaster = api.toaster;
const openFilePicker = api.openFilePicker;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

const createStoreImpl = (createState) => {
  let state;
  const listeners = /* @__PURE__ */ new Set();
  const setState = (partial, replace) => {
    const nextState = typeof partial === "function" ? partial(state) : partial;
    if (!Object.is(nextState, state)) {
      const previousState = state;
      state = (replace != null ? replace : typeof nextState !== "object" || nextState === null) ? nextState : Object.assign({}, state, nextState);
      listeners.forEach((listener) => listener(state, previousState));
    }
  };
  const getState = () => state;
  const getInitialState = () => initialState;
  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };
  const api = { setState, getState, getInitialState, subscribe };
  const initialState = state = createState(setState, getState, api);
  return api;
};
const createStore = ((createState) => createState ? createStoreImpl(createState) : createStoreImpl);

const identity = (arg) => arg;
function useStore(api, selector = identity) {
  const slice = SP_REACT.useSyncExternalStore(
    api.subscribe,
    SP_REACT.useCallback(() => selector(api.getState()), [api, selector]),
    SP_REACT.useCallback(() => selector(api.getInitialState()), [api, selector])
  );
  SP_REACT.useDebugValue(slice);
  return slice;
}
const createImpl = (createState) => {
  const api = createStore(createState);
  const useBoundStore = (selector) => useStore(api, selector);
  Object.assign(useBoundStore, api);
  return useBoundStore;
};
const create = ((createState) => createState ? createImpl(createState) : createImpl);

// Create the store
const useLocalSendStore = create((set) => ({
    // Initial state
    devices: [],
    selectedDevice: null,
    selectedFiles: [],
    shareLinkSessions: [],
    pendingShare: null,
    favorites: [],
    receiveProgress: null,
    uploadProgress: [],
    sendProgressTotalFiles: null,
    sendProgressCompletedCount: null,
    currentUploadSessionId: null,
    // Actions for devices
    setDevices: (devices) => set({ devices }),
    // Actions for selected device
    setSelectedDevice: (device) => set({ selectedDevice: device }),
    // Actions for selected files
    setSelectedFiles: (files) => set({ selectedFiles: files }),
    addFile: (file) => set((state) => {
        // Prevent duplicate files
        if (file.textContent) {
            // For text files, check if same text content already exists
            if (state.selectedFiles.some((item) => item.textContent === file.textContent && item.fileName === file.fileName)) {
                return state;
            }
        }
        else if (file.isFolder && file.folderPath) {
            // For folders, check by folderPath
            if (state.selectedFiles.some((item) => item.isFolder && item.folderPath === file.folderPath)) {
                return state;
            }
        }
        else {
            // For regular files, check by sourcePath
            if (state.selectedFiles.some((item) => !item.isFolder && item.sourcePath === file.sourcePath)) {
                return state;
            }
        }
        return { selectedFiles: [...state.selectedFiles, file] };
    }),
    removeFile: (fileId) => set((state) => ({
        selectedFiles: state.selectedFiles.filter((file) => file.id !== fileId),
    })),
    clearFiles: () => set({ selectedFiles: [] }),
    addShareLinkSession: (session) => set((state) => ({
        shareLinkSessions: [...state.shareLinkSessions, session],
    })),
    removeShareLinkSession: (sessionId) => set((state) => ({
        shareLinkSessions: state.shareLinkSessions.filter((s) => s.sessionId !== sessionId),
    })),
    clearShareLinkSessions: () => set({ shareLinkSessions: [] }),
    setPendingShare: (pending) => set({ pendingShare: pending }),
    setFavorites: (favorites) => set({ favorites }),
    setReceiveProgress: (value) => set((state) => ({
        receiveProgress: typeof value === "function" ? value(state.receiveProgress) : value,
    })),
    setUploadProgress: (value) => set((state) => ({
        uploadProgress: typeof value === "function" ? value(state.uploadProgress) : value,
    })),
    setSendProgressStats: (total, completed) => set({ sendProgressTotalFiles: total, sendProgressCompletedCount: completed }),
    setCurrentUploadSessionId: (id) => set({ currentUploadSessionId: id }),
    // Reset all state to initial values
    resetAll: () => set({
        devices: [],
        selectedDevice: null,
        selectedFiles: [],
        shareLinkSessions: [],
        pendingShare: null,
        favorites: [],
        receiveProgress: null,
        uploadProgress: [],
        sendProgressTotalFiles: null,
        sendProgressCompletedCount: null,
        currentUploadSessionId: null,
    }),
}));

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }
function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } } return target; }
function _extends() { _extends = Object.assign ? Object.assign.bind() : function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(obj, key, value) { key = _toPropertyKey(key); if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var {
        attr,
        size,
        title
      } = props,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaGithub (props) {
  return GenIcon({"attr":{"viewBox":"0 0 496 512"},"child":[{"tag":"path","attr":{"d":"M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3.7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3.3 2.9 2.3 3.9 1.6 1 3.6.7 4.3-.7.7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3.7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3.7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"},"child":[]}]})(props);
}function FaFileAlt (props) {
  return GenIcon({"attr":{"viewBox":"0 0 384 512"},"child":[{"tag":"path","attr":{"d":"M224 136V0H24C10.7 0 0 10.7 0 24v464c0 13.3 10.7 24 24 24h336c13.3 0 24-10.7 24-24V160H248c-13.2 0-24-10.8-24-24zm64 236c0 6.6-5.4 12-12 12H108c-6.6 0-12-5.4-12-12v-8c0-6.6 5.4-12 12-12h168c6.6 0 12 5.4 12 12v8zm0-64c0 6.6-5.4 12-12 12H108c-6.6 0-12-5.4-12-12v-8c0-6.6 5.4-12 12-12h168c6.6 0 12 5.4 12 12v8zm0-72v8c0 6.6-5.4 12-12 12H108c-6.6 0-12-5.4-12-12v-8c0-6.6 5.4-12 12-12h168c6.6 0 12 5.4 12 12zm96-114.1v6.1H256V0h6.1c6.4 0 12.5 2.5 17 7l97.9 98c4.5 4.5 7 10.6 7 16.9z"},"child":[]}]})(props);
}function FaFolder (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M464 128H272l-64-64H48C21.49 64 0 85.49 0 112v288c0 26.51 21.49 48 48 48h416c26.51 0 48-21.49 48-48V176c0-26.51-21.49-48-48-48z"},"child":[]}]})(props);
}function FaHeart (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M462.3 62.6C407.5 15.9 326 24.3 275.7 76.2L256 96.5l-19.7-20.3C186.1 24.3 104.5 15.9 49.7 62.6c-62.8 53.6-66.1 149.8-9.9 207.9l193.5 199.8c12.5 12.9 32.8 12.9 45.3 0l193.5-199.8c56.3-58.1 53-154.3-9.8-207.9z"},"child":[]}]})(props);
}function FaSync (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M440.65 12.57l4 82.77A247.16 247.16 0 0 0 255.83 8C134.73 8 33.91 94.92 12.29 209.82A12 12 0 0 0 24.09 224h49.05a12 12 0 0 0 11.67-9.26 175.91 175.91 0 0 1 317-56.94l-101.46-4.86a12 12 0 0 0-12.57 12v47.41a12 12 0 0 0 12 12H500a12 12 0 0 0 12-12V12a12 12 0 0 0-12-12h-47.37a12 12 0 0 0-11.98 12.57zM255.83 432a175.61 175.61 0 0 1-146-77.8l101.8 4.87a12 12 0 0 0 12.57-12v-47.4a12 12 0 0 0-12-12H12a12 12 0 0 0-12 12V500a12 12 0 0 0 12 12h47.35a12 12 0 0 0 12-12.6l-4.15-82.57A247.17 247.17 0 0 0 255.83 504c121.11 0 221.93-86.92 243.55-201.82a12 12 0 0 0-11.8-14.18h-49.05a12 12 0 0 0-11.67 9.26A175.86 175.86 0 0 1 255.83 432z"},"child":[]}]})(props);
}function FaTimes (props) {
  return GenIcon({"attr":{"viewBox":"0 0 352 512"},"child":[{"tag":"path","attr":{"d":"M242.72 256l100.07-100.07c12.28-12.28 12.28-32.19 0-44.48l-22.24-22.24c-12.28-12.28-32.19-12.28-44.48 0L176 189.28 75.93 89.21c-12.28-12.28-32.19-12.28-44.48 0L9.21 111.45c-12.28 12.28-12.28 32.19 0 44.48L109.28 256 9.21 356.07c-12.28 12.28-12.28 32.19 0 44.48l22.24 22.24c12.28 12.28 32.2 12.28 44.48 0L176 322.72l100.07 100.07c12.28 12.28 32.2 12.28 44.48 0l22.24-22.24c12.28-12.28 12.28-32.19 0-44.48L242.72 256z"},"child":[]}]})(props);
}function FaRegHeart (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M458.4 64.3C400.6 15.7 311.3 23 256 79.3 200.7 23 111.4 15.6 53.6 64.3-21.6 127.6-10.6 230.8 43 285.5l175.4 178.7c10 10.2 23.4 15.9 37.6 15.9 14.3 0 27.6-5.6 37.6-15.8L469 285.6c53.5-54.7 64.7-157.9-10.6-221.3zm-23.6 187.5L259.4 430.5c-2.4 2.4-4.4 2.4-6.8 0L77.2 251.8c-36.5-37.2-43.9-107.6 7.3-150.7 38.9-32.7 98.9-27.8 136.5 10.5l35 35.7 35-35.7c37.8-38.5 97.8-43.2 136.5-10.6 51.1 43.1 43.5 113.9 7.3 150.8z"},"child":[]}]})(props);
}

const en = {
    backend: {
        title: "LocalSend Backend",
        status: "Backend Status",
        running: "Backend is running",
        stopped: "Backend is stopped",
        scanDevices: "Scan Devices",
        refreshDevices: "Refresh Lists",
        scanNow: "Scan Now",
        scanning: "Scanning...",
        availableDevices: "Available Devices",
        noDevices: "No devices",
        selected: "Selected",
    },
    // Network Info Section
    networkInfo: {
        title: "Info",
        deviceName: "Device Name",
        port: "Port",
        number: "Number",
        ipAddress: "IP Address",
        multicastPort: "Multicast Port",
        noNetwork: "No network info",
    },
    // File Upload Section
    upload: {
        title: "File Upload",
        selectedDevice: "Selected Device",
        none: "None",
        chooseFile: "Choose File",
        chooseFolder: "Choose Folder",
        addText: "Add Text",
        confirmSend: "Confirm Send",
        uploading: "Uploading...",
        quickSendFavorites: "Quick Send to Favorites",
        sendTo: "Send to",
        deviceOffline: "Offline",
        selectedFiles: "Selected Files",
        clearFiles: "Clear Files",
        uploadProgress: "Upload Progress",
        textAdded: "Text added",
        readyToSend: "Ready to send as .txt",
        folderAdded: "Folder added",
        folderFiles: "files",
        manualSend: "Manual Send",
        createShareLink: "Create Share Link",
        noDeviceSelectedTitle: "No device selected",
        noDeviceSelectedMessage: "Please select a target device first",
        noFilesSelectedTitle: "No files selected",
        noFilesSelectedMessage: "Please select files to upload",
        pinRequiredToContinue: "PIN required to continue",
        failedTitle: "Upload failed",
        uploadCompletedTitle: "Upload complete",
        uploadCompletedBody: "Successfully uploaded {count} {files}",
        partialCompletedTitle: "Partial upload complete",
        partialCompletedBody: "Success: {success}, Failed: {failed}",
    },
    // Configuration Section
    config: {
        title: "Configuration",
        openConfig: "Open Configuration",
        basicConfig: "Basic",
        networkConfig: "Network",
        securityConfig: "Security",
        advancedConfig: "Advanced",
        alias: "Alias",
        default: "Default",
        editAlias: "Edit Alias",
        downloadFolder: "Download Folder",
        editDownloadFolder: "Edit Download Folder",
        chooseDownloadFolder: "Choose Download Folder",
        multicastAddress: "Multicast Address",
        editMulticastAddress: "Edit Multicast Address",
        multicastPort: "Multicast Port",
        editMulticastPort: "Edit Multicast Port",
        scanMode: "Scan Mode",
        scanModeDesc: "Mixed: UDP + HTTP | Normal: UDP multicast | Legacy: HTTP scan",
        scanModeMixed: "Mixed",
        scanModeNormal: "Normal",
        scanModeHTTP: "HTTP",
        skipNotify: "Skip Notify",
        skipNotifyDesc: "Skip notification when receiving files. Note: This feature will affect the history record saving!",
        pin: "PIN",
        pinConfigured: "Configured",
        pinNotSet: "Not set",
        editPin: "Edit PIN",
        clearPin: "Clear PIN",
        clearPinTitle: "Clear PIN",
        clearPinMessage: "Are you sure you want to clear the PIN?",
        autoSave: "Auto Save",
        autoSaveDesc: "Auto accept files from all devices",
        autoSaveFromFavorites: "Auto Save from Favorites",
        autoSaveFromFavoritesDesc: "Auto accept files from favorite devices only",
        favorites: "Favorite Devices",
        favoritesDesc: "Manage your favorite devices",
        favoritesEmpty: "No favorite devices",
        favoritesAdd: "Add to Favorites",
        refreshFavoritesDevices: "Refresh Favorite Devices",
        favoritesRemove: "Remove",
        favoritesAdded: "Added to favorites",
        favoritesRemoved: "Removed from favorites",
        removeFavoriteConfirm: "Remove this device from favorites?",
        scanningDevices: "Scanning for devices…",
        editFavoriteAlias: "Edit Favorite Name",
        deviceAlias: "Device Name",
        favoritesManage: "Manage Favorites",
        networkInterface: "Network Interface",
        networkInterfaceDesc: "Select network interface for device scanning",
        networkInterfaceAll: "All Interfaces",
        useHttps: "Use Encrypted Connection",
        useHttpsDesc: "Enable encrypted connection (HTTPS). Disable for unencrypted (HTTP)",
        notifyOnDownload: "Notify on Download Complete",
        notifyOnDownloadDesc: "Show notification when file download is complete",
        useDownload: "Use Download (Share via Link)",
        useDownloadDesc: "Enable Download API for share via link. Restart backend to take effect.",
        doNotMakeSessionFolder: "Do Not Create Session Subfolder",
        doNotMakeSessionFolderDesc: "When enabled, save files directly in download folder; same filename becomes name-2.ext, name-3.ext, …",
        saveReceiveHistory: "Save Receive History",
        saveReceiveHistoryDesc: "Save received file history for later viewing",
        disableInfoLogging: "Disable INFO Logging",
        disableInfoLoggingDesc: "Disable backend INFO level logging, prevent log output from occupying too much space",
        scanTimeout: "Scan Timeout",
        scanTimeoutDesc: "Auto scan timeout in seconds. Set to 0 to disable timeout",
        editScanTimeout: "Edit Scan Timeout",
        apply: "APPLY",
        configSaved: "Config saved",
        backendRestarted: "Backend restarted",
        restartToTakeEffect: "Restart backend to take effect",
        configUpdated: "Config updated",
        reloadConfig: "Reload Config",
        reloadConfigDesc: "Reload current saved config into the form",
        configReloaded: "Config reloaded",
    },
    // Settings Section
    settings: {
        title: "Settings",
        resetAllData: "Reset All Data",
        resetAllDataConfirm: "Are you sure you want to reset all settings to default? This will delete all configuration files and stop the backend.",
        factoryResetTitle: "Reset All Data",
        factoryResetMessage: "Are you sure you want to reset all settings to default?\n\nThis will delete all configuration files and stop the backend.",
        resetComplete: "Reset Complete",
        allDataCleared: "All data has been cleared",
        factoryResetComplete: "Reset Complete",
        allSettingsReset: "All settings have been reset to default",
        resetSuccess: "Reset Success",
        resetSuccessDesc: "All settings have been reset to default, please restart backend to take effect",
    },
    // Developer Tools Section
    devTools: {
        title: "Developer Tools",
        showTools: "Show Tools",
        hideTools: "Hide Tools",
        checkNotifyServer: "Check Notify Server",
        viewUploadHistory: "View Upload History",
        clearHistory: "Clear History",
    },
    // About Section
    about: {
        title: "About",
        aboutPlugin: "About This Plugin",
        pluginTitle: "Decky Localsend Plugin",
        pluginDesc: "A plugin for Decky Loader that brings LocalSend functionality to Steam Deck in gaming mode.",
        starOnGitHub: "If you like this plugin, please consider giving it a star on GitHub!",
        pluginRepo: "Decky Localsend Plugin",
        githubRepo: "GitHub Repo",
        developer: "Developer",
        githubProfile: "GitHub Profile",
        dependencies: "Dependencies",
        protocolDesc: "This plugin is developed based on the localsend/protocol.",
    },
    // Common
    common: {
        confirm: "Confirm",
        cancel: "Cancel",
        clear: "Clear",
        reset: "Reset",
        error: "Error",
        success: "Success",
        failed: "Failed",
        files: "file(s)",
        devices: "device(s)",
    },
    // Modals
    modal: {
        sendText: "Send Text",
        enterTextContent: "Enter text content",
        enterAlias: "Enter alias",
        enterMulticastAddress: "Enter multicast address",
        enterDownloadFolder: "Enter download folder path",
        enterMulticastPort: "Enter multicast port",
        enterPin: "Enter PIN",
        enterScanTimeout: "Enter scan timeout (seconds)",
        enterIpOrSuffix: "Enter IP address or suffix (e.g. 123 or 192.168.1.123)",
    },
    // Toasts
    toast: {
        backendNotRunning: "Backend not running",
        backendNotRunningBody: "Please start the LocalSend backend first",
        failedGetBackendStatus: "Failed to get backend status",
        failedLoadConfig: "Failed to load config",
        failedSelectFolder: "Failed to select folder",
        failedSaveConfig: "Failed to save config",
        failedUpdateConfig: "Failed to update config",
        factoryResetFailed: "Reset Failed",
        confirmFailed: "Confirm failed",
        missingSessionId: "Missing sessionId",
        accepted: "Accepted",
        rejected: "Rejected",
        receiveConfirmed: "Receive confirmed",
        receiveRejected: "Receive rejected",
        pinRequired: "PIN Required",
        pinRequiredForFiles: "PIN required for incoming files",
        notification: "Notification",
    },
    // Confirm Receive Modal
    confirmReceive: {
        title: "Incoming Files",
        from: "From",
        fileCount: "File count",
        accept: "Accept",
        reject: "Reject",
    },
    // Confirm Download Modal (receiver requests to download from Decky)
    confirmDownload: {
        title: "Confirm Download",
        message: "Someone is requesting to download",
        fromClient: "From {clientLabel} ({clientIp})",
        accept: "Allow",
        reject: "Reject",
    },
    // Share Link Modal (create share session, show download URL)
    shareLink: {
        orVisitDirect: "Or Visit Directly",
        title: "Share via Link List",
        Link: "Link",
        description: "Share this link with the receiver. They can open it in a browser to download the files.",
        copyLink: "Copy Link",
        copied: "Link copied!",
        closeShare: "End Share",
        shareEnded: "Share ended",
        selectFiles: "Please select files, folders, or add text to share",
        noActiveShare: "No active share",
        createFromMain: "Select files on the main page and use \"Create Share Link\" to start.",
        // Create share settings
        createShareSettings: "Create Share Settings",
        pinForShare: "PIN for Share",
        pinForShareDesc: "Require PIN to access shared files",
        autoAccept: "Auto Accept",
        autoAcceptDesc: "Automatically accept download requests",
        startShare: "Start Share",
        cancelCreate: "Cancel",
        enterPin: "Enter PIN",
        sessionId: "Session ID",
        expiresIn: "Expires in",
        minutes: "minutes",
        expired: "Expired",
        qrCode: "QR Code",
        backendRequired: "Backend must be running to share",
        accessHint: "Full link below; open in browser and enter Session ID to access.",
        httpsCertHint: "When using HTTPS, you may need to trust the certificate in your browser.",
        httpHint: "To use HTTP, turn off \"Use HTTPS\" (encryption) in configuration.",
        sameNetworkHint: "Ensure the receiver is on the same network as you.",
        filesInShare: "Files in this share",
        backToList: "Back to list",
    },
    // Text Received Modal
    textReceived: {
        copyToClipboard: "Copy to Clipboard",
        copied: "Copied!",
        close: "Close",
        charactersCount: "{count} characters",
    },
    text: {
        sendNoDeviceTitle: "No device selected",
        sendNoDeviceMessage: "Please select a target device first",
        emptyTextTitle: "Empty text",
        emptyTextMessage: "Please enter text to send",
        sendSuccessTitle: "Text sent",
        sendSuccessBody: "Successfully sent text message to {device}",
        sendFailedTitle: "Failed to send text",
        defaultFileName: "message.txt",
    },
    devices: {
        unknownAlias: "Unknown Device",
        unknownModel: "unknown",
    },
    // Receive progress modal (during transfer)
    receiveProgress: {
        receiving: "Receiving...",
        filesCount: "{current} / {total} files",
        cancelReceive: "Cancel receive",
    },
    // Send progress (sender-side: during upload)
    sendProgress: {
        sending: "Sending...",
        filesCount: "{current} / {total} files",
        cancelSend: "Cancel send",
        cancelSendToast: "Send cancelled",
        sendCompleteToast: "Transfer complete",
        rejectedToast: "Rejected by receiver",
        rejectedBody: "{success} transferred, {failed} failed",
    },
    // Notifications (receiver-side: upload started/cancelled/completed etc.)
    notify: {
        uploadStarted: "Upload Started",
        uploadCompleted: "Upload Completed",
        textUploadStarted: "Text Upload Started",
        textUploadCompleted: "Text Upload Completed",
        uploadEvent: "Upload Event",
        uploadCancelled: "Transfer cancelled by sender",
        receiveCancelled: "Receive cancelled",
    },
    // File Received Modal
    fileReceived: {
        folderPath: "Folder Path",
        fileCount: "File Count",
        files: "Files",
        andMoreFiles: "and {count} more files",
        copyPath: "Copy Path",
        pathCopied: "Path Copied!",
        close: "Close",
        total: "Total",
        success: "Success",
        failed: "Failed",
        failedFileIds: "Failed Files",
    },
    // Receive History
    receiveHistory: {
        title: "Receive History",
        loading: "Loading...",
        refresh: "Refresh",
        empty: "No receive history",
        recordCount: "Records",
        clearAll: "Clear All",
        clearAllTitle: "Clear History",
        clearAllMessage: "Are you sure you want to clear all receive history?",
        cleared: "History cleared",
        disabled: "Receive history is disabled",
        justNow: "Just now",
        minutesAgo: "min ago",
        hoursAgo: "hours ago",
        daysAgo: "days ago",
        textReceived: "Text",
    },
    // Screenshot Gallery (Experimental)
    screenshot: {
        title: "Steam Screenshots",
        openGallery: "Browse Screenshots",
        experimental: "Experimental Feature",
        warning: "This feature will scan screenshot files in ~/.local/share/Steam/userdata/ directory. This is an experimental feature. Do you want to continue?",
        warningDetails: "This feature will scan screenshot files in ~/.local/share/Steam/userdata/ directory. This is an experimental feature. Do you want to continue?",
        understand: "I Understand",
        gallery: "Screenshot Gallery",
        loading: "Loading...",
        noScreenshots: "No screenshots found",
        selectAll: "Select All",
        selected: "Selected",
        preview: "Preview",
        refresh: "Refresh",
        addToQueue: "Add to Queue",
        noSelection: "No screenshots selected",
        pleaseSelectScreenshots: "Please select at least one screenshot",
        loadFailed: "Failed to load screenshots",
        imageNotLoaded: "Image not loaded yet",
        added: "Screenshots Added",
        screenshotsAdded: "screenshot(s) added to send queue",
        page: "Page",
        prevPage: "Previous",
        nextPage: "Next",
    },
    unknownError: "Unknown error",
};

const zhCN = {
    // Backend Section
    backend: {
        title: "LocalSend 后端",
        status: "后端状态",
        running: "后端运行中",
        stopped: "后端已停止",
        scanDevices: "扫描设备",
        refreshDevices: "刷新列表",
        scanNow: "立即扫描",
        scanning: "扫描中...",
        availableDevices: "可用设备",
        noDevices: "无设备",
        selected: "已选中",
    },
    // Network Info Section
    networkInfo: {
        title: "信息",
        deviceName: "设备名称",
        port: "端口",
        number: "编号",
        ipAddress: "IP 地址",
        multicastPort: "多播端口",
        noNetwork: "无网络信息",
    },
    // File Upload Section
    upload: {
        title: "文件上传",
        selectedDevice: "已选设备",
        none: "无",
        chooseFile: "选择文件",
        chooseFolder: "选择文件夹",
        addText: "添加文本",
        confirmSend: "确认发送",
        uploading: "上传中...",
        quickSendFavorites: "快捷发送到收藏",
        sendTo: "发送到",
        deviceOffline: "离线",
        selectedFiles: "已选文件",
        clearFiles: "清空文件",
        uploadProgress: "上传进度",
        textAdded: "文本已添加",
        readyToSend: "准备以 .txt 发送",
        folderAdded: "文件夹已添加",
        folderFiles: "个文件",
        noDeviceSelectedTitle: "未选择设备",
        noDeviceSelectedMessage: "请先选择一个目标设备",
        noFilesSelectedTitle: "未选择文件",
        noFilesSelectedMessage: "请选择要上传的文件",
        pinRequiredToContinue: "继续操作需要 PIN 码",
        failedTitle: "上传失败",
        uploadCompletedTitle: "上传完成",
        uploadCompletedBody: "已成功上传 {count} 个{files}",
        partialCompletedTitle: "部分上传成功",
        partialCompletedBody: "成功: {success}，失败: {failed}",
        manualSend: "手动发送",
        createShareLink: "创建分享链接",
    },
    // Configuration Section
    config: {
        title: "配置",
        openConfig: "打开配置",
        basicConfig: "基本设置",
        networkConfig: "网络设置",
        securityConfig: "安全设置",
        advancedConfig: "高级设置",
        alias: "别名",
        default: "默认",
        editAlias: "编辑别名",
        downloadFolder: "下载文件夹",
        editDownloadFolder: "编辑下载文件夹",
        chooseDownloadFolder: "选择下载文件夹",
        multicastAddress: "组播地址",
        editMulticastAddress: "编辑组播地址",
        multicastPort: "组播端口",
        editMulticastPort: "编辑组播端口",
        scanMode: "扫描模式",
        scanModeDesc: "混合: UDP + HTTP | 普通: UDP 组播 | 传统: HTTP 扫描",
        scanModeMixed: "混合",
        scanModeNormal: "普通",
        scanModeHTTP: "HTTP",
        skipNotify: "跳过通知",
        skipNotifyDesc: "接收文件时截断Decky的通知，注意此功能会影响到历史记录保存！",
        pin: "PIN 码",
        pinConfigured: "已设置",
        pinNotSet: "未设置",
        editPin: "编辑 PIN",
        clearPin: "清除 PIN",
        clearPinTitle: "清除 PIN",
        clearPinMessage: "确定要清除 PIN 码吗？",
        autoSave: "自动保存",
        autoSaveDesc: "自动接受所有设备的文件",
        autoSaveFromFavorites: "收藏设备自动保存",
        autoSaveFromFavoritesDesc: "仅对收藏设备自动接受文件",
        favorites: "收藏设备",
        favoritesDesc: "管理收藏的设备",
        favoritesEmpty: "暂无收藏设备",
        favoritesAdd: "添加到收藏",
        refreshFavoritesDevices: "刷新收藏夹设备",
        favoritesRemove: "移除",
        favoritesAdded: "已添加到收藏",
        favoritesRemoved: "已从收藏移除",
        removeFavoriteConfirm: "确定要移除此收藏设备吗？",
        scanningDevices: "正在扫描设备…",
        editFavoriteAlias: "编辑收藏名称",
        deviceAlias: "设备名称",
        favoritesManage: "管理收藏",
        networkInterface: "网络接口",
        networkInterfaceDesc: "选择扫描设备使用的网络接口",
        networkInterfaceAll: "全部接口",
        useHttps: "使用加密",
        useHttpsDesc: "启用加密连接 (HTTPS)。关闭后使用非加密连接 (HTTP)",
        notifyOnDownload: "下载完成后提示",
        notifyOnDownloadDesc: "文件下载完成后显示通知",
        useDownload: "启用下载（通过链接分享）",
        useDownloadDesc: "启用通过链接分享的下载 API。需重启后端生效。",
        doNotMakeSessionFolder: "不创建会话子文件夹",
        doNotMakeSessionFolderDesc: "启用后，文件直接保存到下载目录；同名文件会保存为 name-2.ext、name-3.ext 等。",
        saveReceiveHistory: "保存接收历史",
        saveReceiveHistoryDesc: "保存接收的文件历史记录以便后续查看",
        disableInfoLogging: "禁用 INFO 日志",
        disableInfoLoggingDesc: "禁用后端 INFO 级别日志，可避免日志输出过多占用空间",
        scanTimeout: "扫描超时",
        scanTimeoutDesc: "自动扫描超时时间（秒）。设置为 0 禁用超时",
        editScanTimeout: "编辑扫描超时",
        apply: "应用",
        configSaved: "配置已保存",
        backendRestarted: "后端已重启",
        restartToTakeEffect: "重启后端以生效",
        configUpdated: "配置已更新",
        reloadConfig: "重载配置",
        reloadConfigDesc: "从当前保存的配置重新加载到界面",
        configReloaded: "配置已重载",
    },
    // Settings Section
    settings: {
        title: "设置",
        resetAllData: "重置所有数据",
        resetAllDataConfirm: "确定要将所有设置重置为默认值吗？这将删除所有配置文件并停止后端。",
        factoryResetTitle: "重置所有数据",
        factoryResetMessage: "确定要将所有设置重置为默认值吗？这将删除所有配置文件并停止后端。",
        resetComplete: "重置完成",
        allDataCleared: "所有数据已清除",
        factoryResetComplete: "重置完成",
        allSettingsReset: "所有设置已重置为默认值",
        resetSuccess: "重置成功",
        resetSuccessDesc: "所有设置已重置为默认值，请重启后端以生效",
    },
    // Developer Tools Section
    devTools: {
        title: "开发者工具",
        showTools: "显示工具",
        hideTools: "隐藏工具",
        checkNotifyServer: "检查通知服务器",
        viewUploadHistory: "查看上传历史",
        clearHistory: "清除历史",
    },
    // About Section
    about: {
        title: "关于",
        aboutPlugin: "关于此插件",
        pluginTitle: "Decky Localsend 插件",
        pluginDesc: "一款为 Decky Loader 打造的插件，在 Steam Deck 游戏模式下提供 LocalSend 功能。",
        starOnGitHub: "如果你喜欢本插件，欢迎在 GitHub 上给个 Star！",
        pluginRepo: "Decky Localsend 插件",
        githubRepo: "GitHub 仓库",
        developer: "开发者",
        githubProfile: "GitHub 主页",
        dependencies: "依赖",
        protocolDesc: "此插件基于 localsend/protocol 协议开发。",
    },
    // Common
    common: {
        confirm: "确认",
        cancel: "取消",
        clear: "清除",
        reset: "重置",
        error: "错误",
        success: "成功",
        failed: "失败",
        files: "个文件",
        devices: "台设备",
    },
    // Modals
    modal: {
        sendText: "发送文本",
        enterTextContent: "输入文本内容",
        enterAlias: "输入别名",
        enterMulticastAddress: "输入组播地址",
        enterDownloadFolder: "输入下载文件夹路径",
        enterMulticastPort: "输入组播端口",
        enterPin: "输入 PIN 码",
        enterScanTimeout: "输入扫描超时时间（秒）",
        enterIpOrSuffix: "输入 IP 地址或后缀（例如 123 或 192.168.1.123）",
    },
    // Toasts
    toast: {
        backendNotRunning: "后端未运行",
        backendNotRunningBody: "请先启动 LocalSend 后端",
        failedGetBackendStatus: "获取后端状态失败",
        failedLoadConfig: "加载配置失败",
        failedSelectFolder: "选择文件夹失败",
        failedSaveConfig: "保存配置失败",
        failedUpdateConfig: "更新配置失败",
        factoryResetFailed: "重置失败",
        confirmFailed: "确认失败",
        missingSessionId: "缺少会话ID",
        accepted: "已接受",
        rejected: "已拒绝",
        receiveConfirmed: "已确认接收",
        receiveRejected: "已拒绝接收",
        pinRequired: "需要 PIN 码",
        pinRequiredForFiles: "接收文件需要 PIN 码",
        notification: "通知",
    },
    // Confirm Receive Modal
    confirmReceive: {
        title: "收到文件",
        from: "来自",
        fileCount: "文件数量",
        accept: "接受",
        reject: "拒绝",
    },
    // Confirm Download Modal
    confirmDownload: {
        title: "确认下载",
        message: "有人请求下载",
        fromClient: "来自 {clientLabel}（{clientIp}）",
        accept: "允许",
        reject: "拒绝",
    },
    // Share Link Modal
    shareLink: {
        orVisitDirect: "或者直接访问",
        title: "通过链接分享列表",
        Link: "链接",
        description: "将链接分享给接收方，对方在浏览器中打开即可下载文件。",
        copyLink: "复制链接",
        copied: "链接已复制！",
        closeShare: "结束分享",
        shareEnded: "分享已结束",
        selectFiles: "请选择文件、文件夹或添加文本来分享",
        noActiveShare: "暂无分享",
        createFromMain: "请在主页面选择文件后点击「创建分享链接」开始。",
        // Create share settings
        createShareSettings: "创建分享设置",
        pinForShare: "分享 PIN 码",
        pinForShareDesc: "需要 PIN 码才能访问分享的文件",
        autoAccept: "自动接受",
        autoAcceptDesc: "自动接受下载请求",
        startShare: "开始分享",
        cancelCreate: "取消",
        enterPin: "输入 PIN 码",
        sessionId: "会话 ID",
        expiresIn: "过期时间",
        minutes: "分钟",
        expired: "已过期",
        qrCode: "二维码",
        backendRequired: "后端需要运行才能分享",
        accessHint: "完整链接见下方，在浏览器中打开并输入 SessionID 即可访问。",
        httpsCertHint: "使用 HTTPS 时，您可能需要在浏览器中信任证书。",
        httpHint: "如果需要使用 HTTP，请在配置中关闭「使用加密」。",
        sameNetworkHint: "请确保接收方与您在同一网络环境下访问。",
        filesInShare: "分享中的文件",
        backToList: "返回列表",
    },
    // Text Received Modal
    textReceived: {
        copyToClipboard: "复制到剪贴板",
        copied: "已复制！",
        close: "关闭",
        charactersCount: "{count} 个字符",
    },
    text: {
        sendNoDeviceTitle: "未选择设备",
        sendNoDeviceMessage: "请先选择一个目标设备",
        emptyTextTitle: "文本为空",
        emptyTextMessage: "请输入要发送的文本内容",
        sendSuccessTitle: "文本已发送",
        sendSuccessBody: "已成功向 {device} 发送文本消息",
        sendFailedTitle: "发送文本失败",
        defaultFileName: "message.txt",
    },
    devices: {
        unknownAlias: "未知设备",
        unknownModel: "未知型号",
    },
    // Receive progress modal (during transfer)
    receiveProgress: {
        receiving: "接收中...",
        filesCount: "{current} / {total} 个文件",
        cancelReceive: "取消接收",
    },
    // Send progress (sender-side: during upload)
    sendProgress: {
        sending: "正在发送...",
        filesCount: "{current} / {total} 个文件",
        cancelSend: "取消发送",
        cancelSendToast: "已取消发送",
        sendCompleteToast: "传输完毕",
        rejectedToast: "对方已拒绝",
        rejectedBody: "已传输 {success} 个，失败 {failed} 个",
    },
    // Notifications (receiver-side: upload started/cancelled/completed etc.)
    notify: {
        uploadStarted: "上传开始",
        uploadCompleted: "上传完成",
        textUploadStarted: "文本上传开始",
        textUploadCompleted: "文本上传完成",
        uploadEvent: "上传事件",
        uploadCancelled: "对方已取消传输",
        receiveCancelled: "已取消接收",
    },
    // File Received Modal
    fileReceived: {
        folderPath: "文件夹路径",
        fileCount: "文件数量",
        files: "文件列表",
        andMoreFiles: "等 {count} 个文件",
        copyPath: "复制路径",
        pathCopied: "路径已复制！",
        close: "关闭",
        total: "总计",
        success: "成功",
        failed: "失败",
        failedFileIds: "失败文件",
    },
    // Receive History
    receiveHistory: {
        title: "接收历史",
        loading: "加载中...",
        refresh: "刷新",
        empty: "暂无接收记录",
        recordCount: "记录数",
        clearAll: "清除全部",
        clearAllTitle: "清除历史",
        clearAllMessage: "确定要清除所有接收历史记录吗？",
        cleared: "历史记录已清除",
        disabled: "接收历史记录已关闭",
        justNow: "刚刚",
        minutesAgo: "分钟前",
        hoursAgo: "小时前",
        daysAgo: "天前",
        textReceived: "文本",
    },
    // Screenshot Gallery (Experimental)
    screenshot: {
        title: "Steam 截图",
        openGallery: "浏览截图",
        experimental: "实验性功能",
        warning: "此功能将会启用截图扫描功能，扫描 ~/.local/share/Steam/userdata/ 目录下的截图文件。",
        warningDetails: "该功能将扫描 ~/.local/share/Steam/userdata/ 目录下的截图文件。这是一个实验性功能，请确认是否继续？",
        understand: "我已了解",
        gallery: "截图画廊",
        loading: "加载中...",
        noScreenshots: "未找到截图",
        selectAll: "全选",
        selected: "已选",
        preview: "预览",
        refresh: "刷新",
        addToQueue: "添加到发送列表",
        noSelection: "未选择截图",
        pleaseSelectScreenshots: "请至少选择一张截图",
        loadFailed: "加载截图失败",
        imageNotLoaded: "图片尚未加载完成",
        added: "已添加截图",
        screenshotsAdded: "张截图已添加到发送列表",
        page: "页码",
        prevPage: "上一页",
        nextPage: "下一页",
    },
    unknownError: "未知错误",
};

const translations = {
    en,
    "en-US": en,
    "en-GB": en,
    "zh-CN": zhCN,
    "zh-Hans": zhCN,
    zh: zhCN,
};
let currentLanguage = "en";
/**
 * Initialize i18n with system language detection
 */
function initI18n() {
    try {
        // Try to get Steam's language setting
        const steamLang = window.LocalizationManager?.m_rgLocalesToUse?.[0];
        if (steamLang && translations[steamLang]) {
            currentLanguage = steamLang;
            return;
        }
        // Fallback to browser language
        const browserLang = navigator.language;
        if (translations[browserLang]) {
            currentLanguage = browserLang;
            return;
        }
        // Try base language (e.g., "zh" from "zh-TW")
        const baseLang = browserLang.split("-")[0];
        if (translations[baseLang]) {
            currentLanguage = baseLang;
            return;
        }
        // Default to English
        currentLanguage = "en";
    }
    catch (e) {
        console.error("Failed to detect language:", e);
        currentLanguage = "en";
    }
}
/**
 * Get translation by key path (e.g., "backend.title")
 */
function t(key) {
    const keys = key.split(".");
    let result = translations[currentLanguage] || translations.en;
    for (const k of keys) {
        if (result && typeof result === "object" && k in result) {
            result = result[k];
        }
        else {
            // Fallback to English if key not found
            result = translations.en;
            for (const fallbackKey of keys) {
                if (result && typeof result === "object" && fallbackKey in result) {
                    result = result[fallbackKey];
                }
                else {
                    return key; // Return key if translation not found
                }
            }
            break;
        }
    }
    return typeof result === "string" ? result : key;
}
// Initialize on import
initI18n();

// Modal for editing favorite alias
const EditFavoriteAliasModal = ({ device, onSave, closeModal, }) => {
    const [alias, setAlias] = SP_REACT.useState(device.alias || "");
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: closeModal, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: t("config.editFavoriteAlias") }), SP_JSX.jsxs(DFL.DialogBody, { children: [SP_JSX.jsx(DFL.TextField, { label: t("config.deviceAlias"), value: alias, onChange: (e) => setAlias(e.target.value) }), SP_JSX.jsxs("div", { style: { marginTop: "16px", display: "flex", gap: "8px", justifyContent: "flex-end" }, children: [SP_JSX.jsx(DFL.DialogButton, { onClick: closeModal, children: t("common.cancel") }), SP_JSX.jsx(DFL.DialogButton, { onClick: () => onSave(alias), children: t("common.confirm") })] })] })] }));
};
function DevicesPanel({ devices, selectedDevice, onSelectDevice, favorites = [], onAddToFavorites, onRemoveFromFavorites, }) {
    const isFavorite = (fingerprint) => favorites.some((f) => f.favorite_fingerprint === fingerprint);
    const handleFavoriteClick = (device, e) => {
        e.stopPropagation();
        if (!device.fingerprint)
            return;
        if (isFavorite(device.fingerprint)) {
            // Already a favorite: click to remove
            if (onRemoveFromFavorites) {
                onRemoveFromFavorites(device.fingerprint);
            }
            return;
        }
        // Not a favorite: show modal to add with alias
        if (!onAddToFavorites)
            return;
        const modal = DFL.showModal(SP_JSX.jsx(EditFavoriteAliasModal, { device: device, onSave: async (alias) => {
                await onAddToFavorites(device.fingerprint, alias);
                modal.Close();
            }, closeModal: () => modal.Close() }));
    };
    return (SP_JSX.jsx(DFL.PanelSection, { title: t("backend.availableDevices"), children: devices.length === 0 ? (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { children: t("backend.noDevices") }) })) : (devices.map((device, index) => (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => {
                    // Toggle selection: if already selected, deselect; otherwise select
                    if (selectedDevice?.fingerprint === device.fingerprint) {
                        onSelectDevice(null);
                    }
                    else {
                        onSelectDevice(device);
                    }
                }, children: SP_JSX.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }, children: [SP_JSX.jsxs("div", { style: { flex: 1 }, children: [SP_JSX.jsxs("div", { style: { fontWeight: 'bold' }, children: [device.alias ?? t("devices.unknownAlias"), selectedDevice?.fingerprint === device.fingerprint ? ` (${t("backend.selected")})` : ""] }), SP_JSX.jsxs("div", { style: { fontSize: '12px', opacity: 0.7 }, children: [device.ip_address, " - ", device.deviceModel ?? t("devices.unknownModel")] })] }), (onAddToFavorites || onRemoveFromFavorites) && device.fingerprint && (SP_JSX.jsx("div", { onClick: (e) => handleFavoriteClick(device, e), style: {
                                padding: "8px",
                                cursor: "pointer",
                                color: isFavorite(device.fingerprint) ? "#ff6b6b" : "#888",
                            }, children: isFavorite(device.fingerprint) ? SP_JSX.jsx(FaHeart, { size: 18 }) : SP_JSX.jsx(FaRegHeart, { size: 18 }) }))] }) }) }, `${device.fingerprint ?? device.alias ?? "device"}-${index}`)))) }));
}

// refer to https://github.com/xXJSONDeruloXx/decky-lsfg-vk/blob/97a70cd68813f2174fe145ee79784e509d11a742/src/utils/clipboardUtils.ts#L43
async function copyToClipboard(text) {
    const tempInput = document.createElement('input');
    tempInput.value = text;
    tempInput.style.position = 'absolute';
    tempInput.style.left = '-9999px';
    document.body.appendChild(tempInput);
    try {
        tempInput.focus();
        tempInput.select();
        let copySuccess = false;
        try {
            if (document.execCommand('copy')) {
                copySuccess = true;
            }
        }
        catch (e) {
            try {
                await navigator.clipboard.writeText(text);
                copySuccess = true;
            }
            catch (clipboardError) {
                console.error('Both copy methods failed:', e, clipboardError);
            }
        }
        return copySuccess;
    }
    finally {
        document.body.removeChild(tempInput);
    }
}

/**
 * Modal component for displaying received text content
 * Shows text with preview and copy option
 */
const TextReceivedModal = ({ title, content, fileName, onClose, closeModal }) => {
    const handleCopyToClipboard = async () => {
        const success = await copyToClipboard(content);
        if (success) {
            toaster.toast({
                title: t("textReceived.copied"),
                body: "",
            });
            closeModal?.();
            onClose();
        }
        else {
            toaster.toast({
                title: t("common.failed"),
                body: "",
            });
        }
    };
    const handleClose = () => {
        closeModal?.();
        onClose();
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: handleClose, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsxs(DFL.Focusable, { style: { padding: '10px', maxHeight: '400px', overflowY: 'auto' }, children: [SP_JSX.jsxs("div", { style: {
                                marginBottom: '10px',
                                paddingBottom: '10px',
                                borderBottom: '1px solid #3d3d3d'
                            }, children: [SP_JSX.jsx("div", { style: {
                                        color: '#b8b6b4',
                                        fontSize: '12px',
                                        marginBottom: '5px'
                                    }, children: SP_JSX.jsx("strong", { children: fileName }) }), SP_JSX.jsx("div", { style: {
                                        color: '#b8b6b4',
                                        fontSize: '12px'
                                    }, children: t("textReceived.charactersCount").replace("{count}", String(content.length)) })] }), SP_JSX.jsx("div", { style: { marginBottom: '10px' }, children: SP_JSX.jsx("div", { style: {
                                    padding: '12px',
                                    backgroundColor: '#0e0e0e',
                                    border: '1px solid #3d3d3d',
                                    borderRadius: '4px',
                                    maxHeight: '250px',
                                    overflowY: 'auto',
                                    fontSize: '13px',
                                    fontFamily: 'monospace',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                    lineHeight: '1.5',
                                    color: '#e8e8e8',
                                }, children: content }) })] }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: handleClose, style: { marginTop: "10px" }, children: t("textReceived.close") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: handleCopyToClipboard, style: { marginTop: "10px" }, children: t("textReceived.copyToClipboard") })] })] }));
};

const ConfirmReceiveModal = ({ title, from, fileCount, files, totalFiles, onConfirm, closeModal, }) => {
    const handleConfirm = (confirmed) => {
        closeModal?.();
        onConfirm(confirmed);
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: () => handleConfirm(false), closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title || t("confirmReceive.title") }), SP_JSX.jsxs(DFL.DialogBody, { children: [SP_JSX.jsxs("div", { style: { marginBottom: "10px", fontSize: "12px", color: "#b8b6b4" }, children: [t("confirmReceive.from"), ": ", SP_JSX.jsx("strong", { children: from || "Unknown" }), " (", fileCount, " ", t("common.files"), ")"] }), files.length > 0 && (SP_JSX.jsxs(DFL.Focusable, { style: { maxHeight: "240px", overflowY: "auto" }, children: [files.map((file, idx) => (SP_JSX.jsxs("div", { style: { padding: "4px 0", fontSize: "12px" }, children: [file.fileName, typeof file.size === "number" ? ` (${file.size} bytes)` : ""] }, `${file.fileName}-${idx}`))), totalFiles != null && totalFiles > files.length && (SP_JSX.jsx("div", { style: { marginTop: "6px", color: "#8a8a8a", fontSize: "12px" }, children: t("fileReceived.andMoreFiles").replace("{count}", String(totalFiles - files.length)) }))] }))] }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: () => handleConfirm(false), style: { marginTop: "10px" }, children: t("confirmReceive.reject") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: () => handleConfirm(true), style: { marginTop: "10px" }, children: t("confirmReceive.accept") })] })] }));
};

function clientLabel(clientType, userAgent) {
    if (clientType)
        return clientType;
    if (userAgent && userAgent.length > 50)
        return userAgent.slice(0, 50) + "…";
    return userAgent || "";
}
const ConfirmDownloadModal = ({ title, message, fileCount, files, totalFiles, clientIp, clientType, userAgent, onConfirm, closeModal, }) => {
    const handleConfirm = (confirmed) => {
        closeModal?.();
        onConfirm(confirmed);
    };
    const fromLine = clientIp != null
        ? t("confirmDownload.fromClient")
            .replace("{clientLabel}", clientLabel(clientType, userAgent) || "Unknown")
            .replace("{clientIp}", clientIp)
        : null;
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: () => handleConfirm(false), closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title || t("confirmDownload.title") }), SP_JSX.jsxs(DFL.DialogBody, { children: [fromLine && (SP_JSX.jsx("div", { style: { marginBottom: "8px", fontSize: "12px", color: "#b8b6b4" }, children: fromLine })), SP_JSX.jsx("div", { style: { marginBottom: "10px", fontSize: "12px", color: "#b8b6b4" }, children: message || `${t("confirmDownload.message")} ${fileCount} ${t("common.files")}` }), files.length > 0 && (SP_JSX.jsxs(DFL.Focusable, { style: { maxHeight: "240px", overflowY: "auto" }, children: [files.map((file, idx) => (SP_JSX.jsxs("div", { style: { padding: "4px 0", fontSize: "12px" }, children: [file.fileName, typeof file.size === "number" ? ` (${file.size} bytes)` : ""] }, `${file.id ?? file.fileName}-${idx}`))), totalFiles != null && totalFiles > files.length && (SP_JSX.jsx("div", { style: { marginTop: "6px", color: "#8a8a8a", fontSize: "12px" }, children: t("fileReceived.andMoreFiles").replace("{count}", String(totalFiles - files.length)) }))] }))] }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: () => handleConfirm(false), style: { marginTop: "10px" }, children: t("confirmDownload.reject") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: () => handleConfirm(true), style: { marginTop: "10px" }, children: t("confirmDownload.accept") })] })] }));
};

/**
 * Modal component for displaying file download completion notification
 * Shows folder path with copy option
 */
const FileReceivedModal = ({ title, folderPath, fileCount, files, totalFiles, successFiles, failedFiles, failedFileIds, onClose, closeModal }) => {
    const hasFailures = failedFiles !== undefined && failedFiles > 0;
    const handleCopyPath = async () => {
        const success = await copyToClipboard(folderPath);
        if (success) {
            toaster.toast({
                title: t("fileReceived.pathCopied"),
                body: "",
            });
            closeModal?.();
            onClose();
        }
        else {
            toaster.toast({
                title: t("common.failed"),
                body: "",
            });
        }
    };
    const handleClose = () => {
        closeModal?.();
        onClose();
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: handleClose, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsxs(DFL.Focusable, { style: { padding: '10px', maxHeight: '400px', overflowY: 'auto' }, children: [SP_JSX.jsxs("div", { style: {
                                marginBottom: '10px',
                                paddingBottom: '10px',
                                borderBottom: '1px solid #3d3d3d'
                            }, children: [SP_JSX.jsx("div", { style: {
                                        color: '#b8b6b4',
                                        fontSize: '12px',
                                        marginBottom: '5px'
                                    }, children: SP_JSX.jsxs("strong", { children: [t("fileReceived.fileCount"), ": ", totalFiles ?? fileCount] }) }), totalFiles !== undefined && (SP_JSX.jsxs("div", { style: {
                                        color: hasFailures ? '#ff6b6b' : '#b8b6b4',
                                        fontSize: '12px',
                                        marginTop: '5px'
                                    }, children: [t("fileReceived.total"), ": ", totalFiles, " | ", t("fileReceived.success"), ": ", successFiles, " | ", t("fileReceived.failed"), ": ", failedFiles] }))] }), SP_JSX.jsxs("div", { style: { marginBottom: '10px' }, children: [SP_JSX.jsxs("div", { style: {
                                        color: '#b8b6b4',
                                        fontSize: '12px',
                                        marginBottom: '5px'
                                    }, children: [t("fileReceived.folderPath"), ":"] }), SP_JSX.jsx("div", { style: {
                                        padding: '12px',
                                        backgroundColor: '#0e0e0e',
                                        border: '1px solid #3d3d3d',
                                        borderRadius: '4px',
                                        fontSize: '13px',
                                        fontFamily: 'monospace',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        lineHeight: '1.5',
                                        color: '#e8e8e8',
                                    }, children: folderPath })] }), files.length > 0 && (SP_JSX.jsxs("div", { style: { marginBottom: '10px' }, children: [SP_JSX.jsxs("div", { style: {
                                        color: '#b8b6b4',
                                        fontSize: '12px',
                                        marginBottom: '5px'
                                    }, children: [t("fileReceived.files"), ":"] }), SP_JSX.jsxs("div", { style: {
                                        padding: '12px',
                                        backgroundColor: '#0e0e0e',
                                        border: '1px solid #3d3d3d',
                                        borderRadius: '4px',
                                        maxHeight: '150px',
                                        overflowY: 'auto',
                                        fontSize: '12px',
                                        fontFamily: 'monospace',
                                        lineHeight: '1.5',
                                        color: '#e8e8e8',
                                    }, children: [files.map((file, index) => (SP_JSX.jsxs("div", { style: { marginBottom: '2px' }, children: ["\u2022 ", file] }, index))), totalFiles != null && totalFiles > files.length && (SP_JSX.jsx("div", { style: { marginTop: '6px', color: '#8a8a8a', fontSize: '12px' }, children: t("fileReceived.andMoreFiles").replace("{count}", String(totalFiles - files.length)) }))] })] })), hasFailures && failedFileIds && failedFileIds.length > 0 && (SP_JSX.jsxs("div", { style: { marginBottom: '10px' }, children: [SP_JSX.jsxs("div", { style: {
                                        color: '#ff6b6b',
                                        fontSize: '12px',
                                        marginBottom: '5px'
                                    }, children: [t("fileReceived.failedFileIds"), ":"] }), SP_JSX.jsx("div", { style: {
                                        padding: '12px',
                                        backgroundColor: '#1a0e0e',
                                        border: '1px solid #5d3d3d',
                                        borderRadius: '4px',
                                        maxHeight: '100px',
                                        overflowY: 'auto',
                                        fontSize: '12px',
                                        fontFamily: 'monospace',
                                        lineHeight: '1.5',
                                        color: '#ff9999',
                                    }, children: failedFileIds.map((fileId, index) => (SP_JSX.jsxs("div", { style: { marginBottom: '2px' }, children: ["\u2022 ", fileId] }, index))) })] }))] }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: handleClose, style: { marginTop: "10px" }, children: t("fileReceived.close") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: handleCopyPath, style: { marginTop: "10px" }, children: t("fileReceived.copyPath") })] })] }));
};

// reference: https://github.com/musick-dev/museck/blob/main/src/components/ProgressCard.tsx
const theme$1 = {
    surfaceContainer: "#1e1e2a",
    surfaceContainerHigh: "#262636",
    surfaceContainerHighest: "#2e2e42",
    primary: "#4a9eff",
    onSurfaceVariant: "#9898a8",
    outline: "#48485a",
    error: "#ff6b6b",
    radiusMd: "16px",
    radiusFull: "9999px",
    transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
};
/**
 * Panel block showing receive progress (X / Y files) during an upload session.
 * reference: https://github.com/musick-dev/museck/blob/main/src/components/ProgressCard.tsx
 */
const ReceiveProgressPanel = ({ receiveProgress, onCancelReceive }) => {
    const { totalFiles, completedCount, currentFileName, sessionId } = receiveProgress;
    const percent = totalFiles > 0 ? Math.min(100, Math.round((completedCount / totalFiles) * 100)) : 0;
    const filesCountText = t("receiveProgress.filesCount")
        .replace("{current}", String(completedCount))
        .replace("{total}", String(totalFiles));
    return (SP_JSX.jsxs(DFL.PanelSection, { title: t("receiveProgress.receiving"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: {
                        width: "100%",
                        maxWidth: "92%",
                        margin: "0 auto",
                        padding: "14px 16px",
                        background: `linear-gradient(135deg, ${theme$1.surfaceContainerHigh} 0%, ${theme$1.surfaceContainer} 100%)`,
                        borderRadius: theme$1.radiusMd,
                        boxShadow: "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)",
                        border: `1px solid ${theme$1.outline}22`,
                    }, children: [SP_JSX.jsxs("div", { style: {
                                display: "flex",
                                alignItems: "center",
                                gap: "12px",
                                marginBottom: currentFileName ? "10px" : "0",
                                fontSize: "12px",
                                color: theme$1.onSurfaceVariant,
                                fontWeight: "500",
                                fontVariantNumeric: "tabular-nums",
                            }, children: [SP_JSX.jsx("span", { style: { flexShrink: 0, minWidth: "72px", textAlign: "right" }, children: filesCountText }), SP_JSX.jsx("div", { style: {
                                        flex: 1,
                                        minWidth: 0,
                                        height: "6px",
                                        backgroundColor: theme$1.surfaceContainerHighest,
                                        borderRadius: theme$1.radiusFull,
                                        overflow: "hidden",
                                        position: "relative",
                                    }, children: SP_JSX.jsx("div", { style: {
                                            position: "absolute",
                                            left: 0,
                                            top: 0,
                                            width: `${percent}%`,
                                            height: "100%",
                                            background: `linear-gradient(90deg, ${theme$1.primary}88 0%, ${theme$1.primary} 100%)`,
                                            borderRadius: theme$1.radiusFull,
                                            transition: theme$1.transition,
                                            boxShadow: `0 0 12px ${theme$1.primary}66`,
                                        } }) })] }), currentFileName && (SP_JSX.jsx("div", { style: {
                                fontSize: "11px",
                                color: theme$1.onSurfaceVariant,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                paddingTop: "4px",
                                borderTop: `1px solid ${theme$1.outline}22`,
                            }, children: currentFileName }))] }) }), onCancelReceive && sessionId && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => onCancelReceive(sessionId), children: SP_JSX.jsxs("div", { style: {
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "8px",
                            color: theme$1.error,
                            fontSize: "12px",
                            fontWeight: "500",
                        }, children: [SP_JSX.jsx(FaTimes, { style: { fontSize: "12px", flexShrink: 0 } }), t("receiveProgress.cancelReceive")] }) }) }))] }));
};

const proxyGet = callable("proxy_get");
const proxyPost = callable("proxy_post");
const proxyDelete = callable("proxy_delete");

// Same theme as ReceiveProgressPanel for consistent card + progress bar layout
const theme = {
    surfaceContainer: "#1e1e2a",
    surfaceContainerHigh: "#262636",
    surfaceContainerHighest: "#2e2e42",
    primary: "#4a9eff",
    onSurfaceVariant: "#9898a8",
    outline: "#48485a",
    radiusMd: "16px",
    radiusFull: "9999px",
    transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
};
/**
 * Panel block showing send progress (X / Y files) during an upload session.
 * Shown at top (same position as ReceiveProgressPanel) when uploadProgress has items.
 * Uses sendProgressTotalFiles/sendProgressCompletedCount from store when set (e.g. folder uploads);
 * otherwise falls back to uploadProgress length and done/error count.
 * Layout matches ReceiveProgressPanel  .
 */
const themeError = "#ff6b6b";
const SendProgressPanel = ({ uploadProgress }) => {
    const sendProgressTotalFiles = useLocalSendStore((state) => state.sendProgressTotalFiles);
    const sendProgressCompletedCount = useLocalSendStore((state) => state.sendProgressCompletedCount);
    const currentUploadSessionId = useLocalSendStore((state) => state.currentUploadSessionId);
    const setUploadProgress = useLocalSendStore((state) => state.setUploadProgress);
    const setSendProgressStats = useLocalSendStore((state) => state.setSendProgressStats);
    const setCurrentUploadSessionId = useLocalSendStore((state) => state.setCurrentUploadSessionId);
    const handleCancelSend = async () => {
        const sessionId = currentUploadSessionId;
        if (!sessionId)
            return;
        try {
            await proxyPost(`/api/self/v1/cancel?sessionId=${encodeURIComponent(sessionId)}`);
        }
        finally {
            setUploadProgress([]);
            setSendProgressStats(null, null);
            setCurrentUploadSessionId(null);
            toaster.toast({ title: t("sendProgress.cancelSendToast"), body: "" });
        }
    };
    const totalFiles = sendProgressTotalFiles ?? uploadProgress.length;
    const completedCount = sendProgressCompletedCount ??
        uploadProgress.filter((p) => p.status === "done" || p.status === "error").length;
    const currentItem = uploadProgress.find((p) => p.status === "uploading");
    const currentFileName = currentItem?.fileName ?? "";
    const percent = totalFiles > 0
        ? Math.min(100, Math.round((completedCount / totalFiles) * 100))
        : 0;
    const filesCountText = t("sendProgress.filesCount")
        .replace("{current}", String(completedCount))
        .replace("{total}", String(totalFiles));
    return (SP_JSX.jsxs(DFL.PanelSection, { title: t("sendProgress.sending"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: {
                        width: "100%",
                        maxWidth: "92%",
                        margin: "0 auto",
                        padding: "14px 16px",
                        background: `linear-gradient(135deg, ${theme.surfaceContainerHigh} 0%, ${theme.surfaceContainer} 100%)`,
                        borderRadius: theme.radiusMd,
                        boxShadow: "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)",
                        border: `1px solid ${theme.outline}22`,
                    }, children: [SP_JSX.jsxs("div", { style: {
                                display: "flex",
                                alignItems: "center",
                                gap: "12px",
                                marginBottom: currentFileName ? "10px" : "0",
                                fontSize: "12px",
                                color: theme.onSurfaceVariant,
                                fontWeight: "500",
                                fontVariantNumeric: "tabular-nums",
                            }, children: [SP_JSX.jsx("span", { style: { flexShrink: 0, minWidth: "72px", textAlign: "right" }, children: filesCountText }), SP_JSX.jsx("div", { style: {
                                        flex: 1,
                                        minWidth: 0,
                                        height: "6px",
                                        backgroundColor: theme.surfaceContainerHighest,
                                        borderRadius: theme.radiusFull,
                                        overflow: "hidden",
                                        position: "relative",
                                    }, children: SP_JSX.jsx("div", { style: {
                                            position: "absolute",
                                            left: 0,
                                            top: 0,
                                            width: `${percent}%`,
                                            height: "100%",
                                            background: `linear-gradient(90deg, ${theme.primary}88 0%, ${theme.primary} 100%)`,
                                            borderRadius: theme.radiusFull,
                                            transition: theme.transition,
                                            boxShadow: `0 0 12px ${theme.primary}66`,
                                        } }) })] }), currentFileName && (SP_JSX.jsx("div", { style: {
                                fontSize: "11px",
                                color: theme.onSurfaceVariant,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                paddingTop: "4px",
                                borderTop: `1px solid ${theme.outline}22`,
                            }, children: currentFileName }))] }) }), currentUploadSessionId && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleCancelSend, children: SP_JSX.jsxs("div", { style: {
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "8px",
                            color: themeError,
                            fontSize: "12px",
                            fontWeight: "500",
                        }, children: [SP_JSX.jsx(FaTimes, { style: { fontSize: "12px", flexShrink: 0 } }), t("sendProgress.cancelSend")] }) }) }))] }));
};

const BasicInputBoxModal = ({ title = "", label = "", onSubmit, onCancel, closeModal, }) => {
    const [inputValue, setInputValue] = SP_REACT.useState("");
    const handleCancel = () => {
        closeModal?.();
        onCancel();
    };
    const handleSubmit = () => {
        const trimmed = inputValue.trim();
        if (!trimmed)
            return;
        closeModal?.();
        onSubmit(inputValue);
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: handleCancel, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsx(DFL.Field, { label: label, children: SP_JSX.jsx(DFL.TextField, { value: inputValue, onChange: (e) => setInputValue(e?.target?.value || ""), style: { width: "100%", minWidth: "200px" } }) }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: handleCancel, style: { marginTop: "10px" }, children: t("common.cancel") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: handleSubmit, disabled: !inputValue.trim(), style: { marginTop: "10px" }, children: t("common.confirm") })] })] }));
};

// Backend API
const startBackend = callable("start_backend");
const stopBackend = callable("stop_backend");
const getBackendStatus = callable("get_backend_status");
// File API
const writeTempTextFile = callable("write_temp_text_file");
const listFolderFiles = callable("list_folder_files");
// Upload Sessions API
callable("get_upload_sessions");
callable("clear_upload_sessions");
// Notification API
callable("get_notify_server_status");
// Factory Reset API
const factoryReset = callable("factory_reset");
const getReceiveHistory = callable("get_receive_history");
const clearReceiveHistory = callable("clear_receive_history");
const deleteReceiveHistoryItem = callable("delete_receive_history_item");
// Backend Config API
const getBackendConfig = callable("get_backend_config");
const setBackendConfig = callable("set_backend_config");

const ConfirmModal = ({ title, message, confirmText = t("common.confirm"), cancelText = t("common.cancel"), onConfirm, onCancel, closeModal, }) => {
    const handleConfirm = () => {
        closeModal?.();
        onConfirm();
    };
    const handleCancel = () => {
        closeModal?.();
        onCancel?.();
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: handleCancel, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsx("div", { style: { fontSize: "14px", color: "#b8b6b4", whiteSpace: "pre-wrap" }, children: message }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: handleCancel, style: { marginTop: "10px" }, children: cancelText }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: handleConfirm, style: { marginTop: "10px" }, children: confirmText })] })] }));
};

const ReceiveHistoryPanel = ({ saveReceiveHistory }) => {
    const [history, setHistory] = SP_REACT.useState([]);
    const [loading, setLoading] = SP_REACT.useState(false);
    const loadHistory = async () => {
        if (!saveReceiveHistory) {
            setHistory([]);
            return;
        }
        setLoading(true);
        try {
            const data = await getReceiveHistory();
            setHistory(data || []);
        }
        catch (error) {
            console.error("Failed to load receive history:", error);
        }
        finally {
            setLoading(false);
        }
    };
    SP_REACT.useEffect(() => {
        loadHistory();
    }, [saveReceiveHistory]);
    const handleRefresh = () => {
        loadHistory();
    };
    const handleClearAll = () => {
        const modal = DFL.showModal(SP_JSX.jsx(ConfirmModal, { title: t("receiveHistory.clearAllTitle"), message: t("receiveHistory.clearAllMessage"), confirmText: t("common.clear"), cancelText: t("common.cancel"), onConfirm: async () => {
                try {
                    await clearReceiveHistory();
                    setHistory([]);
                    toaster.toast({
                        title: t("receiveHistory.cleared"),
                        body: "",
                    });
                }
                catch (error) {
                    toaster.toast({
                        title: t("common.failed"),
                        body: String(error),
                    });
                }
            }, closeModal: () => modal.Close() }));
    };
    const handleDeleteItem = async (itemId) => {
        try {
            const result = await deleteReceiveHistoryItem(itemId);
            if (result.success) {
                setHistory((prev) => prev.filter((item) => item.id !== itemId));
            }
        }
        catch (error) {
            toaster.toast({
                title: t("common.failed"),
                body: String(error),
            });
        }
    };
    const handleViewItem = (item) => {
        if (item.isText && item.textContent) {
            // Show text modal for text items
            const modalResult = DFL.showModal(SP_JSX.jsx(TextReceivedModal, { title: item.title, content: item.textContent, fileName: item.files[0] || "text.txt", onClose: () => { }, closeModal: () => modalResult.Close() }));
        }
        else {
            // Show file modal for file items (pass totalFiles etc so modal shows correct count and "and N more")
            const modalResult = DFL.showModal(SP_JSX.jsx(FileReceivedModal, { title: item.title, folderPath: item.folderPath, fileCount: item.fileCount, files: item.files, totalFiles: item.totalFiles ?? item.fileCount, successFiles: item.successFiles, failedFiles: item.failedFiles, failedFileIds: item.failedFileIds, onClose: () => { }, closeModal: () => modalResult.Close() }));
        }
    };
    const formatTime = (timestamp) => {
        const date = new Date(timestamp * 1000);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        if (diffMins < 1)
            return t("receiveHistory.justNow");
        if (diffMins < 60)
            return `${diffMins} ${t("receiveHistory.minutesAgo")}`;
        if (diffHours < 24)
            return `${diffHours} ${t("receiveHistory.hoursAgo")}`;
        if (diffDays < 7)
            return `${diffDays} ${t("receiveHistory.daysAgo")}`;
        return date.toLocaleDateString();
    };
    if (!saveReceiveHistory) {
        return (SP_JSX.jsx(DFL.PanelSection, { title: t("receiveHistory.title"), children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { color: '#888', fontSize: '12px' }, children: t("receiveHistory.disabled") }) }) }));
    }
    return (SP_JSX.jsxs(DFL.PanelSection, { title: t("receiveHistory.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleRefresh, disabled: loading, children: SP_JSX.jsxs("span", { style: { display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }, children: [SP_JSX.jsx(FaSync, { size: 12 }), loading ? t("receiveHistory.loading") : t("receiveHistory.refresh")] }) }) }), history.length === 0 ? (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { color: '#888', fontSize: '12px', textAlign: 'center' }, children: t("receiveHistory.empty") }) })) : (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("receiveHistory.recordCount"), children: history.length }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { maxHeight: '200px', overflowY: 'auto' }, children: history.map((item) => (SP_JSX.jsxs("div", { style: {
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '8px 4px',
                                    borderBottom: '1px solid #3d3d3d',
                                    fontSize: '12px',
                                }, children: [SP_JSX.jsxs("div", { style: {
                                            flex: 1,
                                            cursor: 'pointer',
                                            overflow: 'hidden',
                                        }, onClick: () => handleViewItem(item), children: [SP_JSX.jsxs("div", { style: {
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '6px',
                                                    marginBottom: '2px'
                                                }, children: [item.isText ? (SP_JSX.jsx(FaFileAlt, { size: 12, style: { color: '#ffa500' } })) : (SP_JSX.jsx(FaFolder, { size: 12, style: { color: '#4a9eff' } })), SP_JSX.jsx("span", { style: {
                                                            fontWeight: 'bold',
                                                            overflow: 'hidden',
                                                            textOverflow: 'ellipsis',
                                                            whiteSpace: 'nowrap',
                                                        }, children: item.isText
                                                            ? (item.textPreview || t("receiveHistory.textReceived"))
                                                            : `${item.fileCount} ${t("common.files")}` })] }), SP_JSX.jsx("div", { style: {
                                                    color: '#888',
                                                    fontSize: '10px',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap',
                                                }, children: formatTime(item.timestamp) })] }), SP_JSX.jsx("button", { onClick: (e) => {
                                            e.stopPropagation();
                                            handleDeleteItem(item.id);
                                        }, style: {
                                            marginLeft: '8px',
                                            padding: '4px 8px',
                                            fontSize: '10px',
                                            backgroundColor: '#dc3545',
                                            color: '#fff',
                                            border: 'none',
                                            borderRadius: '3px',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                        }, children: SP_JSX.jsx(FaTimes, { size: 10 }) })] }, item.id))) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleClearAll, children: t("receiveHistory.clearAll") }) })] }))] }));
};

const ScreenshotGalleryModal = ({ onSelectScreenshots, closeModal }) => {
    const [screenshots, setScreenshots] = SP_REACT.useState([]);
    const [total, setTotal] = SP_REACT.useState(0);
    const [currentPage, setCurrentPage] = SP_REACT.useState(1);
    const [selectedScreenshots, setSelectedScreenshots] = SP_REACT.useState(new Map());
    const [loading, setLoading] = SP_REACT.useState(true);
    const [imageBlobUrls, setImageBlobUrls] = SP_REACT.useState(new Map());
    // Per-page "select all": derived from current page only
    const selectAll = screenshots.length > 0 && screenshots.every((s) => selectedScreenshots.has(s.path));
    const pageSize = 10;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    SP_REACT.useEffect(() => {
        loadScreenshots(1);
    }, []);
    // Load images through proxyGet
    SP_REACT.useEffect(() => {
        if (screenshots.length === 0)
            return;
        const loadImages = async () => {
            const urlMap = new Map();
            for (const screenshot of screenshots) {
                try {
                    const imageUrl = `/api/self/v1/get-image?fileName=file://${encodeURIComponent(screenshot.path)}`;
                    const result = await proxyGet(imageUrl);
                    if (result.status === 200 && result.data) {
                        // Convert base64 to blob URL
                        const base64Data = result.data;
                        const binaryString = atob(base64Data);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        const blob = new Blob([bytes], { type: 'image/png' });
                        const blobUrl = URL.createObjectURL(blob);
                        urlMap.set(screenshot.path, blobUrl);
                    }
                }
                catch (error) {
                    console.error(`Failed to load image for ${screenshot.filename}:`, error);
                }
            }
            setImageBlobUrls(urlMap);
        };
        loadImages();
        // Cleanup blob URLs on unmount
        return () => {
            imageBlobUrls.forEach(url => URL.revokeObjectURL(url));
        };
    }, [screenshots]);
    const loadScreenshots = async (page, refreshNow) => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page: String(page),
                pageSize: String(pageSize),
            });
            if (refreshNow) {
                params.set("refresh-now", "1");
            }
            const result = await proxyGet(`/api/self/v1/get-user-screenshot?${params.toString()}`);
            const status = result?.status;
            const data = result?.data;
            if (status !== 200 || data?.error) {
                toaster.toast({
                    title: t("screenshot.loadFailed"),
                    body: data?.error || t("common.unknownError"),
                });
                return;
            }
            const list = data?.data?.screenshots ?? [];
            const totalCount = data?.data?.total ?? 0;
            setScreenshots(list);
            setTotal(totalCount);
            setCurrentPage(page);
        }
        catch (error) {
            toaster.toast({
                title: t("screenshot.loadFailed"),
                body: String(error),
            });
        }
        finally {
            setLoading(false);
        }
    };
    const toggleScreenshot = (path) => {
        setSelectedScreenshots((prev) => {
            const next = new Map(prev);
            if (next.has(path)) {
                next.delete(path);
            }
            else {
                const screenshot = screenshots.find((s) => s.path === path);
                if (screenshot)
                    next.set(path, screenshot);
            }
            return next;
        });
    };
    const toggleSelectAll = (checked) => {
        setSelectedScreenshots((prev) => {
            const next = new Map(prev);
            if (checked) {
                screenshots.forEach((s) => next.set(s.path, s));
            }
            else {
                screenshots.forEach((s) => next.delete(s.path));
            }
            return next;
        });
    };
    const handleConfirm = () => {
        const selected = Array.from(selectedScreenshots.values());
        if (selected.length === 0) {
            toaster.toast({
                title: t("screenshot.noSelection"),
                body: t("screenshot.pleaseSelectScreenshots"),
            });
            return;
        }
        onSelectScreenshots(selected);
        closeModal();
    };
    const formatFileSize = (bytes) => {
        if (bytes < 1024)
            return `${bytes} B`;
        if (bytes < 1024 * 1024)
            return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };
    const currentScreenshots = screenshots;
    const goToNextPage = () => {
        if (currentPage < totalPages) {
            loadScreenshots(currentPage + 1);
        }
    };
    const goToPrevPage = () => {
        if (currentPage > 1) {
            loadScreenshots(currentPage - 1);
        }
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: closeModal, children: [SP_JSX.jsx("style", { children: `
          .screenshot-item.gpfocus {
            box-shadow: 0 0 0 3px #1a9fff !important;
            outline: none !important;
          }
        ` }), SP_JSX.jsxs(DFL.Focusable, { style: {
                    padding: "20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "15px"
                }, children: [SP_JSX.jsx("h2", { style: { margin: 0 }, children: t("screenshot.gallery") }), loading ? (SP_JSX.jsx("div", { style: { textAlign: "center", padding: "20px" }, children: t("screenshot.loading") })) : screenshots.length === 0 ? (SP_JSX.jsx("div", { style: { textAlign: "center", padding: "20px" }, children: t("screenshot.noScreenshots") })) : (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsxs("div", { style: {
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    padding: "10px 0",
                                    flexWrap: "wrap",
                                    gap: "10px"
                                }, children: [SP_JSX.jsx(DFL.ToggleField, { label: t("screenshot.selectAll"), checked: selectAll, onChange: toggleSelectAll }), SP_JSX.jsxs("div", { style: { display: "flex", gap: "15px", alignItems: "center" }, children: [SP_JSX.jsxs("span", { style: { fontSize: "14px", opacity: 0.8 }, children: [t("screenshot.page"), ": ", currentPage, " / ", totalPages] }), SP_JSX.jsxs("span", { style: { fontSize: "14px", opacity: 0.8 }, children: [t("screenshot.selected"), ": ", selectedScreenshots.size, " / ", total] })] })] }), SP_JSX.jsx(DFL.Focusable, { "flow-children": "horizontal", style: {
                                    flex: 1,
                                    overflowY: "auto",
                                    display: "grid",
                                    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                                    gap: "15px",
                                }, children: currentScreenshots.map((screenshot) => (SP_JSX.jsxs(DFL.Focusable, { onActivate: () => toggleScreenshot(screenshot.path), onClick: () => toggleScreenshot(screenshot.path), className: "screenshot-item", style: {
                                        border: selectedScreenshots.has(screenshot.path)
                                            ? "3px solid #4CAF50"
                                            : "1px solid #666",
                                        borderRadius: "8px",
                                        overflow: "hidden",
                                        cursor: "pointer",
                                        backgroundColor: "#1a1a1a",
                                        transition: "all 0.2s",
                                        outline: "none"
                                    }, children: [SP_JSX.jsxs("div", { style: {
                                                position: "relative",
                                                paddingTop: "56.25%",
                                                backgroundColor: "#000"
                                            }, children: [imageBlobUrls.has(screenshot.path) ? (SP_JSX.jsx("img", { src: imageBlobUrls.get(screenshot.path), alt: screenshot.filename, style: {
                                                        position: "absolute",
                                                        top: 0,
                                                        left: 0,
                                                        width: "100%",
                                                        height: "100%",
                                                        objectFit: "contain"
                                                    } })) : (SP_JSX.jsx("div", { style: {
                                                        position: "absolute",
                                                        top: 0,
                                                        left: 0,
                                                        width: "100%",
                                                        height: "100%",
                                                        display: "flex",
                                                        alignItems: "center",
                                                        justifyContent: "center",
                                                        color: "#666"
                                                    }, children: t("screenshot.loading") })), selectedScreenshots.has(screenshot.path) && (SP_JSX.jsx("div", { style: {
                                                        position: "absolute",
                                                        top: "5px",
                                                        right: "5px",
                                                        backgroundColor: "#4CAF50",
                                                        borderRadius: "50%",
                                                        width: "24px",
                                                        height: "24px",
                                                        display: "flex",
                                                        alignItems: "center",
                                                        justifyContent: "center",
                                                        color: "white",
                                                        fontWeight: "bold"
                                                    }, children: "\u2713" }))] }), SP_JSX.jsxs("div", { style: { padding: "10px" }, children: [SP_JSX.jsx("div", { style: {
                                                        fontSize: "12px",
                                                        overflow: "hidden",
                                                        textOverflow: "ellipsis",
                                                        whiteSpace: "nowrap",
                                                        marginBottom: "5px"
                                                    }, children: screenshot.filename }), SP_JSX.jsx("div", { style: {
                                                        fontSize: "10px",
                                                        opacity: 0.7,
                                                        display: "flex",
                                                        justifyContent: "space-between"
                                                    }, children: SP_JSX.jsx("span", { children: formatFileSize(screenshot.size) }) }), SP_JSX.jsx("div", { style: { fontSize: "10px", opacity: 0.7 }, children: screenshot.mtime_str })] })] }, screenshot.path))) }), SP_JSX.jsxs(DFL.Focusable, { style: {
                                    display: "flex",
                                    gap: "8px",
                                    justifyContent: "space-between",
                                    paddingTop: "10px",
                                    borderTop: "1px solid #333"
                                }, children: [SP_JSX.jsxs("div", { style: { display: "flex", gap: "8px" }, children: [SP_JSX.jsx(DFL.DialogButton, { style: { minWidth: "60px", padding: "8px 12px", fontSize: "13px" }, onClick: goToPrevPage, disabled: currentPage === 1, children: t("screenshot.prevPage") }), SP_JSX.jsx(DFL.DialogButton, { style: { minWidth: "60px", padding: "8px 12px", fontSize: "13px" }, onClick: goToNextPage, disabled: currentPage === totalPages, children: t("screenshot.nextPage") })] }), SP_JSX.jsxs("div", { style: { display: "flex", gap: "8px" }, children: [SP_JSX.jsx(DFL.DialogButton, { style: { minWidth: "50px", padding: "8px 12px", fontSize: "13px" }, onClick: () => loadScreenshots(currentPage, true), children: t("screenshot.refresh") }), SP_JSX.jsx(DFL.DialogButton, { style: { minWidth: "50px", padding: "8px 12px", fontSize: "13px" }, onClick: closeModal, children: t("common.cancel") }), SP_JSX.jsxs(DFL.DialogButton, { style: { minWidth: "80px", padding: "8px 12px", fontSize: "13px" }, onClick: handleConfirm, disabled: selectedScreenshots.size === 0, children: [t("screenshot.addToQueue"), " (", selectedScreenshots.size, ")"] })] })] })] }))] })] }));
};

const createBackendHandlers = (setBackend) => {
    const handleToggleBackend = async (enabled) => {
        if (enabled) {
            const status = await startBackend();
            setBackend(status);
            if (!status.running) {
                toaster.toast({
                    title: "Failed to start",
                    body: status.error ?? "Unknown error",
                });
            }
        }
        else {
            const status = await stopBackend();
            setBackend(status);
        }
    };
    return { handleToggleBackend };
};

const createDeviceHandlers = (backend, setDevices, setRefreshLoading, setScanLoading, selectedDevice, setSelectedDevice) => {
    // Helper function to update device list
    const updateDeviceList = (newDevices) => {
        setDevices(newDevices);
        if (selectedDevice) {
            const stillExists = newDevices.some((d) => d.fingerprint === selectedDevice.fingerprint);
            if (stillExists) {
                const updatedDevice = newDevices.find((d) => d.fingerprint === selectedDevice.fingerprint);
                setSelectedDevice(updatedDevice ?? null);
            }
        }
    };
    // Refresh device list - gets current cached devices (scan-current)
    const handleRefreshDevices = async () => {
        if (!backend.running) {
            toaster.toast({
                title: t("toast.backendNotRunning"),
                body: t("toast.backendNotRunningBody"),
            });
            return;
        }
        setRefreshLoading(true);
        try {
            const result = await proxyGet("/api/self/v1/scan-current");
            if (result.status !== 200) {
                throw new Error(`Refresh failed: ${result.status}`);
            }
            const newDevices = result.data?.data ?? [];
            updateDeviceList(newDevices);
        }
        catch (error) {
            toaster.toast({
                title: "Refresh failed",
                body: `${error}`,
            });
        }
        finally {
            setRefreshLoading(false);
        }
    };
    // Trigger immediate scan (scan-now)
    const handleScanNow = async () => {
        if (!backend.running) {
            toaster.toast({
                title: t("toast.backendNotRunning"),
                body: t("toast.backendNotRunningBody"),
            });
            return;
        }
        setScanLoading(true);
        // Clear current devices before scanning
        setDevices([]);
        setSelectedDevice(null);
        try {
            const result = await proxyGet("/api/self/v1/scan-now");
            if (result.status !== 200) {
                throw new Error(`Scan failed: ${result.status}`);
            }
            const newDevices = result.data?.data ?? [];
            updateDeviceList(newDevices);
        }
        catch (error) {
            toaster.toast({
                title: "Scan failed",
                body: `${error}`,
            });
        }
        finally {
            setScanLoading(false);
        }
    };
    // Legacy handleScan - now calls scan-now for immediate scan
    const handleScan = handleScanNow;
    return { handleScan, handleRefreshDevices, handleScanNow };
};

// Simplified from https://github.com/SteamGridDB/decky-steamgriddb/blob/main/src/utils/openFilePicker.tsx
var fileOpener = (startPath, includeFiles, filter, filePickerSettings, usingFolder = false) => {
    return new Promise((resolve, reject) => {
        openFilePicker(usingFolder ? 1 /* FileSelectionType.FOLDER */ : 0 /* FileSelectionType.FILE */, startPath, includeFiles, true, filter, filePickerSettings?.validFileExtensions, filePickerSettings?.defaultHidden, false).then(resolve, () => reject('User Canceled'));
    });
};

const createFileHandlers = (addFile, uploading) => {
    const handleFileSelect = async () => {
        if (uploading)
            return;
        try {
            const result = await openFilePicker(0 /* FileSelectionType.FILE */, "/home/deck");
            const realpath = result.realpath ?? result.path;
            const fileName = result.path.split("/").pop() || "unknown";
            const newFile = {
                id: `file-${Date.now()}-${Math.random().toString(16).slice(2)}`,
                fileName,
                sourcePath: realpath,
            };
            addFile(newFile);
            toaster.toast({
                title: "File selected",
                body: result.path,
            });
        }
        catch (error) {
            toaster.toast({
                title: "Failed to select file",
                body: String(error),
            });
        }
    };
    const handleFolderSelect = async () => {
        if (uploading)
            return;
        try {
            const result = await fileOpener("/home/deck", false, undefined, undefined, true);
            // Get the real folder path
            const folderPath = result.realpath ?? result.path;
            const folderResult = await listFolderFiles(folderPath);
            if (!folderResult.success || folderResult.files.length === 0) {
                throw new Error(folderResult.error || "Folder is empty or inaccessible");
            }
            // Add folder as a single item
            const folderFile = {
                id: `folder-${Date.now()}-${Math.random().toString(16).slice(2)}`,
                fileName: folderResult.folderName || folderPath.split("/").pop() || "folder",
                sourcePath: folderPath,
                isFolder: true,
                folderPath: folderPath,
                fileCount: folderResult.count,
            };
            addFile(folderFile);
            toaster.toast({
                title: "Folder selected",
                body: `${folderResult.count} files from ${folderResult.folderName}`,
            });
        }
        catch (error) {
            toaster.toast({
                title: "Failed to select folder",
                body: String(error),
            });
        }
    };
    return { handleFileSelect, handleFolderSelect };
};

const PinPromptModal = ({ title = t("toast.pinRequired"), onSubmit, onCancel, closeModal, }) => {
    const [pin, setPin] = SP_REACT.useState("");
    const handleCancel = () => {
        closeModal?.();
        onCancel();
    };
    const handleSubmit = () => {
        const trimmed = pin.trim();
        if (!trimmed)
            return;
        closeModal?.();
        onSubmit(trimmed);
    };
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: handleCancel, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: title }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsx(DFL.Field, { label: "PIN", children: SP_JSX.jsx(DFL.TextField, { value: pin, onChange: (e) => setPin(e?.target?.value || ""), style: { width: "100%", minWidth: "200px" } }) }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: handleCancel, style: { marginTop: "10px" }, children: t("common.cancel") }), SP_JSX.jsx(DFL.DialogButtonPrimary, { onClick: handleSubmit, disabled: !pin.trim(), style: { marginTop: "10px" }, children: t("common.confirm") })] })] }));
};

const requestPin = (title) => {
    return new Promise((resolve) => {
        const modal = DFL.showModal(SP_JSX.jsx(PinPromptModal, { title: title, onSubmit: (pin) => {
                resolve(pin);
                modal.Close();
            }, onCancel: () => {
                resolve(null);
                modal.Close();
            }, closeModal: () => modal.Close() }));
    });
};

const SEND_FINISHED_SAFETY_TIMEOUT_MS = 15000;
const createUploadHandlers = (selectedDevice, selectedFiles, setUploading, setUploadProgress, clearFiles, setSendProgressStats, setCurrentUploadSessionId) => {
    // handleUpload now accepts an optional override device for quick send scenarios
    const handleUpload = async (overrideDevice) => {
        const targetDevice = overrideDevice || selectedDevice;
        if (!targetDevice) {
            toaster.toast({
                title: t("upload.noDeviceSelectedTitle"),
                body: t("upload.noDeviceSelectedMessage"),
            });
            return;
        }
        if (selectedFiles.length === 0) {
            toaster.toast({
                title: t("upload.noFilesSelectedTitle"),
                body: t("upload.noFilesSelectedMessage"),
            });
            return;
        }
        setUploading(true);
        // Result of upload-batch (used for error handling when not 200/207)
        let batchUploadResult;
        let batchWaitForSendFinished = false;
        let batchSessionIdForSafety;
        // Build progress display (folders show as single items)
        let progress = selectedFiles.map((f) => ({
            fileId: f.id,
            fileName: f.isFolder ? `📁 ${f.fileName} (${f.fileCount} ${t("upload.folderFiles")})` : f.fileName,
            status: 'pending',
        }));
        setUploadProgress(progress);
        try {
            // Separate items by type
            const textFiles = selectedFiles.filter((f) => f.textContent);
            const folderItems = selectedFiles.filter((f) => f.isFolder && f.folderPath);
            const regularFiles = selectedFiles.filter((f) => !f.textContent && !f.isFolder);
            // Build files map for non-folder files
            const filesMap = {};
            // Add regular files with fileUrl
            regularFiles.forEach((f) => {
                filesMap[f.id] = {
                    id: f.id,
                    fileUrl: `file://${f.sourcePath}`,
                };
            });
            // Add text files with size and type info
            textFiles.forEach((f) => {
                const textBytes = new TextEncoder().encode(f.textContent || "");
                filesMap[f.id] = {
                    id: f.id,
                    fileName: f.fileName ?? t("text.defaultFileName"),
                    size: textBytes.length,
                    fileType: "text/plain",
                };
            });
            // Determine if we're using folder upload mode
            const hasFolders = folderItems.length > 0;
            const folderPaths = hasFolders ? folderItems.map((f) => f.folderPath).filter(Boolean) : [];
            const hasExtraFiles = Object.keys(filesMap).length > 0;
            const prepareUpload = (pin) => {
                const pinParam = pin ? `?pin=${encodeURIComponent(pin)}` : "";
                if (hasFolders && folderPaths.length > 0) {
                    // Mixed mode: folder(s) + extra files
                    return proxyPost(`/api/self/v1/prepare-upload${pinParam}`, {
                        targetTo: targetDevice.fingerprint,
                        useFolderUpload: true,
                        folderPaths: folderPaths,
                        ...(hasExtraFiles && { files: filesMap }),
                    });
                }
                // Standard mode: only individual files
                return proxyPost(`/api/self/v1/prepare-upload${pinParam}`, {
                    targetTo: targetDevice.fingerprint,
                    files: filesMap,
                });
            };
            let prepareResult = await prepareUpload();
            if (prepareResult.status === 401) {
                const pin = await requestPin(t("toast.pinRequired"));
                if (!pin) {
                    throw new Error(t("upload.pinRequiredToContinue"));
                }
                prepareResult = await prepareUpload(pin);
            }
            if (prepareResult.status !== 200) {
                throw new Error(prepareResult.data?.error || `Prepare upload failed: ${prepareResult.status}`);
            }
            const { sessionId, files: tokens } = prepareResult.data.data;
            setSendProgressStats?.(Object.keys(tokens).length, 0);
            setCurrentUploadSessionId?.(sessionId);
            progress = progress.map((p) => ({ ...p, status: 'uploading' }));
            setUploadProgress(progress);
            // Upload text files individually (text content needs special handling)
            for (const textFile of textFiles) {
                try {
                    const textBytes = new TextEncoder().encode(textFile.textContent || "");
                    const uploadResult = await proxyPost(`/api/self/v1/upload?sessionId=${sessionId}&fileId=${textFile.id}&token=${tokens[textFile.id]}`, undefined, Array.from(textBytes));
                    if (uploadResult.status === 200) {
                        progress = progress.map((p) => p.fileId === textFile.id ? { ...p, status: 'done' } : p);
                    }
                    else {
                        progress = progress.map((p) => p.fileId === textFile.id
                            ? { ...p, status: 'error', error: uploadResult.data?.error || t("upload.failedTitle") }
                            : p);
                    }
                }
                catch (error) {
                    progress = progress.map((p) => p.fileId === textFile.id
                        ? { ...p, status: 'error', error: String(error) }
                        : p);
                }
                setUploadProgress([...progress]);
            }
            // Upload folders and regular files
            const hasFilesToUpload = hasFolders || regularFiles.length > 0;
            if (hasFilesToUpload) {
                if (hasFolders && folderPaths.length > 0) {
                    // Build extra files array for mixed upload
                    const extraFiles = regularFiles.map((fileInfo) => ({
                        fileId: fileInfo.id,
                        token: tokens[fileInfo.id] || "",
                        fileUrl: `file://${fileInfo.sourcePath}`,
                    }));
                    batchUploadResult = await proxyPost("/api/self/v1/upload-batch", {
                        sessionId: sessionId,
                        useFolderUpload: true,
                        folderPaths: folderPaths,
                        ...(extraFiles.length > 0 && { files: extraFiles }),
                    });
                }
                else {
                    // Standard batch upload with individual files only
                    const batchFiles = regularFiles.map((fileInfo) => ({
                        fileId: fileInfo.id,
                        token: tokens[fileInfo.id] || "",
                        fileUrl: `file://${fileInfo.sourcePath}`,
                    }));
                    batchUploadResult = await proxyPost("/api/self/v1/upload-batch", {
                        sessionId: sessionId,
                        files: batchFiles,
                    });
                }
                if (!batchUploadResult)
                    throw new Error("batch result missing");
                if (batchUploadResult.status === 200 || batchUploadResult.status === 207) {
                    // Success: let send_finished event handle cleanup and toast
                    batchWaitForSendFinished = true;
                    batchSessionIdForSafety = sessionId;
                }
                else {
                    // Error: clear state and show toast
                    const result = batchUploadResult.data?.result;
                    const success = result?.success ?? 0;
                    const failed = result?.failed ?? 0;
                    setUploadProgress([]);
                    setSendProgressStats?.(null, null);
                    setCurrentUploadSessionId?.(null);
                    if (failed > 0) {
                        toaster.toast({
                            title: t("upload.partialCompletedTitle"),
                            body: t("upload.partialCompletedBody")
                                .replace("{success}", String(success))
                                .replace("{failed}", String(failed)),
                        });
                    }
                    else {
                        toaster.toast({
                            title: t("upload.failedTitle"),
                            body: batchUploadResult.data?.error || t("upload.failedTitle"),
                        });
                    }
                }
            }
            if (!hasFilesToUpload || !batchWaitForSendFinished) {
                // Text-only or no batch: use UI progress for completion toast
                const allDone = progress.every((p) => p.status === 'done');
                const hasErrors = progress.some((p) => p.status === 'error');
                if (allDone) {
                    const doneCount = progress.filter((p) => p.status === 'done').length;
                    toaster.toast({
                        title: t("upload.uploadCompletedTitle"),
                        body: t("upload.uploadCompletedBody")
                            .replace("{count}", String(doneCount))
                            .replace("{files}", t("common.files")),
                    });
                    setSendProgressStats?.(null, null);
                    setCurrentUploadSessionId?.(null);
                    setUploadProgress([]);
                    clearFiles();
                }
                else if (hasErrors) {
                    const successCount = progress.filter((p) => p.status === 'done').length;
                    const failedCount = progress.filter((p) => p.status === 'error').length;
                    toaster.toast({
                        title: t("upload.partialCompletedTitle"),
                        body: t("upload.partialCompletedBody")
                            .replace("{success}", String(successCount))
                            .replace("{failed}", String(failedCount)),
                    });
                    setSendProgressStats?.(null, null);
                    setCurrentUploadSessionId?.(null);
                    setUploadProgress([]);
                }
            }
        }
        catch (error) {
            toaster.toast({
                title: t("upload.failedTitle"),
                body: String(error),
            });
            setSendProgressStats?.(null, null);
            setCurrentUploadSessionId?.(null);
            setUploadProgress([]);
        }
        finally {
            setUploading(false);
            if (batchWaitForSendFinished && batchSessionIdForSafety) {
                setTimeout(() => {
                    const state = useLocalSendStore.getState();
                    if (state.currentUploadSessionId === batchSessionIdForSafety) {
                        state.setUploadProgress([]);
                        state.setSendProgressStats(null, null);
                        state.setCurrentUploadSessionId(null);
                        toaster.toast({ title: t("sendProgress.sendCompleteToast"), body: "" });
                    }
                }, SEND_FINISHED_SAFETY_TIMEOUT_MS);
            }
        }
    };
    const handleClearFiles = () => {
        setSendProgressStats?.(null, null);
        clearFiles();
        setUploadProgress([]);
    };
    return { handleUpload, handleClearFiles };
};

/**
 * Create a share session for Download API (reverse file transfer).
 * Supports regular files, text content, and folders (folders are expanded to all internal files).
 */
async function createShareSession(files, pin, autoAccept = true) {
    const regularFiles = files.filter((f) => !f.textContent && !f.isFolder && f.sourcePath);
    const folderItems = files.filter((f) => f.isFolder && f.folderPath);
    const textFiles = files.filter((f) => f.textContent);
    if (regularFiles.length === 0 && folderItems.length === 0 && textFiles.length === 0) {
        throw new Error("No valid files to share.");
    }
    const filesMap = {};
    regularFiles.forEach((f, i) => {
        const fileId = f.id || `file${i}`;
        filesMap[fileId] = {
            id: fileId,
            fileName: f.fileName,
            fileUrl: f.sourcePath.startsWith("file://") ? f.sourcePath : `file://${f.sourcePath}`,
        };
    });
    folderItems.forEach((f, i) => {
        const fileId = f.id || `folder${i}`;
        const path = f.folderPath.startsWith("file://") ? f.folderPath : `file://${f.folderPath}`;
        filesMap[fileId] = {
            id: fileId,
            fileName: f.fileName,
            fileUrl: path,
        };
    });
    for (let i = 0; i < textFiles.length; i++) {
        const f = textFiles[i];
        const fileId = f.id || `text${i}`;
        const result = await writeTempTextFile(f.textContent || "", f.fileName || "text.txt");
        if (!result.success || !result.path) {
            throw new Error(result.error || "Failed to create temp file for text");
        }
        const textBytes = new TextEncoder().encode(f.textContent || "");
        filesMap[fileId] = {
            id: fileId,
            fileName: f.fileName || "text.txt",
            size: textBytes.length,
            fileType: "text/plain",
            fileUrl: result.path.startsWith("file://") ? result.path : `file://${result.path}`,
        };
    }
    const res = await proxyPost("/api/self/v1/create-share-session", {
        files: filesMap,
        pin: pin ?? "",
        autoAccept,
    });
    if (res.status !== 200) {
        throw new Error(res.data?.error || `Create share session failed: ${res.status}`);
    }
    const data = res.data?.data;
    if (!data?.sessionId || !data?.downloadUrl) {
        throw new Error("Invalid response from create-share-session");
    }
    return { sessionId: data.sessionId, downloadUrl: data.downloadUrl };
}
/**
 * Close a share session. The download link will no longer work.
 */
async function closeShareSession(sessionId) {
    const res = await proxyDelete(`/api/self/v1/close-share-session?sessionId=${encodeURIComponent(sessionId)}`);
    if (res.status !== 200) {
        throw new Error(res.data?.error || `Close share session failed: ${res.status}`);
    }
}
/**
 * Confirm or reject a download request (when autoAccept=false).
 * clientKey identifies the requesting device (e.g. IP) for per-device confirmation.
 */
async function confirmDownload(sessionId, clientKey, confirmed) {
    const res = await proxyGet(`/api/self/v1/confirm-download?sessionId=${encodeURIComponent(sessionId)}&clientKey=${encodeURIComponent(clientKey)}&confirmed=${confirmed}`);
    if (res.status !== 200) {
        throw new Error(res.data?.error || `Confirm download failed: ${res.status}`);
    }
}

// Helper: fetch favorites from API (no backendRunning check, always fetches)
const fetchFavoritesFromApi = async () => {
    try {
        const result = await proxyGet("/api/self/v1/favorites");
        if (result.status !== 200)
            return [];
        const body = result.data;
        return Array.isArray(body?.data) ? body.data : [];
    }
    catch (error) {
        console.error("Failed to fetch favorites:", error);
        return [];
    }
};
const createFavoritesHandlers = (backendRunning, setFavorites) => {
    // Fetch favorites list - GET /api/self/v1/favorites
    // When backend is not running, do NOT clear favorites (avoids clearing on re-enter before status is fetched).
    const fetchFavorites = async () => {
        if (!backendRunning) {
            return;
        }
        const list = await fetchFavoritesFromApi();
        setFavorites(list);
    };
    // Add device to favorites - POST /api/self/v1/favorites
    // Body: { fingerprint, alias }, backend returns FastReturnSuccess() => { status: "ok" }
    // Uses optimistic update + re-fetch to avoid closure issues
    const handleAddToFavorites = async (fingerprint, alias) => {
        try {
            const result = await proxyPost("/api/self/v1/favorites", {
                favorite_fingerprint: fingerprint,
                favorite_alias: alias,
            });
            if (result.status === 200) {
                toaster.toast({
                    title: t("config.favoritesAdded"),
                    body: alias || fingerprint,
                });
                // Directly fetch from API to avoid closure issue with backendRunning
                const list = await fetchFavoritesFromApi();
                setFavorites(list);
            }
            else {
                const errMsg = result.data?.error ?? "Failed to add favorite";
                throw new Error(errMsg);
            }
        }
        catch (error) {
            toaster.toast({
                title: t("common.error"),
                body: String(error),
            });
        }
    };
    // Remove device from favorites - DELETE /api/self/v1/favorites/:fingerprint
    // Backend returns FastReturnSuccess() => { status: "ok" }
    // Uses optimistic update + re-fetch to avoid closure issues
    const handleRemoveFromFavorites = async (fingerprint) => {
        try {
            const result = await proxyDelete(`/api/self/v1/favorites/${encodeURIComponent(fingerprint)}`);
            if (result.status === 200) {
                toaster.toast({
                    title: t("config.favoritesRemoved"),
                    body: "",
                });
                // Directly fetch from API to avoid closure issue with backendRunning
                const list = await fetchFavoritesFromApi();
                setFavorites(list);
            }
            else {
                const errMsg = result.data?.error ?? "Failed to remove favorite";
                throw new Error(errMsg);
            }
        }
        catch (error) {
            toaster.toast({
                title: t("common.error"),
                body: String(error),
            });
        }
    };
    return { fetchFavorites, handleAddToFavorites, handleRemoveFromFavorites };
};

// THIS FILE IS AUTO GENERATED
function FiGithub (props) {
  return GenIcon({"attr":{"viewBox":"0 0 24 24","fill":"none","stroke":"currentColor","strokeWidth":"2","strokeLinecap":"round","strokeLinejoin":"round"},"child":[{"tag":"path","attr":{"d":"M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"},"child":[]}]})(props);
}

const PROTOCOL_GITHUB_URL = "https://github.com/localsend/protocol";
const PLUGIN_GITHUB_URL = "https://github.com/MoYoez/Decky-Localsend";
const DEVELOPER_GITHUB_URL = "https://github.com/MoYoez";
const About = () => {
    return (SP_JSX.jsxs("div", { children: [SP_JSX.jsx("h2", { style: { fontWeight: "bold", fontSize: "1.5em", marginBottom: "0px" }, children: t("about.pluginTitle") }), SP_JSX.jsxs("span", { style: { marginBottom: "10px 10px" }, children: [t("about.pluginDesc"), SP_JSX.jsx("br", {})] }), SP_JSX.jsxs(DFL.PanelSectionRow, { children: [SP_JSX.jsx("span", { children: t("about.starOnGitHub") }), SP_JSX.jsx(DFL.ButtonItem, { icon: SP_JSX.jsx(FiGithub, { style: { display: "block" } }), label: t("about.pluginRepo"), onClick: () => {
                            DFL.Navigation.NavigateToExternalWeb(PLUGIN_GITHUB_URL);
                        }, children: t("about.githubRepo") })] }), SP_JSX.jsx("h3", { style: { fontWeight: "bold", fontSize: "1.5em", marginBottom: "0px" }, children: t("about.developer") }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { icon: SP_JSX.jsx(FaGithub, { style: { display: "block" } }), label: "MoeMagicMango", onClick: () => {
                        DFL.Navigation.NavigateToExternalWeb(DEVELOPER_GITHUB_URL);
                    }, children: t("about.githubProfile") }) }), SP_JSX.jsx("h2", { style: { fontWeight: "bold", fontSize: "1.5em", marginBottom: "5px" }, children: t("about.dependencies") }), SP_JSX.jsxs(DFL.PanelSectionRow, { children: [SP_JSX.jsx("span", { children: t("about.protocolDesc") }), SP_JSX.jsx(DFL.ButtonItem, { icon: SP_JSX.jsx(FiGithub, { style: { display: "block" } }), label: "localsend/protocol", onClick: () => {
                            DFL.Navigation.NavigateToExternalWeb(PROTOCOL_GITHUB_URL);
                        }, children: t("about.githubRepo") })] })] }));
};

// One hour in milliseconds
const ONE_HOUR_MS = 60 * 60 * 1000;
function getRemaining(session) {
    const elapsed = Date.now() - session.createdAt;
    return Math.max(0, ONE_HOUR_MS - elapsed);
}
const SharedViaLinkPage = () => {
    const shareLinkSessions = useLocalSendStore((state) => state.shareLinkSessions);
    const addShareLinkSession = useLocalSendStore((state) => state.addShareLinkSession);
    const removeShareLinkSession = useLocalSendStore((state) => state.removeShareLinkSession);
    const pendingShare = useLocalSendStore((state) => state.pendingShare);
    const setPendingShare = useLocalSendStore((state) => state.setPendingShare);
    // Backend status
    const [backendRunning, setBackendRunning] = SP_REACT.useState(false);
    // Create share settings
    const [sharePin, setSharePin] = SP_REACT.useState("");
    const [autoAccept, setAutoAccept] = SP_REACT.useState(true);
    const [creating, setCreating] = SP_REACT.useState(false);
    // QR code images loaded via proxyGet (sessionId -> data URL)
    const [qrCodeUrls, setQrCodeUrls] = SP_REACT.useState({});
    // Selected session for detail view; null = list view
    const [selectedSessionId, setSelectedSessionId] = SP_REACT.useState(null);
    // Clear selection when the selected session is removed (e.g. closed)
    SP_REACT.useEffect(() => {
        if (selectedSessionId &&
            !shareLinkSessions.some((s) => s.sessionId === selectedSessionId)) {
            setSelectedSessionId(null);
        }
    }, [selectedSessionId, shareLinkSessions]);
    // Tick every second to update remaining times and auto-remove expired sessions
    const [, setTick] = SP_REACT.useState(0);
    SP_REACT.useEffect(() => {
        const interval = setInterval(async () => {
            const sessions = useLocalSendStore.getState().shareLinkSessions;
            if (sessions.length === 0)
                return;
            const now = Date.now();
            for (const session of sessions) {
                const remaining = ONE_HOUR_MS - (now - session.createdAt);
                if (remaining <= 0) {
                    try {
                        await closeShareSession(session.sessionId);
                    }
                    catch {
                        // ignore
                    }
                    useLocalSendStore.getState().removeShareLinkSession(session.sessionId);
                    toaster.toast({ title: t("shareLink.expired"), body: "" });
                }
            }
            setTick((n) => n + 1);
        }, 1000);
        return () => clearInterval(interval);
    }, []);
    // Check backend status
    SP_REACT.useEffect(() => {
        getBackendStatus()
            .then((status) => {
            setBackendRunning(status.running);
        })
            .catch(() => {
            setBackendRunning(false);
        });
    }, []);
    const handleCopy = SP_REACT.useCallback(async (session) => {
        const ok = await copyToClipboard(session.downloadUrl);
        if (ok) {
            toaster.toast({ title: t("shareLink.copied"), body: "" });
        }
    }, []);
    const handleCloseSession = SP_REACT.useCallback(async (session) => {
        try {
            await closeShareSession(session.sessionId);
            removeShareLinkSession(session.sessionId);
            toaster.toast({ title: t("shareLink.shareEnded"), body: "" });
        }
        catch (error) {
            toaster.toast({ title: t("common.error"), body: String(error) });
        }
    }, [removeShareLinkSession]);
    // Create share with settings
    const handleStartShare = async () => {
        if (!pendingShare?.files || pendingShare.files.length === 0) {
            toaster.toast({ title: t("common.error"), body: t("shareLink.selectFiles") });
            return;
        }
        if (!backendRunning) {
            toaster.toast({ title: t("common.error"), body: t("shareLink.backendRequired") });
            return;
        }
        setCreating(true);
        try {
            const { sessionId, downloadUrl } = await createShareSession(pendingShare.files, sharePin || undefined, autoAccept);
            addShareLinkSession({
                sessionId,
                downloadUrl,
                createdAt: Date.now(),
                files: pendingShare.files,
            });
            setPendingShare(null);
            toaster.toast({ title: t("common.success"), body: "" });
        }
        catch (error) {
            toaster.toast({ title: t("common.error"), body: String(error) });
        }
        finally {
            setCreating(false);
        }
    };
    // Cancel creating share
    const handleCancelCreate = () => {
        setPendingShare(null);
        DFL.Navigation.NavigateBack();
    };
    // Edit PIN with modal
    const handleEditPin = () => {
        const modal = DFL.showModal(SP_JSX.jsx(BasicInputBoxModal, { title: t("shareLink.pinForShare"), label: t("shareLink.enterPin"), onSubmit: (value) => {
                setSharePin(value);
                modal.Close();
            }, onCancel: () => modal.Close(), closeModal: () => modal.Close() }));
    };
    // Format remaining time
    const formatRemainingTime = (ms) => {
        if (ms <= 0)
            return t("shareLink.expired");
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        return `${minutes}:${seconds.toString().padStart(2, "0")} ${t("shareLink.minutes")}`;
    };
    // Load QR code via proxyGet for each session
    SP_REACT.useEffect(() => {
        if (!backendRunning || shareLinkSessions.length === 0)
            return;
        const loadQrCodes = async () => {
            const next = {};
            for (const session of shareLinkSessions) {
                if (qrCodeUrls[session.sessionId])
                    continue;
                try {
                    const path = `/api/self/v1/create-qr-code?size=200x200&data=${encodeURIComponent(session.downloadUrl)}`;
                    const result = await proxyGet(path);
                    if (result?.status === 200 && result?.data) {
                        next[session.sessionId] = `data:image/png;base64,${result.data}`;
                    }
                }
                catch {
                    // ignore
                }
            }
            if (Object.keys(next).length > 0) {
                setQrCodeUrls((prev) => ({ ...prev, ...next }));
            }
        };
        loadQrCodes();
    }, [backendRunning, shareLinkSessions, qrCodeUrls]);
    // Scrollable page container: standalone route has no SidebarNavigation, so we need our own scroll root.
    const scrollRootStyle = {
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
        height: "100%",
    };
    const scrollContentStyle = {
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        padding: "40px 16px",
        boxSizing: "border-box",
    };
    // Backend not running warning
    if (!backendRunning) {
        return (SP_JSX.jsx("div", { style: scrollRootStyle, children: SP_JSX.jsx("div", { style: scrollContentStyle, children: SP_JSX.jsx(DFL.PanelSection, { title: t("shareLink.title"), children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.backendRequired"), children: t("backend.stopped") }) }) }) }) }));
    }
    // Pending share - show create settings page
    if (pendingShare && pendingShare.files.length > 0) {
        return (SP_JSX.jsx("div", { style: scrollRootStyle, children: SP_JSX.jsxs("div", { style: scrollContentStyle, children: [SP_JSX.jsxs(DFL.PanelSection, { title: t("shareLink.createShareSettings"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.Field, { label: t("upload.selectedFiles"), children: [pendingShare.files.length, " ", t("common.files")] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { maxHeight: "120px", overflowY: "auto" }, children: pendingShare.files.map((file) => (SP_JSX.jsx("div", { style: {
                                            padding: "4px 0",
                                            fontSize: "12px",
                                            overflow: "hidden",
                                            textOverflow: "ellipsis",
                                            whiteSpace: "nowrap",
                                        }, children: file.isFolder
                                            ? `📁 ${file.fileName} (${file.fileCount} ${t("upload.folderFiles")})`
                                            : file.fileName }, file.id))) }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.securityConfig"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.pinForShare"), children: sharePin ? "******" : t("config.pinNotSet") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditPin, children: t("config.editPin") }) }), sharePin && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setSharePin(""), children: t("config.clearPin") }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("shareLink.autoAccept"), description: t("shareLink.autoAcceptDesc"), checked: autoAccept, onChange: setAutoAccept }) })] }), SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleStartShare, disabled: creating, children: creating ? "..." : t("shareLink.startShare") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleCancelCreate, children: t("shareLink.cancelCreate") }) })] })] }) }));
    }
    // No active share: show hint text (createFromMain as description), keep Cancel button
    if (shareLinkSessions.length === 0) {
        return (SP_JSX.jsx("div", { style: scrollRootStyle, children: SP_JSX.jsx("div", { style: scrollContentStyle, children: SP_JSX.jsxs(DFL.PanelSection, { title: t("shareLink.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.noActiveShare"), children: t("shareLink.createFromMain") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => DFL.Navigation.NavigateBack(), children: t("common.cancel") }) })] }) }) }));
    }
    // Detail view: single session (selectedSessionId set)
    const selectedSession = selectedSessionId
        ? shareLinkSessions.find((s) => s.sessionId === selectedSessionId)
        : null;
    if (selectedSessionId && selectedSession) {
        const session = selectedSession;
        const remaining = getRemaining(session);
        const isHttps = session.downloadUrl.startsWith("https://");
        const files = session.files ?? [];
        return (SP_JSX.jsx("div", { style: scrollRootStyle, children: SP_JSX.jsxs("div", { style: scrollContentStyle, children: [SP_JSX.jsx(DFL.PanelSection, { title: t("shareLink.title"), children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setSelectedSessionId(null), children: t("shareLink.backToList") }) }) }), SP_JSX.jsxs(DFL.PanelSection, { title: `${t("shareLink.sessionId")}: ${session.sessionId.toLowerCase()}`, children: [isHttps && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { marginBottom: "6px", fontSize: "11px", color: "#f0b429" }, children: t("shareLink.httpsCertHint") }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.Link"), children: session.downloadUrl.replace(/\/\?.*$/, "").replace(/\/$/, "") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.sessionId"), children: session.sessionId }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("shareLink.expiresIn"), children: SP_JSX.jsx("span", { style: { color: remaining < 5 * 60 * 1000 ? "#ff6b6b" : "#4ade80" }, children: formatRemainingTime(remaining) }) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.Focusable, { style: {
                                        padding: "6px 8px",
                                        backgroundColor: "rgba(0,0,0,0.3)",
                                        borderRadius: "6px",
                                        fontSize: "10px",
                                        wordBreak: "break-all",
                                        marginBottom: "8px",
                                    }, children: [t("shareLink.orVisitDirect"), ": ", session.downloadUrl] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { textAlign: "center", marginBottom: "8px" }, children: [SP_JSX.jsx("div", { style: { fontSize: "11px", marginBottom: "4px", color: "#b8b6b4" }, children: t("shareLink.qrCode") }), SP_JSX.jsx("img", { src: qrCodeUrls[session.sessionId] ?? "", alt: "QR Code", style: {
                                                width: "160px",
                                                height: "160px",
                                                backgroundColor: "#fff",
                                                borderRadius: "6px",
                                                padding: "6px",
                                            } })] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleCopy(session), children: t("shareLink.copyLink") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleCloseSession(session), children: t("shareLink.closeShare") }) })] }), files.length > 0 && (SP_JSX.jsx(DFL.PanelSection, { title: t("shareLink.filesInShare"), children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { maxHeight: "150px", overflowY: "auto" }, children: files.map((file) => (SP_JSX.jsx("div", { style: {
                                        padding: "4px 0",
                                        fontSize: "12px",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                    }, children: file.isFolder
                                        ? `📁 ${file.fileName} (${file.fileCount ?? 0} ${t("upload.folderFiles")})`
                                        : file.fileName }, file.id))) }) }) })), SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setSelectedSessionId(null), children: t("shareLink.backToList") }) }) })] }) }));
    }
    // List view: show all active sessions; click to open detail
    return (SP_JSX.jsx("div", { style: scrollRootStyle, children: SP_JSX.jsxs("div", { style: scrollContentStyle, children: [SP_JSX.jsxs(DFL.PanelSection, { title: t("shareLink.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { marginBottom: "8px", fontSize: "12px", color: "#b8b6b4" }, children: t("shareLink.accessHint") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { marginBottom: "8px", fontSize: "12px", color: "#b8b6b4" }, children: t("shareLink.httpHint") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { marginBottom: "8px", fontSize: "12px", color: "#b8b6b4" }, children: t("shareLink.sameNetworkHint") }) })] }), SP_JSX.jsx(DFL.PanelSection, { title: t("shareLink.title"), children: shareLinkSessions.map((session) => {
                        const remaining = getRemaining(session);
                        const fileCount = session.files?.length ?? 0;
                        return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setSelectedSessionId(session.sessionId), children: SP_JSX.jsxs("span", { style: { fontSize: "13px" }, children: [session.sessionId.toLowerCase().slice(0, 8), "\u2026 \u00B7 ", formatRemainingTime(remaining), fileCount > 0 && ` · ${fileCount} ${t("common.files")}`] }) }) }, session.sessionId));
                    }) })] }) }));
};

const NetworkInterfaceSelectModal = ({ options, currentValue, onSelect, closeModal, }) => {
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: closeModal, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: t("config.networkInterface") }), SP_JSX.jsxs(DFL.DialogBody, { children: [SP_JSX.jsx("div", { style: { fontSize: "14px", color: "#b8b6b4", marginBottom: "12px" }, children: t("config.networkInterfaceDesc") }), SP_JSX.jsx(DFL.Focusable, { style: { display: "flex", flexDirection: "column", gap: "8px" }, children: options.map((option) => (SP_JSX.jsx(DFL.DialogButton, { onClick: () => onSelect(option.value), style: {
                                backgroundColor: currentValue === option.value ? "#1a9fff" : undefined,
                            }, children: option.label }, option.value))) })] })] }));
};

const FavoritesAddModal = ({ devices, favorites, onAdd, closeModal, }) => {
    // Filter out already favorited devices
    const availableDevices = devices.filter((d) => d.fingerprint && !favorites.some((f) => f.favorite_fingerprint === d.fingerprint));
    return (SP_JSX.jsxs(DFL.ModalRoot, { onCancel: closeModal, closeModal: closeModal, children: [SP_JSX.jsx(DFL.DialogHeader, { children: t("config.favoritesAdd") }), SP_JSX.jsx(DFL.DialogBody, { children: availableDevices.length === 0 ? (SP_JSX.jsx("div", { style: { fontSize: "14px", color: "#b8b6b4" }, children: t("backend.noDevices") })) : (SP_JSX.jsx(DFL.Focusable, { style: { display: "flex", flexDirection: "column", gap: "8px" }, children: availableDevices.map((device) => (SP_JSX.jsx(DFL.DialogButton, { onClick: () => onAdd(device.fingerprint, device.alias || ""), children: device.alias || device.ip_address || device.fingerprint }, device.fingerprint))) })) })] }));
};

// Main Config Page with SidebarNavigation
const ConfigPage = () => {
    const devices = useLocalSendStore((state) => state.devices);
    const setDevices = useLocalSendStore((state) => state.setDevices);
    // Backend running state
    const [backendRunning, setBackendRunning] = SP_REACT.useState(false);
    // Config states
    const [configAlias, setConfigAlias] = SP_REACT.useState("");
    const [downloadFolder, setDownloadFolder] = SP_REACT.useState("");
    const [skipNotify, setSkipNotify] = SP_REACT.useState(false);
    const [multicastAddress, setMulticastAddress] = SP_REACT.useState("");
    const [multicastPort, setMulticastPort] = SP_REACT.useState("");
    const [pin, setPin] = SP_REACT.useState("");
    const [autoSave, setAutoSave] = SP_REACT.useState(true);
    const [autoSaveFromFavorites, setAutoSaveFromFavorites] = SP_REACT.useState(false);
    const [useHttps, setUseHttps] = SP_REACT.useState(true);
    const [networkInterface, setNetworkInterface] = SP_REACT.useState("*");
    const [notifyOnDownload, setNotifyOnDownload] = SP_REACT.useState(false);
    const [saveReceiveHistory, setSaveReceiveHistory] = SP_REACT.useState(true);
    const [enableExperimental, setEnableExperimental] = SP_REACT.useState(false);
    const [useDownload, setUseDownload] = SP_REACT.useState(false);
    const [doNotMakeSessionFolder, setDoNotMakeSessionFolder] = SP_REACT.useState(false);
    const [disableInfoLogging, setDisableInfoLogging] = SP_REACT.useState(false);
    const [scanTimeout, setScanTimeout] = SP_REACT.useState("500");
    const favorites = useLocalSendStore((state) => state.favorites);
    const setFavorites = useLocalSendStore((state) => state.setFavorites);
    const [networkInterfaces, setNetworkInterfaces] = SP_REACT.useState([]);
    // Favorites handlers
    const { fetchFavorites, handleAddToFavorites, handleRemoveFromFavorites } = createFavoritesHandlers(backendRunning, setFavorites);
    // Fetch network interfaces
    const fetchNetworkInterfaces = async () => {
        if (!backendRunning)
            return;
        try {
            const result = await proxyGet("/api/self/v1/get-network-interfaces");
            if (result.status === 200 && result.data?.data) {
                const interfaces = result.data.data;
                const options = [
                    { label: t("config.networkInterfaceAll"), value: "*" },
                    ...interfaces.map((iface) => ({
                        label: `${iface.interface_name} (${iface.ip_address})`,
                        value: iface.interface_name,
                    })),
                ];
                setNetworkInterfaces(options);
            }
        }
        catch (error) {
            console.error("Failed to fetch network interfaces:", error);
        }
    };
    // Load config on mount - use getBackendStatus() (same as main page) to detect if backend is running
    SP_REACT.useEffect(() => {
        getBackendStatus()
            .then((status) => setBackendRunning(status.running))
            .catch(() => setBackendRunning(false));
        getBackendConfig()
            .then((result) => {
            setConfigAlias(result.alias ?? "");
            setDownloadFolder(result.download_folder ?? "");
            setSkipNotify(!!result.skip_notify);
            setMulticastAddress(result.multicast_address ?? "");
            setMulticastPort(result.multicast_port === 0 || result.multicast_port == null ? "" : String(result.multicast_port));
            setPin(result.pin ?? "");
            setAutoSave(!!result.auto_save);
            setAutoSaveFromFavorites(!!result.auto_save_from_favorites);
            setUseHttps(result.use_https !== false);
            setNetworkInterface(result.network_interface ?? "*");
            setNotifyOnDownload(!!result.notify_on_download);
            setSaveReceiveHistory(result.save_receive_history !== false);
            setEnableExperimental(!!result.enable_experimental);
            setUseDownload(!!result.use_download);
            setDoNotMakeSessionFolder(!!result.do_not_make_session_folder);
            setDisableInfoLogging(!!result.disable_info_logging);
            setScanTimeout(String(result.scan_timeout ?? 500));
        })
            .catch((error) => {
            toaster.toast({
                title: t("toast.failedGetBackendConfig"),
                body: `${error}`,
            });
        });
    }, []);
    // When backend becomes running, re-load full config so network_interface etc. stay in sync
    SP_REACT.useEffect(() => {
        if (backendRunning) {
            getBackendConfig()
                .then((result) => {
                setNetworkInterface(result.network_interface ?? "*");
                fetchFavorites();
                fetchNetworkInterfaces();
            })
                .catch(() => {
                fetchFavorites();
                fetchNetworkInterfaces();
            });
        }
        else {
            setNetworkInterfaces([]);
            setFavorites([]);
        }
    }, [backendRunning]);
    // Save config helper
    const saveConfig = async (updates) => {
        try {
            const result = await setBackendConfig({
                alias: updates.alias ?? configAlias,
                download_folder: updates.download_folder ?? downloadFolder,
                legacy_mode: false,
                use_mixed_scan: true,
                skip_notify: updates.skip_notify ?? skipNotify,
                multicast_address: updates.multicast_address ?? multicastAddress,
                multicast_port: updates.multicast_port ?? multicastPort,
                pin: updates.pin ?? pin,
                auto_save: updates.auto_save ?? autoSave,
                auto_save_from_favorites: updates.auto_save_from_favorites ?? autoSaveFromFavorites,
                use_https: updates.use_https ?? useHttps,
                network_interface: updates.network_interface ?? networkInterface,
                notify_on_download: updates.notify_on_download ?? notifyOnDownload,
                save_receive_history: updates.save_receive_history ?? saveReceiveHistory,
                enable_experimental: updates.enable_experimental ?? enableExperimental,
                use_download: updates.use_download ?? useDownload,
                do_not_make_session_folder: updates.do_not_make_session_folder ?? doNotMakeSessionFolder,
                disable_info_logging: updates.disable_info_logging ?? disableInfoLogging,
                scan_timeout: updates.scan_timeout ?? (parseInt(scanTimeout) || 500),
            });
            if (result.success) {
                toaster.toast({
                    title: result.restarted ? t("config.restartToTakeEffect") : t("config.configSaved"),
                    body: t("config.configUpdated"),
                });
            }
        }
        catch (error) {
            toaster.toast({
                title: t("common.error"),
                body: `${error}`,
            });
        }
    };
    // Helper for input modal
    const openInputModal = (title, label) => new Promise((resolve) => {
        const modal = DFL.showModal(SP_JSX.jsx(BasicInputBoxModal, { title: title, label: label, onSubmit: (value) => {
                resolve(value);
                modal.Close();
            }, onCancel: () => {
                resolve(null);
                modal.Close();
            }, closeModal: () => modal.Close() }));
    });
    // Handler functions
    const handleEditAlias = async () => {
        const value = await openInputModal(t("config.editAlias"), t("modal.enterAlias"));
        if (value !== null) {
            setConfigAlias(value);
            saveConfig({ alias: value });
        }
    };
    const handleEditDownloadFolder = async () => {
        const value = await openInputModal(t("config.editDownloadFolder"), t("modal.enterDownloadFolder"));
        if (value !== null) {
            setDownloadFolder(value);
            saveConfig({ download_folder: value });
        }
    };
    const handleChooseDownloadFolder = async () => {
        try {
            const result = await openFilePicker(1 /* FileSelectionType.FOLDER */, "/home/deck");
            const folder = result.realpath ?? result.path;
            if (folder) {
                setDownloadFolder(folder);
                saveConfig({ download_folder: folder });
                toaster.toast({ title: t("config.downloadFolder"), body: folder });
            }
        }
        catch (error) {
            toaster.toast({ title: t("toast.failedSelectFolder"), body: `${error}` });
        }
    };
    const handleEditMulticastAddress = async () => {
        const value = await openInputModal(t("config.editMulticastAddress"), t("modal.enterMulticastAddress"));
        if (value !== null) {
            setMulticastAddress(value);
            saveConfig({ multicast_address: value });
        }
    };
    const handleEditMulticastPort = async () => {
        const value = await openInputModal(t("config.editMulticastPort"), t("modal.enterMulticastPort"));
        if (value !== null) {
            setMulticastPort(value);
            saveConfig({ multicast_port: value });
        }
    };
    const handleEditScanTimeout = async () => {
        const value = await openInputModal(t("config.editScanTimeout"), t("modal.enterScanTimeout"));
        if (value !== null) {
            setScanTimeout(value);
            saveConfig({ scan_timeout: parseInt(value) || 500 });
        }
    };
    const handleSelectNetworkInterface = () => {
        const modal = DFL.showModal(SP_JSX.jsx(NetworkInterfaceSelectModal, { options: networkInterfaces, currentValue: networkInterface, onSelect: (value) => {
                setNetworkInterface(value);
                saveConfig({ network_interface: value });
                modal.Close();
            }, closeModal: () => modal.Close() }));
    };
    const handleEditPin = async () => {
        const value = await openInputModal(t("config.editPin"), t("modal.enterPin"));
        if (value !== null) {
            setPin(value);
            saveConfig({ pin: value });
        }
    };
    const handleClearPin = () => {
        DFL.showModal(SP_JSX.jsx(ConfirmModal, { title: t("config.clearPinTitle"), message: t("config.clearPinMessage"), onConfirm: () => {
                setPin("");
                saveConfig({ pin: "" });
            } }));
    };
    const handleFactoryReset = () => {
        DFL.showModal(SP_JSX.jsx(ConfirmModal, { title: t("settings.resetAllData"), message: t("settings.resetAllDataConfirm"), onConfirm: async () => {
                try {
                    const result = await factoryReset();
                    if (result.success) {
                        setConfigAlias("");
                        setDownloadFolder("");
                        setSkipNotify(false);
                        setMulticastAddress("");
                        setMulticastPort("");
                        setPin("");
                        setAutoSave(true);
                        setAutoSaveFromFavorites(false);
                        setUseHttps(true);
                        setNetworkInterface("*");
                        setNotifyOnDownload(false);
                        setSaveReceiveHistory(true);
                        setEnableExperimental(false);
                        setUseDownload(false);
                        setDisableInfoLogging(false);
                        setScanTimeout("500");
                        toaster.toast({
                            title: t("settings.resetSuccess"),
                            body: t("settings.resetSuccessDesc"),
                        });
                    }
                }
                catch (error) {
                    toaster.toast({ title: t("common.error"), body: `${error}` });
                }
            } }));
    };
    // Settings Page Component (all config in one page)
    const SettingsPage = () => (SP_JSX.jsxs("div", { style: { padding: "16px" }, children: [SP_JSX.jsxs(DFL.PanelSection, { title: t("config.basicConfig"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.alias"), children: configAlias || t("config.default") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditAlias, children: t("config.editAlias") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.downloadFolder"), children: downloadFolder || t("config.default") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditDownloadFolder, children: t("config.editDownloadFolder") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleChooseDownloadFolder, children: t("config.chooseDownloadFolder") }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.autoSave"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.autoSave"), description: t("config.autoSaveDesc"), checked: autoSave, onChange: (checked) => {
                                setAutoSave(checked);
                                if (checked && autoSaveFromFavorites) {
                                    setAutoSaveFromFavorites(false);
                                    saveConfig({ auto_save: true, auto_save_from_favorites: false });
                                }
                                else {
                                    saveConfig({ auto_save: checked });
                                }
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.autoSaveFromFavorites"), description: t("config.autoSaveFromFavoritesDesc"), checked: autoSaveFromFavorites, onChange: (checked) => {
                                setAutoSaveFromFavorites(checked);
                                if (checked && autoSave) {
                                    setAutoSave(false);
                                    saveConfig({ auto_save: false, auto_save_from_favorites: true });
                                }
                                else {
                                    saveConfig({ auto_save_from_favorites: checked });
                                }
                            } }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.favorites"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.Field, { label: t("config.favorites"), children: [favorites.length, " ", t("common.devices")] }) }), favorites.length > 0 && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { maxHeight: "150px", overflowY: "auto" }, children: favorites.map((fav) => (SP_JSX.jsxs("div", { style: {
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    padding: "6px 0",
                                    fontSize: "13px",
                                }, children: [SP_JSX.jsx("span", { style: { flex: 1, overflow: "hidden", textOverflow: "ellipsis" }, children: fav.favorite_alias || fav.favorite_fingerprint.substring(0, 16) + "..." }), SP_JSX.jsx("button", { onClick: () => {
                                            const confirmModal = DFL.showModal(SP_JSX.jsx(ConfirmModal, { title: t("config.favoritesRemove"), message: t("config.removeFavoriteConfirm"), confirmText: t("config.favoritesRemove"), onConfirm: () => {
                                                    handleRemoveFromFavorites(fav.favorite_fingerprint);
                                                    confirmModal.Close();
                                                }, closeModal: () => confirmModal.Close() }));
                                        }, style: {
                                            marginLeft: "8px",
                                            padding: "3px 6px",
                                            fontSize: "11px",
                                            backgroundColor: "#dc3545",
                                            color: "#fff",
                                            border: "none",
                                            borderRadius: "3px",
                                            cursor: "pointer",
                                        }, children: SP_JSX.jsx(FaTimes, { size: 10 }) })] }, fav.favorite_fingerprint))) }) })), favorites.length === 0 && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: "13px", color: "#888" }, children: t("config.favoritesEmpty") }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => fetchFavorites(), disabled: !backendRunning, children: t("config.refreshFavoritesDevices") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: async () => {
                                let devicesToShow = devices;
                                if (devices.length === 0 && backendRunning) {
                                    toaster.toast({ title: t("config.scanningDevices"), body: "" });
                                    await proxyGet("/api/self/v1/scan-now");
                                    const res = await proxyGet("/api/self/v1/scan-current");
                                    const list = res.status === 200 && res.data?.data ? res.data.data : [];
                                    setDevices(list);
                                    devicesToShow = list;
                                }
                                const modal = DFL.showModal(SP_JSX.jsx(FavoritesAddModal, { devices: devicesToShow, favorites: favorites, onAdd: async (fingerprint, alias) => {
                                        await handleAddToFavorites(fingerprint, alias);
                                        modal.Close();
                                    }, closeModal: () => modal.Close() }));
                            }, disabled: !backendRunning, children: t("config.favoritesAdd") }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.networkConfig"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.multicastAddress"), children: multicastAddress || t("config.default") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditMulticastAddress, children: t("config.editMulticastAddress") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.multicastPort"), children: !multicastPort || multicastPort === "0" ? t("config.default") : multicastPort }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditMulticastPort, children: t("config.editMulticastPort") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.Field, { label: t("config.scanTimeout"), children: [scanTimeout || "500", "s"] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditScanTimeout, children: t("config.editScanTimeout") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.networkInterface"), children: networkInterface === "*" ? t("config.networkInterfaceAll") : networkInterface }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleSelectNetworkInterface, disabled: !backendRunning, children: t("config.networkInterface") }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.securityConfig"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.skipNotify"), description: t("config.skipNotifyDesc"), checked: skipNotify, onChange: (checked) => {
                                setSkipNotify(checked);
                                saveConfig({ skip_notify: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("config.pin"), children: pin ? t("config.pinConfigured") : t("config.pinNotSet") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditPin, children: t("config.editPin") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleClearPin, disabled: !pin, children: t("config.clearPin") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.useHttps"), description: t("config.useHttpsDesc"), checked: useHttps, onChange: (checked) => {
                                setUseHttps(checked);
                                saveConfig({ use_https: checked });
                            } }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("config.advancedConfig"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.notifyOnDownload"), description: t("config.notifyOnDownloadDesc"), checked: notifyOnDownload, onChange: (checked) => {
                                setNotifyOnDownload(checked);
                                saveConfig({ notify_on_download: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.useDownload"), description: t("config.useDownloadDesc"), checked: useDownload, onChange: (checked) => {
                                setUseDownload(checked);
                                saveConfig({ use_download: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.doNotMakeSessionFolder"), description: t("config.doNotMakeSessionFolderDesc"), checked: doNotMakeSessionFolder, onChange: (checked) => {
                                setDoNotMakeSessionFolder(checked);
                                saveConfig({ do_not_make_session_folder: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.saveReceiveHistory"), description: t("config.saveReceiveHistoryDesc"), checked: saveReceiveHistory, onChange: (checked) => {
                                setSaveReceiveHistory(checked);
                                saveConfig({ save_receive_history: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("config.disableInfoLogging"), description: t("config.disableInfoLoggingDesc"), checked: disableInfoLogging, onChange: (checked) => {
                                setDisableInfoLogging(checked);
                                saveConfig({ disable_info_logging: checked });
                            } }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleFactoryReset, children: t("settings.resetAllData") }) })] })] }));
    return (SP_JSX.jsx(DFL.SidebarNavigation, { title: "Decky Localsend", showTitle: true, pages: [
            {
                title: t("config.title"),
                content: SP_JSX.jsx(SettingsPage, {}),
                route: "/decky-localsend-config/settings",
            },
            {
                title: t("about.title"),
                content: SP_JSX.jsx(About, {}),
                route: "/decky-localsend-config/about",
            },
        ] }));
};

// THIS FILE IS AUTO GENERATED
function LuSendToBack (props) {
  return GenIcon({"attr":{"viewBox":"0 0 24 24","fill":"none","stroke":"currentColor","strokeWidth":"2","strokeLinecap":"round","strokeLinejoin":"round"},"child":[{"tag":"rect","attr":{"x":"14","y":"14","width":"8","height":"8","rx":"2"},"child":[]},{"tag":"rect","attr":{"x":"2","y":"2","width":"8","height":"8","rx":"2"},"child":[]},{"tag":"path","attr":{"d":"M7 14v1a2 2 0 0 0 2 2h1"},"child":[]},{"tag":"path","attr":{"d":"M14 7h1a2 2 0 0 1 2 2v1"},"child":[]}]})(props);
}

let selfCancelledSessionId = null;
function Content() {
    const devices = useLocalSendStore((state) => state.devices);
    const setDevices = useLocalSendStore((state) => state.setDevices);
    const selectedDevice = useLocalSendStore((state) => state.selectedDevice);
    const setSelectedDevice = useLocalSendStore((state) => state.setSelectedDevice);
    const selectedFiles = useLocalSendStore((state) => state.selectedFiles);
    const addFile = useLocalSendStore((state) => state.addFile);
    const removeFile = useLocalSendStore((state) => state.removeFile);
    const clearFiles = useLocalSendStore((state) => state.clearFiles);
    // Default config
    const [backend, setBackend] = SP_REACT.useState({
        running: false,
        url: "https://127.0.0.1:53317",
    });
    const [refreshLoading, setRefreshLoading] = SP_REACT.useState(false);
    const [scanLoading, setScanLoading] = SP_REACT.useState(false);
    const uploadProgress = useLocalSendStore((state) => state.uploadProgress);
    const setUploadProgress = useLocalSendStore((state) => state.setUploadProgress);
    const setSendProgressStats = useLocalSendStore((state) => state.setSendProgressStats);
    const setCurrentUploadSessionId = useLocalSendStore((state) => state.setCurrentUploadSessionId);
    const [uploading, setUploading] = SP_REACT.useState(false);
    const [saveReceiveHistory, setSaveReceiveHistory] = SP_REACT.useState(true);
    const [networkInfo, setNetworkInfo] = SP_REACT.useState([]);
    const [useDownload, setUseDownload] = SP_REACT.useState(false);
    const [deviceAlias, setDeviceAlias] = SP_REACT.useState("");
    const [devicePort, setDevicePort] = SP_REACT.useState(53317);
    const favorites = useLocalSendStore((state) => state.favorites);
    const setFavorites = useLocalSendStore((state) => state.setFavorites);
    const receiveProgress = useLocalSendStore((state) => state.receiveProgress);
    // Fetch network info when backend is running
    const fetchNetworkInfo = async () => {
        if (!backend.running) {
            setNetworkInfo([]);
            return;
        }
        try {
            const result = await proxyGet("/api/self/v1/get-network-info");
            if (result.status === 200 && result.data?.data) {
                setNetworkInfo(result.data.data);
            }
        }
        catch (error) {
            console.error("Failed to fetch network info:", error);
        }
    };
    // Fetch device alias from backend info endpoint (GET /api/localsend/v2/info)
    const fetchDeviceInfo = async () => {
        if (!backend.running) {
            setDeviceAlias("");
            return;
        }
        try {
            const result = await proxyGet("/api/localsend/v2/info");
            if (result.status === 200 && result.data) {
                const alias = result.data.alias;
                setDeviceAlias(alias ?? "");
            }
        }
        catch (error) {
            console.error("Failed to fetch device info:", error);
        }
    };
    SP_REACT.useEffect(() => {
        getBackendStatus().then(setBackend).catch((error) => {
            toaster.toast({
                title: t("toast.failedGetBackendStatus"),
                body: `${error}`,
            });
        });
        getBackendConfig()
            .then((result) => {
            setSaveReceiveHistory(result.save_receive_history !== false);
            setUseDownload(!!result.use_download);
            setDevicePort(result.multicast_port || 53317);
        })
            .catch((error) => {
            toaster.toast({
                title: t("toast.failedLoadConfig"),
                body: `${error}`,
            });
        });
    }, []);
    // Fetch network info and device alias when backend status changes
    SP_REACT.useEffect(() => {
        fetchNetworkInfo();
        fetchDeviceInfo();
    }, [backend.running]);
    // Reload config: re-fetch backend config + device info (alias from info) + network info
    const handleReloadConfig = async () => {
        try {
            const result = await getBackendConfig();
            setSaveReceiveHistory(result.save_receive_history !== false);
            setUseDownload(!!result.use_download);
            setDevicePort(result.multicast_port || 53317);
            await fetchDeviceInfo();
            await fetchNetworkInfo();
            toaster.toast({
                title: t("config.configReloaded"),
                body: t("config.reloadConfigDesc"),
            });
        }
        catch (error) {
            toaster.toast({
                title: t("common.error"),
                body: `${error}`,
            });
        }
    };
    const { handleToggleBackend } = createBackendHandlers(setBackend);
    const { handleRefreshDevices, handleScanNow } = createDeviceHandlers(backend, setDevices, setRefreshLoading, setScanLoading, selectedDevice, setSelectedDevice);
    const { handleFileSelect, handleFolderSelect } = createFileHandlers(addFile, uploading);
    const { handleUpload, handleClearFiles } = createUploadHandlers(selectedDevice, selectedFiles, setUploading, setUploadProgress, clearFiles, setSendProgressStats, setCurrentUploadSessionId);
    const { fetchFavorites, handleAddToFavorites, handleRemoveFromFavorites } = createFavoritesHandlers(backend.running, setFavorites);
    // Only clear device list, favorites, and share link session when backend *transitions* from running to stopped.
    // Avoid clearing on initial mount (backend.running starts false) or when Content remounts (e.g. after closing favorite modal).
    const prevBackendRunningRef = SP_REACT.useRef(null);
    SP_REACT.useEffect(() => {
        const wasRunning = prevBackendRunningRef.current;
        prevBackendRunningRef.current = backend.running;
        if (wasRunning === true && !backend.running) {
            setDevices([]);
            setSelectedDevice(null);
            setFavorites([]);
            // Clear all share link sessions when backend stops
            clearShareLinkSessions();
        }
    }, [backend.running]);
    // Fetch favorites when backend status changes
    SP_REACT.useEffect(() => {
        fetchFavorites();
    }, [backend.running]);
    // Get online favorite devices (match by fingerprint with scanned devices)
    const getOnlineFavorites = () => {
        return favorites.map((fav) => {
            const onlineDevice = devices.find((d) => d.fingerprint === fav.favorite_fingerprint);
            return {
                ...fav,
                online: !!onlineDevice,
                device: onlineDevice,
            };
        });
    };
    // Handle quick send to a favorite device
    const handleQuickSendToFavorite = async (favoriteFingerprint) => {
        const onlineFav = getOnlineFavorites().find((f) => f.favorite_fingerprint === favoriteFingerprint && f.online && f.device);
        if (!onlineFav || !onlineFav.device) {
            toaster.toast({
                title: t("common.error"),
                body: t("upload.deviceOffline"),
            });
            return;
        }
        // Set selected device for UI display and directly pass device to upload
        setSelectedDevice(onlineFav.device);
        // Pass the device directly to handleUpload to avoid closure issues
        handleUpload(onlineFav.device);
    };
    const openInputModal = (title, label) => new Promise((resolve) => {
        const modal = DFL.showModal(SP_JSX.jsx(BasicInputBoxModal, { title: title, label: label, onSubmit: (value) => {
                resolve(value);
                modal.Close();
            }, onCancel: () => {
                resolve(null);
                modal.Close();
            }, closeModal: () => modal.Close() }));
    });
    const handleAddText = async () => {
        const value = await openInputModal(t("modal.sendText"), t("modal.enterTextContent"));
        if (value === null) {
            return;
        }
        const now = Date.now();
        addFile({
            id: `text-${now}-${Math.random().toString(16).slice(2)}`,
            fileName: `text-${now}.txt`,
            sourcePath: "",
            textContent: value,
        });
        toaster.toast({
            title: t("upload.textAdded"),
            body: t("upload.readyToSend"),
        });
    };
    // Handle manual send (FastSender mode)
    const handleManualSend = async () => {
        if (selectedFiles.length === 0) {
            toaster.toast({
                title: t("common.error"),
                body: t("upload.selectedFiles") + ": 0",
            });
            return;
        }
        const input = await openInputModal(t("upload.manualSend"), t("modal.enterIpOrSuffix"));
        if (!input) {
            return;
        }
        const trimmedInput = input.trim();
        // Check if it's a full IP address
        const isFullIp = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(trimmedInput);
        setUploading(true);
        // Build progress display
        let progress = selectedFiles.map((f) => ({
            fileId: f.id,
            fileName: f.isFolder ? `📁 ${f.fileName} (${f.fileCount} files)` : f.fileName,
            status: 'pending',
        }));
        setUploadProgress(progress);
        let batchWaitForSendFinished = false;
        let batchSessionIdForSafety;
        try {
            // Separate items by type
            const textFiles = selectedFiles.filter((f) => f.textContent);
            const folderItems = selectedFiles.filter((f) => f.isFolder && f.folderPath);
            const regularFiles = selectedFiles.filter((f) => !f.textContent && !f.isFolder);
            // Build files map for non-folder files
            const filesMap = {};
            regularFiles.forEach((f) => {
                filesMap[f.id] = {
                    id: f.id,
                    fileUrl: `file://${f.sourcePath}`,
                };
            });
            textFiles.forEach((f) => {
                const textBytes = new TextEncoder().encode(f.textContent || "");
                filesMap[f.id] = {
                    id: f.id,
                    fileName: f.fileName,
                    size: textBytes.length,
                    fileType: "text/plain",
                };
            });
            const hasFolders = folderItems.length > 0;
            const folderPaths = hasFolders ? folderItems.map((f) => f.folderPath).filter(Boolean) : [];
            const hasExtraFiles = Object.keys(filesMap).length > 0;
            // Build FastSender request
            const fastSenderParams = {
                useFastSender: true,
            };
            if (isFullIp) {
                fastSenderParams.useFastSenderIp = trimmedInput;
            }
            else {
                fastSenderParams.useFastSenderIPSuffex = trimmedInput;
            }
            const prepareUpload = (pin) => {
                const pinParam = pin ? `?pin=${encodeURIComponent(pin)}` : "";
                if (hasFolders && folderPaths.length > 0) {
                    return proxyPost(`/api/self/v1/prepare-upload${pinParam}`, {
                        ...fastSenderParams,
                        useFolderUpload: true,
                        folderPaths: folderPaths,
                        ...(hasExtraFiles && { files: filesMap }),
                    });
                }
                return proxyPost(`/api/self/v1/prepare-upload${pinParam}`, {
                    ...fastSenderParams,
                    files: filesMap,
                });
            };
            let prepareResult = await prepareUpload();
            if (prepareResult.status === 401) {
                toaster.toast({
                    title: t("toast.pinRequired"),
                    body: t("toast.pinRequiredForFiles"),
                });
                const pin = await requestPin(t("toast.pinRequired"));
                if (!pin) {
                    throw new Error(t("upload.pinRequiredToContinue"));
                }
                prepareResult = await prepareUpload(pin);
            }
            if (prepareResult.status !== 200) {
                throw new Error(prepareResult.data?.error || `Prepare upload failed: ${prepareResult.status}`);
            }
            const { sessionId, files: tokens } = prepareResult.data.data;
            setSendProgressStats(Object.keys(tokens).length, 0);
            setCurrentUploadSessionId(sessionId);
            progress = progress.map((p) => ({ ...p, status: 'uploading' }));
            setUploadProgress(progress);
            // Upload text files individually
            for (const textFile of textFiles) {
                try {
                    const textBytes = new TextEncoder().encode(textFile.textContent || "");
                    const uploadResult = await proxyPost(`/api/self/v1/upload?sessionId=${sessionId}&fileId=${textFile.id}&token=${tokens[textFile.id]}`, undefined, Array.from(textBytes));
                    if (uploadResult.status === 200) {
                        progress = progress.map((p) => p.fileId === textFile.id ? { ...p, status: 'done' } : p);
                    }
                    else {
                        progress = progress.map((p) => p.fileId === textFile.id
                            ? { ...p, status: 'error', error: uploadResult.data?.error || t("upload.failedTitle") }
                            : p);
                    }
                }
                catch (error) {
                    progress = progress.map((p) => p.fileId === textFile.id
                        ? { ...p, status: 'error', error: String(error) }
                        : p);
                }
                setUploadProgress([...progress]);
            }
            // Upload folders and regular files
            const hasFilesToUpload = hasFolders || regularFiles.length > 0;
            if (hasFilesToUpload) {
                let batchUploadResult;
                if (hasFolders && folderPaths.length > 0) {
                    const extraFiles = regularFiles.map((fileInfo) => ({
                        fileId: fileInfo.id,
                        token: tokens[fileInfo.id] || "",
                        fileUrl: `file://${fileInfo.sourcePath}`,
                    }));
                    batchUploadResult = await proxyPost("/api/self/v1/upload-batch", {
                        sessionId: sessionId,
                        useFolderUpload: true,
                        folderPaths: folderPaths,
                        ...(extraFiles.length > 0 && { files: extraFiles }),
                    });
                }
                else {
                    const batchFiles = regularFiles.map((fileInfo) => ({
                        fileId: fileInfo.id,
                        token: tokens[fileInfo.id] || "",
                        fileUrl: `file://${fileInfo.sourcePath}`,
                    }));
                    batchUploadResult = await proxyPost("/api/self/v1/upload-batch", {
                        sessionId: sessionId,
                        files: batchFiles,
                    });
                }
                if (batchUploadResult.status === 200 || batchUploadResult.status === 207) {
                    batchWaitForSendFinished = true;
                    batchSessionIdForSafety = sessionId;
                }
                else {
                    const result = batchUploadResult.data?.result;
                    const success = result?.success ?? 0;
                    const failed = result?.failed ?? 0;
                    setUploadProgress([]);
                    setSendProgressStats(null, null);
                    setCurrentUploadSessionId(null);
                    if (failed > 0) {
                        toaster.toast({
                            title: t("upload.partialCompletedTitle"),
                            body: t("upload.partialCompletedBody")
                                .replace("{success}", String(success))
                                .replace("{failed}", String(failed)),
                        });
                    }
                    else {
                        toaster.toast({
                            title: t("upload.failedTitle"),
                            body: batchUploadResult.data?.error || t("upload.failedTitle"),
                        });
                    }
                }
            }
            if (!hasFilesToUpload) {
                setUploadProgress(progress);
                const allDone = progress.every((p) => p.status === 'done');
                const hasErrors = progress.some((p) => p.status === 'error');
                if (allDone) {
                    toaster.toast({
                        title: t("common.success"),
                        body: `${selectedFiles.length} ${t("common.files")}`,
                    });
                    setSendProgressStats(null, null);
                    clearFiles();
                }
                else if (hasErrors) {
                    const successCount = progress.filter((p) => p.status === 'done').length;
                    const failedCount = progress.filter((p) => p.status === 'error').length;
                    toaster.toast({
                        title: t("upload.partialCompletedTitle"),
                        body: t("upload.partialCompletedBody")
                            .replace("{success}", String(successCount))
                            .replace("{failed}", String(failedCount)),
                    });
                    setSendProgressStats(null, null);
                    setUploadProgress([]);
                }
            }
        }
        catch (error) {
            toaster.toast({
                title: t("upload.failedTitle"),
                body: String(error),
            });
            setSendProgressStats(null, null);
            setCurrentUploadSessionId(null);
            setUploadProgress([]);
        }
        finally {
            setUploading(false);
            if (batchWaitForSendFinished && batchSessionIdForSafety) {
                setTimeout(() => {
                    const state = useLocalSendStore.getState();
                    if (state.currentUploadSessionId === batchSessionIdForSafety) {
                        state.setUploadProgress([]);
                        state.setSendProgressStats(null, null);
                        state.setCurrentUploadSessionId(null);
                        toaster.toast({ title: t("sendProgress.sendCompleteToast"), body: "" });
                    }
                }, 15000);
            }
        }
    };
    const clearShareLinkSessions = useLocalSendStore((state) => state.clearShareLinkSessions);
    const setPendingShare = useLocalSendStore((state) => state.setPendingShare);
    // Handle create share link (Download API) -> navigate to Shared via Link page for settings
    const handleCreateShareLink = () => {
        if (!backend.running) {
            toaster.toast({
                title: t("common.error"),
                body: t("shareLink.backendRequired"),
            });
            return;
        }
        const shareableFiles = selectedFiles.filter((f) => f.textContent ||
            (!f.isFolder && f.sourcePath) ||
            (f.isFolder && f.folderPath));
        if (shareableFiles.length === 0) {
            toaster.toast({
                title: t("common.error"),
                body: t("shareLink.selectFiles"),
            });
            return;
        }
        // Set pending share and navigate to settings page (no session created yet)
        setPendingShare({ files: shareableFiles });
        DFL.Router.CloseSideMenus();
        DFL.Router.Navigate("/decky-localsend-share-link");
    };
    // Handle screenshot gallery (experimental)
    const handleOpenScreenshotGallery = () => {
        // Show warning modal first
        const warningModal = DFL.showModal(SP_JSX.jsx(ConfirmModal, { title: t("screenshot.experimental"), message: t("screenshot.warningDetails"), confirmText: t("screenshot.understand"), cancelText: t("common.cancel"), onConfirm: () => {
                // Open screenshot gallery
                const galleryModal = DFL.showModal(SP_JSX.jsx(ScreenshotGalleryModal, { backendUrl: backend.url, onSelectScreenshots: (screenshots) => {
                        // Add selected screenshots to upload queue
                        screenshots.forEach((screenshot) => {
                            const now = Date.now();
                            addFile({
                                id: `screenshot-${now}-${Math.random().toString(16).slice(2)}`,
                                fileName: screenshot.filename,
                                sourcePath: screenshot.path,
                            });
                        });
                        toaster.toast({
                            title: t("screenshot.added"),
                            body: `${screenshots.length} ${t("screenshot.screenshotsAdded")}`,
                        });
                    }, closeModal: () => galleryModal.Close() }));
            }, closeModal: () => warningModal.Close() }));
    };
    return (SP_JSX.jsxs(SP_JSX.Fragment, { children: [receiveProgress && (SP_JSX.jsx(ReceiveProgressPanel, { receiveProgress: receiveProgress, onCancelReceive: async (sessionId) => {
                    selfCancelledSessionId = sessionId;
                    try {
                        await proxyPost(`/api/localsend/v2/cancel?sessionId=${encodeURIComponent(sessionId)}`);
                    }
                    finally {
                        useLocalSendStore.getState().setReceiveProgress(null);
                        toaster.toast({ title: t("notify.receiveCancelled"), body: "" });
                    }
                } })), uploadProgress.length > 0 && (SP_JSX.jsx(SendProgressPanel, { uploadProgress: uploadProgress })), SP_JSX.jsxs(DFL.PanelSection, { title: t("backend.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: t("backend.status"), description: backend.running ? t("backend.running") : t("backend.stopped"), checked: backend.running, onChange: handleToggleBackend }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleRefreshDevices, disabled: refreshLoading, children: refreshLoading ? t("backend.scanning") : t("backend.refreshDevices") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleScanNow, disabled: scanLoading, children: scanLoading ? t("backend.scanning") : t("backend.scanNow") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleReloadConfig, children: t("config.reloadConfig") }) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: t("networkInfo.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("networkInfo.deviceName"), children: deviceAlias || "-" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("networkInfo.port"), children: devicePort }) }), networkInfo.length === 0 ? (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { children: t("networkInfo.noNetwork") }) })) : (networkInfo.map((info, index) => (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: info.number, children: info.ip_address }) }, `${info.interface_name}-${index}`))))] }), SP_JSX.jsx(DevicesPanel, { devices: devices, selectedDevice: selectedDevice, onSelectDevice: setSelectedDevice, favorites: favorites, onAddToFavorites: handleAddToFavorites, onRemoveFromFavorites: handleRemoveFromFavorites }), SP_JSX.jsxs(DFL.PanelSection, { title: t("upload.title"), children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("upload.selectedDevice"), children: selectedDevice ? selectedDevice.alias : t("upload.none") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleFileSelect, disabled: uploading, children: t("upload.chooseFile") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleFolderSelect, disabled: uploading, children: t("upload.chooseFolder") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleAddText, disabled: uploading, children: t("upload.addText") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleOpenScreenshotGallery, disabled: uploading || !backend.running, children: t("screenshot.openGallery") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleUpload(), disabled: uploading || !selectedDevice || selectedFiles.length === 0, children: uploading ? t("upload.uploading") : t("upload.confirmSend") }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleManualSend, disabled: uploading || selectedFiles.length === 0, children: t("upload.manualSend") }) }), useDownload && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.ButtonItem, { layout: "below", onClick: handleCreateShareLink, disabled: uploading || selectedFiles.length === 0 || !backend.running, children: ["\uD83D\uDD17 ", t("upload.createShareLink")] }) })), useDownload && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.ButtonItem, { layout: "below", onClick: () => {
                                if (!backend.running) {
                                    toaster.toast({
                                        title: t("common.error"),
                                        body: t("shareLink.backendRequired"),
                                    });
                                    return;
                                }
                                DFL.Router.CloseSideMenus();
                                DFL.Router.Navigate("/decky-localsend-share-link");
                            }, disabled: !backend.running, children: ["\uD83D\uDD17 ", t("shareLink.title")] }) })), selectedFiles.length > 0 && favorites.length > 0 && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t("upload.quickSendFavorites"), children: favorites.length }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { display: 'flex', flexDirection: 'column', gap: '4px' }, children: getOnlineFavorites().map((fav) => (SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleQuickSendToFavorite(fav.favorite_fingerprint), disabled: uploading || !fav.online, children: SP_JSX.jsxs("span", { style: { fontSize: '13px', opacity: fav.online ? 1 : 0.5 }, children: [fav.online ? '🟢' : '⚫', " ", t("upload.sendTo"), " ", fav.favorite_alias || fav.favorite_fingerprint.substring(0, 8), !fav.online && ` (${t("upload.deviceOffline")})`] }) }, fav.favorite_fingerprint))) }) })] })), selectedFiles.length > 0 && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.Field, { label: t("upload.selectedFiles"), children: [selectedFiles.length, " ", t("common.files")] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Focusable, { style: { maxHeight: '150px', overflowY: 'auto' }, children: selectedFiles.map((file) => (SP_JSX.jsxs("div", { style: {
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            padding: '4px 0',
                                            fontSize: '12px'
                                        }, children: [SP_JSX.jsx("span", { style: { flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }, children: file.isFolder
                                                    ? `📁 ${file.fileName} (${file.fileCount} ${t("upload.folderFiles")})`
                                                    : file.fileName }), SP_JSX.jsx("button", { onClick: () => removeFile(file.id), disabled: uploading, style: {
                                                    marginLeft: '8px',
                                                    padding: '2px 6px',
                                                    fontSize: '10px',
                                                    backgroundColor: '#dc3545',
                                                    color: '#fff',
                                                    border: 'none',
                                                    borderRadius: '3px',
                                                    cursor: uploading ? 'not-allowed' : 'pointer',
                                                    opacity: uploading ? 0.5 : 1,
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '2px'
                                                }, children: SP_JSX.jsx(FaTimes, { size: 10 }) })] }, file.id))) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleClearFiles, disabled: uploading, children: t("upload.clearFiles") }) })] }))] }), SP_JSX.jsx(ReceiveHistoryPanel, { saveReceiveHistory: saveReceiveHistory }), SP_JSX.jsx(DFL.PanelSection, { title: t("config.title"), children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => {
                            DFL.Router.CloseSideMenus();
                            DFL.Router.Navigate("/decky-localsend-config");
                        }, children: t("config.openConfig") }) }) })] }));
}
var index = definePlugin(() => {
    // Register config page route (without exact to allow sub-routes)
    routerHook.addRoute("/decky-localsend-config", ConfigPage);
    routerHook.addRoute("/decky-localsend-share-link", SharedViaLinkPage);
    // Helper function to update device in store
    const updateDeviceInStore = (deviceData) => {
        const store = useLocalSendStore.getState();
        const currentDevices = store.devices;
        const fingerprint = deviceData.fingerprint;
        if (!fingerprint)
            return;
        const newDevice = {
            fingerprint: deviceData.fingerprint,
            alias: deviceData.alias,
            ip_address: deviceData.ip_address,
            port: deviceData.port,
            protocol: deviceData.protocol,
            deviceType: deviceData.deviceType,
            deviceModel: deviceData.deviceModel,
        };
        // Check if device already exists
        const existingIndex = currentDevices.findIndex(d => d.fingerprint === fingerprint);
        if (existingIndex >= 0) {
            // Update existing device
            const updatedDevices = [...currentDevices];
            updatedDevices[existingIndex] = { ...updatedDevices[existingIndex], ...newDevice };
            store.setDevices(updatedDevices);
            // Update selected device if it's the same one
            const selectedDevice = store.selectedDevice;
            if (selectedDevice?.fingerprint === fingerprint) {
                store.setSelectedDevice({ ...selectedDevice, ...newDevice });
            }
        }
        else {
            // Add new device
            store.setDevices([...currentDevices, newDevice]);
        }
    };
    const EmitEventListener = addEventListener("unix_socket_notification", (event) => {
        // Handle device discovered/updated events - update device list without toast
        if (event.type === "device_discovered" || event.type === "device_updated") {
            const deviceData = event.data ?? {};
            updateDeviceInStore(deviceData);
            // Don't show toast for device events, just update the list silently
            return;
        }
        if (event.type === "confirm_recv") {
            const data = event.data ?? {};
            const sessionId = String(data.sessionId || "");
            const files = Array.isArray(data.files) ? data.files : [];
            const totalFiles = data.totalFiles != null ? Number(data.totalFiles) : undefined;
            const modalResult = DFL.showModal(SP_JSX.jsx(ConfirmReceiveModal, { from: String(data.from || ""), fileCount: Number(data.fileCount || 0), files: files, totalFiles: totalFiles, onConfirm: async (confirmed) => {
                    if (!sessionId) {
                        toaster.toast({
                            title: t("toast.confirmFailed"),
                            body: t("toast.missingSessionId"),
                        });
                        return;
                    }
                    try {
                        const result = await proxyGet(`/api/self/v1/confirm-recv?sessionId=${encodeURIComponent(sessionId)}&confirmed=${confirmed}`);
                        if (result.status !== 200) {
                            throw new Error(result.data?.error || "Confirm request failed");
                        }
                        toaster.toast({
                            title: confirmed ? t("toast.accepted") : t("toast.rejected"),
                            body: confirmed ? t("toast.receiveConfirmed") : t("toast.receiveRejected"),
                        });
                    }
                    catch (error) {
                        toaster.toast({
                            title: t("toast.confirmFailed"),
                            body: String(error),
                        });
                    }
                }, closeModal: () => modalResult.Close() }));
            return;
        }
        if (event.type === "confirm_download") {
            const data = event.data ?? {};
            const sessionId = String(data.sessionId || "");
            const clientKey = String(data.clientKey || "");
            const fileCount = Number(data.fileCount || 0);
            const files = Array.isArray(data.files) ? data.files : [];
            const totalFiles = data.totalFiles != null ? Number(data.totalFiles) : undefined;
            const modalResult = DFL.showModal(SP_JSX.jsx(ConfirmDownloadModal, { fileCount: fileCount, files: files, totalFiles: totalFiles, clientIp: data.clientIp != null ? String(data.clientIp) : undefined, clientType: data.clientType != null ? String(data.clientType) : undefined, userAgent: data.userAgent != null ? String(data.userAgent) : undefined, onConfirm: async (confirmed) => {
                    if (!sessionId || !clientKey) {
                        toaster.toast({
                            title: t("toast.confirmFailed"),
                            body: t("toast.missingSessionId"),
                        });
                        return;
                    }
                    try {
                        await confirmDownload(sessionId, clientKey, confirmed);
                        toaster.toast({
                            title: confirmed ? t("toast.accepted") : t("toast.rejected"),
                            body: confirmed ? t("toast.receiveConfirmed") : t("toast.receiveRejected"),
                        });
                    }
                    catch (error) {
                        toaster.toast({
                            title: t("toast.confirmFailed"),
                            body: String(error),
                        });
                    }
                }, closeModal: () => modalResult.Close() }));
            return;
        }
        if (event.type === "pin_required") {
            toaster.toast({
                title: event.title || t("toast.pinRequired"),
                body: event.message || t("toast.pinRequiredForFiles"),
            });
            return;
        }
        if (event.type === "upload_cancelled") {
            useLocalSendStore.getState().setReceiveProgress(null);
            const dataSessionId = event.data?.sessionId;
            if (dataSessionId === selfCancelledSessionId) {
                selfCancelledSessionId = null;
                return;
            }
            toaster.toast({
                title: t("notify.uploadCancelled"),
                body: "",
            });
            return;
        }
        if (event.type === "upload_start") {
            const data = event.data ?? {};
            useLocalSendStore.getState().setReceiveProgress({
                sessionId: String(data.sessionId ?? ""),
                totalFiles: Number(data.totalFiles ?? 0),
                completedCount: 0,
                currentFileName: "",
            });
        }
        if (event.type === "upload_progress") {
            const data = event.data ?? {};
            useLocalSendStore.getState().setReceiveProgress((prev) => {
                if (!prev || String(data.sessionId ?? "") !== prev.sessionId)
                    return prev;
                const completed = Number(data.successFiles ?? 0) + Number(data.failedFiles ?? 0);
                return {
                    ...prev,
                    completedCount: completed,
                    currentFileName: String(data.currentFileName ?? ""),
                };
            });
            return;
        }
        if (event.type === "upload_end") {
            const data = event.data ?? {};
            useLocalSendStore.getState().setReceiveProgress((prev) => (prev?.sessionId === data.sessionId ? null : prev));
        }
        if (event.type === "send_finished") {
            const data = event.data ?? {};
            const reason = String(data.reason ?? "completed");
            const successCount = Number(data.successCount ?? 0);
            const failedCount = Number(data.failedCount ?? 0);
            useLocalSendStore.getState().setUploadProgress([]);
            useLocalSendStore.getState().setSendProgressStats(null, null);
            useLocalSendStore.getState().setCurrentUploadSessionId(null);
            if (reason === "completed") {
                useLocalSendStore.getState().clearFiles();
                toaster.toast({ title: t("sendProgress.sendCompleteToast"), body: "" });
            }
            else if (reason === "cancelled") {
                toaster.toast({ title: t("sendProgress.cancelSendToast"), body: "" });
            }
            else if (reason === "rejected") {
                toaster.toast({
                    title: t("sendProgress.rejectedToast"),
                    body: t("sendProgress.rejectedBody").replace("{success}", String(successCount)).replace("{failed}", String(failedCount)),
                });
            }
            return;
        }
        if (event.type === "send_progress") {
            const data = event.data ?? {};
            const fileId = String(data.fileId ?? "");
            const success = !!data.success;
            const errorMsg = String(data.error ?? "");
            useLocalSendStore.getState().setUploadProgress((prev) => prev.map((p) => p.fileId === fileId
                ? { ...p, status: success ? "done" : "error", error: success ? undefined : errorMsg }
                : p));
            const state = useLocalSendStore.getState();
            const currentCompleted = state.sendProgressCompletedCount ?? 0;
            const currentTotal = state.sendProgressTotalFiles;
            // 添加上限检查，不超过 totalFiles
            if (currentTotal != null) {
                const newCompleted = Math.min(currentCompleted + 1, currentTotal);
                state.setSendProgressStats(currentTotal, newCompleted);
            }
            return;
        }
        // Skip toast for info type notifications (don't show decky info)
        if (event.type === "info") {
            return;
        }
        // i18n for upload_start / upload_end toast title (including text-only variant)
        const isTextOnly = !!event.isTextOnly;
        let notifyTitleKey = null;
        if (event.type === "upload_start") {
            notifyTitleKey = isTextOnly ? "notify.textUploadStarted" : "notify.uploadStarted";
        }
        else if (event.type === "upload_end") {
            notifyTitleKey = isTextOnly ? "notify.textUploadCompleted" : "notify.uploadCompleted";
        }
        const title = notifyTitleKey ? t(notifyTitleKey) : (event.title || t("toast.notification"));
        toaster.toast({
            title,
            body: event.message || "",
        });
    });
    // Listen for text received events from backend
    const TextReceivedListener = addEventListener("text_received", (event) => {
        const sessionId = String(event.sessionId ?? "");
        const modalResult = DFL.showModal(SP_JSX.jsx(TextReceivedModal, { title: event.title, content: event.content, fileName: event.fileName, onClose: () => { }, closeModal: () => {
                if (sessionId) {
                    proxyGet(`/api/self/v1/text-received-dismiss?sessionId=${encodeURIComponent(sessionId)}`).finally(() => modalResult.Close());
                }
                else {
                    modalResult.Close();
                }
            } }));
    });
    // Listen for file received events from backend
    const FileReceivedListener = addEventListener("file_received", (event) => {
        const modalResult = DFL.showModal(SP_JSX.jsx(FileReceivedModal, { title: event.title, folderPath: event.folderPath, fileCount: event.fileCount, files: event.files, totalFiles: event.totalFiles, successFiles: event.successFiles, failedFiles: event.failedFiles, failedFileIds: event.failedFileIds, onClose: () => { }, closeModal: () => modalResult.Close() }));
    });
    return {
        // The name shown in various decky menus
        name: "Decky Localsend",
        // The element displayed at the top of your plugin's menu
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "Decky Localsend" }),
        // The content of your plugin's menu
        content: SP_JSX.jsx(Content, {}),
        // The icon displayed in the plugin list
        icon: SP_JSX.jsx(LuSendToBack, {}),
        // The function triggered when your plugin unloads
        onDismount() {
            console.log("Unloading");
            removeEventListener("unix_socket_notification", EmitEventListener);
            removeEventListener("text_received", TextReceivedListener);
            removeEventListener("file_received", FileReceivedListener);
            routerHook.removeRoute("/decky-localsend-config");
            routerHook.removeRoute("/decky-localsend-share-link");
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map
