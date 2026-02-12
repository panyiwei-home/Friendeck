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
import asyncio
import hashlib
from aiohttp import web

# Import decky for logging and event emission
import decky
import utils


def _get_upload_session_store(plugin):
    sessions = getattr(plugin, "_upload_sessions", None)
    if sessions is None:
        sessions = {}
        setattr(plugin, "_upload_sessions", sessions)
    lock = getattr(plugin, "_upload_sessions_lock", None)
    if lock is None:
        lock = asyncio.Lock()
        setattr(plugin, "_upload_sessions_lock", lock)
    return sessions, lock

def _normalize_hash_algo(algo):
    if not algo:
        return "sha256"
    lower = str(algo).lower().replace('-', '')
    if lower in ("sha1", "sha256", "md5"):
        return lower
    return "sha256"


def _compute_file_hash(path, algo="sha256", chunk_size=8 * 1024 * 1024):
    algo_name = _normalize_hash_algo(algo)
    hasher = hashlib.new(algo_name)
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


async def _compute_file_hash_async(path, algo="sha256"):
    return await asyncio.to_thread(_compute_file_hash, path, algo)



async def _emit_decky(plugin, event, payload):
    try:
        target_loop = getattr(plugin, "main_loop", None)
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if target_loop and target_loop.is_running() and target_loop is not current_loop:
            future = asyncio.run_coroutine_threadsafe(decky.emit(event, payload), target_loop)
            try:
                await asyncio.wrap_future(future)
            except Exception as emit_error:
                decky.logger.error(f"Decky emit failed ({event}): {emit_error}")
            return
        await decky.emit(event, payload)
    except Exception as emit_error:
        decky.logger.error(f"Decky emit failed ({event}): {emit_error}")



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
            .breadcrumb,
            .breadcrumb * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .action-buttons,
            .action-buttons * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .file-grid.list-mode {
                flex-direction: column;
            }
            .file-grid.list-mode .file-item {
                flex: 1 1 auto;
                max-width: none;
                width: 100%;
                flex-direction: row;
                align-items: center;
                justify-content: flex-start;
                gap: 10px;
                min-height: 56px;
            }
            .file-grid.list-mode .file-icon {
                font-size: 20px;
            }
            .file-grid.list-mode .file-name {
                text-align: left;
                flex: 1 1 auto;
            }
            .file-grid.list-mode .file-details {
                margin-left: auto;
                text-align: right;
            }
            .file-grid .file-item {
                min-width: 0;
                position: relative;
            }
            .file-grid .pin-badge {
                position: absolute;
                top: 6px;
                left: 6px;
                font-size: 12px;
                color: #ffffff;
                background: #000000;
                padding: 2px 4px;
                border-radius: 6px;
                border: 1px solid #ffffff;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
                pointer-events: none;
            }
            .file-grid.list-mode {
                flex-direction: column;
            }
            .file-grid.list-mode .file-item {
                flex: 1 1 auto;
                max-width: none;
                width: 100%;
                flex-direction: row;
                align-items: center;
                justify-content: flex-start;
                gap: 10px;
                min-height: 56px;
            }
            .file-grid.list-mode .file-icon {
                font-size: 20px;
            }
            .file-grid.list-mode .file-name {
                text-align: left;
                flex: 1 1 auto;
            }
            .file-grid.list-mode .file-details {
                margin-left: auto;
                text-align: right;
            }
            .file-grid .file-name {
                max-width: 100%;
                min-width: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .file-item.is-dir .file-details {
                display: none;
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
                -webkit-touch-callout: none;
            }
            .file-item,
            .file-item * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .unpack-progress-bar {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                overflow: hidden;
                margin-top: 12px;
            }
            .unpack-progress-fill {
                height: 100%;
                width: 0%;
                background: #1b73e8;
                transition: width 0.2s ease;
            }
            .unpack-progress-text {
                font-size: 12px;
                color: #bdbdbd;
                margin-top: 8px;
                text-align: right;
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
                .file-grid.list-mode .file-item {
                    min-height: 52px;
                    padding: 8px 10px;
                    gap: 8px;
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
                <span class="breadcrumb-item" data-path="" data-i18n="breadcrumb.home">主页</span>
            </div>
            <button id="sdcard-btn" data-i18n="actions.sdcard" style="padding: 6px 12px; background-color: #1b73e8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; margin: 0; display: none; white-space: nowrap;">
                内存卡
            </button>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-buttons">
            <button id="back-btn" data-i18n="actions.back">返回</button>
            <button id="refresh-btn" data-i18n="actions.refresh">刷新</button>
            <button id="paste-btn" data-i18n="actions.paste" style="display: none;">粘贴</button>
            <button id="new-file-btn" data-i18n="actions.newFile">新建文件</button>
            <button id="new-dir-btn" data-i18n="actions.newFolder">新建文件夹</button>
            <button id="new-btn" data-i18n="actions.new" style="display: none;">新建</button>
        </div>
        
        <!-- File List -->
        <div class="file-list-container" style="flex: 1 1 auto; overflow: auto; max-height: none; min-height: 0; display: flex;">
            <div id="file-manager-list" class="file-grid"></div>
        </div>
        
        <!-- File Editor Modal -->
        <div id="file-editor-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="editor-title" data-i18n="modal.editorTitle">文件编辑器</h3>
                    <button id="close-editor">×</button>
                </div>
                <textarea id="file-content"></textarea>
                <div style="margin: 15px 0; display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="save-file-btn" data-i18n="actions.save">保存</button>
                    <button id="cancel-edit-btn" data-i18n="actions.cancel">取消</button>
                </div>
            </div>
        </div>
        
        <!-- Confirmation Modal -->
        <div id="confirm-modal" class="modal">
            <div class="modal-content">
                <h3 data-i18n="modal.confirmTitle" style="margin: 0 0 15px 0;">确认操作</h3>
                <p id="confirm-message"></p>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="confirm-yes" data-i18n="modal.confirmYes">确认</button>
                    <button id="confirm-no" data-i18n="modal.confirmNo">取消</button>
                </div>
            </div>
        </div>
        
        <!-- Input Modal for New Files/Folders -->
        <div id="input-modal" class="modal">
            <div class="modal-content">
                <h3 id="input-title"></h3>
                <input type="text" id="input-field">
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="input-ok" data-i18n="modal.inputOk">确认</button>
                    <button id="input-cancel" data-i18n="modal.inputCancel">取消</button>
                </div>
            </div>
        </div>

        <!-- Unpack Progress Modal -->
        <div id="unpack-modal" class="modal">
            <div class="modal-content" style="max-width: 420px;">
                <div class="modal-header">
                    <h3 data-i18n="modal.unpackTitle">正在解压</h3>
                    <button id="unpack-close" style="visibility: hidden;">×</button>
                </div>
                <div id="unpack-filename" style="font-size: 13px; color: #bdbdbd;"></div>
                <div class="unpack-progress-bar">
                    <div id="unpack-progress-fill" class="unpack-progress-fill"></div>
                </div>
                <div id="unpack-progress-text" class="unpack-progress-text">0%</div>
            </div>
        </div>

        <!-- File Operation Progress Modal -->
        <div id="fileop-modal" class="modal">
            <div class="modal-content" style="max-width: 420px;">
                <div class="modal-header">
                    <h3 id="fileop-title" data-i18n="modal.fileOpCopy">正在复制</h3>
                    <button id="fileop-close" style="visibility: hidden;">×</button>
                </div>
                <div id="fileop-filename" style="font-size: 13px; color: #bdbdbd;"></div>
                <div class="unpack-progress-bar">
                    <div id="fileop-progress-fill" class="unpack-progress-fill"></div>
                </div>
                <div id="fileop-progress-text" class="unpack-progress-text">0%</div>
            </div>
        </div>
        
        <!-- Context Menu -->
        <div class="context-menu" id="context-menu"></div>
        <div class="context-menu" id="new-menu"></div>
        
        <script>
            const PAGE_TITLE_KEY = 'title.fileManager';
            const I18N = {
                'zh-CN': {
                    title: {
                        fileManager: 'decky-send 文件管理器',
                        upload: 'decky-send 文件上传'
                    },
                    subtitle: '将文件或文本上传到 Steam Deck',
                    tabs: {
                        file: '文件上传',
                        text: '文本传输',
                        fileManager: '文件管理'
                    },
                    breadcrumb: {
                        home: '主页'
                    },
                    upload: {
                        hint: '点击或拖拽文件/文件夹到此处',
                        sendFile: '发送文件'
                    },
                    text: {
                        placeholder: '在此输入要传输的文本...',
                        send: '发送文本'
                    },
                    actions: {
                        back: '返回',
                        refresh: '刷新',
                        paste: '粘贴',
                        newFile: '新建文件',
                        newFolder: '新建文件夹',
                        new: '新建',
                        save: '保存',
                        cancel: '取消',
                        sdcard: '内存卡'
                    },
                    status: {
                        done: '完成',
                        failed: '失败'
                    },
                    modal: {
                        confirmTitle: '确认操作',
                        confirmYes: '确认',
                        confirmNo: '取消',
                        inputOk: '确认',
                        inputCancel: '取消',
                        editorTitle: '文件编辑器',
                        editorTitleWithName: '编辑文件：{{name}}',
                        unpackTitle: '正在解压',
                        unpacking: '正在解压...',
                        unpackingWithName: '正在解压：{{name}}',
                        fileOpCopy: '正在复制',
                        fileOpMove: '正在剪切',
                        fileOpTarget: '目标：{{name}}',
                        renameTitle: '重命名',
                        newFileTitle: '新建文件',
                        newFolderTitle: '新建文件夹',
                        renamePlaceholder: '请输入新名称',
                        newFilePlaceholder: '请输入文件名',
                        newFolderPlaceholder: '请输入文件夹名',
                        deleteConfirm: '确定要删除此项目吗？',
                        uploadPathTitle: '选择传输路径',
                        uploadPathUp: '上一级',
                        uploadPathSelect: '选择当前目录',
                        uploadPathCancel: '取消',
                        uploadPathCurrent: '当前路径：{{path}}',
                        uploadPathError: '无法读取目录'
                    },
                    menu: {
                        open: '打开',
                        download: '下载到本地',
                        addToSteam: '添加到Steam',
                        unpack: '解压',
                        pin: '置顶',
                        unpin: '取消置顶',
                        copy: '复制',
                        cut: '剪切',
                        delete: '删除',
                        rename: '重命名'
                    }
                },
                'en-US': {
                    title: {
                        fileManager: 'decky-send File Manager',
                        upload: 'decky-send File Transfer'
                    },
                    subtitle: 'Upload files or text to Steam Deck',
                    tabs: {
                        file: 'File Upload',
                        text: 'Text Transfer',
                        fileManager: 'File Manager'
                    },
                    breadcrumb: {
                        home: 'Home'
                    },
                    upload: {
                        hint: 'Click or drag files/folders here',
                        sendFile: 'Send Files'
                    },
                    text: {
                        placeholder: 'Enter text to send...',
                        send: 'Send Text'
                    },
                    actions: {
                        back: 'Back',
                        refresh: 'Refresh',
                        paste: 'Paste',
                        newFile: 'New File',
                        newFolder: 'New Folder',
                        new: 'New',
                        save: 'Save',
                        cancel: 'Cancel',
                        sdcard: 'SD Card'
                    },
                    status: {
                        done: 'Done',
                        failed: 'Failed'
                    },
                    modal: {
                        confirmTitle: 'Confirm',
                        confirmYes: 'Confirm',
                        confirmNo: 'Cancel',
                        inputOk: 'OK',
                        inputCancel: 'Cancel',
                        editorTitle: 'File Editor',
                        editorTitleWithName: 'Edit file: {{name}}',
                        unpackTitle: 'Extracting',
                        unpacking: 'Extracting...',
                        unpackingWithName: 'Extracting: {{name}}',
                        fileOpCopy: 'Copying',
                        fileOpMove: 'Moving',
                        fileOpTarget: 'Target: {{name}}',
                        renameTitle: 'Rename',
                        newFileTitle: 'New File',
                        newFolderTitle: 'New Folder',
                        renamePlaceholder: 'Enter new name',
                        newFilePlaceholder: 'Enter file name',
                        newFolderPlaceholder: 'Enter folder name',
                        deleteConfirm: 'Delete this item?',
                        uploadPathTitle: 'Choose destination',
                        uploadPathUp: 'Up',
                        uploadPathSelect: 'Select current folder',
                        uploadPathCancel: 'Cancel',
                        uploadPathCurrent: 'Current path: {{path}}',
                        uploadPathError: 'Failed to read directory'
                    },
                    menu: {
                        open: 'Open',
                        download: 'Download',
                        addToSteam: 'Add to Steam',
                        unpack: 'Extract',
                        pin: 'Pin',
                        unpin: 'Unpin',
                        copy: 'Copy',
                        cut: 'Cut',
                        delete: 'Delete',
                        rename: 'Rename'
                    }
                }
            };

            let currentLang = 'zh-CN';

            function normalizeLang(lang) {
                if (!lang) return 'zh-CN';
                const lower = String(lang).toLowerCase();
                if (lower === 'auto') return normalizeLang(navigator.language);
                if (lower.startsWith('zh')) return 'zh-CN';
                if (lower.startsWith('en')) return 'en-US';
                return I18N[lang] ? lang : 'zh-CN';
            }

            function t(key, vars) {
                const table = I18N[currentLang] || I18N['zh-CN'];
                const parts = key.split('.');
                let value = table;
                for (const part of parts) {
                    if (value && typeof value === 'object' && part in value) {
                        value = value[part];
                    } else {
                        value = null;
                        break;
                    }
                }
                if (typeof value !== 'string') return key;
                if (vars) {
                    Object.keys(vars).forEach((varKey) => {
                        value = value.replace(new RegExp(`{{\\s*${varKey}\\s*}}`, 'g'), String(vars[varKey]));
                    });
                }
                return value;
            }

            function applyTranslations() {
                document.documentElement.lang = currentLang;
                if (PAGE_TITLE_KEY) {
                    document.title = t(PAGE_TITLE_KEY);
                }
                document.querySelectorAll('[data-i18n]').forEach((el) => {
                    const key = el.getAttribute('data-i18n');
                    if (key) {
                        el.textContent = t(key);
                    }
                });
                document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                    const key = el.getAttribute('data-i18n-placeholder');
                    if (key) {
                        el.setAttribute('placeholder', t(key));
                    }
                });
            }

            const ALERT_FULL_MAP = {
                '只能下载文件，不能下载文件夹': 'Only files can be downloaded',
                '下载失败': 'Download failed',
                '文件已添加到Steam库': 'File added to Steam',
                '只能将文件添加到Steam库，不能添加文件夹': 'Only files can be added to Steam',
                '重命名功能将在后续版本中实现': 'Rename will be available in a future version',
                '获取文件列表出错': 'Failed to load file list',
                '打开文件出错': 'Failed to open file',
                '文件保存成功': 'File saved',
                '保存文件出错': 'Failed to save file',
                '文件名不能为空': 'File name cannot be empty',
                '文件创建成功': 'File created',
                '创建文件出错': 'Failed to create file',
                '文件夹名不能为空': 'Folder name cannot be empty',
                '文件夹创建成功': 'Folder created',
                '创建文件夹出错': 'Failed to create folder',
                '删除成功': 'Deleted',
                '复制成功': 'Copied',
                '复制出错': 'Copy failed',
                '剪切成功': 'Moved',
                '剪切出错': 'Move failed',
                '粘贴成功': 'Pasted',
                '粘贴失败: 没有要粘贴的内容': 'Paste failed: nothing to paste',
                '粘贴失败: 目标路径不能为空': 'Paste failed: destination is empty',
                '粘贴出错': 'Paste failed',
                '无法读取目录': 'Failed to read directory',
                '未知错误': 'Unknown error',
                '请直接点击右键或双击文件进行操作': 'Please right-click or double click to operate',
                '请先选择文件': 'Please select files',
                '请先选择传输路径': 'Please choose a destination first',
                '所有文件上传完成': 'All files uploaded',
                '部分文件上传失败': 'Some files failed to upload',
                '部分文件上传超时': 'Some files timed out',
                '请先输入要传输的文本': 'Please enter text to send',
                '文本传输成功': 'Text sent',
                '文本传输失败': 'Text transfer failed',
                '文本传输出错': 'Text transfer error',
                '解压完成': 'Extraction complete',
                '解压出错': 'Extraction error',
                '请先选择一个文件或文件夹': 'Please select a file or folder'
            };

            const ALERT_PREFIX_MAP = {
                '下载失败: ': 'Download failed: ',
                '添加到Steam失败: ': 'Add to Steam failed: ',
                '获取文件列表失败: ': 'Failed to load file list: ',
                '打开文件失败: ': 'Failed to open file: ',
                '保存文件失败: ': 'Failed to save file: ',
                '创建文件失败: ': 'Failed to create file: ',
                '创建文件夹失败: ': 'Failed to create folder: ',
                '删除失败: ': 'Delete failed: ',
                '复制失败: ': 'Copy failed: ',
                '剪切失败: ': 'Move failed: ',
                '粘贴失败: ': 'Paste failed: ',
                '粘贴出错: ': 'Paste error: ',
                '解压失败: ': 'Extraction failed: '
            };

            function translateMessage(message) {
                if (currentLang.startsWith('zh')) return message;
                const text = String(message ?? '');
                if (ALERT_FULL_MAP[text]) return ALERT_FULL_MAP[text];
                for (const prefix in ALERT_PREFIX_MAP) {
                    if (text.startsWith(prefix)) {
                        return ALERT_PREFIX_MAP[prefix] + text.slice(prefix.length);
                    }
                }
                return text;
            }

            const rawAlert = window.alert.bind(window);
            window.alert = (message) => rawAlert(translateMessage(message));

            async function initLanguage() {
                try {
                    const response = await fetch('/api/settings/language');
                    if (response.ok) {
                        const data = await response.json();
                        if (data && data.language) {
                            currentLang = normalizeLang(data.language);
                        } else {
                            currentLang = normalizeLang('auto');
                        }
                    }
                } catch (e) {
                    currentLang = normalizeLang('auto');
                }
                applyTranslations();
            }

            // Wait for DOM to fully load before executing scripts
            document.addEventListener('DOMContentLoaded', async () => {
                await initLanguage();
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
                const newBtn = document.getElementById('new-btn');
                const sdcardBtn = document.getElementById('sdcard-btn');
                let sdcardPath = '';

                const contextMenu = document.getElementById('context-menu');
                const newMenu = document.getElementById('new-menu');

                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
                    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
                let suppressNextClick = false;
                
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

                const unpackModal = document.getElementById('unpack-modal');
                const unpackFilename = document.getElementById('unpack-filename');
                const unpackProgressFill = document.getElementById('unpack-progress-fill');
                const unpackProgressText = document.getElementById('unpack-progress-text');
                let unpackTimer = null;
                let unpackProgressValue = 0;

                const fileOpModal = document.getElementById('fileop-modal');
                const fileOpTitle = document.getElementById('fileop-title');
                const fileOpFilename = document.getElementById('fileop-filename');
                const fileOpProgressFill = document.getElementById('fileop-progress-fill');
                const fileOpProgressText = document.getElementById('fileop-progress-text');
                let fileOpTimer = null;
                let fileOpProgressValue = 0;

                if (sdcardBtn) {
                    sdcardBtn.addEventListener('click', () => {
                        if (sdcardPath) {
                            navigateTo(sdcardPath);
                        }
                    });
                }
                
                // Context Menu Items
                let pinMenuItem = null;
                let unpackMenuItem = null;
                const contextMenuItems = [
                    { text: t('menu.open'), action: 'open' },
                    { text: t('menu.download'), action: 'download' },
                    { text: t('menu.addToSteam'), action: 'add-to-steam' },
                    { text: t('menu.unpack'), action: 'unpack' },
                    { text: t('menu.pin'), action: 'pin' },
                    { text: t('menu.copy'), action: 'copy' },
                    { text: t('menu.cut'), action: 'cut' },
                    { text: t('menu.delete'), action: 'delete' },
                    { text: t('menu.rename'), action: 'rename' }
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
                    if (item.action === 'pin') {
                        pinMenuItem = menuItem;
                    }
                    if (item.action === 'unpack') {
                        unpackMenuItem = menuItem;
                    }
                });

                // New Menu Items (for compact screens)
                const newMenuItems = [
                    { text: t('actions.newFile'), action: 'new-file' },
                    { text: t('actions.newFolder'), action: 'new-dir' }
                ];
                
                newMenuItems.forEach(item => {
                    const menuItem = document.createElement('div');
                    menuItem.className = 'context-menu-item';
                    menuItem.textContent = item.text;
                    menuItem.addEventListener('click', () => {
                        if (item.action === 'new-file') {
                            showInputModal(t('modal.newFileTitle'), t('modal.newFilePlaceholder'), createFile);
                        } else {
                            showInputModal(t('modal.newFolderTitle'), t('modal.newFolderPlaceholder'), createDirectory);
                        }
                        hideNewMenu();
                    });
                    newMenu.appendChild(menuItem);
                });

                const PINNED_STORAGE_KEY = 'decky_send_pinned_items';

                function loadPinnedMap() {
                    try {
                        const raw = localStorage.getItem(PINNED_STORAGE_KEY);
                        if (!raw) return {};
                        const parsed = JSON.parse(raw);
                        return parsed && typeof parsed === 'object' ? parsed : {};
                    } catch (e) {
                        console.error('读取置顶信息失败:', e);
                        return {};
                    }
                }

                function savePinnedMap(map) {
                    try {
                        localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(map));
                    } catch (e) {
                        console.error('保存置顶信息失败:', e);
                    }
                }

                function getPinnedSet(path) {
                    const map = loadPinnedMap();
                    const list = Array.isArray(map[path]) ? map[path] : [];
                    return new Set(list);
                }

                function setPinnedSet(path, set) {
                    const map = loadPinnedMap();
                    map[path] = Array.from(set);
                    savePinnedMap(map);
                }

                function togglePin(path) {
                    const set = getPinnedSet(currentPath);
                    if (set.has(path)) {
                        set.delete(path);
                    } else {
                        set.add(path);
                    }
                    setPinnedSet(currentPath, set);
                }

                function updatePinMenuLabel() {
                    if (!pinMenuItem) return;
                    const set = getPinnedSet(currentPath);
                    pinMenuItem.textContent = set.has(contextMenuPath) ? t('menu.unpin') : t('menu.pin');
                }

                function isArchiveFile(name) {
                    if (!name) return false;
                    const lower = name.toLowerCase();
                    const exts = ['.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz', '.tbz2', '.txz', '.tar', '.zip', '.7z', '.rar', '.exe'];
                    return exts.some(ext => lower.endsWith(ext));
                }

                function updateUnpackMenuVisibility() {
                    if (!unpackMenuItem) return;
                    const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                    const isDir = fileItem && fileItem.dataset.isDir === 'true';
                    const filename = contextMenuPath ? contextMenuPath.split('/').pop() : '';
                    const canUnpack = !isDir && isArchiveFile(filename);
                    unpackMenuItem.style.display = canUnpack ? 'block' : 'none';
                }
                
                // Context Menu Functions
                let copiedPath = null; // Store copied/cut file/folder path
                let clipboardMode = 'copy';

                function bindLongPressContextMenu(element, path, beforeShow) {
                    if (!isIOS) {
                        return;
                    }

                    let pressTimer = null;
                    let startX = 0;
                    let startY = 0;
                    let lastX = 0;
                    let lastY = 0;
                    const longPressMs = 550;
                    const moveTolerance = 10;

                    const clearPressTimer = () => {
                        if (pressTimer) {
                            clearTimeout(pressTimer);
                            pressTimer = null;
                        }
                    };

                    element.addEventListener('touchstart', (e) => {
                        if (!e.touches || e.touches.length !== 1) {
                            return;
                        }
                        const touch = e.touches[0];
                        startX = touch.clientX;
                        startY = touch.clientY;
                        lastX = startX;
                        lastY = startY;
                        clearPressTimer();
                        pressTimer = setTimeout(() => {
                            pressTimer = null;
                            suppressNextClick = true;
                            if (beforeShow) {
                                beforeShow();
                            }
                            showContextMenu({ clientX: lastX, clientY: lastY, preventDefault: () => {} }, path);
                        }, longPressMs);
                    }, { passive: true });

                    element.addEventListener('touchmove', (e) => {
                        if (!pressTimer || !e.touches || e.touches.length !== 1) {
                            return;
                        }
                        const touch = e.touches[0];
                        lastX = touch.clientX;
                        lastY = touch.clientY;
                        if (Math.abs(lastX - startX) > moveTolerance || Math.abs(lastY - startY) > moveTolerance) {
                            clearPressTimer();
                        }
                    }, { passive: true });

                    element.addEventListener('touchend', clearPressTimer);
                    element.addEventListener('touchcancel', clearPressTimer);
                }
                
                function showContextMenu(e, path) {
                    if (e && e.preventDefault) {
                        e.preventDefault();
                    }
                    contextMenuPath = path;
                    updatePinMenuLabel();
                    updateUnpackMenuVisibility();
                    contextMenu.style.display = 'block';
                    
                    const padding = 8;
                    const menuRect = contextMenu.getBoundingClientRect();
                    const point = (e && e.touches && e.touches[0]) ||
                        (e && e.changedTouches && e.changedTouches[0]) ||
                        e || { clientX: 0, clientY: 0 };
                    let x = point.clientX;
                    let y = point.clientY;
                    const maxX = window.innerWidth - menuRect.width - padding;
                    const maxY = window.innerHeight - menuRect.height - padding;
                    if (maxX < padding) {
                        x = padding;
                    } else {
                        x = Math.min(Math.max(x, padding), maxX);
                    }
                    if (maxY < padding) {
                        y = padding;
                    } else {
                        y = Math.min(Math.max(y, padding), maxY);
                    }
                    
                    contextMenu.style.left = x + 'px';
                    contextMenu.style.top = y + 'px';
                }
                
                function hideContextMenu() {
                    contextMenu.style.display = 'none';
                    contextMenuPath = '';
                }

                function showNewMenu() {
                    if (!newMenu || !newBtn) return;
                    newMenu.style.display = 'block';
                    
                    const padding = 8;
                    const rect = newBtn.getBoundingClientRect();
                    const menuRect = newMenu.getBoundingClientRect();
                    let x = rect.left;
                    let y = rect.bottom + 6;
                    
                    if (y + menuRect.height > window.innerHeight - padding) {
                        y = rect.top - menuRect.height - 6;
                    }
                    
                    const maxX = window.innerWidth - menuRect.width - padding;
                    const maxY = window.innerHeight - menuRect.height - padding;
                    if (maxX < padding) {
                        x = padding;
                    } else {
                        x = Math.min(Math.max(x, padding), maxX);
                    }
                    if (maxY < padding) {
                        y = padding;
                    } else {
                        y = Math.min(Math.max(y, padding), maxY);
                    }
                    
                    newMenu.style.left = x + 'px';
                    newMenu.style.top = y + 'px';
                }
                
                function hideNewMenu() {
                    if (!newMenu) return;
                    newMenu.style.display = 'none';
                }

                function isCompactScreen() {
                    const area = window.innerWidth * window.innerHeight;
                    return area < 420000 || window.innerWidth < 520;
                }

                function applyFileManagerLayout() {
                    const compact = isCompactScreen();
                    if (fileManagerList) {
                        fileManagerList.classList.toggle('list-mode', compact);
                        const items = fileManagerList.querySelectorAll('.file-item');
                        items.forEach(item => {
                            item.style.flex = compact ? '1 1 auto' : '1 1 120px';
                            item.style.maxWidth = compact ? 'none' : '200px';
                            item.style.width = compact ? '100%' : '';
                            item.style.flexDirection = compact ? 'row' : 'column';
                            item.style.justifyContent = compact ? 'flex-start' : 'center';
                            item.style.alignItems = 'center';
                            item.style.gap = compact ? '10px' : '5px';
                            item.style.minHeight = compact ? '52px' : '100px';
                            item.style.padding = compact ? '8px 10px' : '10px';
                            
                            const icon = item.querySelector('.file-icon');
                            if (icon) {
                                icon.style.fontSize = compact ? '20px' : '24px';
                            }
                            
                            const name = item.querySelector('.file-name');
                            if (name) {
                                name.style.textAlign = compact ? 'left' : 'center';
                                name.style.flex = compact ? '1 1 auto' : '';
                            }
                            
                            const details = item.querySelector('.file-details');
                                if (details) {
                                    details.style.textAlign = compact ? 'right' : 'center';
                                    details.style.marginLeft = compact ? 'auto' : '';
                                }
                            });
                        }
                    if (newBtn && newFileBtn && newDirBtn) {
                        newBtn.style.display = compact ? 'inline-block' : 'none';
                        newFileBtn.style.display = compact ? 'none' : 'inline-block';
                        newDirBtn.style.display = compact ? 'none' : 'inline-block';
                    }
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
                        case 'cut':
                            if (contextMenuPath) {
                                await cutPath(contextMenuPath);
                            }
                            break;
                        case 'paste':
                            await pastePath(currentPath);
                            break;
                        case 'delete':
                            if (contextMenuPath) {
                                // Save the path before showing confirm modal (which hides context menu)
                                const pathToDelete = contextMenuPath;
                                showConfirmModal(t('modal.deleteConfirm'), async () => {
                                    await deletePath(pathToDelete);
                                });
                            }
                            break;
                        case 'rename':
                            if (contextMenuPath) {
                                // Implement rename functionality
                                const oldName = contextMenuPath.split('/').pop() || '';
                                showInputModal(t('modal.renameTitle'), t('modal.renamePlaceholder'), (newName) => {
                                    // Implement rename API call here
                                    alert('重命名功能将在后续版本中实现');
                                }, oldName);
                            }
                            break;
                    }
                }
                
                if (newBtn) {
                    newBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        hideContextMenu();
                        showNewMenu();
                    });
                }
                
                if (newMenu) {
                    newMenu.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                }
                
                // Hide menus when clicking elsewhere
                document.addEventListener('click', (e) => {
                    if (suppressNextClick && e.target.closest('.file-item')) {
                        suppressNextClick = false;
                        return;
                    }
                    suppressNextClick = false;
                    hideContextMenu();
                    hideNewMenu();
                });
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape') {
                        hideContextMenu();
                        hideNewMenu();
                    }
                });
                
                window.addEventListener('resize', applyFileManagerLayout);
                
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
                
                function showInputModal(title, placeholder, action, defaultValue = '') {
                    inputTitle.textContent = title;
                    inputField.placeholder = placeholder;
                    inputField.value = defaultValue || '';
                    currentInputAction = action;
                    inputModal.style.display = 'block';
                    inputField.focus();
                    try {
                        if (inputField.value) {
                            inputField.setSelectionRange(0, inputField.value.length);
                        }
                    } catch (e) {
                        // ignore
                    }
                }
                
                function hideInputModal() {
                    inputModal.style.display = 'none';
                    currentInputAction = null;
                }

                function showUnpackProgress(filename) {
                    if (!unpackModal) return;
                    if (unpackFilename) {
                        unpackFilename.textContent = filename ? t('modal.unpackingWithName', { name: filename }) : t('modal.unpacking');
                    }
                    unpackProgressValue = 0;
                    if (unpackProgressFill) {
                        unpackProgressFill.style.width = '0%';
                    }
                    if (unpackProgressText) {
                        unpackProgressText.textContent = '0%';
                    }
                    unpackModal.style.display = 'block';
                    if (unpackTimer) {
                        clearInterval(unpackTimer);
                    }
                    unpackTimer = setInterval(() => {
                        const increment = Math.max(1, Math.round(Math.random() * 4));
                        unpackProgressValue = Math.min(90, unpackProgressValue + increment);
                        if (unpackProgressFill) {
                            unpackProgressFill.style.width = `${unpackProgressValue}%`;
                        }
                        if (unpackProgressText) {
                            unpackProgressText.textContent = `${unpackProgressValue}%`;
                        }
                    }, 200);
                }

                function finishUnpackProgress(success) {
                    if (!unpackModal) return;
                    if (unpackTimer) {
                        clearInterval(unpackTimer);
                        unpackTimer = null;
                    }
                    if (unpackProgressFill) {
                        unpackProgressFill.style.width = '100%';
                    }
                    if (unpackProgressText) {
                        unpackProgressText.textContent = success ? t('status.done') : t('status.failed');
                    }
                    setTimeout(() => {
                        unpackModal.style.display = 'none';
                    }, 500);
                }

                function showFileOpProgress(title, filename) {
                    if (!fileOpModal) return;
                    if (fileOpTitle) {
                        fileOpTitle.textContent = title || t('modal.fileOpCopy');
                    }
                    if (fileOpFilename) {
                        fileOpFilename.textContent = filename ? t('modal.fileOpTarget', { name: filename }) : '';
                    }
                    fileOpProgressValue = 0;
                    if (fileOpProgressFill) {
                        fileOpProgressFill.style.width = '0%';
                    }
                    if (fileOpProgressText) {
                        fileOpProgressText.textContent = '0%';
                    }
                    fileOpModal.style.display = 'block';
                    if (fileOpTimer) {
                        clearInterval(fileOpTimer);
                    }
                    fileOpTimer = setInterval(() => {
                        const increment = Math.max(1, Math.round(Math.random() * 4));
                        fileOpProgressValue = Math.min(90, fileOpProgressValue + increment);
                        if (fileOpProgressFill) {
                            fileOpProgressFill.style.width = `${fileOpProgressValue}%`;
                        }
                        if (fileOpProgressText) {
                            fileOpProgressText.textContent = `${fileOpProgressValue}%`;
                        }
                    }, 200);
                }

                function finishFileOpProgress(success) {
                    if (!fileOpModal) return;
                    if (fileOpTimer) {
                        clearInterval(fileOpTimer);
                        fileOpTimer = null;
                    }
                    if (fileOpProgressFill) {
                        fileOpProgressFill.style.width = '100%';
                    }
                    if (fileOpProgressText) {
                        fileOpProgressText.textContent = success ? t('status.done') : t('status.failed');
                    }
                    setTimeout(() => {
                        fileOpModal.style.display = 'none';
                    }, 500);
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
                    if (unpackModal) {
                        unpackModal.style.display = 'none';
                    }
                    if (typeof closeUploadPathModal === 'function') {
                        closeUploadPathModal(null);
                    } else if (typeof uploadPathModal !== 'undefined' && uploadPathModal) {
                        uploadPathModal.style.display = 'none';
                    }
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

                            const pinnedSet = getPinnedSet(data.current_path);
                            const currentPaths = new Set(data.files.map(item => item.path));
                            let cleaned = false;
                            for (const pinnedPath of Array.from(pinnedSet)) {
                                if (!currentPaths.has(pinnedPath)) {
                                    pinnedSet.delete(pinnedPath);
                                    cleaned = true;
                                }
                            }
                            if (cleaned) {
                                setPinnedSet(data.current_path, pinnedSet);
                            }

                            const files = data.files.map((file, index) => ({ ...file, __index: index }));
                            files.sort((a, b) => {
                                const aPinned = pinnedSet.has(a.path);
                                const bPinned = pinnedSet.has(b.path);
                                if (aPinned !== bPinned) return aPinned ? -1 : 1;
                                return a.__index - b.__index;
                            });
                            
                            files.forEach(file => {
                                const fileItem = document.createElement('div');
                                fileItem.className = 'file-item';
                                if (file.is_dir) {
                                    fileItem.classList.add('is-dir');
                                }
                                fileItem.dataset.path = file.path;
                                fileItem.dataset.isDir = file.is_dir;
                                const isPinned = pinnedSet.has(file.path);
                                if (isPinned) {
                                    fileItem.classList.add('pinned');
                                }

                                const pinBadge = document.createElement('div');
                                pinBadge.className = 'pin-badge';
                                pinBadge.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="#ffffff" d="M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-9a1 1 0 0 1 1-1h1zm2 0h6V7a3 3 0 0 0-6 0v3zm3 4a2 2 0 0 0-1 3.732V19a1 1 0 0 0 2 0v-1.268A2 2 0 0 0 12 14z"/></svg>';
                                if (!isPinned) {
                                    pinBadge.style.display = 'none';
                                }
                                fileItem.appendChild(pinBadge);
                                
                                fileItem.addEventListener('click', (e) => {
                                    if (suppressNextClick) {
                                        suppressNextClick = false;
                                        e.preventDefault();
                                        e.stopPropagation();
                                        return;
                                    }
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

                                bindLongPressContextMenu(fileItem, file.path);
                                
                                // File Icon
                                const icon = document.createElement('div');
                                icon.className = 'file-icon';
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
                                fileDetails.className = 'file-details';
                                fileDetails.style.fontSize = '10px';
                                fileDetails.style.color = '#888';
                                fileDetails.style.textAlign = 'center';
                                
                                if (file.is_dir) {
                                    fileDetails.textContent = '';
                                    fileDetails.style.display = 'none';
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
                        applyFileManagerLayout();
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
                            showFileEditor(t('modal.editorTitleWithName', { name: filePath.split('/').pop() || '' }), data.content, filePath);
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
                        clipboardMode = 'copy';
                        alert('复制成功');
                        // Show paste button
                        updatePasteButtonVisibility();
                    } catch (error) {
                        console.error('复制出错:', error);
                        alert('复制出错');
                    }
                }

                async function cutPath(path) {
                    try {
                        if (!path) {
                            alert('剪切失败: 路径不能为空');
                            return;
                        }

                        copiedPath = path;
                        clipboardMode = 'cut';
                        alert('剪切成功');
                        updatePasteButtonVisibility();
                    } catch (error) {
                        console.error('剪切出错:', error);
                        alert('剪切出错');
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
                        const isCut = clipboardMode === 'cut';
                        const opTitle = isCut ? t('modal.fileOpMove') : t('modal.fileOpCopy');
                        showFileOpProgress(opTitle, filename);
                        const endpoint = isCut ? '/api/files/move' : '/api/files/copy';
                        
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ source: copiedPath, destination: targetPath })
                        });
                        
                        const data = await response.json();
                        finishFileOpProgress(data.status === 'success');
                        if (data.status === 'success') {
                            await renderFileList(currentPath);
                            alert(isCut ? '剪切成功' : '粘贴成功');
                            // Hide paste button after successful paste
                            copiedPath = null;
                            clipboardMode = 'copy';
                            updatePasteButtonVisibility();
                        } else {
                            alert((isCut ? '剪切' : '粘贴') + '失败: ' + data.message);
                        }
                    } catch (error) {
                        console.error('粘贴出错:', error);
                        finishFileOpProgress(false);
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
                    showInputModal(t('modal.newFileTitle'), t('modal.newFilePlaceholder'), createFile);
                });
                
                newDirBtn.addEventListener('click', () => {
                    showInputModal(t('modal.newFolderTitle'), t('modal.newFolderPlaceholder'), createDirectory);
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
                applyFileManagerLayout();
                
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
            html {
                height: 100%;
                background-color: var(--bg);
                background-image:
                    radial-gradient(900px 500px at 20% -10%, rgba(77, 182, 172, 0.16), transparent 60%),
                    radial-gradient(800px 400px at 120% 20%, rgba(94, 156, 255, 0.12), transparent 60%),
                    linear-gradient(180deg, #0f1216 0%, #10161b 100%);
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-size: cover;
            }
            html, body {
                height: 100%;
                overflow: hidden;
            }
            body {
                font-family: "IBM Plex Sans", "Noto Sans", "Ubuntu", "Segoe UI", sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 24px;
                text-align: center;
                background: transparent;
                color: var(--text);
                min-height: 100vh;
            }
            body::after {
                content: "";
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                height: 30vh;
                background: linear-gradient(180deg, rgba(15, 18, 22, 0) 0%, rgba(15, 18, 22, 0.7) 100%);
                pointer-events: none;
                z-index: 0;
            }
            body > * {
                position: relative;
                z-index: 1;
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
            .subtitle {
                margin-bottom: 0;
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
            .tab-buttons,
            .tab-buttons * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
                position: relative;
            }
            .file-grid .pin-badge {
                position: absolute;
                top: 6px;
                left: 6px;
                font-size: 12px;
                color: #ffffff;
                background: #000000;
                padding: 2px 4px;
                border-radius: 6px;
                border: 1px solid #ffffff;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
                pointer-events: none;
            }
            .file-grid .file-name {
                max-width: 100%;
                min-width: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .file-item.is-dir .file-details {
                display: none;
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
                -webkit-touch-callout: none;
            }
            .file-item,
            .file-item * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .breadcrumb-bar,
            .breadcrumb-bar * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .action-buttons,
            .action-buttons * {
                user-select: none;
                -webkit-user-select: none;
                -ms-user-select: none;
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
            .unpack-progress-bar {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                overflow: hidden;
                margin-top: 12px;
            }
            .unpack-progress-fill {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, var(--accent) 0%, #5fa6ff 100%);
                transition: width 0.2s ease;
            }
            .unpack-progress-text {
                font-size: 12px;
                color: var(--muted);
                margin-top: 8px;
                text-align: right;
            }
            .upload-path-current {
                font-size: 12px;
                color: var(--muted);
                margin-bottom: 10px;
                word-break: break-all;
            }
            .upload-path-list {
                border: 1px solid var(--border);
                border-radius: 10px;
                background: var(--panel);
                max-height: 260px;
                overflow-y: auto;
                padding: 6px;
                text-align: left;
            }
            .upload-path-item {
                padding: 8px 10px;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text);
                transition: background-color 0.15s ease;
            }
            .upload-path-item:hover {
                background: rgba(77, 182, 172, 0.12);
            }
            .upload-path-actions {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                margin-top: 14px;
                flex-wrap: wrap;
            }

            @media (max-width: 640px) {
                body {
                    max-width: 100%;
                    padding: 16px;
                }
                .subtitle {
                    display: none;
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
                #file-manager .file-grid.list-mode .file-item {
                    min-height: 52px;
                    padding: 8px 10px;
                    gap: 8px;
                }
            }
        </style>
    </head>
    <body>
        <h1>decky-send</h1>
        <p class="subtitle" data-i18n="subtitle">将文件或文本上传到 Steam Deck</p>
        
        <!-- Tab Container -->
        <div class="tab-container">
            <!-- Tab Buttons -->
            <div class="tab-buttons">
                <button class="tab-button active" data-tab="file" data-i18n="tabs.file">文件上传</button>
                <button class="tab-button" data-tab="text" data-i18n="tabs.text">文本传输</button>
                <button class="tab-button" data-tab="file-manager" data-i18n="tabs.fileManager">文件管理</button>
            </div>
            
            <!-- File Upload Tab -->
            <div id="file" class="tab-panel active">
                <div class="upload-area" id="upload-area">
                    <p data-i18n="upload.hint">点击或拖拽文件/文件夹到此处</p>
                    <input type="file" id="file-input" multiple accept="*/*" webkitdirectory>
                </div>
                
                <div class="file-list" id="file-list"></div>
                
                <div style="margin: 10px 0; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                    <button id="upload-btn" data-i18n="upload.sendFile">发送文件</button>
                </div>
            </div>
            
            <!-- Text Transfer Tab -->
            <div id="text" class="tab-panel">
                <div style="margin: 15px 0;">
                    <textarea 
                        id="text-input" 
                        placeholder="在此输入要传输的文本..." 
                        data-i18n-placeholder="text.placeholder"
                        rows="6" 
                        style="width: 100%; resize: vertical;"></textarea>
                </div>
                
                <div style="margin: 10px 0;">
                    <button id="send-text-btn" data-i18n="text.send" style="margin: 0;">
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
                        <button id="back-btn" data-i18n="actions.back" style="margin: 0; padding: 6px 10px; font-size: 12px;">
                            返回
                        </button>
                        <div class="breadcrumb" id="breadcrumb" style="flex: 1; overflow-x: auto; white-space: nowrap;"></div>
                        <button id="sdcard-btn" data-i18n="actions.sdcard" style="padding: 6px 12px; font-size: 12px; margin: 0; display: none; white-space: nowrap;">
                            内存卡
                        </button>
                    </div>
                    
                    <!-- Action Buttons -->
            <div class="action-buttons" style="display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap;">
                <button id="refresh-btn" data-i18n="actions.refresh" style="margin: 0;">
                    刷新
                </button>
                <button id="new-file-btn" data-i18n="actions.newFile" style="margin: 0;">
                    新建文件
                </button>
                <button id="new-dir-btn" data-i18n="actions.newFolder" style="margin: 0;">
                    新建文件夹
                </button>
                <button id="new-btn" data-i18n="actions.new" style="margin: 0; display: none;">
                    新建
                </button>
                <button id="paste-btn" data-i18n="actions.paste" style="margin: 0; display: none;">
                    粘贴
                </button>
                <button id="copy-btn" data-i18n="menu.copy" style="margin: 0;">
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
                            <h3 id="editor-title" data-i18n="modal.editorTitle" style="margin: 0; color: var(--text);">文件编辑器</h3>
                            <button id="close-editor" style="background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; box-shadow: none;">×</button>
                        </div>
                        <textarea id="file-content" style="width: 100%; height: 300px; padding: 10px; border: 1px solid var(--border); border-radius: 10px; background-color: var(--panel); color: var(--text); font-size: 14px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, \"Liberation Mono\", monospace;"></textarea>
                        <div style="margin: 15px 0; display: flex; gap: 10px; justify-content: flex-end;">
                            <button id="save-file-btn" data-i18n="actions.save" style="padding: 10px 20px; margin: 0;">
                                保存
                            </button>
                            <button id="cancel-edit-btn" data-i18n="actions.cancel" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                                取消
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Confirmation Modal -->
                <div id="confirm-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 400px; margin: 100px auto;">
                        <h3 data-i18n="modal.confirmTitle" style="margin: 0 0 15px 0; color: var(--text);">确认操作</h3>
                        <p id="confirm-message" style="color: var(--muted); margin: 0 0 20px 0;"></p>
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button id="confirm-yes" data-i18n="modal.confirmYes" style="padding: 10px 20px; margin: 0;">
                                确认
                            </button>
                            <button id="confirm-no" data-i18n="modal.confirmNo" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
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
                            <button id="input-ok" data-i18n="modal.inputOk" style="padding: 10px 20px; margin: 0;">
                                确认
                            </button>
                            <button id="input-cancel" data-i18n="modal.inputCancel" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                                取消
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Unpack Progress Modal -->
                <div id="unpack-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 420px; margin: 100px auto;">
                        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h3 data-i18n="modal.unpackTitle" style="margin: 0; color: var(--text);">正在解压</h3>
                            <button id="unpack-close" style="visibility: hidden;">×</button>
                        </div>
                        <div id="unpack-filename" style="font-size: 13px; color: var(--muted);"></div>
                        <div class="unpack-progress-bar">
                            <div id="unpack-progress-fill" class="unpack-progress-fill"></div>
                        </div>
                        <div id="unpack-progress-text" class="unpack-progress-text">0%</div>
                    </div>
                </div>

                <!-- File Operation Progress Modal -->
                <div id="fileop-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
                    <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 420px; margin: 100px auto;">
                        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h3 id="fileop-title" data-i18n="modal.fileOpCopy" style="margin: 0; color: var(--text);">正在复制</h3>
                            <button id="fileop-close" style="visibility: hidden;">×</button>
                        </div>
                        <div id="fileop-filename" style="font-size: 13px; color: var(--muted);"></div>
                        <div class="unpack-progress-bar">
                            <div id="fileop-progress-fill" class="unpack-progress-fill"></div>
                        </div>
                        <div id="fileop-progress-text" class="unpack-progress-text">0%</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Upload Path Modal -->
        <div id="upload-path-modal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(8, 10, 12, 0.7); padding: 20px;">
            <div class="modal-content" style="background-color: var(--bg-elev); border: 1px solid var(--border); border-radius: 14px; padding: 20px; max-width: 420px; margin: 100px auto;">
                <h3 data-i18n="modal.uploadPathTitle" style="margin: 0 0 12px 0; color: var(--text);">选择传输路径</h3>
                <div id="upload-path-current" class="upload-path-current"></div>
                <div id="upload-path-list" class="upload-path-list"></div>
                <div class="upload-path-actions">
                    <button id="upload-path-up" data-i18n="modal.uploadPathUp" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                        上一级
                    </button>
                    <button id="upload-path-ok" data-i18n="modal.uploadPathSelect" style="padding: 10px 20px; margin: 0;">
                        选择当前目录
                    </button>
                    <button id="upload-path-cancel" data-i18n="modal.uploadPathCancel" style="padding: 10px 20px; margin: 0; background: var(--panel-strong); color: var(--text); border: 1px solid var(--border); box-shadow: none;">
                        取消
                    </button>
                </div>
            </div>
        </div>

        <script>
            const PAGE_TITLE_KEY = 'title.upload';
            const I18N = {
                'zh-CN': {
                    title: {
                        fileManager: 'decky-send 文件管理器',
                        upload: 'decky-send 文件上传'
                    },
                    subtitle: '将文件或文本上传到 Steam Deck',
                    tabs: {
                        file: '文件上传',
                        text: '文本传输',
                        fileManager: '文件管理'
                    },
                    breadcrumb: {
                        home: '主页'
                    },
                    upload: {
                        hint: '点击或拖拽文件/文件夹到此处',
                        sendFile: '发送文件'
                    },
                    text: {
                        placeholder: '在此输入要传输的文本...',
                        send: '发送文本'
                    },
                    actions: {
                        back: '返回',
                        refresh: '刷新',
                        paste: '粘贴',
                        newFile: '新建文件',
                        newFolder: '新建文件夹',
                        new: '新建',
                        save: '保存',
                        cancel: '取消',
                        sdcard: '内存卡'
                    },
                    status: {
                        done: '完成',
                        failed: '失败'
                    },
                    modal: {
                        confirmTitle: '确认操作',
                        confirmYes: '确认',
                        confirmNo: '取消',
                        inputOk: '确认',
                        inputCancel: '取消',
                        editorTitle: '文件编辑器',
                        editorTitleWithName: '编辑文件：{{name}}',
                        unpackTitle: '正在解压',
                        unpacking: '正在解压...',
                        unpackingWithName: '正在解压：{{name}}',
                        fileOpCopy: '正在复制',
                        fileOpMove: '正在剪切',
                        fileOpTarget: '目标：{{name}}',
                        renameTitle: '重命名',
                        newFileTitle: '新建文件',
                        newFolderTitle: '新建文件夹',
                        renamePlaceholder: '请输入新名称',
                        newFilePlaceholder: '请输入文件名',
                        newFolderPlaceholder: '请输入文件夹名',
                        deleteConfirm: '确定要删除此项目吗？',
                        uploadPathTitle: '选择传输路径',
                        uploadPathUp: '上一级',
                        uploadPathSelect: '选择当前目录',
                        uploadPathCancel: '取消',
                        uploadPathCurrent: '当前路径：{{path}}',
                        uploadPathError: '无法读取目录'
                    },
                    menu: {
                        open: '打开',
                        download: '下载到本地',
                        addToSteam: '添加到Steam',
                        unpack: '解压',
                        pin: '置顶',
                        unpin: '取消置顶',
                        copy: '复制',
                        cut: '剪切',
                        delete: '删除',
                        rename: '重命名'
                    }
                },
                'en-US': {
                    title: {
                        fileManager: 'decky-send File Manager',
                        upload: 'decky-send File Transfer'
                    },
                    subtitle: 'Upload files or text to Steam Deck',
                    tabs: {
                        file: 'File Upload',
                        text: 'Text Transfer',
                        fileManager: 'File Manager'
                    },
                    breadcrumb: {
                        home: 'Home'
                    },
                    upload: {
                        hint: 'Click or drag files/folders here',
                        sendFile: 'Send Files'
                    },
                    text: {
                        placeholder: 'Enter text to send...',
                        send: 'Send Text'
                    },
                    actions: {
                        back: 'Back',
                        refresh: 'Refresh',
                        paste: 'Paste',
                        newFile: 'New File',
                        newFolder: 'New Folder',
                        new: 'New',
                        save: 'Save',
                        cancel: 'Cancel',
                        sdcard: 'SD Card'
                    },
                    status: {
                        done: 'Done',
                        failed: 'Failed'
                    },
                    modal: {
                        confirmTitle: 'Confirm',
                        confirmYes: 'Confirm',
                        confirmNo: 'Cancel',
                        inputOk: 'OK',
                        inputCancel: 'Cancel',
                        editorTitle: 'File Editor',
                        editorTitleWithName: 'Edit file: {{name}}',
                        unpackTitle: 'Extracting',
                        unpacking: 'Extracting...',
                        unpackingWithName: 'Extracting: {{name}}',
                        fileOpCopy: 'Copying',
                        fileOpMove: 'Moving',
                        fileOpTarget: 'Target: {{name}}',
                        renameTitle: 'Rename',
                        newFileTitle: 'New File',
                        newFolderTitle: 'New Folder',
                        renamePlaceholder: 'Enter new name',
                        newFilePlaceholder: 'Enter file name',
                        newFolderPlaceholder: 'Enter folder name',
                        deleteConfirm: 'Delete this item?',
                        uploadPathTitle: 'Choose destination',
                        uploadPathUp: 'Up',
                        uploadPathSelect: 'Select current folder',
                        uploadPathCancel: 'Cancel',
                        uploadPathCurrent: 'Current path: {{path}}',
                        uploadPathError: 'Failed to read directory'
                    },
                    menu: {
                        open: 'Open',
                        download: 'Download',
                        addToSteam: 'Add to Steam',
                        unpack: 'Extract',
                        pin: 'Pin',
                        unpin: 'Unpin',
                        copy: 'Copy',
                        cut: 'Cut',
                        delete: 'Delete',
                        rename: 'Rename'
                    }
                }
            };

            let currentLang = 'zh-CN';

            function normalizeLang(lang) {
                if (!lang) return 'zh-CN';
                const lower = String(lang).toLowerCase();
                if (lower === 'auto') return normalizeLang(navigator.language);
                if (lower.startsWith('zh')) return 'zh-CN';
                if (lower.startsWith('en')) return 'en-US';
                return I18N[lang] ? lang : 'zh-CN';
            }

            function t(key, vars) {
                const table = I18N[currentLang] || I18N['zh-CN'];
                const parts = key.split('.');
                let value = table;
                for (const part of parts) {
                    if (value && typeof value === 'object' && part in value) {
                        value = value[part];
                    } else {
                        value = null;
                        break;
                    }
                }
                if (typeof value !== 'string') return key;
                if (vars) {
                    Object.keys(vars).forEach((varKey) => {
                        value = value.replace(new RegExp(`{{\\s*${varKey}\\s*}}`, 'g'), String(vars[varKey]));
                    });
                }
                return value;
            }

            function applyTranslations() {
                document.documentElement.lang = currentLang;
                if (PAGE_TITLE_KEY) {
                    document.title = t(PAGE_TITLE_KEY);
                }
                document.querySelectorAll('[data-i18n]').forEach((el) => {
                    const key = el.getAttribute('data-i18n');
                    if (key) {
                        el.textContent = t(key);
                    }
                });
                document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                    const key = el.getAttribute('data-i18n-placeholder');
                    if (key) {
                        el.setAttribute('placeholder', t(key));
                    }
                });
            }

            const ALERT_FULL_MAP = {
                '只能下载文件，不能下载文件夹': 'Only files can be downloaded',
                '下载失败': 'Download failed',
                '文件已添加到Steam库': 'File added to Steam',
                '只能将文件添加到Steam库，不能添加文件夹': 'Only files can be added to Steam',
                '重命名功能将在后续版本中实现': 'Rename will be available in a future version',
                '获取文件列表出错': 'Failed to load file list',
                '打开文件出错': 'Failed to open file',
                '文件保存成功': 'File saved',
                '保存文件出错': 'Failed to save file',
                '文件名不能为空': 'File name cannot be empty',
                '文件创建成功': 'File created',
                '创建文件出错': 'Failed to create file',
                '文件夹名不能为空': 'Folder name cannot be empty',
                '文件夹创建成功': 'Folder created',
                '创建文件夹出错': 'Failed to create folder',
                '删除成功': 'Deleted',
                '复制成功': 'Copied',
                '复制出错': 'Copy failed',
                '剪切成功': 'Moved',
                '剪切出错': 'Move failed',
                '粘贴成功': 'Pasted',
                '粘贴失败: 没有要粘贴的内容': 'Paste failed: nothing to paste',
                '粘贴失败: 目标路径不能为空': 'Paste failed: destination is empty',
                '粘贴出错': 'Paste failed',
                '无法读取目录': 'Failed to read directory',
                '未知错误': 'Unknown error',
                '请直接点击右键或双击文件进行操作': 'Please right-click or double click to operate',
                '请先选择文件': 'Please select files',
                '请先选择传输路径': 'Please choose a destination first',
                '所有文件上传完成': 'All files uploaded',
                '部分文件上传失败': 'Some files failed to upload',
                '部分文件上传超时': 'Some files timed out',
                '请先输入要传输的文本': 'Please enter text to send',
                '文本传输成功': 'Text sent',
                '文本传输失败': 'Text transfer failed',
                '文本传输出错': 'Text transfer error',
                '解压完成': 'Extraction complete',
                '解压出错': 'Extraction error',
                '请先选择一个文件或文件夹': 'Please select a file or folder'
            };

            const ALERT_PREFIX_MAP = {
                '下载失败: ': 'Download failed: ',
                '添加到Steam失败: ': 'Add to Steam failed: ',
                '获取文件列表失败: ': 'Failed to load file list: ',
                '打开文件失败: ': 'Failed to open file: ',
                '保存文件失败: ': 'Failed to save file: ',
                '创建文件失败: ': 'Failed to create file: ',
                '创建文件夹失败: ': 'Failed to create folder: ',
                '删除失败: ': 'Delete failed: ',
                '复制失败: ': 'Copy failed: ',
                '剪切失败: ': 'Move failed: ',
                '粘贴失败: ': 'Paste failed: ',
                '粘贴出错: ': 'Paste error: ',
                '解压失败: ': 'Extraction failed: '
            };

            function translateMessage(message) {
                if (currentLang.startsWith('zh')) return message;
                const text = String(message ?? '');
                if (ALERT_FULL_MAP[text]) return ALERT_FULL_MAP[text];
                for (const prefix in ALERT_PREFIX_MAP) {
                    if (text.startsWith(prefix)) {
                        return ALERT_PREFIX_MAP[prefix] + text.slice(prefix.length);
                    }
                }
                return text;
            }

            const rawAlert = window.alert.bind(window);
            window.alert = (message) => rawAlert(translateMessage(message));

            async function initLanguage() {
                try {
                    const response = await fetch('/api/settings/language');
                    if (response.ok) {
                        const data = await response.json();
                        if (data && data.language) {
                            currentLang = normalizeLang(data.language);
                        } else {
                            currentLang = normalizeLang('auto');
                        }
                    }
                } catch (e) {
                    currentLang = normalizeLang('auto');
                }
                applyTranslations();
            }

            // Wait for DOM to fully load before executing scripts
            document.addEventListener('DOMContentLoaded', async () => {
                await initLanguage();
                // Tab functionality
                const tabButtons = document.querySelectorAll('.tab-button');
                const tabPanels = document.querySelectorAll('.tab-panel');
                
                const activateTab = (targetTab) => {
                    if (!targetTab) return;
                    
                    // Remove active class from all buttons and panels
                    tabButtons.forEach(btn => btn.classList.remove('active'));
                    tabPanels.forEach(panel => panel.classList.remove('active'));
                    
                    // Add active class to corresponding button and panel
                    const targetButton = Array.from(tabButtons).find(btn => btn.getAttribute('data-tab') === targetTab);
                    if (targetButton) {
                        targetButton.classList.add('active');
                    }
                    const targetPanel = document.getElementById(targetTab);
                    if (targetPanel) {
                        targetPanel.classList.add('active');
                    }
                    
                    // Render file list when file manager tab is activated
                    if (targetTab === 'file-manager') {
                        // Check if fileManagerList exists before calling renderFileList
                        if (typeof renderFileList === 'function') {
                            resizeFileManagerPanel();
                            updateSdcardButton();
                            applyFileManagerLayout();
                            renderFileList(currentPath);
                        }
                    }
                };
                
                tabButtons.forEach(button => {
                    button.addEventListener('click', () => {
                        activateTab(button.getAttribute('data-tab'));
                    });
                });

                const hasFileDrag = (event) => {
                    const dt = event.dataTransfer;
                    if (!dt) return false;
                    
                    if (dt.types) {
                        const types = Array.from(dt.types);
                        if (types.includes('Files') ||
                            types.includes('application/x-moz-file') ||
                            types.includes('application/x-moz-file-promise')) {
                            return true;
                        }
                    }
                    
                    if (dt.items && dt.items.length) {
                        for (const item of dt.items) {
                            if (item && item.kind === 'file') {
                                return true;
                            }
                        }
                    }
                    
                    if (dt.files && dt.files.length) {
                        return true;
                    }
                    
                    return false;
                };

                const handleFileDrag = (event) => {
                    if (hasFileDrag(event)) {
                        activateTab('file');
                    }
                };

                document.addEventListener('dragenter', handleFileDrag, true);
                document.addEventListener('dragover', handleFileDrag, true);
                document.addEventListener('drop', handleFileDrag, true);
                window.addEventListener('dragenter', handleFileDrag, true);
                window.addEventListener('dragover', handleFileDrag, true);
                window.addEventListener('drop', handleFileDrag, true);

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
            const folderDisplayMap = new Map();
            let uploadPromptEnabled = false;
            let defaultUploadDir = '';
            const uploadPathModal = document.getElementById('upload-path-modal');
            const uploadPathCurrent = document.getElementById('upload-path-current');
            const uploadPathList = document.getElementById('upload-path-list');
            const uploadPathUp = document.getElementById('upload-path-up');
            const uploadPathOk = document.getElementById('upload-path-ok');
            const uploadPathCancel = document.getElementById('upload-path-cancel');
            let uploadPathResolve = null;
            let uploadPathCurrentValue = '';

            async function refreshUploadOptions() {
                try {
                    const response = await fetch('/api/settings/upload-options');
                    if (!response.ok) return;
                    const data = await response.json();
                    if (data.status === 'success') {
                        uploadPromptEnabled = !!data.prompt_upload_path;
                        defaultUploadDir = data.default_dir || '';
                    }
                } catch (error) {
                    console.error('获取上传设置失败:', error);
                }
            }

            async function loadUploadPathList(path) {
                if (!uploadPathList || !uploadPathCurrent) return;
                try {
                    const response = await fetch('/api/files/list', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ path })
                    });
                    const data = await response.json();
                    if (data.status !== 'success') {
                        throw new Error(data.message || t('modal.uploadPathError'));
                    }
                    uploadPathCurrentValue = data.current_path;
                    uploadPathCurrent.textContent = t('modal.uploadPathCurrent', { path: uploadPathCurrentValue });
                    uploadPathList.innerHTML = '';

                    if (uploadPathCurrentValue && uploadPathCurrentValue !== '/') {
                        const parent = uploadPathCurrentValue.split('/').filter(Boolean);
                        parent.pop();
                        const parentPath = '/' + parent.join('/');
                        const parentItem = document.createElement('div');
                        parentItem.className = 'upload-path-item';
                        parentItem.textContent = '⬆️ ..';
                        parentItem.addEventListener('click', () => loadUploadPathList(parentPath || '/'));
                        uploadPathList.appendChild(parentItem);
                    }

                    data.files
                        .filter(item => item.is_dir)
                        .forEach(dir => {
                            const item = document.createElement('div');
                            item.className = 'upload-path-item';
                            item.textContent = `📁 ${dir.name}`;
                            item.addEventListener('click', () => loadUploadPathList(dir.path));
                            uploadPathList.appendChild(item);
                        });
                } catch (error) {
                    console.error('读取目录失败:', error);
                    uploadPathCurrent.textContent = t('modal.uploadPathError');
                    uploadPathList.innerHTML = '';
                }
            }

            function closeUploadPathModal(value) {
                if (uploadPathModal) {
                    uploadPathModal.style.display = 'none';
                }
                if (uploadPathResolve) {
                    uploadPathResolve(value);
                    uploadPathResolve = null;
                }
            }

            function promptUploadPath() {
                return new Promise((resolve) => {
                    if (!uploadPathModal) {
                        resolve(null);
                        return;
                    }
                    uploadPathResolve = resolve;
                    uploadPathModal.style.display = 'block';
                    const startPath = defaultUploadDir || '/home/deck';
                    loadUploadPathList(startPath);

                    if (uploadPathOk) {
                        uploadPathOk.onclick = () => {
                            closeUploadPathModal(uploadPathCurrentValue || null);
                        };
                    }
                    if (uploadPathCancel) {
                        uploadPathCancel.onclick = () => {
                            closeUploadPathModal(null);
                        };
                    }
                    if (uploadPathUp) {
                        uploadPathUp.onclick = () => {
                            if (!uploadPathCurrentValue || uploadPathCurrentValue === '/') return;
                            const parent = uploadPathCurrentValue.split('/').filter(Boolean);
                            parent.pop();
                            const parentPath = '/' + parent.join('/');
                            loadUploadPathList(parentPath || '/');
                        };
                    }
                });
            }
            
            uploadArea.addEventListener('click', () => {
                // Reset input so selecting the same file triggers change
                fileInput.value = '';
                fileInput.click();
            });
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', async (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = await getFilesFromDataTransfer(e.dataTransfer);
                addFiles(files, { groupFolders: true });
            });
            
            fileInput.addEventListener('change', (e) => {
                addFiles(e.target.files, { groupFolders: true });
                // Clear value so re-selecting the same file works next time
                fileInput.value = '';
            });

            refreshUploadOptions();

            function getFileKey(file) {
                return file._relativePath || file.webkitRelativePath || file.name;
            }

            function getFileRelativePath(file) {
                return file._relativePath || file.webkitRelativePath || '';
            }

            function getTopFolderName(file) {
                const rel = getFileRelativePath(file);
                if (!rel) return '';
                const parts = rel.split('/');
                if (parts.length <= 1) return '';
                return parts[0] || '';
            }


            async function getFilesFromDataTransfer(dt) {
                if (!dt) return [];
                const items = dt.items ? Array.from(dt.items) : [];
                const entries = items
                    .map(item => item.webkitGetAsEntry && item.webkitGetAsEntry())
                    .filter(Boolean);
                if (entries.length) {
                    const files = [];
                    for (const entry of entries) {
                        const entryFiles = await walkEntry(entry, '');
                        files.push(...entryFiles);
                    }
                    return files;
                }
                return Array.from(dt.files || []);
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
                            } catch (e) {
                                // ignore
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
                        const childFiles = await walkEntry(child, `${pathPrefix}${entry.name}/`);
                        files.push(...childFiles);
                    }
                    return files;
                }
                return [];
            }
            
            
function addFiles(files, options = {}) {
    const groupFolders = !!options.groupFolders;
    for (let file of files) {
        const folderName = groupFolders ? getTopFolderName(file) : '';
        if (folderName) {
            const folderKey = folderName;
            try {
                file._folderKey = folderKey;
            } catch (e) {
                // ignore if readonly
            }
            selectedFiles.push(file);
            if (!folderDisplayMap.has(folderKey)) {
                folderDisplayMap.set(folderKey, { name: folderName });
                const folderItem = document.createElement('div');
                folderItem.className = 'file-item';
                folderItem.dataset.folderKey = folderKey;

                const fileHeader = document.createElement('div');
                fileHeader.className = 'file-item-header';

                const fileInfo = document.createElement('span');
                fileInfo.className = 'file-item-info';
                fileInfo.textContent = `📁 ${folderName}`;
                fileInfo.title = folderName;

                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'cancel-btn';
                cancelBtn.textContent = t('actions.cancel');
                cancelBtn.onclick = () => {
                    selectedFiles = selectedFiles.filter((item) => item._folderKey !== folderKey);
                    folderDisplayMap.delete(folderKey);
                    const existing = document.querySelector(`[data-folder-key="${folderKey}"]`);
                    if (existing) {
                        existing.remove();
                    }
                };

                fileHeader.appendChild(fileInfo);
                fileHeader.appendChild(cancelBtn);
                folderItem.appendChild(fileHeader);
                fileList.appendChild(folderItem);
            }
            continue;
        }

        selectedFiles.push(file);
        const fileKey = getFileKey(file);
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.dataset.fileKey = fileKey;

        // File header (info + cancel button)
        const fileHeader = document.createElement('div');
        fileHeader.className = 'file-item-header';


        // Create file info element
        const fileInfo = document.createElement('span');
        fileInfo.className = 'file-item-info';
        fileInfo.textContent = `${fileKey} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;

        // Create cancel button
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'cancel-btn';
        cancelBtn.textContent = t('actions.cancel');
        cancelBtn.onclick = () => cancelFile(file);

        fileHeader.appendChild(fileInfo);
        fileHeader.appendChild(cancelBtn);

        // Progress section (hidden by default, shown during upload)
        const progressSection = document.createElement('div');
        progressSection.className = 'file-item-progress';
        progressSection.id = `progress-section-${fileKey.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

        const progressBar = document.createElement('div');
        progressBar.className = 'file-progress-bar';

        const progressFill = document.createElement('div');
        progressFill.className = 'file-progress-fill';
        progressFill.id = `progress-fill-${fileKey.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

        progressBar.appendChild(progressFill);

        const progressText = document.createElement('div');
        progressText.className = 'file-progress-text';
        progressText.innerHTML = `
            <span id="progress-percent-${fileKey.replace(/[^a-zA-Z0-9_-]/g, '_')}">0%</span>
            <span class="speed" id="progress-speed-${fileKey.replace(/[^a-zA-Z0-9_-]/g, '_')}">0 KB/s</span>
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
                const key = getFileKey(file);
                const index = selectedFiles.findIndex(f => getFileKey(f) === key);
                if (index > -1) {
                    // Remove file from array
                    selectedFiles.splice(index, 1);
                    
                    // Remove corresponding DOM element
                    const fileItems = document.querySelectorAll('.file-item');
                    fileItems.forEach(item => {
                        if (item.dataset.fileKey === key) {
                            item.remove();
                        }
                    });
                }
            }
            
            // 更新文件列表内的进度条
            function updateFileProgress(fileKey, progress, speed, status = 'uploading') {
                const safeFileName = fileKey.replace(/[^a-zA-Z0-9_-]/g, '_');
                const progressSection = document.getElementById(`progress-section-${safeFileName}`);
                const progressFill = document.getElementById(`progress-fill-${safeFileName}`);
                const progressPercent = document.getElementById(`progress-percent-${safeFileName}`);
                const progressSpeed = document.getElementById(`progress-speed-${safeFileName}`);
                
                console.log(`updateFileProgress调用: ${fileKey}`, {
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
                        progressPercent.textContent = t('status.done');
                    } else if (status === 'error') {
                        progressPercent.textContent = t('status.failed');
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
            
                        
const FILE_PARALLEL = 2;
const CHUNK_THRESHOLD = 512 * 1024 * 1024;
const CHUNK_SIZE = 8 * 1024 * 1024;
const CHUNK_PARALLEL = 3;
const CHUNK_MAX_RETRIES = 3;
const CHUNK_RETRY_BASE = 500;
const HASH_THRESHOLD = 256 * 1024 * 1024;
const HASH_ALGO = 'SHA-256';

function createUploadId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }
    return `upload_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function hashString(input) {
    let hash = 5381;
    for (let i = 0; i < input.length; i++) {
        hash = ((hash << 5) + hash) + input.charCodeAt(i);
        hash &= 0xffffffff;
    }
    return (hash >>> 0).toString(16);
}

function buildUploadId(file, chosenPath) {
    const relPath = getFileRelativePath(file) || '';
    const base = `${file.name}|${file.size}|${file.lastModified}|${relPath}|${chosenPath || ''}`;
    return `up_${hashString(base)}`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function computeFileHash(file) {
    if (!window.crypto || !window.crypto.subtle) {
        return null;
    }
    const buffer = await file.arrayBuffer();
    const digest = await window.crypto.subtle.digest(HASH_ALGO, buffer);
    const bytes = new Uint8Array(digest);
    return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function computeFileHashIfNeeded(file) {
    if (file.size > HASH_THRESHOLD) {
        return null;
    }
    try {
        return await computeFileHash(file);
    } catch (error) {
        console.warn('Hash compute failed', error);
        return null;
    }
}

async function getResumeInfo(uploadId, totalChunks, totalSize) {
    try {
        const response = await fetch('/upload-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ upload_id: uploadId, total_chunks: totalChunks, total_size: totalSize })
        });
        if (!response.ok) return null;
        const data = await response.json();
        if (data.status !== 'success') return null;
        return data;
    } catch (error) {
        console.warn('Upload resume check failed', error);
        return null;
    }
}

function activateProgress(fileKey) {
    const safeFileName = fileKey.replace(/[^a-zA-Z0-9_-]/g, '_');
    const progressSection = document.getElementById(`progress-section-${safeFileName}`);
    if (progressSection) {
        progressSection.classList.add('active');
    }
}

function uploadFileSimple(file, chosenPath, fileHash) {
    return new Promise((resolve) => {
        const fileKey = getFileKey(file);
        activateProgress(fileKey);

        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        if (chosenPath) {
            formData.append('dest_path', chosenPath);
        }
        const relPath = getFileRelativePath(file);
        if (relPath) {
            formData.append('relative_path', relPath);
        }
        if (fileHash) {
            formData.append('file_hash', fileHash);
            formData.append('hash_algo', HASH_ALGO);
        }
        formData.append('file', file);

        let lastUpdateTime = Date.now();
        let lastUploadedBytes = 0;

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const currentTime = Date.now();
                const timeDiff = (currentTime - lastUpdateTime) / 1000;
                const bytesDiff = e.loaded - lastUploadedBytes;

                if (timeDiff >= 0.2 || e.loaded === e.total) {
                    const progress = Math.min(100, Math.round((e.loaded / e.total) * 100));
                    const speed = timeDiff > 0 ? Math.round((bytesDiff / 1024) / timeDiff) : 0;
                    updateFileProgress(fileKey, progress, speed);

                    lastUpdateTime = currentTime;
                    lastUploadedBytes = e.loaded;
                }
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                updateFileProgress(fileKey, 100, 0, 'success');
                resolve({ status: 'success' });
            } else {
                updateFileProgress(fileKey, 100, 0, 'error');
                resolve({ status: 'error' });
            }
        });

        xhr.addEventListener('error', () => {
            updateFileProgress(fileKey, 0, 0, 'error');
            resolve({ status: 'error' });
        });

        xhr.addEventListener('timeout', () => {
            updateFileProgress(fileKey, 0, 0, 'error');
            resolve({ status: 'timeout' });
        });

        xhr.timeout = 0;
        xhr.open('POST', '/upload');
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
    if (resumeInfo && Array.isArray(resumeInfo.received) && resumeInfo.total_chunks === totalChunks && resumeInfo.total_size === file.size) {
        completedChunks = new Set(resumeInfo.received);
        if (completedChunks.size > 0) {
            completedChunks.forEach((index) => {
                const chunkSize = index === totalChunks - 1 ? (file.size - (totalChunks - 1) * CHUNK_SIZE) : CHUNK_SIZE;
                chunkProgress[index] = chunkSize;
                uploadedBytes += chunkSize;
            });
            const progress = Math.min(100, Math.round((uploadedBytes / file.size) * 100));
            updateFileProgress(fileKey, progress, 0);
        }
        if (completedChunks.size >= totalChunks) {
            updateFileProgress(fileKey, 100, 0, 'success');
            return { status: 'success' };
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
        updateFileProgress(fileKey, progress, speed);
    };

    const uploadChunk = (index) => new Promise((resolve, reject) => {
        const start = index * CHUNK_SIZE;
        const end = Math.min(file.size, start + CHUNK_SIZE);
        const blob = file.slice(start, end);

        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('upload_id', uploadId);
        formData.append('chunk_index', String(index));
        formData.append('total_chunks', String(totalChunks));
        formData.append('total_size', String(file.size));
        formData.append('chunk_offset', String(start));
        formData.append('filename', file.name);
        if (chosenPath) {
            formData.append('dest_path', chosenPath);
        }
        const relPath = getFileRelativePath(file);
        if (relPath) {
            formData.append('relative_path', relPath);
        }
        if (fileHash) {
            formData.append('file_hash', fileHash);
            formData.append('hash_algo', HASH_ALGO);
        }
        formData.append('chunk', blob, file.name);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                updateOverallProgress(index, e.loaded);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                updateOverallProgress(index, blob.size);
                resolve();
            } else {
                reject(new Error('chunk upload failed'));
            }
        });
        xhr.addEventListener('error', () => reject(new Error('chunk upload error')));
        xhr.addEventListener('timeout', () => reject(new Error('chunk upload timeout')));
        xhr.timeout = 0;
        xhr.open('POST', '/upload-chunk');
        xhr.send(formData);
    });

    const uploadChunkWithRetry = async (index) => {
        if (completedChunks.has(index)) {
            return;
        }
        for (let attempt = 0; attempt <= CHUNK_MAX_RETRIES; attempt++) {
            try {
                await uploadChunk(index);
                completedChunks.add(index);
                return;
            } catch (err) {
                if (attempt === CHUNK_MAX_RETRIES) {
                    throw err;
                }
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
            if (completedChunks.has(current)) {
                continue;
            }
            await uploadChunkWithRetry(current);
        }
    });

    await Promise.all(workers);
    updateFileProgress(fileKey, 100, 0, 'success');
    return { status: 'success' };
}

async function uploadFile(file, chosenPath) {
    const fileHash = await computeFileHashIfNeeded(file);
    if (file.size >= CHUNK_THRESHOLD) {
        try {
            return await uploadFileChunked(file, chosenPath, fileHash);
        } catch (error) {
            console.error(`${file.name} chunk upload failed`, error);
            updateFileProgress(getFileKey(file), 100, 0, 'error');
            return { status: 'error' };
        }
    }
    return await uploadFileSimple(file, chosenPath, fileHash);
}

uploadBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) {
        alert('请先选择文件');
        return;
    }

    await refreshUploadOptions();
    let chosenPath = null;
    if (uploadPromptEnabled) {
        chosenPath = await promptUploadPath();
        if (!chosenPath) {
            alert('请先选择传输路径');
            return;
        }
    }

    const queueFiles = [...selectedFiles].sort((a, b) => b.size - a.size);
    let uploadedFiles = 0;
    let failedFiles = 0;
    const totalFiles = queueFiles.length;
    let queueIndex = 0;

    const fileWorkers = Array.from({ length: Math.min(FILE_PARALLEL, totalFiles) }, async () => {
        while (true) {
            const currentIndex = queueIndex;
            queueIndex += 1;
            if (currentIndex >= totalFiles) {
                break;
            }
            const file = queueFiles[currentIndex];
            const result = await uploadFile(file, chosenPath);
            uploadedFiles += 1;
            if (!result || result.status !== 'success') {
                failedFiles += 1;
            }
        }
    });

    await Promise.all(fileWorkers);

    if (uploadedFiles === totalFiles) {
        if (failedFiles === 0) {
            setTimeout(() => {
                alert('所有文件上传完成');
                setTimeout(() => {
                    selectedFiles = [];
                    fileList.innerHTML = '';
                                    folderDisplayMap.clear();
                }, 2000);
            }, 500);
        } else {
            setTimeout(() => {
                alert('部分文件上传失败');
            }, 500);
        }
    }
});
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

            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
                (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
            let suppressNextClick = false;
            
            // DOM Elements
            const breadcrumb = document.getElementById('breadcrumb');
            const fileManagerList = document.getElementById('file-manager-list');
            const backBtn = document.getElementById('back-btn');
            const refreshBtn = document.getElementById('refresh-btn');
            const pasteBtn = document.getElementById('paste-btn');
            const newFileBtn = document.getElementById('new-file-btn');
            const newDirBtn = document.getElementById('new-dir-btn');
            const newBtn = document.getElementById('new-btn');
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

            const unpackModal = document.getElementById('unpack-modal');
            const unpackFilename = document.getElementById('unpack-filename');
            const unpackProgressFill = document.getElementById('unpack-progress-fill');
            const unpackProgressText = document.getElementById('unpack-progress-text');
            let unpackTimer = null;
            let unpackProgressValue = 0;

            const fileOpModal = document.getElementById('fileop-modal');
            const fileOpTitle = document.getElementById('fileop-title');
            const fileOpFilename = document.getElementById('fileop-filename');
            const fileOpProgressFill = document.getElementById('fileop-progress-fill');
            const fileOpProgressText = document.getElementById('fileop-progress-text');
            let fileOpTimer = null;
            let fileOpProgressValue = 0;

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

            const newMenu = document.createElement('div');
            newMenu.style.cssText = `
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
            document.body.appendChild(newMenu);
            
            // Context Menu Items
            let pinMenuItem = null;
            let unpackMenuItem = null;
            const contextMenuItems = [
                { text: t('menu.open'), action: 'open' },
                { text: t('menu.download'), action: 'download' },
                { text: t('menu.addToSteam'), action: 'add-to-steam' },
                { text: t('menu.unpack'), action: 'unpack' },
                { text: t('menu.pin'), action: 'pin' },
                { text: t('menu.copy'), action: 'copy' },
                { text: t('menu.cut'), action: 'cut' },
                { text: t('menu.delete'), action: 'delete' },
                { text: t('menu.rename'), action: 'rename' }
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
                if (item.action === 'pin') {
                    pinMenuItem = menuItem;
                }
                if (item.action === 'unpack') {
                    unpackMenuItem = menuItem;
                }
            });

            // New Menu Items (for compact screens)
            const newMenuItems = [
                { text: t('actions.newFile'), action: 'new-file' },
                { text: t('actions.newFolder'), action: 'new-dir' }
            ];
            
            newMenuItems.forEach(item => {
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
                menuItem.addEventListener('click', () => {
                    if (item.action === 'new-file') {
                        showInputModal(t('modal.newFileTitle'), t('modal.newFilePlaceholder'), createFile);
                    } else {
                        showInputModal(t('modal.newFolderTitle'), t('modal.newFolderPlaceholder'), createDirectory);
                    }
                    hideNewMenu();
                });
                newMenu.appendChild(menuItem);
            });

            const PINNED_STORAGE_KEY = 'decky_send_pinned_items';

            function loadPinnedMap() {
                try {
                    const raw = localStorage.getItem(PINNED_STORAGE_KEY);
                    if (!raw) return {};
                    const parsed = JSON.parse(raw);
                    return parsed && typeof parsed === 'object' ? parsed : {};
                } catch (e) {
                    console.error('读取置顶信息失败:', e);
                    return {};
                }
            }

            function savePinnedMap(map) {
                try {
                    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(map));
                } catch (e) {
                    console.error('保存置顶信息失败:', e);
                }
            }

            function getPinnedSet(path) {
                const map = loadPinnedMap();
                const list = Array.isArray(map[path]) ? map[path] : [];
                return new Set(list);
            }

            function setPinnedSet(path, set) {
                const map = loadPinnedMap();
                map[path] = Array.from(set);
                savePinnedMap(map);
            }

            function togglePin(path) {
                const set = getPinnedSet(currentPath);
                if (set.has(path)) {
                    set.delete(path);
                } else {
                    set.add(path);
                }
                setPinnedSet(currentPath, set);
            }

            function updatePinMenuLabel() {
                if (!pinMenuItem) return;
                const set = getPinnedSet(currentPath);
                pinMenuItem.textContent = set.has(contextMenuPath) ? t('menu.unpin') : t('menu.pin');
            }

            function isArchiveFile(name) {
                if (!name) return false;
                const lower = name.toLowerCase();
                const exts = ['.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz', '.tbz2', '.txz', '.tar', '.zip', '.7z', '.rar', '.exe'];
                return exts.some(ext => lower.endsWith(ext));
            }

            function updateUnpackMenuVisibility() {
                if (!unpackMenuItem) return;
                const fileItem = document.querySelector(`[data-path="${contextMenuPath}"]`);
                const isDir = fileItem && fileItem.dataset.isDir === 'true';
                const filename = contextMenuPath ? contextMenuPath.split('/').pop() : '';
                const canUnpack = !isDir && isArchiveFile(filename);
                unpackMenuItem.style.display = canUnpack ? 'block' : 'none';
            }
            
            // Context Menu Functions
            let copiedPath = null; // Store copied/cut file/folder path
            let clipboardMode = 'copy';

            function bindLongPressContextMenu(element, path, beforeShow) {
                if (!isIOS) {
                    return;
                }

                let pressTimer = null;
                let startX = 0;
                let startY = 0;
                let lastX = 0;
                let lastY = 0;
                const longPressMs = 550;
                const moveTolerance = 10;

                const clearPressTimer = () => {
                    if (pressTimer) {
                        clearTimeout(pressTimer);
                        pressTimer = null;
                    }
                };

                element.addEventListener('touchstart', (e) => {
                    if (!e.touches || e.touches.length !== 1) {
                        return;
                    }
                    const touch = e.touches[0];
                    startX = touch.clientX;
                    startY = touch.clientY;
                    lastX = startX;
                    lastY = startY;
                    clearPressTimer();
                    pressTimer = setTimeout(() => {
                        pressTimer = null;
                        suppressNextClick = true;
                        if (beforeShow) {
                            beforeShow();
                        }
                        showContextMenu({ clientX: lastX, clientY: lastY, preventDefault: () => {} }, path);
                    }, longPressMs);
                }, { passive: true });

                element.addEventListener('touchmove', (e) => {
                    if (!pressTimer || !e.touches || e.touches.length !== 1) {
                        return;
                    }
                    const touch = e.touches[0];
                    lastX = touch.clientX;
                    lastY = touch.clientY;
                    if (Math.abs(lastX - startX) > moveTolerance || Math.abs(lastY - startY) > moveTolerance) {
                        clearPressTimer();
                    }
                }, { passive: true });

                element.addEventListener('touchend', clearPressTimer);
                element.addEventListener('touchcancel', clearPressTimer);
            }
            
            function showContextMenu(e, path) {
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                contextMenuPath = path;
                updatePinMenuLabel();
                updateUnpackMenuVisibility();
                contextMenu.style.display = 'block';
                
                const padding = 8;
                const menuRect = contextMenu.getBoundingClientRect();
                const point = (e && e.touches && e.touches[0]) ||
                    (e && e.changedTouches && e.changedTouches[0]) ||
                    e || { clientX: 0, clientY: 0 };
                let x = point.clientX;
                let y = point.clientY;
                const maxX = window.innerWidth - menuRect.width - padding;
                const maxY = window.innerHeight - menuRect.height - padding;
                if (maxX < padding) {
                    x = padding;
                } else {
                    x = Math.min(Math.max(x, padding), maxX);
                }
                if (maxY < padding) {
                    y = padding;
                } else {
                    y = Math.min(Math.max(y, padding), maxY);
                }
                
                contextMenu.style.left = x + 'px';
                contextMenu.style.top = y + 'px';
            }
            
            function hideContextMenu() {
                contextMenu.style.display = 'none';
                contextMenuPath = '';
            }

            function showNewMenu() {
                if (!newMenu || !newBtn) return;
                newMenu.style.display = 'block';
                
                const padding = 8;
                const rect = newBtn.getBoundingClientRect();
                const menuRect = newMenu.getBoundingClientRect();
                let x = rect.left;
                let y = rect.bottom + 6;
                
                if (y + menuRect.height > window.innerHeight - padding) {
                    y = rect.top - menuRect.height - 6;
                }
                
                const maxX = window.innerWidth - menuRect.width - padding;
                const maxY = window.innerHeight - menuRect.height - padding;
                if (maxX < padding) {
                    x = padding;
                } else {
                    x = Math.min(Math.max(x, padding), maxX);
                }
                if (maxY < padding) {
                    y = padding;
                } else {
                    y = Math.min(Math.max(y, padding), maxY);
                }
                
                newMenu.style.left = x + 'px';
                newMenu.style.top = y + 'px';
            }
            
            function hideNewMenu() {
                if (!newMenu) return;
                newMenu.style.display = 'none';
            }

            function isCompactScreen() {
                const area = window.innerWidth * window.innerHeight;
                return area < 420000 || window.innerWidth < 520;
            }

            function applyFileManagerLayout() {
                const compact = isCompactScreen();
                if (fileManagerList) {
                    fileManagerList.classList.toggle('list-mode', compact);
                    const items = fileManagerList.querySelectorAll('.file-item');
                    items.forEach(item => {
                        item.style.flex = compact ? '1 1 auto' : '1 1 120px';
                        item.style.maxWidth = compact ? 'none' : '200px';
                        item.style.width = compact ? '100%' : '';
                        item.style.flexDirection = compact ? 'row' : 'column';
                        item.style.justifyContent = compact ? 'flex-start' : 'center';
                        item.style.alignItems = 'center';
                        item.style.gap = compact ? '10px' : '5px';
                        item.style.minHeight = compact ? '52px' : '100px';
                        item.style.padding = compact ? '8px 10px' : '10px';
                        
                        const icon = item.querySelector('.file-icon');
                        if (icon) {
                            icon.style.fontSize = compact ? '20px' : '24px';
                        }
                        
                        const name = item.querySelector('.file-name');
                        if (name) {
                            name.style.textAlign = compact ? 'left' : 'center';
                            name.style.flex = compact ? '1 1 auto' : '';
                        }
                        
                        const details = item.querySelector('.file-details');
                        if (details) {
                            details.style.textAlign = compact ? 'right' : 'center';
                            details.style.marginLeft = compact ? 'auto' : '';
                        }
                    });
                }
                if (newBtn && newFileBtn && newDirBtn) {
                    newBtn.style.display = compact ? 'inline-block' : 'none';
                    newFileBtn.style.display = compact ? 'none' : 'inline-block';
                    newDirBtn.style.display = compact ? 'none' : 'inline-block';
                }
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
                    case 'unpack':
                        if (contextMenuPath) {
                            try {
                                showUnpackProgress(contextMenuPath.split('/').pop());
                                const response = await fetch('/api/files/unpack', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({ path: contextMenuPath })
                                });
                                const result = await response.json();
                                if (result.status === 'success') {
                                    finishUnpackProgress(true);
                                    alert(result.message || '解压完成');
                                    await renderFileList(currentPath);
                                } else {
                                    finishUnpackProgress(false);
                                    alert('解压失败: ' + (result.message || '未知错误'));
                                }
                            } catch (error) {
                                console.error('解压出错:', error);
                                finishUnpackProgress(false);
                                alert('解压出错');
                            }
                        }
                        break;
                    case 'unpack':
                        if (contextMenuPath) {
                            try {
                                const response = await fetch('/api/files/unpack', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({ path: contextMenuPath })
                                });
                                const result = await response.json();
                                if (result.status === 'success') {
                                    alert(result.message || '解压完成');
                                    await renderFileList(currentPath);
                                } else {
                                    alert('解压失败: ' + (result.message || '未知错误'));
                                }
                            } catch (error) {
                                console.error('解压出错:', error);
                                alert('解压出错');
                            }
                        }
                        break;
                    case 'pin':
                        if (contextMenuPath) {
                            togglePin(contextMenuPath);
                            await renderFileList(currentPath);
                        }
                        break;
                    case 'copy':
                        if (contextMenuPath) {
                            await copyPath(contextMenuPath);
                        }
                        break;
                    case 'cut':
                        if (contextMenuPath) {
                            await cutPath(contextMenuPath);
                        }
                        break;
                    case 'paste':
                        await pastePath(currentPath);
                        break;
                    case 'delete':
                        if (contextMenuPath) {
                            // Save the path before showing confirm modal (which hides context menu)
                            const pathToDelete = contextMenuPath;
                            showConfirmModal(t('modal.deleteConfirm'), async () => {
                                await deletePath(pathToDelete);
                            });
                        }
                        break;
                    case 'rename':
                        if (contextMenuPath) {
                            // Implement rename functionality
                            const oldName = contextMenuPath.split('/').pop() || '';
                            showInputModal(t('modal.renameTitle'), t('modal.renamePlaceholder'), (newName) => {
                                // Implement rename API call here
                                alert('重命名功能将在后续版本中实现');
                            }, oldName);
                        }
                        break;
                }
            }
            
            if (newBtn) {
                newBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    hideContextMenu();
                    showNewMenu();
                });
            }
            
            if (newMenu) {
                newMenu.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
            }
            
            // Hide menus when clicking elsewhere
            document.addEventListener('click', (e) => {
                if (suppressNextClick && e.target.closest('.file-item')) {
                    suppressNextClick = false;
                    return;
                }
                suppressNextClick = false;
                hideContextMenu();
                hideNewMenu();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    hideContextMenu();
                    hideNewMenu();
                }
            });
            
            window.addEventListener('resize', applyFileManagerLayout);
            
            function showConfirmModal(message, action) {
                confirmMessage.textContent = message;
                currentConfirmAction = action;
                confirmModal.style.display = 'block';
            }
            
            function hideConfirmModal() {
                confirmModal.style.display = 'none';
                currentConfirmAction = null;
            }
            
            function showInputModal(title, placeholder, action, defaultValue = '') {
                inputTitle.textContent = title;
                inputField.placeholder = placeholder;
                inputField.value = defaultValue || '';
                currentInputAction = action;
                inputModal.style.display = 'block';
                inputField.focus();
                try {
                    if (inputField.value) {
                        inputField.setSelectionRange(0, inputField.value.length);
                    }
                } catch (e) {
                    // ignore
                }
            }
            
            function hideInputModal() {
                inputModal.style.display = 'none';
                currentInputAction = null;
            }

            function showUnpackProgress(filename) {
                if (!unpackModal) return;
                if (unpackFilename) {
                    unpackFilename.textContent = filename ? t('modal.unpackingWithName', { name: filename }) : t('modal.unpacking');
                }
                unpackProgressValue = 0;
                if (unpackProgressFill) {
                    unpackProgressFill.style.width = '0%';
                }
                if (unpackProgressText) {
                    unpackProgressText.textContent = '0%';
                }
                unpackModal.style.display = 'block';
                if (unpackTimer) {
                    clearInterval(unpackTimer);
                }
                unpackTimer = setInterval(() => {
                    const increment = Math.max(1, Math.round(Math.random() * 4));
                    unpackProgressValue = Math.min(90, unpackProgressValue + increment);
                    if (unpackProgressFill) {
                        unpackProgressFill.style.width = `${unpackProgressValue}%`;
                    }
                    if (unpackProgressText) {
                        unpackProgressText.textContent = `${unpackProgressValue}%`;
                    }
                }, 200);
            }

            function finishUnpackProgress(success) {
                if (!unpackModal) return;
                if (unpackTimer) {
                    clearInterval(unpackTimer);
                    unpackTimer = null;
                }
                if (unpackProgressFill) {
                    unpackProgressFill.style.width = '100%';
                }
                if (unpackProgressText) {
                    unpackProgressText.textContent = success ? t('status.done') : t('status.failed');
                }
                setTimeout(() => {
                    unpackModal.style.display = 'none';
                }, 500);
            }

            function showFileOpProgress(title, filename) {
                if (!fileOpModal) return;
                if (fileOpTitle) {
                    fileOpTitle.textContent = title || t('modal.fileOpCopy');
                }
                if (fileOpFilename) {
                    fileOpFilename.textContent = filename ? t('modal.fileOpTarget', { name: filename }) : '';
                }
                fileOpProgressValue = 0;
                if (fileOpProgressFill) {
                    fileOpProgressFill.style.width = '0%';
                }
                if (fileOpProgressText) {
                    fileOpProgressText.textContent = '0%';
                }
                fileOpModal.style.display = 'block';
                if (fileOpTimer) {
                    clearInterval(fileOpTimer);
                }
                fileOpTimer = setInterval(() => {
                    const increment = Math.max(1, Math.round(Math.random() * 4));
                    fileOpProgressValue = Math.min(90, fileOpProgressValue + increment);
                    if (fileOpProgressFill) {
                        fileOpProgressFill.style.width = `${fileOpProgressValue}%`;
                    }
                    if (fileOpProgressText) {
                        fileOpProgressText.textContent = `${fileOpProgressValue}%`;
                    }
                }, 200);
            }

            function finishFileOpProgress(success) {
                if (!fileOpModal) return;
                if (fileOpTimer) {
                    clearInterval(fileOpTimer);
                    fileOpTimer = null;
                }
                if (fileOpProgressFill) {
                    fileOpProgressFill.style.width = '100%';
                }
                if (fileOpProgressText) {
                    fileOpProgressText.textContent = success ? t('status.done') : t('status.failed');
                }
                setTimeout(() => {
                    fileOpModal.style.display = 'none';
                }, 500);
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
                        if (unpackModal) {
                            unpackModal.style.display = 'none';
                        }
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

                        const pinnedSet = getPinnedSet(data.current_path);
                        const currentPaths = new Set(data.files.map(item => item.path));
                        let cleaned = false;
                        for (const pinnedPath of Array.from(pinnedSet)) {
                            if (!currentPaths.has(pinnedPath)) {
                                pinnedSet.delete(pinnedPath);
                                cleaned = true;
                            }
                        }
                        if (cleaned) {
                            setPinnedSet(data.current_path, pinnedSet);
                        }

                        const files = data.files.map((file, index) => ({ ...file, __index: index }));
                        files.sort((a, b) => {
                            const aPinned = pinnedSet.has(a.path);
                            const bPinned = pinnedSet.has(b.path);
                            if (aPinned !== bPinned) return aPinned ? -1 : 1;
                            return a.__index - b.__index;
                        });
                        
                        files.forEach(file => {
                            const fileItem = document.createElement('div');
                            fileItem.className = 'file-item';
                            fileItem.dataset.path = file.path;
                            fileItem.dataset.isDir = file.is_dir;
                            if (file.is_dir) {
                                fileItem.classList.add('is-dir');
                            }
                            const isPinned = pinnedSet.has(file.path);
                            if (isPinned) {
                                fileItem.classList.add('pinned');
                            }
                            
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
                            fileItem.addEventListener('click', (e) => {
                                if (suppressNextClick) {
                                    suppressNextClick = false;
                                    e.preventDefault();
                                    e.stopPropagation();
                                    return;
                                }
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

                            bindLongPressContextMenu(fileItem, file.path, () => {
                                document.querySelectorAll('.file-item.selected').forEach(item => {
                                    item.classList.remove('selected');
                                    item.style.backgroundColor = 'var(--panel)';
                                    item.style.borderColor = 'var(--border)';
                                });
                                fileItem.classList.add('selected');
                                fileItem.style.backgroundColor = 'var(--accent-soft)';
                                fileItem.style.borderColor = 'var(--accent)';
                                selectedFileManagerFiles = [file.path];
                            });
                            
                            const pinBadge = document.createElement('div');
                            pinBadge.className = 'pin-badge';
                            pinBadge.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="#ffffff" d="M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-9a1 1 0 0 1 1-1h1zm2 0h6V7a3 3 0 0 0-6 0v3zm3 4a2 2 0 0 0-1 3.732V19a1 1 0 0 0 2 0v-1.268A2 2 0 0 0 12 14z"/></svg>';
                            if (!isPinned) {
                                pinBadge.style.display = 'none';
                            }

                            // File Icon
                            const icon = document.createElement('div');
                            icon.className = 'file-icon';
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
                            fileDetails.className = 'file-details';
                            fileDetails.style.fontSize = '10px';
                            fileDetails.style.color = 'var(--muted)';
                            fileDetails.style.textAlign = 'center';
                            
                            if (file.is_dir) {
                                fileDetails.textContent = '';
                                fileDetails.style.display = 'none';
                            } else {
                                fileDetails.innerHTML = `${formatSize(file.size)}<br>${formatDate(file.mtime)}`;
                            }
                            
                            fileItem.appendChild(pinBadge);
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
                        applyFileManagerLayout();
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
                        showFileEditor(t('modal.editorTitleWithName', { name: filePath.split('/').pop() || '' }), data.content, filePath);
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
                    clipboardMode = 'copy';
                    // Show paste button
                    updatePasteButtonVisibility();
                    alert('复制成功');
                } catch (error) {
                    console.error('复制出错:', error);
                    alert('复制出错');
                }
            }

            async function cutPath(path) {
                try {
                    if (!path) {
                        alert('剪切失败: 路径不能为空');
                        return;
                    }

                    copiedPath = path;
                    clipboardMode = 'cut';
                    updatePasteButtonVisibility();
                    alert('剪切成功');
                } catch (error) {
                    console.error('剪切出错:', error);
                    alert('剪切出错');
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
                    const isCut = clipboardMode === 'cut';
                    const opTitle = isCut ? t('modal.fileOpMove') : t('modal.fileOpCopy');
                    showFileOpProgress(opTitle, filename);
                    const endpoint = isCut ? '/api/files/move' : '/api/files/copy';
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ source: copiedPath, destination: targetPath })
                    });
                    
                    const data = await response.json();
                    finishFileOpProgress(data.status === 'success');
                    if (data.status === 'success') {
                        await renderFileList(currentPath);
                        alert(isCut ? '剪切成功' : '粘贴成功');
                        // Clear copied path and hide paste button
                        copiedPath = null;
                        clipboardMode = 'copy';
                        updatePasteButtonVisibility();
                    } else {
                        alert((isCut ? '剪切' : '粘贴') + '失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('粘贴出错:', error);
                    finishFileOpProgress(false);
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
                showInputModal(t('modal.newFileTitle'), t('modal.newFilePlaceholder'), createFile);
            });
            
            // 新建文件夹按钮事件
            newDirBtn.addEventListener('click', () => {
                showInputModal(t('modal.newFolderTitle'), t('modal.newFolderPlaceholder'), createDirectory);
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


async def handle_upload_options(request, plugin):
    """Return upload options for the web client"""
    try:
        return web.json_response({
            "status": "success",
            "prompt_upload_path": bool(getattr(plugin, "prompt_upload_path_enabled", False)),
            "default_dir": getattr(plugin, "downloads_dir", "")
        })
    except Exception as e:
        decky.logger.error(f"Failed to get upload options: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_language_settings(request, plugin):
    """Return language preference for the web client"""
    try:
        language = getattr(plugin, "language_preference", "auto") or "auto"
        return web.json_response({"status": "success", "language": language})
    except Exception as e:
        decky.logger.error(f"Failed to get language preference: {e}")
        return web.json_response({"status": "error", "message": str(e), "language": "auto"}, status=500)


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
        dest_path = None
        relative_path = None
        file_field = None
        expected_hash = None
        expected_algo = None

        while field:
            if field.name == 'dest_path':
                try:
                    dest_path = (await field.text()).strip()
                except Exception:
                    dest_path = None
            elif field.name == 'relative_path':
                try:
                    relative_path = (await field.text()).strip()
                except Exception:
                    relative_path = None
            elif field.name == 'file_hash':
                try:
                    expected_hash = (await field.text()).strip()
                except Exception:
                    expected_hash = None
            elif field.name == 'hash_algo':
                try:
                    expected_algo = (await field.text()).strip()
                except Exception:
                    expected_algo = None
            elif field.name == 'file' and field.filename:
                file_field = field
                break
            field = await reader.next()

        if file_field and file_field.filename:
            raw_filename = file_field.filename.replace('\x00', '')
            safe_filename = os.path.basename(raw_filename.replace('\\', '/')).strip()
            if safe_filename in ("", ".", ".."):
                safe_filename = f"upload_{int(time.time())}"
            filename = safe_filename
            upload_dir = plugin.downloads_dir
            if dest_path:
                if "\x00" in dest_path:
                    return web.json_response({"status": "error", "message": "目录路径包含非法字符"}, status=400)
                resolved = os.path.realpath(os.path.expanduser(dest_path))
                if not resolved:
                    return web.json_response({"status": "error", "message": "无效的目录路径"}, status=400)
                if os.path.exists(resolved) and not os.path.isdir(resolved):
                    return web.json_response({"status": "error", "message": "目标路径不是文件夹"}, status=400)
                try:
                    os.makedirs(resolved, exist_ok=True)
                except Exception:
                    return web.json_response({"status": "error", "message": "无法创建目标目录"}, status=400)
                upload_dir = resolved
            rel_path = None
            if relative_path:
                cleaned = relative_path.replace('\\', '/').lstrip('/')
                normalized = os.path.normpath(cleaned)
                if normalized.startswith("..") or os.path.isabs(normalized):
                    return web.json_response({"status": "error", "message": "无效的相对路径"}, status=400)
                rel_dir = os.path.dirname(normalized)
                rel_base = os.path.basename(normalized)
                safe_base = os.path.basename(rel_base.replace('\\', '/')).strip()
                if safe_base in ("", ".", ".."):
                    safe_base = safe_filename
                rel_path = os.path.join(rel_dir, safe_base) if rel_dir else safe_base

            file_path = os.path.join(upload_dir, rel_path or filename)
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            except Exception:
                return web.json_response({"status": "error", "message": "无法创建目标目录"}, status=400)
            
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
            with open(file_path, 'wb', buffering=1024 * 1024) as f:
                while True:
                    try:
                        chunk = await file_field.read_chunk(size=1024 * 1024)  # Read 1MB chunk
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
                            await _emit_decky(plugin, 
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
            computed_hash = None
            algo_name = _normalize_hash_algo(expected_algo)
            try:
                computed_hash = await _compute_file_hash_async(file_path, algo_name)
                if expected_hash and computed_hash.lower() != expected_hash.lower():
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    return web.json_response({"status": "error", "message": "文件校验失败"}, status=400)
            except Exception as hash_error:
                decky.logger.error(f"Hash compute error: {hash_error}")
                if expected_hash:
                    return web.json_response({"status": "error", "message": "文件校验出错"}, status=500)

            decky.logger.info(f"Upload completed: {filename}, Actual size: {actual_size} bytes")
            
            # Emit final 100% progress with actual size
            await _emit_decky(plugin, 
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
            await _emit_decky(plugin, "transfer_complete", [filename])
            
            # Send notifications (Decky UI + system) so it works even when UI is closed
            notification_title = "文件传输完成"
            notification_msg = f"文件 '{filename}' 已成功上传到 Steam Deck"
            try:
                await _emit_decky(plugin, "_show_notification", {
                    "title": notification_title,
                    "body": notification_msg,
                    "duration": 5
                })
            except Exception as notify_error:
                decky.logger.error(f"Failed to emit Decky notification for file upload: {notify_error}")
            utils.send_system_notification(notification_title, notification_msg, 5)
            utils.queue_notification(notification_title, notification_msg)
            
            return web.json_response({"filename": filename, "status": "success", "hash": computed_hash, "hash_algo": algo_name})
        
        return web.json_response({"status": "error", "message": "No file provided"}, status=400)
    
    except Exception as e:
        decky.logger.error(f"Upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_upload_chunk(request, plugin):
    """Handle chunked file upload request"""
    try:
        reader = await request.multipart()
        field = await reader.next()
        file_field = None
        expected_hash = None
        expected_algo = None
        fields = {}

        while field:
            if field.name == 'chunk' and field.filename:
                file_field = field
            else:
                try:
                    fields[field.name] = (await field.text()).strip()
                except Exception:
                    fields[field.name] = ''
            field = await reader.next()

        if not file_field:
            return web.json_response({"status": "error", "message": "No chunk provided"}, status=400)

        upload_id = fields.get('upload_id') or fields.get('uploadId') or f"upload_{int(time.time())}"
        try:
            chunk_index = int(fields.get('chunk_index', '0') or 0)
        except ValueError:
            chunk_index = 0
        try:
            total_chunks = int(fields.get('total_chunks', '1') or 1)
        except ValueError:
            total_chunks = 1
        try:
            total_size = int(fields.get('total_size', '0') or 0)
        except ValueError:
            total_size = 0
        try:
            chunk_offset = int(fields.get('chunk_offset', '') or (chunk_index * 0))
        except ValueError:
            chunk_offset = 0

        dest_path = fields.get('dest_path') or None
        expected_hash = fields.get('file_hash') or None
        expected_algo = fields.get('hash_algo') or None
        relative_path = fields.get('relative_path') or None
        filename_field = fields.get('filename') or file_field.filename or ''
        raw_filename = filename_field.replace('\x00', '')
        safe_filename = os.path.basename(raw_filename.replace('\\', '/')).strip()
        if safe_filename in ("", ".", ".."):
            safe_filename = f"upload_{int(time.time())}"
        filename = safe_filename

        upload_dir = plugin.downloads_dir
        if dest_path:
            if "\x00" in dest_path:
                return web.json_response({"status": "error", "message": "目录路径包含非法字符"}, status=400)
            resolved = os.path.realpath(os.path.expanduser(dest_path))
            if not resolved:
                return web.json_response({"status": "error", "message": "无效的目录路径"}, status=400)
            if os.path.exists(resolved) and not os.path.isdir(resolved):
                return web.json_response({"status": "error", "message": "目标路径不是文件夹"}, status=400)
            try:
                os.makedirs(resolved, exist_ok=True)
            except Exception:
                return web.json_response({"status": "error", "message": "无法创建目标目录"}, status=400)
            upload_dir = resolved

        rel_path = None
        if relative_path:
            cleaned = relative_path.replace('\\', '/').lstrip('/')
            normalized = os.path.normpath(cleaned)
            if normalized.startswith("..") or os.path.isabs(normalized):
                return web.json_response({"status": "error", "message": "无效的相对路径"}, status=400)
            rel_dir = os.path.dirname(normalized)
            rel_base = os.path.basename(normalized)
            safe_base = os.path.basename(rel_base.replace('\\', '/')).strip()
            if safe_base in ("", ".", ".."):
                safe_base = safe_filename
            rel_path = os.path.join(rel_dir, safe_base) if rel_dir else safe_base

        file_path = os.path.join(upload_dir, rel_path or filename)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception:
            return web.json_response({"status": "error", "message": "无法创建目标目录"}, status=400)

        temp_path = file_path + ".part"
        sessions, lock = _get_upload_session_store(plugin)
        now = time.time()

        async with lock:
            stale_keys = [key for key, sess in sessions.items() if now - sess.get("last_update", now) > 7200]
            for key in stale_keys:
                sessions.pop(key, None)

            session = sessions.get(upload_id)
            if not session:
                session = {
                    "file_path": file_path,
                    "expected_hash": expected_hash,
                    "hash_algo": _normalize_hash_algo(expected_algo),
                    "temp_path": temp_path,
                    "total_chunks": total_chunks,
                    "total_size": total_size,
                    "received": set(),
                    "received_bytes": 0,
                    "start_time": now,
                    "last_emit": now,
                    "last_update": now,
                    "filename": filename
                }
                sessions[upload_id] = session
            else:
                session["last_update"] = now
                if expected_hash and not session.get("expected_hash"):
                    session["expected_hash"] = expected_hash
                if expected_algo and not session.get("hash_algo"):
                    session["hash_algo"] = _normalize_hash_algo(expected_algo)

        if not os.path.exists(temp_path):
            try:
                with open(temp_path, 'wb') as f:
                    if total_size > 0:
                        f.truncate(total_size)
            except Exception:
                pass

        chunk_data = await file_field.read()

        try:
            if hasattr(os, "pwrite"):
                fd = os.open(temp_path, os.O_RDWR | os.O_CREAT)
                try:
                    os.pwrite(fd, chunk_data, chunk_offset)
                finally:
                    os.close(fd)
            else:
                with open(temp_path, 'r+b') as f:
                    f.seek(chunk_offset)
                    f.write(chunk_data)
        except Exception as write_error:
            decky.logger.error(f"Chunk write error: {write_error}")
            return web.json_response({"status": "error", "message": "写入失败"}, status=500)

        complete = False
        async with lock:
            session = sessions.get(upload_id)
            if session is None:
                session = sessions.setdefault(upload_id, {
                    "file_path": file_path,
                    "expected_hash": expected_hash,
                    "hash_algo": _normalize_hash_algo(expected_algo),
                    "temp_path": temp_path,
                    "total_chunks": total_chunks,
                    "total_size": total_size,
                    "received": set(),
                    "received_bytes": 0,
                    "start_time": now,
                    "last_emit": now,
                    "last_update": now,
                    "filename": filename
                })
            session["last_update"] = now
            if chunk_index not in session["received"]:
                session["received"].add(chunk_index)
                session["received_bytes"] += len(chunk_data)

            received_bytes = session["received_bytes"]
            total_for_progress = session["total_size"] or total_size or received_bytes
            elapsed = max(now - session["start_time"], 0.001)
            if now - session["last_emit"] >= 0.5:
                speed = received_bytes / elapsed
                eta = 0
                if speed > 0 and total_for_progress > received_bytes:
                    eta = int((total_for_progress - received_bytes) / speed)
                await _emit_decky(plugin, 
                    "transfer_status",
                    [
                        session["filename"],
                        total_for_progress,
                        received_bytes,
                        speed,
                        eta
                    ]
                )
                session["last_emit"] = now

            complete = len(session["received"]) >= session["total_chunks"]

        if complete:
            hash_algo = session.get("hash_algo") or "sha256"
            expected = session.get("expected_hash")
            computed_hash = None
            try:
                computed_hash = await _compute_file_hash_async(temp_path, hash_algo)
                if expected and computed_hash.lower() != expected.lower():
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    return web.json_response({"status": "error", "message": "文件校验失败"}, status=400)
            except Exception as hash_error:
                decky.logger.error(f"Hash compute error: {hash_error}")
                if expected:
                    return web.json_response({"status": "error", "message": "文件校验出错"}, status=500)

            try:
                os.replace(temp_path, file_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.replace(temp_path, file_path)

            actual_size = os.path.getsize(file_path)
            await _emit_decky(plugin, "transfer_status", [filename, actual_size, actual_size, 0, 0])
            await _emit_decky(plugin, "transfer_complete", [filename])

            try:
                with open(plugin.text_file_path, "w") as f:
                    f.write("")
                decky.logger.info(f"Cleared text file after file transfer: {plugin.text_file_path}")
            except Exception as e:
                decky.logger.error(f"Error clearing text file: {e}")

            notification_title = "文件传输完成"
            notification_msg = f"文件 '{filename}' 已成功上传到 Steam Deck"
            try:
                await _emit_decky(plugin, "_show_notification", {
                    "title": notification_title,
                    "body": notification_msg,
                    "duration": 5
                })
            except Exception as notify_error:
                decky.logger.error(f"Failed to emit Decky notification for file upload: {notify_error}")
            utils.send_system_notification(notification_title, notification_msg, 5)
            utils.queue_notification(notification_title, notification_msg)

            async with lock:
                sessions.pop(upload_id, None)

            return web.json_response({"status": "success", "complete": True, "filename": filename, "hash": computed_hash, "hash_algo": hash_algo})

        return web.json_response({"status": "success", "complete": False})

    except Exception as e:
        decky.logger.error(f"Chunk upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)



async def handle_upload_status(request, plugin):
    """Return received chunk info for resume"""
    try:
        data = await request.json()
        upload_id = (data.get('upload_id') or '').strip()
        if not upload_id:
            return web.json_response({"status": "error", "message": "Missing upload_id"}, status=400)
        sessions, lock = _get_upload_session_store(plugin)
        async with lock:
            session = sessions.get(upload_id)
            if not session:
                return web.json_response({
                    "status": "success",
                    "found": False,
                    "received": [],
                    "total_chunks": int(data.get('total_chunks') or 0),
                    "total_size": int(data.get('total_size') or 0),
                    "received_bytes": 0
                })
            received = list(session.get('received', set()))
            received.sort()
            return web.json_response({
                "status": "success",
                "found": True,
                "received": received,
                "total_chunks": session.get('total_chunks', 0),
                "total_size": session.get('total_size', 0),
                "received_bytes": session.get('received_bytes', 0)
            })
    except Exception as e:
        decky.logger.error(f"Upload status error: {e}")
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
        await _emit_decky(plugin, "text_received", [text])

        # Auto-copy text to clipboard if enabled
        if getattr(plugin, "auto_copy_text_enabled", False):
            try:
                if not utils.set_clipboard_text(text):
                    decky.logger.warning("Auto copy text failed: clipboard utility not available")
            except Exception as copy_error:
                decky.logger.warning(f"Auto copy text failed: {copy_error}")
        
        # Send notifications (Decky UI + system) so it works even when UI is closed
        notification_title = "文本传输完成"
        notification_msg = "新的文本内容已接收并保存"
        try:
            await _emit_decky(plugin, "_show_notification", {
                "title": notification_title,
                "body": notification_msg,
                "duration": 5
            })
        except Exception as notify_error:
            decky.logger.error(f"Failed to emit Decky notification for text upload: {notify_error}")
        utils.send_system_notification(notification_title, notification_msg, 5)
        utils.queue_notification(notification_title, notification_msg)
        
        return web.json_response({"status": "success", "message": "Text received successfully"})

    except Exception as e:
        decky.logger.error(f"Text upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

