import React, { useState, useCallback } from 'react';
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  IconButton,
  Typography
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ImageUploader from './components/ImageUploader';
import Chat from './components/Chat';
import CodePreview from './components/CodePreview';
import { Message, SessionState } from './types';
import { generateCode, modifyCode } from './utils/api';
import SimpleCodePreview from './components/SimpleCodePreviewer';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2196f3'
    }
  }
});

const App: React.FC = () => {
  const [sessionState, setSessionState] = useState<SessionState>({
    image: null,
    messages: [],
    componentTree: null,
    generatedCode: null,
    isLoading: false,
    error: null
  });

  const handleImageUpload = useCallback(async (file: File) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Image = e.target?.result as string;
      setSessionState(prev => ({
        ...prev,
        image: base64Image,
        isLoading: true,
        error: null
      }));

      try {
        const response = await generateCode(base64Image);
        setSessionState(prev => ({
          ...prev,
          isLoading: false,
          generatedCode: response.output_data.generated_files["src/App.tsx"] || "",
          componentTree: response.componentTree,
          messages: [
            ...prev.messages,
            {
              id: Date.now().toString(),
              content: 'I\'ve analyzed your UI image and generated the React code.',
              role: 'assistant',
              timestamp: new Date()
            }
          ]
        }));
      } catch (error) {
        setSessionState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Failed to generate code. Please try again.'
        }));
      }
    };
    reader.readAsDataURL(file);
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    if (!sessionState.image) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: 'user',
      timestamp: new Date()
    };

    setSessionState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
      isLoading: true
    }));

    try {
      const response = await modifyCode(sessionState.image, message);
      setSessionState(prev => ({
        ...prev,
        isLoading: false,
        generatedCode: response.code,
        componentTree: response.componentTree,
        messages: [
          ...prev.messages,
          {
            id: (Date.now() + 1).toString(),
            content: 'I\'ve updated the code based on your request.',
            role: 'assistant',
            timestamp: new Date()
          }
        ]
      }));
    } catch (error) {
      setSessionState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to modify code. Please try again.'
      }));
    }
  }, [sessionState.image]);

  const handleDownload = useCallback(() => {
    if (!sessionState.generatedCode) return;

    const blob = new Blob([sessionState.generatedCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'generated-component.jsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [sessionState.generatedCode]);

  const handleReset = useCallback(() => {
    setSessionState({
      image: null,
      messages: [],
      componentTree: null,
      generatedCode: null,
      isLoading: false,
      error: null
    });
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ height: '100vh', py: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h4" component="h1">
            UI to Code Generator
          </Typography>
          {sessionState.image && (
            <IconButton onClick={handleReset} color="primary">
              <RefreshIcon />
            </IconButton>
          )}
        </Box>

        {!sessionState.image ? (
          <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            <ImageUploader
              onImageUpload={handleImageUpload}
              isLoading={sessionState.isLoading}
            />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 100px)' }}>
            <Box sx={{ flex: 1 }}>
              <Chat
                messages={sessionState.messages}
                onSendMessage={handleSendMessage}
                isLoading={sessionState.isLoading}
              />
            </Box>
            <Box sx={{ flex: 1 }}>
              <SimpleCodePreview
                  code  ={sessionState.generatedCode || ""}
                  onDownload={handleDownload}  
              />
            </Box>
          </Box>
        )}

        {sessionState.error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {sessionState.error}
          </Typography>
        )}
      </Container>
    </ThemeProvider>
  );
};

export default App; 