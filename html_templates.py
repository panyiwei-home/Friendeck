"""
HTML Templates Module for decky-send

This module contains HTML templates and HTTP request handlers for:
- File manager standalone page
- Main page with file upload, text transfer, and file management tabs
- File upload handling
- Text upload handling
"""

import os
import time
from aiohttp import web

# Import decky for logging and event emission
import decky


def get_file_manager_html():
    """Return HTML content for file manager"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>decky-send 文件管理器</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            html, body {
                font-family: Arial, sans-serif;
                background-color: #121212;
                color: white;
                height: 100%;
                overflow: hidden;
            }
            
            body {
                display: flex;
                flex-direction: column;
                padding: 10px;
            }
            h1 {
                color: #1b73e8;
                text-align: center;
            }
            
            /* Breadcrumb Navigation */
            .breadcrumb {
                margin: 10px 0;
                padding: 8px 12px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                overflow-x: auto;
            }
            .breadcrumb-item {
                margin-right: 8px;
                cursor: pointer;
                color: #1b73e8;
            }
            
            /* Action Buttons */
            .action-buttons {
                display: flex;
                gap: 8px;
                margin: 10px 0;
                flex-wrap: wrap;
            }
            .action-buttons button {
                padding: 8px 16px;
                background-color: #1b73e8;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .action-buttons button:hover {
                background-color: #1557b0;
            }
            #new-file-btn, #new-dir-btn {
                background-color: #34a853;
            }
            #new-file-btn:hover, #new-dir-btn:hover {
                background-color: #2d884d;
            }
            #delete-btn {
                background-color: #ea4335;
            }
            #delete-btn:hover {
                background-color: #d93025;
            }
            
            /* File List */
            .file-list-container {
                border: 1px solid #333;
                border-radius: 6px;
                padding: 10px;
                flex: 1 1 auto;
                overflow: auto;
                background-color: rgba(255, 255, 255, 0.05);
                min-height: 0; /* Prevent overflow in flex container */
                display: flex;
            }
            .file-grid {
                display: flex;
                flex-wrap: wrap;
                align-content: flex-start;
                gap: 12px;
                width: 100%;
            }
            .file-grid .file-item {
                min-width: 0;
            }
            .file-grid .file-name {
                max-width: 100%;
                min-width: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .file-item {
                border: 1px solid #333;
                border-radius: 6px;
                padding: 10px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100px;
                justify-content: center;
                gap: 5px;
                flex: 1 1 120px;
                max-width: 200px;
            }
            .file-item:hover {
                background-color: rgba(27, 115, 232, 0.2);
                border-color: #1b73e8;
            }
            
            /* Modal Styles */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 20px;
            }
            .modal-content {
                background-color: #121212;
                border-radius: 10px;
                padding: 20px;
                max-width: 800px;
                margin: 50px auto;
                max-height: 80vh;
                overflow-y: auto;
            }
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .modal-header h3 {
                margin: 0;
                color: #1b73e8;
            }
            .modal-header button {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
            }

            @media (max-width: 640px) {
                body {
                    padding: 8px;
                }
                .breadcrumb {
                    padding: 6px 8px;
                }
                .action-buttons {
                    gap: 6px;
                }
                .action-buttons button {
                    padding: 6px 12px;
                    font-size: 12px;
                }
                .file-grid {
                    gap: 8px;
                }
                .file-item {
                    min-height: 90px;
                    flex: 1 1 96px;
                    max-width: 160px;
                }
            }
            
            /* Textarea */
            textarea {
                width: 100%;
                height: 300px;
                padding: 10px;
                border: 1px solid #333;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                resize: vertical;
                font-family: monospace;
            }
            
            /* Input */
            input[type="text"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #333;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                margin-bottom: 15px;
            }
            
            /* Context Menu */
            .context-menu {
                position: fixed;
                background-color: #121212;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 5px 0;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
                z-index: 10000;
                display: none;
                min-width: 150px;
            }
            .context-menu-item {
                padding: 8px 12px;
                cursor: pointer;
                font-size: 14px;
                color: white;
                transition: background-color 0.2s;
            }
            .context-menu-item:hover {
                background-color: rgba(27, 115, 232, 0.2);
            }
        </style>
    </head>
    <body style="margin: 0; padding: 10px; overflow: hidden; height: 100vh; display: flex; flex-direction: column;">
        <!-- Breadcrumb Navigation -->
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="breadcrumb" id="breadcrumb" style="flex: 1; overflow-x: auto; white-space: nowrap;">
                <span class="breadcrumb-item" data-path="">主页</span>
            </div>
            <button id="sdcard-btn" style="padding: 6px 12px; background-color: #1b73e8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; margin: 0; display: none; white-space: nowrap;">
                内存卡
            </button>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-buttons">
            <button id="back-btn">返回</button>
            <button id="refresh-btn">刷新</button>
            <button id="paste-btn" style="display: none;">粘贴</button>
            <button id="new-file-btn">新建文件</button>
            <button id="new-dir-btn">新建文件夹</button>
        </div>
        
        <!-- File List -->
        <div class="file-list-container" style="flex: 1 1 auto; overflow: auto; max-height: none; min-height: 0; display: flex;">
            <div id="file-manager-list" class="file-grid"></div>
        </div>
        
        <!-- File Editor Modal -->
        <div id="file-editor-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="editor-title">文件编辑器</h3>
                    <button id="close-editor">×</button>
                </div>
                <textarea id="file-content"></textarea>
                <div style="margin: 15px 0; display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="save-file-btn">保存</button>
                    <button id="cancel-edit-btn">取消</button>
                </div>
            </div>
        </div>
        
        <!-- Confirmation Modal -->
        <div id="confirm-modal" class="modal">
            <div class="modal-content">
                <h3 style="margin: 0 0 15px 0;">确认操作</h3>
                <p id="confirm-message"></p>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="confirm-yes">确认</button>
                    <button id="confirm-no">取消</button>
                </div>
            </div>
        </div>
        
        <!-- Input Modal for New Files/Folders -->
        <div id="input-modal" class="modal">
            <div class="modal-content">
                <h3 id="input-title"></h3>
                <input type="text" id="input-field">
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="input-ok">确认</button>
                    <button id="input-cancel">取消</button>
                </div>
            </div>
        </div>
        
        <!-- Context Menu -->
        <div class="context-menu" id="context-menu"></div>
        
        <script>
            // Wait for DOM to fully load before executing scripts
            document.addEventListener('DOMContentLoaded', () => {
                // Modal handlers
                let currentConfirmAction = null;
                let currentInputAction = null;
                
                // File Manager Functionality
                let currentPath = '/home/deck'; // Set default path to /home/deck
                let editingFile = null;
                let contextMenuPath = '';
                
                // DOM Elements
                const breadcrumb = document.getElementById('breadcrumb');
                const fileManagerList = document.getElementById('file-manager-list');
                const backBtn = document.getElementById('back-btn');
                const refreshBtn = document.getElementById('refresh-btn');
                const pasteBtn = document.getElementById('paste-btn');
                const newFileBtn = document.getElementById('new-file-btn');
                const newDirBtn = document.getElementById('new-dir-btn');
                const sdcardBtn = document.getElementById('sdcard-btn');
                let sdcardPath = '';

                const contextMenu = document.getElementById('context-menu');
                
                // Modal Elements
                const fileEditorModal = document.getElementById('file-editor-modal');
                const editorTitle = document.getElementById('editor-title');
                const fileContent = document.getElementById('file-content');
                const closeEditor = document.getElementById('close-editor');
                const saveFileBtn = document.getElementById('save-file-btn');
                const cancelEditBtn = document.getElementById('cancel-edit-btn');
                
                const confirmModal = document.getElementById('confirm-modal');
                const confirmMessage = document.getElementById('confirm-message');
                const confirmYes = document.getElementById('confirm-yes');
                const confirmNo = document.getElementById('confirm-no');
                
                const inputModal = document.getElementById('input-modal');
                const inputTitle = document.getElementById('input-title');
                const inputField = document.getElementById('input-field');
                const inputOk = document.getElementById('input-ok');
                const inputCancel = document.getElementById('input-cancel');

                if (sdcardBtn) {
                    sdcardBtn.addEventListener('click', () => {
                        if (sdcardPath) {
                            navigateTo(sdcardPath);
                        }
                    });
                }
                
                // Context Menu Items
                const contextMenuItems = [
                    { text: '打开', action: 'open' },
                    { text: '下载到本地', action: 'download' },
                    { text: '添加到steam', action: 'add-to-steam' },
                    { text: '复制', action: 'copy' },
                    { text: '删除', action: 'delete' },
                    { text: '重命名', action: 'rename' }
                ]
                
                // Create context menu items
                contextMenuItems.forEach(item => {
                    const menuItem = document.createElement('div');
                    menuItem.className = 'context-menu-item';
                    menuItem.textContent = item.text;
                    menuItem.addEventListener('click', async () => {
                        await handleContextMenuAction(item.action);
                        hideContextMenu();
                    });
                    contextMenu.appendChild(menuItem);
                });
                
                // Context Menu Functions
                let copiedPath = null; // Store copied file/folder path
                
                function showContextMenu(e, path) {
                    e.preventDefault();
                    contextMenuPath = path;
                    contextMenu.style.display = 'block';
                    contextMenu.style.left = e.clientX + 'px';
                    contextMenu.style.top = e.clientY + 'px';
                }
                
                function hideContextMenu() {
                    contextMenu.style.display = 'none';
                    contextMenuPath = '';
                }
                
                async function handleContextMenuAction(action) {
                    switch (action) {
                        case 'open':
                            if (contextMenuPath) {
                                // Check if it's a directory or file
                                const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                                if (fileItem && fileItem.dataset.isDir === 'true') {
                                    navigateTo(contextMenuPath);
                                } else {
                                    openFile(contextMenuPath);
                                }
                            }
                            break;
                        case 'download':
                            if (contextMenuPath) {
                                // Implement download functionality
                                try {
                                    // Check if it's a file (not directory)
                                    const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                                    if (fileItem && fileItem.dataset.isDir !== 'true') {
                                        // Create a download link and click it
                                        const filename = contextMenuPath.split('/').pop();
                                        const downloadUrl = `/api/files/download?path=${encodeURIComponent(contextMenuPath)}`;
                                        const link = document.createElement('a');
                                        link.href = downloadUrl;
                                        link.download = filename;
                                        link.style.display = 'none';
                                        document.body.appendChild(link);
                                        link.click();
                                        document.body.removeChild(link);
                                    } else {
                                        alert('只能下载文件，不能下载文件夹');
                                    }
                                } catch (error) {
                                    console.error('下载出错:', error);
                                    alert('下载失败');
                                }
                            }
                            break;
                        case 'add-to-steam':
                            if (contextMenuPath) {
                                // Implement add to Steam functionality
                                try {
                                    // Check if it's a file (not directory)
                                    const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                                    if (fileItem && fileItem.dataset.isDir !== 'true') {
                                        // Call backend API to add file to Steam
                                        const response = await fetch('/api/files/add-to-steam', {
                                            method: 'POST',
                                            headers: {
                                                'Content-Type': 'application/json'
                                            },
                                            body: JSON.stringify({ path: contextMenuPath })
                                        });
                                        
                                        const result = await response.json();
                                        
                                        if (result.status === 'success') {
                                            alert(result.message || '文件已添加到Steam库');
                                        } else {
                                            alert('添加到Steam失败: ' + result.message);
                                        }
                                    } else {
                                        alert('只能将文件添加到Steam库，不能添加文件夹');
                                    }
                                } catch (error) {
                                    console.error('添加到Steam出错:', error);
                                    alert('添加到Steam失败: ' + error.message);
                                }
                            }
                            break;
                        case 'copy':
                            if (contextMenuPath) {
                                await copyPath(contextMenuPath);
                            }
                            break;
                        case 'paste':
                            await pastePath(currentPath);
                            break;
                        case 'delete':
                            if (contextMenuPath) {
                                // Save the path before showing confirm modal (which hides context menu)
                                const pathToDelete = contextMenuPath;
                                showConfirmModal('确定要删除此项目吗？', async () => {
                                    await deletePath(pathToDelete);
                                });
                            }
                            break;
                        case 'rename':
                            if (contextMenuPath) {
                                // Implement rename functionality
                                const oldName = contextMenuPath.split('/').pop();
                                showInputModal('重命名', '请输入新名称', (newName) => {
                                    // Implement rename API call here
                                    alert('重命名功能将在后续版本中实现');
                                });
                            }
                            break;
                    }
                }
                
                // Hide context menu when clicking elsewhere
                document.addEventListener('click', hideContextMenu);
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape') {
                        hideContextMenu();
                    }
                });
                
                // Modal functions
                function showConfirmModal(message, action) {
                    confirmMessage.textContent = message;
                    currentConfirmAction = action;
                    confirmModal.style.display = 'block';
                }
                
                function hideConfirmModal() {
                    confirmModal.style.display = 'none';
                    currentConfirmAction = null;
                }
                
                function showInputModal(title, placeholder, action) {
                    inputTitle.textContent = title;
                    inputField.placeholder = placeholder;
                    inputField.value = '';
                    currentInputAction = action;
                    inputModal.style.display = 'block';
                    inputField.focus();
                }
                
                function hideInputModal() {
                    inputModal.style.display = 'none';
                    currentInputAction = null;
                }
                
                function showFileEditor(title, content, filePath) {
                    editorTitle.textContent = title;
                    fileContent.value = content;
                    editingFile = filePath;
                    fileEditorModal.style.display = 'block';
                    fileContent.focus();
                }
                
                function hideFileEditor() {
                    fileEditorModal.style.display = 'none';
                    editingFile = null;
                }
                
                // Event Listeners for Modals
                closeEditor.addEventListener('click', hideFileEditor);
                cancelEditBtn.addEventListener('click', hideFileEditor);
                
                confirmYes.addEventListener('click', async () => {
                    if (currentConfirmAction) {
                        await currentConfirmAction();
                    }
                    hideConfirmModal();
                });
                
                confirmNo.addEventListener('click', hideConfirmModal);
                
                inputOk.addEventListener('click', () => {
                    if (currentInputAction) {
                        currentInputAction(inputField.value);
                    }
                    hideInputModal();
                });
                
                inputCancel.addEventListener('click', hideInputModal);
                
                // Close modals when clicking outside
                window.addEventListener('click', (e) => {
                    if (e.target.classList.contains('modal')) {
                        hideConfirmModal();
                        hideInputModal();
                        hideFileEditor();
                    }
                });
                
                // Update breadcrumb
                function updateBreadcrumb(path) {
                    breadcrumb.innerHTML = '';
                    
                    // Split the path and filter out empty parts
                    const pathParts = path.split('/').filter(Boolean);
                    let currentBreadcrumbPath = '';
                    
                    // Process path parts
                    for (let index = 0; index < pathParts.length; index++) {
                        const part = pathParts[index];
                        
                        // Add separator if not the first item
                        if (index > 0) {
                            const separator = document.createElement('span');
                            separator.textContent = ' > ';
                            separator.style.color = '#888';
                            separator.style.marginRight = '8px';
                            breadcrumb.appendChild(separator);
                        }
                        
                        currentBreadcrumbPath += `/${part}`;
                        
                        const item = document.createElement('span');
                        item.className = 'breadcrumb-item';
                        item.textContent = part;
                        item.dataset.path = currentBreadcrumbPath.startsWith('/') ? currentBreadcrumbPath : `/${currentBreadcrumbPath}`;
                        item.style.marginRight = '8px';
                        item.style.cursor = 'pointer';
                        item.addEventListener('click', () => {
                            navigateTo(item.dataset.path);
                        });
                        breadcrumb.appendChild(item);
                    }
                }

                // Update SD card button visibility and path
                async function updateSdcardButton() {
                    if (!sdcardBtn) return;
                    sdcardBtn.style.display = 'none';
                    sdcardBtn.disabled = true;
                    sdcardPath = '';
                    
                    try {
                        const response = await fetch('/api/system/sdcard');
                        if (!response.ok) return;
                        const data = await response.json();
                        
                        if (data.status === 'success' && data.mounted && data.path) {
                            sdcardPath = data.path;
                            sdcardBtn.style.display = 'inline-block';
                            sdcardBtn.disabled = false;
                        }
                    } catch (error) {
                        console.error('检测内存卡失败:', error);
                    }
                }
                
                // Format file size
                function formatSize(bytes) {
                    if (bytes === 0) return '0 B';
                    const k = 1024;
                    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                }
                
                // Format date
                function formatDate(timestamp) {
                    return new Date(timestamp * 1000).toLocaleString();
                }
                
                // Get file icon based on file extension
                function getFileIcon(filename, isDir) {
                    if (isDir) {
                        return '📁';
                    }
                    
                    // Get file extension
                    const ext = filename.split('.').pop().toLowerCase();
                    
                    // Image files
                    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'].includes(ext)) {
                        return '🖼️';
                    }
                    
                    // Video files
                    if (['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'].includes(ext)) {
                        return '🎬';
                    }
                    
                    // Audio files
                    if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma'].includes(ext)) {
                        return '🎵';
                    }
                    
                    // Compressed files
                    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(ext)) {
                        return '📦';
                    }
                    
                    // Document files
                    if (['txt', 'pdf', 'doc', 'docx', 'odt', 'rtf'].includes(ext)) {
                        return '📄';
                    }
                    
                    // Spreadsheet files
                    if (['xls', 'xlsx', 'ods', 'csv'].includes(ext)) {
                        return '📊';
                    }
                    
                    // Presentation files
                    if (['ppt', 'pptx', 'odp'].includes(ext)) {
                        return '📋';
                    }
                    
                    // Code files
                    if (['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'php', 'java', 'c', 'cpp', 'h', 'hpp', 'go', 'rust'].includes(ext)) {
                        return '💻';
                    }
                    
                    // Executable files
                    if (['exe', 'msi', 'sh', 'bat', 'app', 'dmg', 'deb', 'rpm'].includes(ext)) {
                        return '⚙️';
                    }
                    
                    // Default file icon
                    return '📄';
                }
                
                // Render file list
                async function renderFileList(path) {
                    try {
                        const response = await fetch('/api/files/list', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            fileManagerList.innerHTML = '';
                            
                            data.files.forEach(file => {
                                const fileItem = document.createElement('div');
                                fileItem.className = 'file-item';
                                fileItem.dataset.path = file.path;
                                fileItem.dataset.isDir = file.is_dir;
                                
                                fileItem.addEventListener('click', () => {
                                    // 切换文件选中状态
                                    if (fileItem.classList.contains('selected')) {
                                        // 取消选中
                                        fileItem.classList.remove('selected');
                                        const index = selectedFileManagerFiles.indexOf(file.path);
                                        if (index > -1) {
                                            selectedFileManagerFiles.splice(index, 1);
                                        }
                                    } else {
                                        // 取消其他选中项
                                        document.querySelectorAll('.file-item.selected').forEach(item => {
                                            item.classList.remove('selected');
                                        });
                                        // 选中当前文件
                                        fileItem.classList.add('selected');
                                        selectedFileManagerFiles = [file.path];
                                    }
                                });
                                
                                // 双击事件打开文件或进入目录
                                fileItem.addEventListener('dblclick', () => {
                                    if (file.is_dir) {
                                        navigateTo(file.path);
                                    } else {
                                        openFile(file.path);
                                    }
                                });
                                
                                fileItem.addEventListener('contextmenu', (e) => {
                                    e.preventDefault();
                                    showContextMenu(e, file.path);
                                });
                                
                                // File Icon
                                const icon = document.createElement('div');
                                icon.textContent = getFileIcon(file.name, file.is_dir);
                                icon.style.fontSize = '24px';
                                
                                // File Name
                                const fileName = document.createElement('div');
                                fileName.className = 'file-name';
                                fileName.textContent = file.name;
                                fileName.style.fontSize = '12px';
                                fileName.style.textAlign = 'center';
                                fileName.style.overflow = 'hidden';
                                fileName.style.textOverflow = 'ellipsis';
                                fileName.style.width = '100%';
                                fileName.style.whiteSpace = 'nowrap';
                                fileName.style.maxWidth = '100%';
                                fileName.style.minWidth = '0';
                                
                                // File Details
                                const fileDetails = document.createElement('div');
                                fileDetails.style.fontSize = '10px';
                                fileDetails.style.color = '#888';
                                fileDetails.style.textAlign = 'center';
                                
                                if (file.is_dir) {
                                    fileDetails.textContent = '文件夹';
                                } else {
                                    fileDetails.innerHTML = `${formatSize(file.size)}<br>${formatDate(file.mtime)}`;
                                }
                                
                                fileItem.appendChild(icon);
                                fileItem.appendChild(fileName);
                                fileItem.appendChild(fileDetails);
                                
                                fileManagerList.appendChild(fileItem);
                            });
                            
                            currentPath = data.current_path;
                            updateBreadcrumb(data.current_path);
                        } else {
                            alert('获取文件列表失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('获取文件列表出错:', error);
                        alert('获取文件列表出错');
                    }
                }
                
                // Navigate to directory
                async function navigateTo(path) {
                    await renderFileList(path);
                }
                
                // Open file for editing
                async function openFile(filePath) {
                    try {
                        const response = await fetch('/api/files/read', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path: filePath })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            showFileEditor(`编辑文件: ${filePath.split('/').pop()}`, data.content, filePath);
                        } else {
                            alert('打开文件失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('打开文件出错:', error);
                        alert('打开文件出错');
                    }
                }
                
                // Save file
                async function saveFile(content, filePath) {
                    try {
                        const response = await fetch('/api/files/write', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path: filePath, content })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            alert('文件保存成功');
                            hideFileEditor();
                            await renderFileList(currentPath);
                        } else {
                            alert('保存文件失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('保存文件出错:', error);
                        alert('保存文件出错');
                    }
                }
                
                // Create new file
                async function createFile(fileName) {
                    if (!fileName.trim()) {
                        alert('文件名不能为空');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/files/create', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path: currentPath, filename: fileName })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            await renderFileList(currentPath);
                            alert('文件创建成功');
                        } else {
                            alert('创建文件失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('创建文件出错:', error);
                        alert('创建文件出错');
                    }
                }
                
                // Create new directory
                async function createDirectory(dirName) {
                    if (!dirName.trim()) {
                        alert('文件夹名不能为空');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/files/create-dir', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path: currentPath, dirname: dirName })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            await renderFileList(currentPath);
                            alert('文件夹创建成功');
                        } else {
                            alert('创建文件夹失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('创建文件夹出错:', error);
                        alert('创建文件夹出错');
                    }
                }
                
                // Delete file or directory
                async function deletePath(path) {
                    try {
                        // Ensure path is not empty
                        if (!path) {
                            alert('删除失败: 路径不能为空');
                            return;
                        }
                        
                        const response = await fetch('/api/files/delete', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ path })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            await renderFileList(currentPath);
                            alert('删除成功');
                        } else {
                            alert('删除失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('删除出错:', error);
                        alert('删除出错: ' + error.message);
                    }
                }
                
                // Copy file or directory path
                async function copyPath(path) {
                    try {
                        if (!path) {
                            alert('复制失败: 路径不能为空');
                            return;
                        }
                        
                        copiedPath = path;
                        alert('复制成功');
                        // Show paste button
                        pasteBtn.style.display = 'block';
                    } catch (error) {
                        console.error('复制出错:', error);
                        alert('复制出错');
                    }
                }
                
                // Paste file or directory
                async function pastePath(destPath) {
                    try {
                        if (!copiedPath) {
                            alert('粘贴失败: 没有要粘贴的内容');
                            return;
                        }
                        
                        if (!destPath) {
                            alert('粘贴失败: 目标路径不能为空');
                            return;
                        }
                        
                        // Get filename from copied path
                        const filename = copiedPath.split('/').pop();
                        const targetPath = destPath + '/' + filename;
                        
                        const response = await fetch('/api/files/copy', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ source: copiedPath, destination: targetPath })
                        });
                        
                        const data = await response.json();
                        if (data.status === 'success') {
                            await renderFileList(currentPath);
                            alert('粘贴成功');
                            // Hide paste button after successful paste
                            copiedPath = null;
                            updatePasteButtonVisibility();
                        } else {
                            alert('粘贴失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('粘贴出错:', error);
                        alert('粘贴出错: ' + error.message);
                    }
                }
                
                // Update paste button visibility
                function updatePasteButtonVisibility() {
                    if (copiedPath) {
                        pasteBtn.style.display = 'block';
                    } else {
                        pasteBtn.style.display = 'none';
                    }
                }
                
                // Event listeners for file manager buttons
                backBtn.addEventListener('click', () => {
                    // Get parent directory path
                    const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/'));
                    // If we're at the root, stay at root
                    const newPath = parentPath || '/';
                    renderFileList(newPath);
                });
                
                refreshBtn.addEventListener('click', () => {
                    updateSdcardButton();
                    renderFileList(currentPath);
                });
                
                pasteBtn.addEventListener('click', async () => {
                    await pastePath(currentPath);
                });
                
                newFileBtn.addEventListener('click', () => {
                    showInputModal('新建文件', '请输入文件名', createFile);
                });
                
                newDirBtn.addEventListener('click', () => {
                    showInputModal('新建文件夹', '请输入文件夹名', createDirectory);
                });
                
                deleteBtn.addEventListener('click', () => {
                    // For now, delete functionality requires selecting files
                    // This can be enhanced with multi-select in the future
                    alert('请直接点击右键或双击文件进行操作');
                });
                
                saveFileBtn.addEventListener('click', () => {
                    if (editingFile) {
                        saveFile(fileContent.value, editingFile);
                    }
                });
                
                // Initialize paste button visibility
                updatePasteButtonVisibility();
                
                // Initial render
                updateSdcardButton();
                renderFileList(currentPath);
            });
        </script>
    </body>
    </html>
    """


async def handle_file_manager_index(request):
    """Handle root URL request for file manager server"""
    return web.Response(text=get_file_manager_html(), content_type='text/html')


async def handle_index(request):
    """Handle root URL request, return HTML upload page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>decky-send 文件上传</title>
        <style>
            :root {
                --bg: #0f1216;
                --bg-elev: #141a20;
                --panel: rgba(255, 255, 255, 0.06);
                --panel-strong: rgba(255, 255, 255, 0.12);
                --border: rgba(255, 255, 255, 0.12);
                --text: #e7edf3;
                --muted: #9aa6b2;
                --accent: #4db6ac;
                --accent-strong: #2fa69a;
                --accent-soft: rgba(77, 182, 172, 0.18);
                --danger: #ff6b6b;
                --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
            }
            * {
                box-sizing: border-box;
            }
            body {
                font-family: "IBM Plex Sans", "Noto Sans", "Ubuntu", "Segoe UI", sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 24px;
                text-align: center;
                background-color: var(--bg);
                background-image:
                    radial-gradient(900px 500px at 20% -10%, rgba(77, 182, 172, 0.16), transparent 60%),
                    radial-gradient(800px 400px at 120% 20%, rgba(94, 156, 255, 0.12), transparent 60%),
                    linear-gradient(180deg, #0f1216 0%, #10161b 100%);
                color: var(--text);
            }
            h1 {
                color: var(--text);
                font-weight: 700;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
            }
            p {
                color: var(--muted);
                margin-top: 0;
            }
            
            /* Tab styles */
            .tab-container {
                margin: 20px 0;
            }
            .tab-buttons {
                display: flex;
                justify-content: center;
                gap: 6px;
                margin-bottom: 18px;
                padding: 6px;
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 999px;
                box-shadow: var(--shadow);
            }
            .tab-button {
                background: transparent;
                border: 1px solid transparent;
                color: var(--muted);
                padding: 10px 16px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                border-radius: 999px;
                margin: 0;
            }
            .tab-button.active {
                color: var(--text);
                background: var(--accent-soft);
                border-color: rgba(77, 182, 172, 0.45);
                box-shadow: inset 0 0 0 1px rgba(77, 182, 172, 0.15);
            }
            .tab-button:hover {
                color: var(--text);
                background-color: rgba(255, 255, 255, 0.06);
            }
            
            .tab-panel {
                display: none;
                animation: fadeUp 200ms ease;
            }
            .tab-panel.active {
                display: block;
            }
            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(6px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .upload-area {
                border: 1.5px dashed var(--border);
                border-radius: 16px;
                padding: 36px;
                margin: 18px 0;
                cursor: pointer;
                background: var(--panel);
                box-shadow: var(--shadow);
                transition: all 0.25s ease;
            }
            .upload-area:hover {
                border-color: rgba(77, 182, 172, 0.6);
                background-color: rgba(77, 182, 172, 0.08);
            }
            .upload-area.dragover {
                background-color: rgba(77, 182, 172, 0.16);
                border-color: var(--accent);
            }
            #file-input {
                display: none;
            }
            button {
                background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
                color: #0c1416;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 11px 20px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 14px;
                margin: 8px;
                box-shadow: 0 8px 18px rgba(47, 166, 154, 0.25);
                transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
            }
            button:hover {
                filter: brightness(1.05);
                box-shadow: 0 10px 24px rgba(47, 166, 154, 0.3);
            }
            button:active {
                transform: translateY(1px);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                box-shadow: none;
            }
            textarea,
            input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 1px solid var(--border);
                border-radius: 10px;
                background-color: var(--panel);
                color: var(--text);
                font-size: 14px;
            }
            .file-list {
                margin: 18px 0;
                text-align: left;
            }
            .file-grid .file-item {
                min-width: 0;
            }
            .file-grid .file-name {
                max-width: 100%;
                min-width: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .file-item {
                background-color: var(--panel);
                border: 1px solid var(--border);
                padding: 10px;
                margin: 6px 0;
                border-radius: 10px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .file-item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .file-item-info {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                color: var(--text);
            }
            .file-item-progress {
                width: 100%;
                display: none;
            }
            .file-item-progress.active {
                display: block;
            }
            .file-progress-bar {
                width: 100%;
                height: 6px;
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 4px;
            }
            .file-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--accent) 0%, #5fa6ff 100%);
                border-radius: 3px;
                width: 0%;
                transition: width 0.2s ease;
            }
            .file-progress-text {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                color: var(--muted);
            }
            .file-progress-text .speed {
                color: var(--accent);
            }
            .cancel-btn {
                background-color: var(--danger);
                color: #1a0b0b;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 5px 10px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 12px;
                margin: 0;
                transition: filter 0.2s ease;
                flex-shrink: 0;
                box-shadow: none;
            }
            .cancel-btn:hover {
                filter: brightness(0.95);
            }
            .breadcrumb-bar {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 12px;
            }
            .breadcrumb {
                color: var(--muted);
            }
            .breadcrumb-item {
                color: var(--text);
            }
            .breadcrumb-item:hover {
                color: var(--accent);
            }
            .action-buttons button {
                background: var(--panel-strong);
                color: var(--text);
                border: 1px solid var(--border);
                box-shadow: none;
                padding: 8px 14px;
                font-size: 13px;
                margin: 0;
            }
            .action-buttons button:hover {
                border-color: rgba(77, 182, 172, 0.5);
            }
            .file-list-container {
                border: 1px solid var(--border);
                border-radius: 12px;
                background-color: var(--panel);
            }
            #sdcard-btn {
                background: var(--panel-strong);
                color: var(--text);
                border: 1px solid var(--border);
                box-shadow: none;
            }
            .modal {
                backdrop-filter: blur(4px);
            }
            .modal-content {
                background-color: var(--bg-elev);
                border: 1px solid var(--border);
                box-shadow: var(--shadow);
                border-radius: 14px;
            }

            @media (max-width: 640px) {
                body {
                    max-width: 100%;
                    padding: 16px;
                }
                .tab-buttons {
                    flex-wrap: wrap;
                    border-radius: 18px;
                }
                .tab-button {
                    padding: 8px 12px;
                    font-size: 13px;
                }
                .upload-area {
                    padding: 26px 18px;
                }
                button {
                    padding: 10px 16px;
                    font-size: 13px;
                }
                .file-grid {
                    gap: 8px;
                }
                #file-manager .file-grid .file-item {
                    min-height: 90px;
                    flex: 1 1 96px;
                    max-width: 160px;
                }
                #file-manager .breadcrumb-bar {
                    padding: 6px 8px;
                }
            }
        </style>
    </head>
    <body>
        <h1>decky-send</h1>
        <p>将文件或文本上传到 Steam Deck</p>
        
        <!-- Tab Container -->
        <div class="tab-container">
            <!-- Tab Buttons -->
            <div class="tab-buttons">
                <button class="tab-button active" data-tab="file">文件上传</button>
                <button class="tab-button" data-tab="text">文本传输</button>
                <button class="tab-button" data-tab="file-manager">文件管理</button>
            </div>
            
            <!-- File Upload Tab -->
            <div id="file" class="tab-panel active">
                <div class="upload-area" id="upload-area">
                    <p>点击或拖拽文件到此处</p>
                    <input type="file" id="file-input" multiple accept="*/*" capture="filesystem">
                </div>
                
                <div class="file-list" id="file-list"></div>
                
                <div style="margin: 10px 0;">
                    <button id="upload-btn">开始上传文件</button>
                </div>
            </div>
            
            <!-- Text Transfer Tab -->
            <div id="text" class="tab-panel">
                <div style="margin: 15px 0;">
                    <textarea 
                        id="text-input" 
                        placeholder="在此输入要传输的文本..." 
                        rows="6" 
                        style="width: 100%; resize: vertical;"></textarea>
                </div>
                
                <div style="margin: 10px 0;">
                    <button id="send-text-btn" style="width: 100%; margin: 0;">
                        发送文本
                    </button>
                </div>
            </div>
            
            <!-- File Manager Tab -->
            <div id="file-manager" class="tab-panel">
                <!-- File Manager UI -->
                <div id="file-manager-wrap" style="margin: 15px 0; display: flex; flex-direction: column; height: 100%; min-height: 0;">
                    <!-- Breadcrumb Navigation -->
                    <div class="breadcrumb-bar" style="margin: 10px 0; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                        <div class="breadcrumb" id="breadcrumb" style="flex: 1; overflow-x: auto; white-space: nowrap;"></div>
                        <button id="sdcard-btn" style="padding: 6px 12px; font-size: 12px; margin: 0; display: none; white-space: nowrap;">
                            内存卡
                        </button>
                    </div>
                    
                    <!-- Action Buttons -->
            <div class="action-buttons" style="display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap;">
                <button id="back-btn" style="margin: 0;">
                    返回
                </button>
                <button id="refresh-btn" style="margin: 0;">
                    刷新
                </button>
                <button id="new-file-btn" style="margin: 0;">
                    新建文件
                </button>
                <button id="new-dir-btn" style="margin: 0;">
                    新建文件夹
                </button>
                <button id="paste-btn" style="margin: 0; display: none;">
                    粘贴
                </button>
                <button id="copy-btn" style="margin: 0;">
                    复制
                </button>
            </div>
                    
                    <!-- File List -->
                    <div class="file-list-container" style="padding: 10px; flex: 1 1 auto; overflow: auto; min-height: 0; display: flex;">
                        <div id="file-manager-list" class="file-grid" style="display: flex; flex-wrap: wrap; align-content: flex-start; gap: 12px; width: 100%;"></div>
                    </div>
                </div>
                
                <!-- File Editor Modal -->
                <div id="file-editor-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 800px; margin: 50px auto; max-height: 80vh; overflow-y: auto;">
                        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 id="editor-title" style="margin: 0; color: var(--text);">文件编辑器</h3>
                            <button id="close-editor" style="background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; box-shadow: none;">×</button>
                        </div>
                        <textarea id="file-content" style="width: 100%; height: 300px; padding: 10px; border: 1px solid var(--border); border-radius: 10px; background-color: var(--panel); color: var(--text); font-size: 14px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, \"Liberation Mono\", monospace;"></textarea>
                        <div style="margin: 15px 0; display: flex; gap: 10px; justify-content: flex-end;">
                            <button id="save-file-btn" style="padding: 10px 20px; margin: 0;">
                                保存
                            </button>
                            <button id="cancel-edit-btn" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                                取消
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Confirmation Modal -->
                <div id="confirm-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 400px; margin: 100px auto;">
                        <h3 style="margin: 0 0 15px 0; color: var(--text);">确认操作</h3>
                        <p id="confirm-message" style="color: var(--muted); margin: 0 0 20px 0;"></p>
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button id="confirm-yes" style="padding: 10px 20px; margin: 0;">
                                确认
                            </button>
                            <button id="confirm-no" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                                取消
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Input Modal for New Files/Folders -->
                <div id="input-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 400px; margin: 100px auto;">
                        <h3 id="input-title" style="margin: 0 0 15px 0; color: var(--text);"></h3>
                        <input type="text" id="input-field" style="width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 10px; background-color: var(--panel); color: var(--text); font-size: 14px; margin-bottom: 15px;">
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button id="input-ok" style="padding: 10px 20px; margin: 0;">
                                确认
                            </button>
                            <button id="input-cancel" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Wait for DOM to fully load before executing scripts
            document.addEventListener('DOMContentLoaded', () => {
                // Tab functionality
                const tabButtons = document.querySelectorAll('.tab-button');
                const tabPanels = document.querySelectorAll('.tab-panel');
                
                tabButtons.forEach(button => {
                    button.addEventListener('click', () => {
                        const targetTab = button.getAttribute('data-tab');
                        
                        // Remove active class from all buttons and panels
                        tabButtons.forEach(btn => btn.classList.remove('active'));
                        tabPanels.forEach(panel => panel.classList.remove('active'));
                        
                        // Add active class to clicked button and corresponding panel
                        button.classList.add('active');
                        document.getElementById(targetTab).classList.add('active');
                        
                        // Render file list when file manager tab is activated
                        if (targetTab === 'file-manager') {
                            // Check if fileManagerList exists before calling renderFileList
                            if (typeof renderFileList === 'function') {
                                resizeFileManagerPanel();
                                updateSdcardButton();
                                renderFileList(currentPath);
                            }
                        }
                    });
                });

                window.addEventListener('resize', () => {
                    const panel = document.getElementById('file-manager');
                    if (panel && panel.classList.contains('active')) {
                        resizeFileManagerPanel();
                    }
                });
            
            // 文件上传功能
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const fileList = document.getElementById('file-list');
            const uploadBtn = document.getElementById('upload-btn');
            
            let selectedFiles = [];
            
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                addFiles(e.dataTransfer.files);
            });
            
            fileInput.addEventListener('change', (e) => {
                addFiles(e.target.files);
            });
            
            function addFiles(files) {
                for (let file of files) {
                    selectedFiles.push(file);
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    
                    // File header (info + cancel button)
                    const fileHeader = document.createElement('div');
                    fileHeader.className = 'file-item-header';
                    
                    // Create file info element
                    const fileInfo = document.createElement('span');
                    fileInfo.className = 'file-item-info';
                    fileInfo.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
                    
                    // Create cancel button
                    const cancelBtn = document.createElement('button');
                    cancelBtn.className = 'cancel-btn';
                    cancelBtn.textContent = '取消';
                    cancelBtn.onclick = () => cancelFile(file);
                    
                    fileHeader.appendChild(fileInfo);
                    fileHeader.appendChild(cancelBtn);
                    
                    // Progress section (hidden by default, shown during upload)
                    const progressSection = document.createElement('div');
                    progressSection.className = 'file-item-progress';
                    progressSection.id = `progress-section-${file.name.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
                    
                    const progressBar = document.createElement('div');
                    progressBar.className = 'file-progress-bar';
                    
                    const progressFill = document.createElement('div');
                    progressFill.className = 'file-progress-fill';
                    progressFill.id = `progress-fill-${file.name.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
                    
                    progressBar.appendChild(progressFill);
                    
                    const progressText = document.createElement('div');
                    progressText.className = 'file-progress-text';
                    progressText.innerHTML = `
                        <span id="progress-percent-${file.name.replace(/[^a-zA-Z0-9_-]/g, '_')}">0%</span>
                        <span class="speed" id="progress-speed-${file.name.replace(/[^a-zA-Z0-9_-]/g, '_')}">0 KB/s</span>
                    `;
                    
                    progressSection.appendChild(progressBar);
                    progressSection.appendChild(progressText);
                    
                    // Add elements to file item
                    fileItem.appendChild(fileHeader);
                    fileItem.appendChild(progressSection);
                    fileItem.dataset.filename = file.name;
                    
                    fileList.appendChild(fileItem);
                }
            }
            
            function cancelFile(file) {
                // Find the file index in selectedFiles array
                const index = selectedFiles.findIndex(f => f.name === file.name && f.size === file.size);
                if (index > -1) {
                    // Remove file from array
                    selectedFiles.splice(index, 1);
                    
                    // Remove corresponding DOM element
                    const fileItems = document.querySelectorAll('.file-item');
                    fileItems.forEach(item => {
                        if (item.dataset.filename === file.name) {
                            item.remove();
                        }
                    });
                }
            }
            
            // 更新文件列表内的进度条
            function updateFileProgress(fileName, progress, speed, status = 'uploading') {
                const safeFileName = fileName.replace(/[^a-zA-Z0-9_-]/g, '_');
                const progressSection = document.getElementById(`progress-section-${safeFileName}`);
                const progressFill = document.getElementById(`progress-fill-${safeFileName}`);
                const progressPercent = document.getElementById(`progress-percent-${safeFileName}`);
                const progressSpeed = document.getElementById(`progress-speed-${safeFileName}`);
                
                console.log(`updateFileProgress调用: ${fileName}`, {
                    progressSection: !!progressSection,
                    progressFill: !!progressFill,
                    progressPercent: !!progressPercent,
                    progressSpeed: !!progressSpeed,
                    progress: progress,
                    speed: speed,
                    status: status
                });
                
                if (progressSection) {
                    progressSection.classList.add('active');
                }
                
                if (progressFill) {
                    progressFill.style.width = `${progress}%`;
                    
                    // 根据状态改变颜色
                    if (status === 'success') {
                        progressFill.style.background = 'linear-gradient(90deg, #34a853 0%, #4CAF50 100%)';
                    } else if (status === 'error') {
                        progressFill.style.background = 'linear-gradient(90deg, #ea4335 0%, #ff6b6b 100%)';
                    } else {
                        progressFill.style.background = 'linear-gradient(90deg, var(--accent) 0%, #5fa6ff 100%)';
                    }
                }
                
                if (progressPercent) {
                    if (status === 'success') {
                        progressPercent.textContent = '完成';
                    } else if (status === 'error') {
                        progressPercent.textContent = '失败';
                    } else {
                        progressPercent.textContent = `${progress}%`;
                    }
                }
                
                if (progressSpeed) {
                    if (status === 'success' || status === 'error') {
                        progressSpeed.textContent = '';
                    } else {
                        progressSpeed.textContent = `${speed} KB/s`;
                    }
                }
            }
            
            uploadBtn.addEventListener('click', () => {
                if (selectedFiles.length === 0) {
                    alert('请先选择文件');
                    return;
                }
                
                let uploadedFiles = 0;
                const totalFiles = selectedFiles.length;
                
                selectedFiles.forEach(file => {
                    // 显示该文件的进度条
                    const safeFileName = file.name.replace(/[^a-zA-Z0-9_-]/g, '_');
                    const progressSection = document.getElementById(`progress-section-${safeFileName}`);
                    
                    console.log(`准备上传文件: ${file.name}, 进度条元素:`, progressSection);
                    
                    if (progressSection) {
                        progressSection.classList.add('active');
                        console.log(`已激活进度条显示: ${file.name}`);
                    } else {
                        console.error(`找不到进度条元素: progress-section-${safeFileName}`);
                    }
                    
                    // 使用XMLHttpRequest上传文件
                    const xhr = new XMLHttpRequest();
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // 记录时间和字节数用于计算速度
                    let lastUpdateTime = Date.now();
                    let lastUploadedBytes = 0;
                    
                    // 监听上传进度
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            const currentTime = Date.now();
                            const timeDiff = (currentTime - lastUpdateTime) / 1000;
                            const bytesDiff = e.loaded - lastUploadedBytes;
                            
                            // 限制更新频率
                            if (timeDiff >= 0.2 || e.loaded === e.total) {
                                const progress = Math.min(100, Math.round((e.loaded / e.total) * 100));
                                const speed = Math.round((bytesDiff / 1024) / timeDiff);
                                
                                console.log(`更新进度: ${file.name} - ${progress}% (${speed} KB/s)`);
                                updateFileProgress(file.name, progress, speed);
                                
                                lastUpdateTime = currentTime;
                                lastUploadedBytes = e.loaded;
                            }
                        }
                    });
                    
                    // 监听上传完成
                    xhr.addEventListener('load', () => {
                        uploadedFiles++;
                        
                        if (xhr.status === 200) {
                            console.log(`${file.name} 上传成功`);
                            updateFileProgress(file.name, 100, 0, 'success');
                        } else {
                            console.error(`${file.name} 上传失败`);
                            updateFileProgress(file.name, 100, 0, 'error');
                        }
                        
                        // 检查是否所有文件都上传完成
                        if (uploadedFiles === totalFiles) {
                            setTimeout(() => {
                                alert('所有文件上传完成');
                                // 延迟后清空文件列表
                                setTimeout(() => {
                                    selectedFiles = [];
                                    fileList.innerHTML = '';
                                }, 2000);
                            }, 500);
                        }
                    });
                    
                    // 监听上传错误
                    xhr.addEventListener('error', () => {
                        uploadedFiles++;
                        console.error(`${file.name} 上传出错`);
                        updateFileProgress(file.name, 0, 0, 'error');
                        
                        if (uploadedFiles === totalFiles) {
                            setTimeout(() => {
                                alert('部分文件上传失败');
                            }, 500);
                        }
                    });
                    
                    // 设置超时（10分钟）
                    xhr.timeout = 600000;
                    xhr.addEventListener('timeout', () => {
                        uploadedFiles++;
                        console.error(`${file.name} 上传超时`);
                        updateFileProgress(file.name, 0, 0, 'error');
                        
                        if (uploadedFiles === totalFiles) {
                            setTimeout(() => {
                                alert('部分文件上传超时');
                            }, 500);
                        }
                    });
                    
                    // 发送请求
                    xhr.open('POST', '/upload');
                    xhr.send(formData);
                });
            });
            
            // 文本传输功能
            const textInput = document.getElementById('text-input');
            const sendTextBtn = document.getElementById('send-text-btn');
            
            sendTextBtn.addEventListener('click', async () => {
                const text = textInput.value.trim();
                
                if (!text) {
                    alert('请先输入要传输的文本');
                    return;
                }
                
                try {
                    const response = await fetch('/upload-text', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ text: text })
                    });
                    
                    if (response.ok) {
                        alert('文本传输成功');
                        textInput.value = '';
                    } else {
                        alert('文本传输失败');
                    }
                } catch (error) {
                    console.error('文本传输出错:', error);
                    alert('文本传输出错');
                }
            });
            
            // Modal handlers
            let currentConfirmAction = null;
            let currentInputAction = null;
            
            // File Manager Functionality
            let currentPath = '/home/deck'; // Set default path to /home/deck
            let selectedFileManagerFiles = [];
            let editingFile = null;
            let contextMenuPath = '';
            
            // DOM Elements
            const breadcrumb = document.getElementById('breadcrumb');
            const fileManagerList = document.getElementById('file-manager-list');
            const backBtn = document.getElementById('back-btn');
            const refreshBtn = document.getElementById('refresh-btn');
            const pasteBtn = document.getElementById('paste-btn');
            const newFileBtn = document.getElementById('new-file-btn');
            const newDirBtn = document.getElementById('new-dir-btn');
            const deleteBtn = document.getElementById('delete-btn');
            const sdcardBtn = document.getElementById('sdcard-btn');
            let sdcardPath = '';
            
            // Modal Elements
            const fileEditorModal = document.getElementById('file-editor-modal');
            const editorTitle = document.getElementById('editor-title');
            const fileContent = document.getElementById('file-content');
            const closeEditor = document.getElementById('close-editor');
            const saveFileBtn = document.getElementById('save-file-btn');
            const cancelEditBtn = document.getElementById('cancel-edit-btn');
            
            const confirmModal = document.getElementById('confirm-modal');
            const confirmMessage = document.getElementById('confirm-message');
            const confirmYes = document.getElementById('confirm-yes');
            const confirmNo = document.getElementById('confirm-no');
            
            const inputModal = document.getElementById('input-modal');
            const inputTitle = document.getElementById('input-title');
            const inputField = document.getElementById('input-field');
            const inputOk = document.getElementById('input-ok');
            const inputCancel = document.getElementById('input-cancel');

            if (sdcardBtn) {
                sdcardBtn.addEventListener('click', () => {
                    if (sdcardPath) {
                        navigateTo(sdcardPath);
                    }
                });
            }
            
            // Context Menu
            const contextMenu = document.createElement('div');
            contextMenu.style.cssText = `
                position: fixed;
                background-color: var(--bg-elev);
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 5px 0;
                box-shadow: var(--shadow);
                z-index: 10000;
                display: none;
                min-width: 150px;
            `;
            document.body.appendChild(contextMenu);
            
            // Context Menu Items
            const contextMenuItems = [
                { text: '打开', action: 'open' },
                { text: '添加到本地', action: 'download' },
                { text: '添加到steam', action: 'add-to-steam' },
                { text: '复制', action: 'copy' },
                { text: '删除', action: 'delete' },
                { text: '重命名', action: 'rename' }
            ];
            
            contextMenuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.textContent = item.text;
                menuItem.style.cssText = `
                    padding: 8px 12px;
                    cursor: pointer;
                    font-size: 14px;
                    color: var(--text);
                    transition: background-color 0.2s;
                `;
                menuItem.addEventListener('mouseenter', () => {
                    menuItem.style.backgroundColor = 'rgba(77, 182, 172, 0.2)';
                });
                menuItem.addEventListener('mouseleave', () => {
                    menuItem.style.backgroundColor = 'transparent';
                });
                menuItem.addEventListener('click', async () => {
                    await handleContextMenuAction(item.action);
                    hideContextMenu();
                });
                contextMenu.appendChild(menuItem);
            });
            
            // Context Menu Functions
            let copiedPath = null; // Store copied file/folder path
            
            function showContextMenu(e, path) {
                e.preventDefault();
                contextMenuPath = path;
                contextMenu.style.display = 'block';
                contextMenu.style.left = e.clientX + 'px';
                contextMenu.style.top = e.clientY + 'px';
            }
            
            function hideContextMenu() {
                contextMenu.style.display = 'none';
                contextMenuPath = '';
            }
            
            async function handleContextMenuAction(action) {
                switch (action) {
                    case 'open':
                        if (contextMenuPath) {
                            // Check if it's a directory or file
                            const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                            if (fileItem && fileItem.dataset.isDir === 'true') {
                                navigateTo(contextMenuPath);
                            } else {
                                openFile(contextMenuPath);
                            }
                        }
                        break;
                    case 'download':
                        if (contextMenuPath) {
                            // Implement download functionality
                            try {
                                // Check if it's a file (not directory)
                                const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                                if (fileItem && fileItem.dataset.isDir !== 'true') {
                                    // Create a download link and click it
                                    const filename = contextMenuPath.split('/').pop();
                                    const downloadUrl = `/api/files/download?path=${encodeURIComponent(contextMenuPath)}`;
                                    const link = document.createElement('a');
                                    link.href = downloadUrl;
                                    link.download = filename;
                                    link.style.display = 'none';
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                } else {
                                    alert('只能下载文件，不能下载文件夹');
                                }
                            } catch (error) {
                                console.error('下载出错:', error);
                                alert('下载失败');
                            }
                        }
                        break;
                    case 'add-to-steam':
                        if (contextMenuPath) {
                            // Implement add to Steam functionality
                            try {
                                // Check if it's a file (not directory)
                                const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                                if (fileItem && fileItem.dataset.isDir !== 'true') {
                                    // Call backend API to add file to Steam
                                    const response = await fetch('/api/files/add-to-steam', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({ path: contextMenuPath })
                                    });
                                    
                                    const result = await response.json();
                                    
                                    if (result.status === 'success') {
                                        alert(result.message || '文件已添加到Steam库');
                                    } else {
                                        alert('添加到Steam失败: ' + result.message);
                                    }
                                } else {
                                    alert('只能将文件添加到Steam库，不能添加文件夹');
                                }
                            } catch (error) {
                                console.error('添加到Steam出错:', error);
                                alert('添加到Steam失败: ' + error.message);
                            }
                        }
                        break;
                    case 'copy':
                        if (contextMenuPath) {
                            await copyPath(contextMenuPath);
                        }
                        break;
                    case 'paste':
                        await pastePath(currentPath);
                        break;
                    case 'delete':
                        if (contextMenuPath) {
                            // Save the path before showing confirm modal (which hides context menu)
                            const pathToDelete = contextMenuPath;
                            showConfirmModal('确定要删除此项目吗？', async () => {
                                await deletePath(pathToDelete);
                            });
                        }
                        break;
                    case 'rename':
                        if (contextMenuPath) {
                            // Implement rename functionality
                            const oldName = contextMenuPath.split('/').pop();
                            showInputModal('重命名', '请输入新名称', (newName) => {
                                // Implement rename API call here
                                alert('重命名功能将在后续版本中实现');
                            });
                        }
                        break;
                }
            }
            
            // Hide context menu when clicking elsewhere
            document.addEventListener('click', hideContextMenu);
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    hideContextMenu();
                }
            });
            
            function showConfirmModal(message, action) {
                confirmMessage.textContent = message;
                currentConfirmAction = action;
                confirmModal.style.display = 'block';
            }
            
            function hideConfirmModal() {
                confirmModal.style.display = 'none';
                currentConfirmAction = null;
            }
            
            function showInputModal(title, placeholder, action) {
                inputTitle.textContent = title;
                inputField.placeholder = placeholder;
                inputField.value = '';
                currentInputAction = action;
                inputModal.style.display = 'block';
                inputField.focus();
            }
            
            function hideInputModal() {
                inputModal.style.display = 'none';
                currentInputAction = null;
            }
            
            function showFileEditor(title, content, filePath) {
                editorTitle.textContent = title;
                fileContent.value = content;
                editingFile = filePath;
                fileEditorModal.style.display = 'block';
                fileContent.focus();
            }
            
            function hideFileEditor() {
                fileEditorModal.style.display = 'none';
                editingFile = null;
            }
            
            // Event Listeners for Modals
            closeEditor.addEventListener('click', hideFileEditor);
            cancelEditBtn.addEventListener('click', hideFileEditor);
            
            confirmYes.addEventListener('click', async () => {
                if (currentConfirmAction) {
                    await currentConfirmAction();
                }
                hideConfirmModal();
            });
            
            confirmNo.addEventListener('click', hideConfirmModal);
            
            inputOk.addEventListener('click', () => {
                if (currentInputAction) {
                    currentInputAction(inputField.value);
                }
                hideInputModal();
            });
            
            inputCancel.addEventListener('click', hideInputModal);
            
            // Close modals when clicking outside
            window.addEventListener('click', (e) => {
                if (e.target.classList.contains('modal')) {
                    hideConfirmModal();
                    hideInputModal();
                    hideFileEditor();
                }
            });
            
            // Close modal with Escape key
            window.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    hideConfirmModal();
                    hideInputModal();
                    hideFileEditor();
                }
            });
            
            // Update breadcrumb
            function updateBreadcrumb(path) {
                breadcrumb.innerHTML = '';
                                
                // Split the path and filter out empty parts
                const pathParts = path.split('/').filter(Boolean);
                let currentBreadcrumbPath = '';
                                
                // Process path parts
                for (let index = 0; index < pathParts.length; index++) {
                    const part = pathParts[index];
                    
                    // Add separator if not the first item
                    if (index > 0) {
                        const separator = document.createElement('span');
                        separator.textContent = ' > ';
                        separator.style.color = '#888';
                        separator.style.marginRight = '8px';
                        breadcrumb.appendChild(separator);
                    }
                    
                    currentBreadcrumbPath += `/${part}`;
                    
                    const item = document.createElement('span');
                    item.className = 'breadcrumb-item';
                    item.textContent = part;
                    item.dataset.path = currentBreadcrumbPath.startsWith('/') ? currentBreadcrumbPath : `/${currentBreadcrumbPath}`;
                    item.style.marginRight = '8px';
                    item.style.cursor = 'pointer';
                    item.addEventListener('click', () => {
                        navigateTo(item.dataset.path);
                    });
                    breadcrumb.appendChild(item);
                }
            }

            // Update SD card button visibility and path
            async function updateSdcardButton() {
                if (!sdcardBtn) return;
                sdcardBtn.style.display = 'none';
                sdcardBtn.disabled = true;
                sdcardPath = '';
                
                try {
                    const response = await fetch('/api/system/sdcard');
                    if (!response.ok) return;
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.mounted && data.path) {
                        sdcardPath = data.path;
                        sdcardBtn.style.display = 'inline-block';
                        sdcardBtn.disabled = false;
                    }
                } catch (error) {
                    console.error('检测内存卡失败:', error);
                }
            }

            function resizeFileManagerPanel() {
                const panel = document.getElementById('file-manager');
                if (!panel) return;
                const rect = panel.getBoundingClientRect();
                const available = window.innerHeight - rect.top - 20;
                if (available > 200) {
                    panel.style.height = `${available}px`;
                }
            }
            
            // Format file size
            function formatSize(bytes) {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            // Format date
            function formatDate(timestamp) {
                return new Date(timestamp * 1000).toLocaleString();
            }
            
            // Get file icon based on file extension
            function getFileIcon(filename, isDir) {
                if (isDir) {
                    return '📁';
                }
                
                // Get file extension
                const ext = filename.split('.').pop().toLowerCase();
                
                // Image files
                if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'].includes(ext)) {
                    return '🖼️';
                }
                
                // Video files
                if (['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'].includes(ext)) {
                    return '🎬';
                }
                
                // Audio files
                if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma'].includes(ext)) {
                    return '🎵';
                }
                
                // Compressed files
                if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(ext)) {
                    return '📦';
                }
                
                // Document files
                if (['txt', 'pdf', 'doc', 'docx', 'odt', 'rtf'].includes(ext)) {
                    return '📄';
                }
                
                // Spreadsheet files
                if (['xls', 'xlsx', 'ods', 'csv'].includes(ext)) {
                    return '📊';
                }
                
                // Presentation files
                if (['ppt', 'pptx', 'odp'].includes(ext)) {
                    return '📋';
                }
                
                // Code files
                if (['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'php', 'java', 'c', 'cpp', 'h', 'hpp', 'go', 'rust'].includes(ext)) {
                    return '💻';
                }
                
                // Executable files
                if (['exe', 'msi', 'sh', 'bat', 'app', 'dmg', 'deb', 'rpm'].includes(ext)) {
                    return '⚙️';
                }
                
                // Default file icon
                return '📄';
            }
            
            // Render file list
            async function renderFileList(path) {
                try {
                    const response = await fetch('/api/files/list', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        fileManagerList.innerHTML = '';
                        
                        data.files.forEach(file => {
                            const fileItem = document.createElement('div');
                            fileItem.className = 'file-item';
                            fileItem.dataset.path = file.path;
                            fileItem.dataset.isDir = file.is_dir;
                            
                            fileItem.style.border = '1px solid var(--border)';
                            fileItem.style.borderRadius = '10px';
                            fileItem.style.padding = '10px';
                            fileItem.style.margin = '0';
                            fileItem.style.cursor = 'pointer';
                            fileItem.style.transition = 'all 0.2s ease';
                            fileItem.style.backgroundColor = 'var(--panel)';
                            fileItem.style.display = 'flex';
                            fileItem.style.flexDirection = 'column';
                            fileItem.style.alignItems = 'center';
                            fileItem.style.minHeight = '100px';
                                fileItem.style.justifyContent = 'center';
                                fileItem.style.gap = '5px';
                                fileItem.style.flex = '1 1 120px';
                                fileItem.style.maxWidth = '200px';
                                fileItem.style.minWidth = '0';
                                fileItem.style.boxSizing = 'border-box';
                            
                            // 点击事件：切换选中状态
                            fileItem.addEventListener('click', () => {
                                if (fileItem.classList.contains('selected')) {
                                    // 取消选中
                                    fileItem.classList.remove('selected');
                                    fileItem.style.backgroundColor = 'var(--panel)';
                                    fileItem.style.borderColor = 'var(--border)';
                                    const index = selectedFileManagerFiles.indexOf(file.path);
                                    if (index > -1) {
                                        selectedFileManagerFiles.splice(index, 1);
                                    }
                                } else {
                                    // 取消其他选中项
                                    document.querySelectorAll('.file-item.selected').forEach(item => {
                                        item.classList.remove('selected');
                                        item.style.backgroundColor = 'var(--panel)';
                                        item.style.borderColor = 'var(--border)';
                                    });
                                    // 选中当前文件
                                    fileItem.classList.add('selected');
                                    fileItem.style.backgroundColor = 'var(--accent-soft)';
                                    fileItem.style.borderColor = 'var(--accent)';
                                    selectedFileManagerFiles = [file.path];
                                }
                            });
                            
                            // 双击事件：打开文件或进入目录
                            fileItem.addEventListener('dblclick', () => {
                                if (file.is_dir) {
                                    navigateTo(file.path);
                                } else {
                                    openFile(file.path);
                                }
                            });
                            
                            fileItem.addEventListener('contextmenu', (e) => {
                                e.preventDefault();
                                // 自动选中当前文件
                                document.querySelectorAll('.file-item.selected').forEach(item => {
                                    item.classList.remove('selected');
                                    item.style.backgroundColor = 'var(--panel)';
                                    item.style.borderColor = 'var(--border)';
                                });
                                fileItem.classList.add('selected');
                                fileItem.style.backgroundColor = 'var(--accent-soft)';
                                fileItem.style.borderColor = 'var(--accent)';
                                selectedFileManagerFiles = [file.path];
                                showContextMenu(e, file.path);
                            });
                            
                            // File Icon
                            const icon = document.createElement('div');
                            icon.textContent = getFileIcon(file.name, file.is_dir);
                            icon.style.fontSize = '24px';
                            
                            // File Name
                            const fileName = document.createElement('div');
                            fileName.className = 'file-name';
                            fileName.textContent = file.name;
                            fileName.style.fontSize = '12px';
                            fileName.style.textAlign = 'center';
                            fileName.style.overflow = 'hidden';
                            fileName.style.textOverflow = 'ellipsis';
                            fileName.style.width = '100%';
                            fileName.style.color = 'var(--text)';
                            fileName.style.whiteSpace = 'nowrap';
                            fileName.style.maxWidth = '100%';
                            fileName.style.minWidth = '0';
                            
                            // File Details
                            const fileDetails = document.createElement('div');
                            fileDetails.style.fontSize = '10px';
                            fileDetails.style.color = 'var(--muted)';
                            fileDetails.style.textAlign = 'center';
                            
                            if (file.is_dir) {
                                fileDetails.textContent = '文件夹';
                            } else {
                                fileDetails.innerHTML = `${formatSize(file.size)}<br>${formatDate(file.mtime)}`;
                            }
                            
                            fileItem.appendChild(icon);
                            fileItem.appendChild(fileName);
                            fileItem.appendChild(fileDetails);
                            
                            // 鼠标悬停效果（仅当未选中时）
                            fileItem.addEventListener('mouseenter', () => {
                                if (!fileItem.classList.contains('selected')) {
                                    fileItem.style.backgroundColor = 'rgba(77, 182, 172, 0.12)';
                                    fileItem.style.borderColor = 'rgba(77, 182, 172, 0.55)';
                                }
                            });
                            
                            fileItem.addEventListener('mouseleave', () => {
                                if (!fileItem.classList.contains('selected')) {
                                    fileItem.style.backgroundColor = 'var(--panel)';
                                    fileItem.style.borderColor = 'var(--border)';
                                }
                            });
                            
                            fileManagerList.appendChild(fileItem);
                        });
                        
                        currentPath = data.current_path;
                        updateBreadcrumb(data.current_path);
                    } else {
                        alert('获取文件列表失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('获取文件列表出错:', error);
                    alert('获取文件列表出错');
                }
            }
            
            // Navigate to directory
            async function navigateTo(path) {
                await renderFileList(path);
            }
            
            // Open file for editing
            async function openFile(filePath) {
                try {
                    const response = await fetch('/api/files/read', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path: filePath })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        showFileEditor(`编辑文件: ${filePath.split('/').pop()}`, data.content, filePath);
                    } else {
                        alert('打开文件失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('打开文件出错:', error);
                    alert('打开文件出错');
                }
            }
            
            // Save file
            async function saveFile(content, filePath) {
                try {
                    const response = await fetch('/api/files/write', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path: filePath, content })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        alert('文件保存成功');
                        hideFileEditor();
                        await renderFileList(currentPath);
                    } else {
                        alert('保存文件失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('保存文件出错:', error);
                    alert('保存文件出错');
                }
            }
            
            // Create new file
            async function createFile(fileName) {
                if (!fileName.trim()) {
                    alert('文件名不能为空');
                    return;
                }
                
                try {
                    const response = await fetch('/api/files/create', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path: currentPath, filename: fileName })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        await renderFileList(currentPath);
                        alert('文件创建成功');
                    } else {
                        alert('创建文件失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('创建文件出错:', error);
                    alert('创建文件出错');
                }
            }
            
            // Create new directory
            async function createDirectory(dirName) {
                if (!dirName.trim()) {
                    alert('文件夹名不能为空');
                    return;
                }
                
                try {
                    const response = await fetch('/api/files/create-dir', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path: currentPath, dirname: dirName })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        await renderFileList(currentPath);
                        alert('文件夹创建成功');
                    } else {
                        alert('创建文件夹失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('创建文件夹出错:', error);
                    alert('创建文件夹出错');
                }
            }
            
            // Delete file or directory
            async function deletePath(path) {
                try {
                    // Ensure path is not empty
                    if (!path) {
                        alert('删除失败: 路径不能为空');
                        return;
                    }
                    
                    const response = await fetch('/api/files/delete', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ path })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        await renderFileList(currentPath);
                        alert('删除成功');
                    } else {
                        alert('删除失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('删除出错:', error);
                    alert('删除出错: ' + error.message);
                }
            }
            
            // Copy file or directory path
            async function copyPath(path) {
                try {
                    if (!path) {
                        alert('复制失败: 路径不能为空');
                        return;
                    }
                    
                    copiedPath = path;
                    // Show paste button
                    updatePasteButtonVisibility();
                    alert('复制成功');
                } catch (error) {
                    console.error('复制出错:', error);
                    alert('复制出错');
                }
            }
            
            // Paste file or directory
            async function pastePath(destPath) {
                try {
                    if (!copiedPath) {
                        alert('粘贴失败: 没有要粘贴的内容');
                        return;
                    }
                    
                    if (!destPath) {
                        alert('粘贴失败: 目标路径不能为空');
                        return;
                    }
                    
                    // Get filename from copied path
                    const filename = copiedPath.split('/').pop();
                    const targetPath = destPath + '/' + filename;
                    
                    const response = await fetch('/api/files/copy', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ source: copiedPath, destination: targetPath })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        await renderFileList(currentPath);
                        alert('粘贴成功');
                        // Clear copied path and hide paste button
                        copiedPath = null;
                        updatePasteButtonVisibility();
                    } else {
                        alert('粘贴失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('粘贴出错:', error);
                    alert('粘贴出错: ' + error.message);
                }
            }
            
            // Update paste button visibility
            function updatePasteButtonVisibility() {
                const pasteBtn = document.getElementById('paste-btn');
                if (pasteBtn) {
                    if (copiedPath) {
                        pasteBtn.style.display = 'block';
                    } else {
                        pasteBtn.style.display = 'none';
                    }
                }
            }
            
            // Event listeners for file manager buttons
            backBtn.addEventListener('click', () => {
                // Get parent directory path
                const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/'));
                // If we're at the root, stay at root
                const newPath = parentPath || '/';
                renderFileList(newPath);
            });
            
            refreshBtn.addEventListener('click', () => {
                updateSdcardButton();
                renderFileList(currentPath);
            });
            
            // 复制按钮事件
            const copyBtn = document.getElementById('copy-btn');
            if (copyBtn) {
                copyBtn.addEventListener('click', async () => {
                    // 如果有选中的文件，复制该文件
                    if (selectedFileManagerFiles.length > 0) {
                        await copyPath(selectedFileManagerFiles[0]);
                    } else {
                        alert('请先选择一个文件或文件夹');
                    }
                });
            }
            
            // 新建文件按钮事件
            newFileBtn.addEventListener('click', () => {
                showInputModal('新建文件', '请输入文件名', createFile);
            });
            
            // 新建文件夹按钮事件
            newDirBtn.addEventListener('click', () => {
                showInputModal('新建文件夹', '请输入文件夹名', createDirectory);
            });
            
            pasteBtn.addEventListener('click', async () => {
                await pastePath(currentPath);
            });
            
            saveFileBtn.addEventListener('click', () => {
                if (editingFile) {
                    saveFile(fileContent.value, editingFile);
                }
            });
            
            // Initialize paste button visibility
            updatePasteButtonVisibility();
        });
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')


async def handle_upload(request, plugin):
    """Handle file upload request
    
    Args:
        request: aiohttp request object
        plugin: Plugin instance to access downloads_dir and text_file_path
    """
    try:
        # Parse multipart form data
        reader = await request.multipart()
        field = await reader.next()
        
        if field.name == 'file' and field.filename:
            filename = field.filename
            file_path = os.path.join(plugin.downloads_dir, filename)
            
            # Get content length from header, but note this includes multipart overhead
            # For more accurate progress, we'll track actual bytes written
            content_length_str = request.headers.get('Content-Length', '0')
            try:
                content_length = int(content_length_str)
            except ValueError:
                content_length = 0
            
            # Estimate actual file size (Content-Length includes multipart headers/boundaries)
            # Use a more conservative estimate to avoid negative values
            estimated_file_size = max(0, content_length - 1024)  # Increased buffer to handle multipart overhead
            
            # If Content-Length is not available, we'll use the actual transferred size
            # and update the size as we receive more data
            if estimated_file_size <= 0:
                decky.logger.info(f"Content-Length not available or invalid, using dynamic sizing for: {filename}")
                estimated_file_size = 0  # Will be updated dynamically
            
            decky.logger.info(f"Starting upload: {filename}, Estimated size: {estimated_file_size} bytes")
            
            # Initialize transfer stats
            transferred = 0
            start_time = time.time()
            last_emit_time = start_time
            
            # Save file and track progress
            with open(file_path, 'wb') as f:
                while True:
                    try:
                        chunk = await field.read_chunk()  # Read chunk
                        if not chunk:  # EOF
                            break
                        f.write(chunk)
                        
                        # Update transfer stats
                        transferred += len(chunk)
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        
                        # Calculate speed in bytes per second
                        if elapsed_time > 0:
                            speed = transferred / elapsed_time
                        else:
                            speed = 0
                        
                        # Emit progress every 500ms to reduce event flood (same as DS)
                        # This improves performance and reduces frontend load
                        if current_time - last_emit_time >= 0.5:
                            # Determine the total size to use for progress calculation
                            # If we have an estimated size, use it; otherwise, use the current transferred amount
                            # This ensures the progress bar works even without Content-Length header
                            total_size = estimated_file_size if estimated_file_size > 0 else transferred
                            if estimated_file_size <= 0:
                                # If we don't have an estimated size, use transferred as the base
                                # but set a reasonable upper bound to show progress
                                total_size = max(transferred, 1)  # Avoid division by zero
                            else:
                                # Use the estimated size, but ensure it's at least the amount transferred
                                total_size = max(estimated_file_size, transferred)
                            
                            eta = 0
                            if speed > 0 and total_size > transferred and estimated_file_size > 0:
                                # Only calculate ETA if we have an estimated size
                                eta = (total_size - transferred) / speed
                            elif speed > 0 and estimated_file_size <= 0:
                                # If no estimated size, provide a rough ETA based on current speed
                                # Assuming remaining data is roughly equal to what's been transferred
                                eta = transferred / speed
                            
                            # Emit transfer status event to frontend
                            # NOTE: Decky frontend expects arguments wrapped in a list for destructuring
                            # If passed as positional args, frontend receives the first arg as the array to destructure
                            await decky.emit(
                                "transfer_status",
                                [
                                    filename,
                                    total_size,  # Use calculated total size
                                    transferred,
                                    speed,
                                    round(eta)
                                ]
                            )
                            last_emit_time = current_time
                    except Exception as chunk_error:
                        decky.logger.error(f"Error reading chunk: {chunk_error}")
                        raise
            
            # Get actual file size after write
            actual_size = os.path.getsize(file_path)
            decky.logger.info(f"Upload completed: {filename}, Actual size: {actual_size} bytes")
            
            # Emit final 100% progress with actual size
            await decky.emit(
                "transfer_status",
                [
                    filename,
                    actual_size,
                    actual_size,
                    0,
                    0
                ]
            )
            
            # Clear the text file after successful file transfer
            try:
                with open(plugin.text_file_path, "w") as f:
                    f.write("")
                decky.logger.info(f"Cleared text file after file transfer: {plugin.text_file_path}")
            except Exception as e:
                decky.logger.error(f"Error clearing text file: {e}")
            
            # Emit transfer complete event
            # NOTE: Wrap in list for frontend destructuring
            await decky.emit("transfer_complete", [filename])
            
            # Send system notification for out-of-plugin UI notifications
            try:
                # Create notification for file upload completion
                notification_msg = f"文件 '{filename}' 已成功上传到 Steam Deck"
                await decky.emit("_show_notification", {
                    "title": "文件传输完成",
                    "body": notification_msg,
                    "duration": 5
                })
            except Exception as notify_error:
                decky.logger.error(f"Failed to send system notification for file upload: {notify_error}")
            
            return web.json_response({"filename": filename, "status": "success"})
        
        return web.json_response({"status": "error", "message": "No file provided"}, status=400)
    
    except Exception as e:
        decky.logger.error(f"Upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_text_upload(request, plugin):
    """Handle text upload request
    
    Args:
        request: aiohttp request object
        plugin: Plugin instance to access decky_send_dir and text_file_path
    """
    try:
        # Parse JSON request body
        data = await request.json()
        text = data.get('text', '')
        
        if not text:
            return web.json_response({"status": "error", "message": "No text provided"}, status=400)
        
        # Ensure decky_send_dir exists
        os.makedirs(plugin.decky_send_dir, exist_ok=True)
        
        # Write text to file (overwrite if exists)
        with open(plugin.text_file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        decky.logger.info(f"Saved text to file: {plugin.text_file_path}")
        
        # Emit text received event to frontend with the saved text
        # NOTE: Wrap in list for frontend destructuring
        await decky.emit("text_received", [text])
        
        # Send system notification for out-of-plugin UI notifications
        try:
            # Create notification for text upload completion
            await decky.emit("_show_notification", {
                "title": "文本传输完成",
                "body": "新的文本内容已接收并保存",
                "duration": 5
            })
        except Exception as notify_error:
            decky.logger.error(f"Failed to send system notification for text upload: {notify_error}")
        
        return web.json_response({"status": "success", "message": "Text received successfully"})

    except Exception as e:
        decky.logger.error(f"Text upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

