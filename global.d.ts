// 全局类型定义，用于解决模块未找到的问题

// Decky 插件 API 类型
declare module "@decky/api" {
  export interface CallableFunction<TArgs extends any[], TReturn> {
    (...args: TArgs): Promise<TReturn>;
  }

  export function callable<TArgs extends any[], TReturn>(name: string): CallableFunction<TArgs, TReturn>;
  export function definePlugin(pluginDefinition: any): any;
  export function addEventListener<T>(event: string, callback: (...args: T[]) => void): any;
  export function removeEventListener(event: string, listener: any): void;

  export const toaster: {
    toast(toastOptions: { title: string; body?: string }): void;
  };
}

// Decky UI 组件类型
declare module "@decky/ui" {
  export const PanelSection: any;
  export const PanelSectionRow: any;
  export const ButtonItem: any;
  export const ToggleField: any;
  export const ProgressBar: any;
  export const Navigation: any;
}

// React 类型
declare module "react" {
  export * from 'react';
}

// React 图标类型
declare module "react-icons/fa" {
  export const FaUpload: any;
}

// QR码组件类型
declare module "qrcode.react" {
  export const QRCodeCanvas: any;
}

// 确保这是一个模块
export {}

// 全局 JSX 支持
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [tagName: string]: any;
    }
  }
}

// React 事件类型
interface ReactFocusEvent<T = Element> {
  currentTarget: T;
  preventDefault(): void;
  stopPropagation(): void;
  target: T;
}

interface ReactKeyboardEvent<T = Element> {
  currentTarget: T;
  preventDefault(): void;
  stopPropagation(): void;
  target: T;
  key: string;
}

interface ReactMouseEvent<T = Element> {
  currentTarget: T;
  preventDefault(): void;
  stopPropagation(): void;
  target: T;
}

// 为组件添加全局命名空间引用
declare global {
  namespace React {
    type FocusEvent<T = Element> = ReactFocusEvent<T>;
    type KeyboardEvent<T = Element> = ReactKeyboardEvent<T>;
    type MouseEvent<T = Element> = ReactMouseEvent<T>;
  }
}