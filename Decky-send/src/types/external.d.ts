// 为第三方库添加类型声明

// React 类型
declare module "react" {
  export * from "react";
  export default React;
  export function useState<S>(initialState: S | (() => S)): [S, React.Dispatch<React.SetStateAction<S>>];
  export function useEffect(effect: React.EffectCallback, deps?: React.DependencyList): void;
  export function useRef<T>(initialValue: T): React.MutableRefObject<T>;
  export function useRef<T>(initialValue: T | null): React.RefObject<T>;
  
  export namespace React {
    type Dispatch<A> = (value: A) => void;
    type SetStateAction<S> = S | ((prevState: S) => S);
    type EffectCallback = () => void | (() => void);
    type DependencyList = readonly unknown[];
    type MutableRefObject<T> = {
      current: T;
    };
    interface RefObject<T> {
      readonly current: T | null;
    }
  }
}

// React Icons 类型
declare module "react-icons/fa" {
  export const FaUpload: any;
}

// QRCode 组件类型
declare module "qrcode.react" {
  export const QRCodeCanvas: any;
}

// Decky API 类型
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

// JSX 运行时类型
declare module "react/jsx-runtime" {
  export default any;
  export const jsx: any;
  export const jsxs: any;
}