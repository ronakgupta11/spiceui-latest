import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Typography
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import Editor from '@monaco-editor/react';
import { LiveProvider, LiveEditor, LiveError, LivePreview } from 'react-live';

interface SimpleCodePreviewProps {
  code?: string;
  onDownload?: () => void;
}

const SimpleCodePreview: React.FC<SimpleCodePreviewProps> = ({ code, onDownload }) => {
  const [tabValue, setTabValue] = useState(0);
  const [editorCode, setEditorCode] = useState(code || '');
  const [previewCode, setPreviewCode] = useState(code || '');

  useEffect(() => {
    setEditorCode(code || '');
    setPreviewCode(code || '');
  }, [code]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    if (newValue === 1) {
      setPreviewCode(editorCode);
    }
    setTabValue(newValue);
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditorCode(value);
    }
  };

  const scope = {
    React,
    Box,
    Typography,
    IconButton,
    DownloadIcon
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
          <Box sx={{ height: '100%' }}>
            <Editor
              height="calc(100vh - 230px)"
              defaultLanguage="javascript"
              value={editorCode}
              onChange={handleEditorChange}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                wordWrap: 'on',
                automaticLayout: true
              }}
            />
          </Box>
        ) : (
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <LiveProvider code={previewCode} scope={scope} noInline={false}>
              <LivePreview style={{ height: '100%', padding: '20px' }} />
              <LiveError />
            </LiveProvider>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default SimpleCodePreview;
