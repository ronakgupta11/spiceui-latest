import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, Tabs, Tab, IconButton, Typography, Alert } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { CodePreviewProps } from '../types';
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackPreview,
  useSandpack,
  SandpackCodeViewer,
  SandpackFiles,
  SandpackSetup,
  SandpackFile
} from '@codesandbox/sandpack-react';
import { atomDark, githubLight } from '@codesandbox/sandpack-themes';

// Debug component to log Sandpack state
const SandpackDebugger: React.FC = () => {
  const { sandpack } = useSandpack();
  
  useEffect(() => {
    console.log('Sandpack State:', {
      status: sandpack.status,
      error: sandpack.error,
      files: sandpack.files,
      activeFile: sandpack.activeFile,
      bundlerState: sandpack.bundlerState
    });
  }, [sandpack.status, sandpack.error, sandpack.files, sandpack.activeFile, sandpack.bundlerState]);

  return null;
};

const CodePreview: React.FC<CodePreviewProps> = ({ code, onDownload }) => {
  const [tabValue, setTabValue] = React.useState(0);
  const codeRef = useRef<HTMLElement>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [sandpackStatus, setSandpackStatus] = useState<string>('initial');

  // Clean up the code by removing markdown code block markers and description
  const cleanCode = React.useMemo(() => {
    if (!code) return '';
    
    // Remove markdown code block markers and language identifier
    let cleaned = code.replace(/```(?:jsx|tsx)?\n/, '');
    cleaned = cleaned.replace(/```\n.*$/, '');
    
    // Remove any trailing description text
    cleaned = cleaned.replace(/\nThis code.*$/, '');
    
    // Remove any remaining backticks
    cleaned = cleaned.replace(/```/g, '');
    
    return cleaned.trim();
  }, [code]);

  useEffect(() => {
    if (cleanCode && codeRef.current) {
      hljs.highlightElement(codeRef.current);
    }
  }, [cleanCode]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    if (newValue === 1) {
      setPreviewError(null);
    }
  };

  // Create Sandpack files
  const files: SandpackFiles = React.useMemo(() => {
    if (!cleanCode) {
      return {
        '/App.js': { code: '', active: true },
        '/index.js': { code: '' },
        '/styles.css': { code: '' }
      };
    }
    
    return {
      '/App.js': {
        code: cleanCode,
        active: true
      },
      '/index.js': {
        code: `
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { SaltProvider } from "@salt-ds/core";
import "@salt-ds/theme/index.css";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<SaltProvider><App /></SaltProvider>); 
        `
      },
      '/styles.css': {
        code: `
body {
  margin: 0;
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
        `
      }
    };
  }, [cleanCode]);

  // Sandpack setup
  const customSetup: SandpackSetup = {
    dependencies: {
      '@salt-ds/core': 'latest',
      '@salt-ds/icons': 'latest',
      '@salt-ds/theme': 'latest',
      'react': '^18.2.0',
      'react-dom': '^18.2.0'
    },
    entry: '/index.js'
  };

  const handleSandpackError = (error: Error) => {
    console.error('Sandpack Error:', error);
    setPreviewError(error.message);
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Code" />
          <Tab label="Preview" />
        </Tabs>
        <Box sx={{ flexGrow: 1 }} />
        <IconButton onClick={onDownload} color="primary" sx={{ mr: 1 }}>
          <DownloadIcon />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {tabValue === 0 ? (
          cleanCode ? (
            <Box
              component="pre"
              sx={{
                margin: 0,
                height: '100%',
                borderRadius: 4,
                fontSize: '14px',
                backgroundColor: '#f6f8fa',
                '& code': {
                  fontFamily: 'monospace',
                  display: 'block',
                  padding: 2,
                  height: '100%',
                  overflow: 'auto'
                }
              }}
            >
              <code ref={codeRef} className="language-jsx">
                {cleanCode}
              </code>
            </Box>
          ) : (
            <Typography color="textSecondary" align="center">
              No code generated yet
            </Typography>
          )
        ) : (
          cleanCode ? (
            <Box sx={{ height: '100%', border: '1px solid #e0e0e0', borderRadius: 1, p: 2 }}>
              {previewError ? (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {previewError}
                </Alert>
              ) : (
                <SandpackProvider
                  template="react"
                  theme={githubLight}
                  files={files}
                  customSetup={customSetup}
                  options={{
                    classes: {
                      'sp-wrapper': 'h-full w-full',
                      'sp-layout': 'h-full w-full',
                      'sp-preview-container': 'h-full w-full'
                    },
                    bundlerURL: 'https://sandpack-bundler.pages.dev',
                    logLevel: 2 // Enable verbose logging
                  }}
                  onError={handleSandpackError}
                >
                  <SandpackDebugger />
                  <SandpackPreview
                    showNavigator={true}
                    showRefreshButton={true}
                    showOpenInCodeSandbox={false}
                    style={{
                      width: '100%',
                      height: '100%',
                      minHeight: '400px'
                    }}
                  />
                </SandpackProvider>
              )}
            </Box>
          ) : (
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Typography color="textSecondary">
                No code to preview
              </Typography>
            </Box>
          )
        )}
      </Box>
    </Paper>
  );
};

export default CodePreview; 