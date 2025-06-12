import React, { useState } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Typography
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackPreview
} from '@codesandbox/sandpack-react';
import { githubLight } from '@codesandbox/sandpack-themes';

interface SimpleCodePreviewProps {
  code?: string;
  onDownload?: () => void;
}

const SimpleCodePreview: React.FC<SimpleCodePreviewProps> = ({ code, onDownload }) => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

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

  const files = {
    '/App.js': {
      code: cleanCode || '',
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
    }
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
        <SandpackProvider
          template="react"
          theme={githubLight}
          files={files}
          customSetup={{
            dependencies: {
              '@salt-ds/core': '^1.46.1',
              '@salt-ds/icons': '^1.13.2',
              '@salt-ds/theme': '^1.29.0',
              '@fontsource/open-sans': '^5.2.6',
              '@fontsource/pt-mono': '^5.2.6'
            }
          }}
          options={{
            classes: {
              'sp-wrapper': 'h-full w-full',
              'sp-layout': 'h-full w-full',
              'sp-preview-container': 'h-full w-full'
            }
          }}
        >
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {tabValue === 0 ? (
              <Box sx={{ flex: 1 }}>
                <SandpackCodeEditor showLineNumbers />
              </Box>
            ) : (
              <Box sx={{ flex: 1 }}>
                <SandpackPreview
                  showNavigator
                  showRefreshButton
                  showOpenInCodeSandbox={false}
                  style={{ height: 'calc(100vh - 185px)', width: '100%' }}
                />
              </Box>
            )}
          </Box>
        </SandpackProvider>
      </Box>
    </Paper>
  );
};

export default SimpleCodePreview;
