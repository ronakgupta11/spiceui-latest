declare module '@codesandbox/sandpack-react' {
  import { ReactNode } from 'react';

  export interface SandpackFile {
    code: string;
    hidden?: boolean;
    active?: boolean;
    readOnly?: boolean;
  }

  export interface SandpackFiles {
    [path: string]: SandpackFile;
  }

  export interface SandpackSetup {
    dependencies?: Record<string, string>;
    entry?: string;
    files?: SandpackFiles;
  }

  export interface SandpackOptions {
    classes?: Record<string, string>;
    bundlerURL?: string;
    logLevel?: number;
  }

  export interface SandpackMessage {
    type: string;
    path?: string;
    code?: string;
  }

  export interface SandpackState {
    status: 'initial' | 'idle' | 'running' | 'done' | 'error';
    error: Error | null;
    files: SandpackFiles;
    activeFile: string;
    bundlerState: {
      status: string;
      errors: Error[];
      warnings: Error[];
    };
    updateFile: (path: string, code: string) => void;
    listen: (callback: (msg: SandpackMessage) => void) => () => void;
  }

  export interface SandpackContextValue {
    sandpack: SandpackState & {
      refresh: () => void;
    };
  }

  export function useSandpack(): SandpackContextValue;

  export interface SandpackProviderProps {
    template?: string;
    theme?: any;
    files?: SandpackFiles;
    customSetup?: SandpackSetup;
    options?: SandpackOptions;
    onError?: (error: Error) => void;
    children: ReactNode;
  }

  export const SandpackProvider: React.FC<SandpackProviderProps>;
  export const SandpackLayout: React.FC<{ children: ReactNode }>;
  export const SandpackCodeEditor: React.FC<{ 
    showLineNumbers?: boolean;
    onChange?: (code: string) => void;
    showTabs?: boolean;
    wrapContent?: boolean;
    showInlineErrors?: boolean;
    style?: React.CSSProperties;
  }>;
  export const SandpackPreview: React.FC<{
    showNavigator?: boolean;
    showRefreshButton?: boolean;
    showOpenInCodeSandbox?: boolean;
    style?: React.CSSProperties;
  }>;
  export const SandpackCodeViewer: React.FC<{ showLineNumbers?: boolean }>;
}

declare module '@codesandbox/sandpack-themes' {
  export const atomDark: any;
  export const githubLight: any;
} 