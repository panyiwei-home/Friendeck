import i18n from "i18next";
import { initReactI18next } from "react-i18next";

export const LANGUAGE_NAMES: Record<string, string> = {
  "en-US": "English",
  "zh-CN": "简体中文",
};

const resources = {
  "zh-CN": {
    translation: {
      common: {
        init: "初始化中...",
        settings: "设置",
        saving: "保存中...",
        savePort: "保存端口",
        copyFailedTitle: "复制失败",
        copyFailedBody: "无法复制文本到剪贴板，请手动复制",
      },
      service: {
        label: "文件传输服务",
        status: {
          switching: "正在切换...",
          running: "服务运行中",
          stopped: "服务已停止",
        },
      },
      access: {
        title: "访问方式",
        qrAria: "QR码: {{url}}",
        urlAria: "服务器URL地址",
      },
      transfer: {
        title: "传输记录",
        none: "当前无传输任务",
        sent: "已传输: {{size}}",
        speed: "速度: {{speed}}/s",
        remaining: "剩余: {{time}}",
        copy: {
          ready: "复制到剪贴板",
          copying: "复制中...",
          success: "复制成功",
        },
      },
      toasts: {
        serviceStartedTitle: "服务已启动",
        serviceStartedBody: "文件传输服务已成功启动",
        startFailedTitle: "启动失败",
        startFailedBody: "无法启动服务",
        serviceStoppedTitle: "服务已停止",
        serviceStoppedBody: "文件传输服务已停止",
        stopFailedTitle: "停止失败",
        stopFailedBody: "无法停止服务",
        toggleFailedTitle: "操作失败",
        toggleFailedBody: "切换服务状态时发生错误",
        settingsFailedTitle: "设置失败",
        autoCopyFailedBody: "无法更新自动复制设置",
        promptPathFailedBody: "无法更新上传路径设置",
        languageFailedBody: "无法更新语言设置",
        downloadDirUpdatedTitle: "下载目录已更新",
        downloadDirFailedBody: "无法更新下载目录",
        filePickerFailedBody: "无法打开文件选择器",
        portInvalidTitle: "端口无效",
        portInvalidBody: "请输入 1-65535 之间的整数端口",
        portUpdatedTitle: "端口已更新",
        portUpdatedBody: "当前端口: {{port}}",
        portUpdateFailedBody: "无法更新端口",
      },
      ui: {
        title: "界面设置",
        showQr: {
          label: "显示二维码",
          description: "在主页展示二维码",
        },
        showUrl: {
          label: "显示访问地址",
          description: "在主页展示访问链接",
        },
        showTransfer: {
          label: "显示传输记录",
          description: "在主页展示传输状态",
        },
        language: {
          label: "界面语言",
          description: "选择界面显示语言",
          auto: "自动 (系统)",
        },
      },
      transferSettings: {
        title: "传输设置",
        text: {
          title: "文本传输",
          autoCopyLabel: "自动复制文本",
          autoCopyDesc: "收到文本后自动复制到剪贴板",
        },
        file: {
          title: "文件传输",
          promptPathLabel: "上传前选择路径",
          promptPathDesc: "每次上传前手动选择保存目录",
          currentDir: "当前下载目录：{{path}}",
          chooseDir: "选择下载目录",
          unset: "未设置",
        },
      },
      portSettings: {
        title: "端口设置",
        portLabel: "端口号",
      },
    },
  },
  "en-US": {
    translation: {
      common: {
        init: "Initializing...",
        settings: "Settings",
        saving: "Saving...",
        savePort: "Save Port",
        copyFailedTitle: "Copy Failed",
        copyFailedBody: "Unable to copy text to clipboard, please copy manually",
      },
      service: {
        label: "File Transfer Service",
        status: {
          switching: "Switching...",
          running: "Running",
          stopped: "Stopped",
        },
      },
      access: {
        title: "Access",
        qrAria: "QR: {{url}}",
        urlAria: "Server URL",
      },
      transfer: {
        title: "Transfer History",
        none: "No active transfers",
        sent: "Transferred: {{size}}",
        speed: "Speed: {{speed}}/s",
        remaining: "Remaining: {{time}}",
        copy: {
          ready: "Copy to Clipboard",
          copying: "Copying...",
          success: "Copied",
        },
      },
      toasts: {
        serviceStartedTitle: "Service Started",
        serviceStartedBody: "File transfer service started successfully",
        startFailedTitle: "Start Failed",
        startFailedBody: "Unable to start service",
        serviceStoppedTitle: "Service Stopped",
        serviceStoppedBody: "File transfer service stopped",
        stopFailedTitle: "Stop Failed",
        stopFailedBody: "Unable to stop service",
        toggleFailedTitle: "Operation Failed",
        toggleFailedBody: "Error while toggling service state",
        settingsFailedTitle: "Settings Failed",
        autoCopyFailedBody: "Unable to update auto-copy setting",
        promptPathFailedBody: "Unable to update upload path setting",
        languageFailedBody: "Unable to update language setting",
        downloadDirUpdatedTitle: "Download directory updated",
        downloadDirFailedBody: "Unable to update download directory",
        filePickerFailedBody: "Unable to open file picker",
        portInvalidTitle: "Invalid Port",
        portInvalidBody: "Please enter an integer port between 1 and 65535",
        portUpdatedTitle: "Port updated",
        portUpdatedBody: "Current port: {{port}}",
        portUpdateFailedBody: "Unable to update port",
      },
      ui: {
        title: "Interface",
        showQr: {
          label: "Show QR Code",
          description: "Show QR code on home screen",
        },
        showUrl: {
          label: "Show URL",
          description: "Show access URL on home screen",
        },
        showTransfer: {
          label: "Show Transfer History",
          description: "Show transfer status on home screen",
        },
        language: {
          label: "Language",
          description: "Choose UI language",
          auto: "Auto (System)",
        },
      },
      transferSettings: {
        title: "Transfer",
        text: {
          title: "Text Transfer",
          autoCopyLabel: "Auto Copy Text",
          autoCopyDesc: "Automatically copy received text to clipboard",
        },
        file: {
          title: "File Transfer",
          promptPathLabel: "Choose Path Before Upload",
          promptPathDesc: "Choose a destination before each upload",
          currentDir: "Current download directory: {{path}}",
          chooseDir: "Choose download directory",
          unset: "Not set",
        },
      },
      portSettings: {
        title: "Port",
        portLabel: "Port",
      },
    },
  },
};

let i18nInitialized = false;

export const loadTranslations = async (language?: string) => {
  const browserLanguage = typeof navigator !== "undefined" && navigator.language ? navigator.language : "en-US";
  const initialLanguage = language && language !== "auto" ? language : browserLanguage;
  if (!i18nInitialized) {
    await i18n
      .use(initReactI18next)
      .init({
        resources,
        lng: initialLanguage,
        fallbackLng: {
          zh: ["zh-CN"],
          en: ["en-US"],
          default: ["en-US"],
        },
        load: "languageOnly",
        interpolation: { escapeValue: false },
      });
    i18nInitialized = true;
    return;
  }
  await i18n.changeLanguage(initialLanguage);
};

export const changeLanguage = async (language: string) => {
  const browserLanguage = typeof navigator !== "undefined" && navigator.language ? navigator.language : "en-US";
  const target = !language || language === "auto" ? browserLanguage : language;
  await i18n.changeLanguage(target);
};

export const getSupportedLanguages = () => Object.keys(resources);

export default i18n;
