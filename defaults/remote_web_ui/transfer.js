(function () {
  "use strict";

  const I18N = {
    "zh-CN": {
      subtitle: "将文件或文本上传到 Steam Deck",
      tabFile: "文件上传",
      uploadHint: "点击下方“选择文件”或拖拽文件到此处",
      clear: "清空",
      sendFile: "开始上传",
      cancel: "取消",
      statusDone: "完成",
      statusFailed: "失败",
      choosePathTitle: "选择传输路径",
      choosePathUp: "上一级",
      choosePathCancel: "取消",
      choosePathSelect: "选择当前目录",
      choosePathCurrent: "当前路径：{{path}}",
      choosePathError: "无法读取目录",
      alertSelectFiles: "请先选择文件",
      alertChoosePath: "请先选择传输路径",
      alertAllSuccess: "所有文件上传完成",
      alertPartialFail: "部分文件上传失败",
      alertUploadError: "上传失败",
      alertNoValidFiles: "未发现可上传文件，请重新选择",
      folderLabel: "文件夹",
    },
    "en-US": {
      subtitle: "Upload files or text to Steam Deck",
      tabFile: "File Upload",
      uploadHint: "Click choose files below or drag files here",
      clear: "Clear",
      sendFile: "Start Upload",
      cancel: "Cancel",
      statusDone: "Done",
      statusFailed: "Failed",
      choosePathTitle: "Choose destination",
      choosePathUp: "Up",
      choosePathCancel: "Cancel",
      choosePathSelect: "Select current folder",
      choosePathCurrent: "Current path: {{path}}",
      choosePathError: "Failed to read directory",
      alertSelectFiles: "Please select files first",
      alertChoosePath: "Please choose an upload destination first",
      alertAllSuccess: "All files uploaded",
      alertPartialFail: "Some files failed to upload",
      alertUploadError: "Upload failed",
      alertNoValidFiles: "No valid files were added. Please pick files again.",
      folderLabel: "Folder",
    },
  };

  const FILE_PARALLEL = 2;
  const CHUNK_THRESHOLD = 512 * 1024 * 1024;
  const CHUNK_SIZE = 8 * 1024 * 1024;
  const CHUNK_PARALLEL = 2;
  const CHUNK_MAX_RETRIES = 5;
  const CHUNK_RETRY_BASE = 500;
  const HASH_THRESHOLD = 256 * 1024 * 1024;
  const HASH_ALGO = "SHA-256";

  const state = {
    lang: "zh-CN",
    selectedFiles: [],
    folderDisplayMap: new Map(),
    uploadPromptEnabled: false,
    defaultUploadDir: "",
    uploading: false,
    uploadPathResolve: null,
    uploadPathCurrentValue: "",
  };

  const els = {
    subtitle: document.getElementById("subtitle"),
    tabFile: document.getElementById("tab-file"),
    uploadHint: document.getElementById("upload-hint"),
    uploadArea: document.getElementById("upload-area"),
    pickBtn: document.getElementById("pick-btn"),
    fileInput: document.getElementById("file-input"),
    fileList: document.getElementById("file-list"),
    clearBtn: document.getElementById("clear-btn"),
    uploadBtn: document.getElementById("upload-btn"),
    pathModal: document.getElementById("upload-path-modal"),
    pathTitle: document.getElementById("upload-path-title"),
    pathCurrent: document.getElementById("upload-path-current"),
    pathList: document.getElementById("upload-path-list"),
    pathUp: document.getElementById("upload-path-up"),
    pathCancel: document.getElementById("upload-path-cancel"),
    pathOk: document.getElementById("upload-path-ok"),
  };

  function normalizeLang(raw) {
    const v = String(raw || "").toLowerCase();
    if (v.startsWith("zh")) return "zh-CN";
    return "en-US";
  }

  function t(key, vars) {
    const dict = I18N[state.lang] || I18N["zh-CN"];
    let value = dict[key] || I18N["zh-CN"][key] || key;
    if (!vars) return value;
    Object.keys(vars).forEach((k) => {
      value = value.replace(new RegExp(`\\{\\{${k}\\}\\}`, "g"), String(vars[k]));
    });
    return value;
  }

  function applyTranslations() {
    if (els.subtitle) els.subtitle.textContent = t("subtitle");
    if (els.tabFile) els.tabFile.textContent = t("tabFile");
    if (els.uploadHint) els.uploadHint.textContent = t("uploadHint");
    if (els.clearBtn) els.clearBtn.textContent = t("clear");
    if (els.uploadBtn) els.uploadBtn.textContent = t("sendFile");
    if (els.pathTitle) els.pathTitle.textContent = t("choosePathTitle");
    if (els.pathUp) els.pathUp.textContent = t("choosePathUp");
    if (els.pathCancel) els.pathCancel.textContent = t("choosePathCancel");
    if (els.pathOk) els.pathOk.textContent = t("choosePathSelect");
  }

  async function initLanguage() {
    try {
      const res = await fetch("/api/settings/language");
      if (res.ok) {
        const data = await res.json();
        state.lang = normalizeLang(data && data.language ? data.language : "auto");
      } else {
        state.lang = normalizeLang("auto");
      }
    } catch (_err) {
      state.lang = normalizeLang("auto");
    }
    applyTranslations();
  }

  function safeId(input) {
    return String(input).replace(/[^a-zA-Z0-9_-]/g, "_");
  }

  function getFileRelativePath(file) {
    return file._relativePath || file.webkitRelativePath || "";
  }

  function getFileKey(file) {
    if (file._displayKey) return file._displayKey;
    const rel = getFileRelativePath(file);
    if (rel) return rel;
    if (file.name) return file.name;
    if (!file._fallbackKey) {
      file._fallbackKey = `blob_${Date.now()}_${Math.random().toString(16).slice(2)}`;
    }
    return file._fallbackKey;
  }

  function getTopFolderName(file) {
    const rel = getFileRelativePath(file);
    if (!rel) return "";
    const parts = rel.split("/");
    if (parts.length <= 1) return "";
    return parts[0] || "";
  }

  function fileFingerprint(file) {
    return `${getFileKey(file)}|${file.size}|${file.lastModified || 0}`;
  }

  function formatSize(size) {
    const v = Number(size) || 0;
    if (v < 1024) return `${v} B`;
    if (v < 1024 * 1024) return `${(v / 1024).toFixed(1)} KB`;
    if (v < 1024 * 1024 * 1024) return `${(v / 1024 / 1024).toFixed(1)} MB`;
    return `${(v / 1024 / 1024 / 1024).toFixed(2)} GB`;
  }

  function syncEmptyState() {
    if (!els.uploadArea) return;
    const hasFiles = state.selectedFiles.length > 0;
    els.uploadArea.classList.toggle("is-empty", !hasFiles);
  }

  function updateUploadButtonState() {
    const hasFiles = state.selectedFiles.length > 0;
    if (els.uploadBtn) els.uploadBtn.disabled = state.uploading || !hasFiles;
    if (els.clearBtn) els.clearBtn.disabled = state.uploading || !hasFiles;
    syncEmptyState();
  }

  function removeFileItemByKey(fileKey) {
    const node = els.fileList.querySelector(`[data-file-key="${CSS.escape(fileKey)}"]`);
    if (node) node.remove();
  }

  function removeFolderItemByKey(folderKey) {
    const node = els.fileList.querySelector(`[data-folder-key="${CSS.escape(folderKey)}"]`);
    if (node) node.remove();
  }

  function addSingleFileRow(file) {
    const fileKey = getFileKey(file);
    const row = document.createElement("div");
    row.className = "file-item";
    row.dataset.fileKey = fileKey;

    const header = document.createElement("div");
    header.className = "file-item-header";

    const info = document.createElement("span");
    info.className = "file-item-info";
    info.textContent = `${fileKey} (${formatSize(file.size)})`;

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "cancel-btn";
    cancelBtn.textContent = t("cancel");
    cancelBtn.addEventListener("click", () => {
      if (state.uploading) return;
      const idx = state.selectedFiles.findIndex((f) => getFileKey(f) === fileKey);
      if (idx >= 0) state.selectedFiles.splice(idx, 1);
      removeFileItemByKey(fileKey);
      updateUploadButtonState();
    });

    header.appendChild(info);
    header.appendChild(cancelBtn);

    const progressSection = document.createElement("div");
    progressSection.className = "file-item-progress";
    progressSection.id = `progress-section-${safeId(fileKey)}`;

    const progressBar = document.createElement("div");
    progressBar.className = "file-progress-bar";

    const progressFill = document.createElement("div");
    progressFill.className = "file-progress-fill";
    progressFill.id = `progress-fill-${safeId(fileKey)}`;

    progressBar.appendChild(progressFill);

    const progressText = document.createElement("div");
    progressText.className = "file-progress-text";
    progressText.innerHTML =
      `<span id="progress-percent-${safeId(fileKey)}">0%</span>` +
      `<span class="speed" id="progress-speed-${safeId(fileKey)}">0 KB/s</span>`;

    progressSection.appendChild(progressBar);
    progressSection.appendChild(progressText);
    row.appendChild(header);
    row.appendChild(progressSection);
    els.fileList.appendChild(row);
  }

  function addFolderRow(folderKey, folderName) {
    if (state.folderDisplayMap.has(folderKey)) return;
    state.folderDisplayMap.set(folderKey, { name: folderName });

    const row = document.createElement("div");
    row.className = "file-item";
    row.dataset.folderKey = folderKey;

    const header = document.createElement("div");
    header.className = "file-item-header";

    const info = document.createElement("span");
    info.className = "file-item-info";
    info.textContent = `📁 ${folderName}`;

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "cancel-btn";
    cancelBtn.textContent = t("cancel");
    cancelBtn.addEventListener("click", () => {
      if (state.uploading) return;
      state.selectedFiles = state.selectedFiles.filter((item) => item._folderKey !== folderKey);
      state.folderDisplayMap.delete(folderKey);
      removeFolderItemByKey(folderKey);
      updateUploadButtonState();
    });

    header.appendChild(info);
    header.appendChild(cancelBtn);
    row.appendChild(header);
    els.fileList.appendChild(row);
  }

  function addFiles(files, options) {
    const opts = options || {};
    const groupFolders = !!opts.groupFolders;
    const incoming = Array.from(files || []);
    const existing = new Set(state.selectedFiles.map(fileFingerprint));
    let added = 0;

    incoming.forEach((file) => {
      if (!file) return;
      const fp = fileFingerprint(file);
      if (existing.has(fp)) return;
      existing.add(fp);

      const folderName = groupFolders ? getTopFolderName(file) : "";
      if (folderName) {
        const folderKey = folderName;
        try {
          file._folderKey = folderKey;
        } catch (_err) {
          // noop
        }
        state.selectedFiles.push(file);
        addFolderRow(folderKey, folderName);
        added += 1;
        return;
      }

      state.selectedFiles.push(file);
      addSingleFileRow(file);
      added += 1;
    });

    if (added === 0 && incoming.length > 0) {
      alert(t("alertNoValidFiles"));
    }
    updateUploadButtonState();
  }

  function clearSelectedFiles() {
    if (state.uploading) return;
    state.selectedFiles = [];
    state.folderDisplayMap.clear();
    if (els.fileList) els.fileList.innerHTML = "";
    updateUploadButtonState();
  }

  function updateFileProgress(fileKey, progress, speed, status) {
    const phase = status || "uploading";
    const sid = safeId(fileKey);
    const section = document.getElementById(`progress-section-${sid}`);
    const fill = document.getElementById(`progress-fill-${sid}`);
    const percent = document.getElementById(`progress-percent-${sid}`);
    const speedEl = document.getElementById(`progress-speed-${sid}`);
    if (!section || !fill || !percent || !speedEl) return;

    section.classList.add("active");
    fill.style.width = `${progress}%`;
    if (phase === "success") {
      fill.style.background = "linear-gradient(90deg, #34a853 0%, #4CAF50 100%)";
      percent.textContent = t("statusDone");
      speedEl.textContent = "";
    } else if (phase === "error") {
      fill.style.background = "linear-gradient(90deg, #ea4335 0%, #ff6b6b 100%)";
      percent.textContent = t("statusFailed");
      speedEl.textContent = "";
    } else {
      fill.style.background = "linear-gradient(90deg, #8fd8cc 0%, #5fa6ff 100%)";
      percent.textContent = `${progress}%`;
      speedEl.textContent = `${Math.max(0, Number(speed) || 0)} KB/s`;
    }
  }

  function activateProgress(fileKey) {
    const section = document.getElementById(`progress-section-${safeId(fileKey)}`);
    if (section) section.classList.add("active");
  }

  function hashString(input) {
    let hash = 5381;
    for (let i = 0; i < input.length; i += 1) {
      hash = ((hash << 5) + hash) + input.charCodeAt(i);
      hash &= 0xffffffff;
    }
    return (hash >>> 0).toString(16);
  }

  function buildUploadId(file, chosenPath) {
    const relPath = getFileRelativePath(file) || "";
    const base = `${file.name}|${file.size}|${file.lastModified}|${relPath}|${chosenPath || ""}`;
    return `up_${hashString(base)}`;
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function computeFileHash(file) {
    if (!window.crypto || !window.crypto.subtle) return null;
    const buffer = await file.arrayBuffer();
    const digest = await window.crypto.subtle.digest(HASH_ALGO, buffer);
    const bytes = new Uint8Array(digest);
    return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function computeFileHashIfNeeded(file) {
    if (file.size > HASH_THRESHOLD) return null;
    try {
      return await computeFileHash(file);
    } catch (_err) {
      return null;
    }
  }

  async function getResumeInfo(uploadId, totalChunks, totalSize) {
    try {
      const response = await fetch("/upload-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: uploadId, total_chunks: totalChunks, total_size: totalSize }),
      });
      if (!response.ok) return null;
      const data = await response.json();
      if (data.status !== "success") return null;
      return data;
    } catch (_err) {
      return null;
    }
  }

  function uploadFileSimple(file, chosenPath, fileHash) {
    return new Promise((resolve) => {
      const fileKey = getFileKey(file);
      activateProgress(fileKey);
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      if (chosenPath) formData.append("dest_path", chosenPath);
      const relPath = getFileRelativePath(file);
      if (relPath) formData.append("relative_path", relPath);
      if (fileHash) {
        formData.append("file_hash", fileHash);
        formData.append("hash_algo", HASH_ALGO);
      }
      formData.append("file_size", String(file.size));
      formData.append("file", file, file.name || "upload.bin");

      let lastUpdateTime = Date.now();
      let lastUploadedBytes = 0;

      xhr.upload.addEventListener("progress", (e) => {
        if (!e.lengthComputable) return;
        const currentTime = Date.now();
        const timeDiff = (currentTime - lastUpdateTime) / 1000;
        const bytesDiff = e.loaded - lastUploadedBytes;
        if (timeDiff >= 0.2 || e.loaded === e.total) {
          const progress = Math.min(100, Math.round((e.loaded / e.total) * 100));
          const speed = timeDiff > 0 ? Math.round((bytesDiff / 1024) / timeDiff) : 0;
          updateFileProgress(fileKey, progress, speed, "uploading");
          lastUpdateTime = currentTime;
          lastUploadedBytes = e.loaded;
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
          updateFileProgress(fileKey, 100, 0, "success");
          resolve({ status: "success" });
        } else {
          updateFileProgress(fileKey, 100, 0, "error");
          resolve({ status: "error" });
        }
      });
      xhr.addEventListener("error", () => {
        updateFileProgress(fileKey, 0, 0, "error");
        resolve({ status: "error" });
      });
      xhr.addEventListener("timeout", () => {
        updateFileProgress(fileKey, 0, 0, "error");
        resolve({ status: "timeout" });
      });

      xhr.timeout = 0;
      xhr.open("POST", "/upload");
      xhr.send(formData);
    });
  }

  async function uploadFileChunked(file, chosenPath, fileHash) {
    const fileKey = getFileKey(file);
    activateProgress(fileKey);
    const uploadId = buildUploadId(file, chosenPath);
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const chunkProgress = new Array(totalChunks).fill(0);
    let uploadedBytes = 0;
    const startTime = Date.now();

    let completedChunks = new Set();
    const resumeInfo = await getResumeInfo(uploadId, totalChunks, file.size);
    if (resumeInfo && Array.isArray(resumeInfo.received) &&
      resumeInfo.total_chunks === totalChunks && resumeInfo.total_size === file.size) {
      completedChunks = new Set(resumeInfo.received);
      if (completedChunks.size >= totalChunks) {
        updateFileProgress(fileKey, 100, 0, "success");
        return { status: "success" };
      }
    }

    const updateOverallProgress = (index, loaded) => {
      const prev = chunkProgress[index] || 0;
      if (loaded < prev) {
        uploadedBytes -= prev;
        chunkProgress[index] = 0;
      }
      const delta = loaded - (chunkProgress[index] || 0);
      if (delta > 0) {
        uploadedBytes += delta;
        chunkProgress[index] = loaded;
      }
      const progress = Math.min(100, Math.round((uploadedBytes / file.size) * 100));
      const elapsed = (Date.now() - startTime) / 1000;
      const speed = elapsed > 0 ? Math.round((uploadedBytes / 1024) / elapsed) : 0;
      updateFileProgress(fileKey, progress, speed, "uploading");
    };

    const uploadChunk = (index) => new Promise((resolve, reject) => {
      const start = index * CHUNK_SIZE;
      const end = Math.min(file.size, start + CHUNK_SIZE);
      const blob = file.slice(start, end);

      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("upload_id", uploadId);
      formData.append("chunk_index", String(index));
      formData.append("total_chunks", String(totalChunks));
      formData.append("total_size", String(file.size));
      formData.append("chunk_size", String(CHUNK_SIZE));
      formData.append("chunk_offset", String(start));
      formData.append("filename", file.name);
      if (chosenPath) formData.append("dest_path", chosenPath);
      const relPath = getFileRelativePath(file);
      if (relPath) formData.append("relative_path", relPath);
      if (fileHash) {
        formData.append("file_hash", fileHash);
        formData.append("hash_algo", HASH_ALGO);
      }
      formData.append("chunk", blob, file.name);

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) updateOverallProgress(index, e.loaded);
      });
      xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
          updateOverallProgress(index, blob.size);
          resolve();
        } else {
          reject(new Error("chunk upload failed"));
        }
      });
      xhr.addEventListener("error", () => reject(new Error("chunk upload error")));
      xhr.addEventListener("timeout", () => reject(new Error("chunk upload timeout")));
      xhr.timeout = 0;
      xhr.open("POST", "/upload-chunk");
      xhr.send(formData);
    });

    const uploadChunkWithRetry = async (index) => {
      if (completedChunks.has(index)) return;
      for (let attempt = 0; attempt <= CHUNK_MAX_RETRIES; attempt += 1) {
        try {
          await uploadChunk(index);
          completedChunks.add(index);
          return;
        } catch (err) {
          if (attempt === CHUNK_MAX_RETRIES) throw err;
          await sleep(CHUNK_RETRY_BASE * Math.pow(2, attempt));
        }
      }
    };

    let nextIndex = 0;
    const workers = Array.from({ length: Math.min(CHUNK_PARALLEL, totalChunks) }, async () => {
      while (true) {
        const current = nextIndex;
        nextIndex += 1;
        if (current >= totalChunks) break;
        await uploadChunkWithRetry(current);
      }
    });
    await Promise.all(workers);
    updateFileProgress(fileKey, 100, 0, "success");
    return { status: "success" };
  }

  async function uploadFile(file, chosenPath) {
    const fileHash = await computeFileHashIfNeeded(file);
    if (file.size >= CHUNK_THRESHOLD) {
      try {
        return await uploadFileChunked(file, chosenPath, fileHash);
      } catch (_err) {
        updateFileProgress(getFileKey(file), 100, 0, "error");
        return { status: "error" };
      }
    }
    return uploadFileSimple(file, chosenPath, fileHash);
  }

  async function refreshUploadOptions() {
    try {
      const response = await fetch("/api/settings/upload-options");
      if (!response.ok) return;
      const data = await response.json();
      if (data.status === "success") {
        state.uploadPromptEnabled = !!data.prompt_upload_path;
        state.defaultUploadDir = data.default_dir || "";
      }
    } catch (_err) {
      // noop
    }
  }

  async function loadUploadPathList(path) {
    if (!els.pathList || !els.pathCurrent) return;
    try {
      const response = await fetch("/api/files/list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      const data = await response.json();
      if (data.status !== "success") throw new Error(data.message || t("choosePathError"));

      state.uploadPathCurrentValue = data.current_path;
      els.pathCurrent.textContent = t("choosePathCurrent", { path: state.uploadPathCurrentValue });
      els.pathList.innerHTML = "";

      if (state.uploadPathCurrentValue && state.uploadPathCurrentValue !== "/") {
        const parent = state.uploadPathCurrentValue.split("/").filter(Boolean);
        parent.pop();
        const parentPath = `/${parent.join("/")}`;
        const parentItem = document.createElement("div");
        parentItem.className = "upload-path-item";
        parentItem.textContent = "⬆️ ..";
        parentItem.addEventListener("click", () => loadUploadPathList(parentPath || "/"));
        els.pathList.appendChild(parentItem);
      }

      (data.files || []).filter((item) => item.is_dir).forEach((dir) => {
        const item = document.createElement("div");
        item.className = "upload-path-item";
        item.textContent = `📁 ${dir.name}`;
        item.addEventListener("click", () => loadUploadPathList(dir.path));
        els.pathList.appendChild(item);
      });
    } catch (_err) {
      els.pathCurrent.textContent = t("choosePathError");
      els.pathList.innerHTML = "";
    }
  }

  function closeUploadPathModal(value) {
    if (els.pathModal) els.pathModal.classList.remove("show");
    if (state.uploadPathResolve) {
      state.uploadPathResolve(value);
      state.uploadPathResolve = null;
    }
  }

  function promptUploadPath() {
    return new Promise((resolve) => {
      state.uploadPathResolve = resolve;
      if (els.pathModal) els.pathModal.classList.add("show");
      const startPath = state.defaultUploadDir || "/home/deck";
      loadUploadPathList(startPath);
    });
  }

  async function startUpload() {
    if (state.uploading) return;
    if (state.selectedFiles.length === 0) {
      alert(t("alertSelectFiles"));
      return;
    }

    await refreshUploadOptions();
    let chosenPath = null;
    if (state.uploadPromptEnabled) {
      chosenPath = await promptUploadPath();
      if (!chosenPath) {
        alert(t("alertChoosePath"));
        return;
      }
    }

    state.uploading = true;
    updateUploadButtonState();

    const queueFiles = [...state.selectedFiles].sort((a, b) => b.size - a.size);
    let uploadedFiles = 0;
    let failedFiles = 0;
    const totalFiles = queueFiles.length;
    let queueIndex = 0;

    const workers = Array.from({ length: Math.min(FILE_PARALLEL, totalFiles) }, async () => {
      while (true) {
        const currentIndex = queueIndex;
        queueIndex += 1;
        if (currentIndex >= totalFiles) break;
        const file = queueFiles[currentIndex];
        const result = await uploadFile(file, chosenPath);
        uploadedFiles += 1;
        if (!result || result.status !== "success") failedFiles += 1;
      }
    });

    try {
      await Promise.all(workers);
      if (uploadedFiles === totalFiles && failedFiles === 0) {
        alert(t("alertAllSuccess"));
        clearSelectedFiles();
      } else if (failedFiles > 0) {
        alert(t("alertPartialFail"));
      }
    } catch (_err) {
      alert(t("alertUploadError"));
    } finally {
      state.uploading = false;
      updateUploadButtonState();
    }
  }

  function readAllEntries(reader) {
    return new Promise((resolve) => {
      const entries = [];
      const readBatch = () => {
        reader.readEntries((batch) => {
          if (!batch.length) {
            resolve(entries);
            return;
          }
          entries.push(...batch);
          readBatch();
        }, () => resolve(entries));
      };
      readBatch();
    });
  }

  async function walkEntry(entry, pathPrefix) {
    if (entry.isFile) {
      return new Promise((resolve) => {
        entry.file((file) => {
          const rel = `${pathPrefix}${file.name}`;
          try {
            file._relativePath = rel;
          } catch (_err) {
            // noop
          }
          resolve([file]);
        }, () => resolve([]));
      });
    }
    if (entry.isDirectory) {
      const reader = entry.createReader();
      const children = await readAllEntries(reader);
      const files = [];
      for (const child of children) {
        const nested = await walkEntry(child, `${pathPrefix}${entry.name}/`);
        files.push(...nested);
      }
      return files;
    }
    return [];
  }

  async function getFilesFromDataTransfer(dt) {
    if (!dt) return [];
    const items = dt.items ? Array.from(dt.items) : [];
    const entries = items.map((item) => item.webkitGetAsEntry && item.webkitGetAsEntry()).filter(Boolean);
    if (entries.length) {
      const files = [];
      for (const entry of entries) {
        const nested = await walkEntry(entry, "");
        files.push(...nested);
      }
      return files;
    }
    return Array.from(dt.files || []);
  }

  function bindEvents() {
    if (els.uploadArea) {
      els.uploadArea.addEventListener("click", () => {
        if (state.uploading) return;
        if (els.fileInput) {
          els.fileInput.value = "";
          els.fileInput.click();
        }
      });
      els.uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        if (!state.uploading) els.uploadArea.classList.add("dragover");
      });
      els.uploadArea.addEventListener("dragleave", () => {
        els.uploadArea.classList.remove("dragover");
      });
      els.uploadArea.addEventListener("drop", async (e) => {
        e.preventDefault();
        els.uploadArea.classList.remove("dragover");
        if (state.uploading) return;
        const files = await getFilesFromDataTransfer(e.dataTransfer);
        addFiles(files, { groupFolders: true });
      });
    }

    if (els.pickBtn) {
      els.pickBtn.addEventListener("click", () => {
        if (state.uploading) return;
        if (els.fileInput) {
          els.fileInput.value = "";
          els.fileInput.click();
        }
      });
    }

    if (els.fileInput) {
      els.fileInput.addEventListener("change", (e) => {
        if (state.uploading) return;
        addFiles(e.target.files, { groupFolders: true });
        els.fileInput.value = "";
      });
    }
    if (els.clearBtn) els.clearBtn.addEventListener("click", clearSelectedFiles);
    if (els.uploadBtn) els.uploadBtn.addEventListener("click", startUpload);

    if (els.pathOk) {
      els.pathOk.addEventListener("click", () => closeUploadPathModal(state.uploadPathCurrentValue || null));
    }
    if (els.pathCancel) {
      els.pathCancel.addEventListener("click", () => closeUploadPathModal(null));
    }
    if (els.pathUp) {
      els.pathUp.addEventListener("click", () => {
        if (!state.uploadPathCurrentValue || state.uploadPathCurrentValue === "/") return;
        const parent = state.uploadPathCurrentValue.split("/").filter(Boolean);
        parent.pop();
        const parentPath = `/${parent.join("/")}`;
        loadUploadPathList(parentPath || "/");
      });
    }
    if (els.pathModal) {
      els.pathModal.addEventListener("click", (e) => {
        if (e.target === els.pathModal) closeUploadPathModal(null);
      });
    }
  }

  async function init() {
    await initLanguage();
    bindEvents();
    await refreshUploadOptions();
    updateUploadButtonState();
  }

  window.addEventListener("DOMContentLoaded", init);
})();
