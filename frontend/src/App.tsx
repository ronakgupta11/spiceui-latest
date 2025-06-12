import React, { useState, useCallback } from 'react';
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  IconButton,
  Typography,
  Grid
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CodeIcon from '@mui/icons-material/Code';
import ImageUploader from './components/ImageUploader';
import Chat from './components/Chat';
import CodePreview from './components/CodePreview';
import LoadingSteps from './components/LoadingSteps';
import { Message, SessionState } from './types';
import { generateCode, modifyCode } from './utils/api';
import SimpleCodePreview from './components/SimpleCodePreviewer';
import CloseIcon from '@mui/icons-material/Close';

export type AppProps = {};

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2196f3'
    }
  }
});

const App: React.FC<AppProps> = () => {
  const [sessionState, setSessionState] = useState<SessionState>({
    image: null,
    messages: [],
    componentTree: null,
    generatedCode: null,
    isLoading: false,
    error: null,
    available_components: []
  });
  const [loadingStep, setLoadingStep] = useState(0);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [view, setView] = useState<'upload' | 'loading' | 'chat'>('upload');

  const handleImageUpload = useCallback(async (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64Image = e.target?.result as string;
      setUploadedImage(base64Image);
      setSessionState(prev => ({
        ...prev,
        image: base64Image,
        error: null
      }));
      setView('upload');
    };
    reader.readAsDataURL(file);
  }, []);

  const handleGenerateCode = useCallback(async () => {
    if (!sessionState.image) return;
    setSessionState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));
    setLoadingStep(0);
    setView('loading');

    try {
      const codeGenerationPromise = generateCode(sessionState.image);

      const loadingDurations = [3000, 5000, 8000]; // 3s, 5s, 8s
      for (let step = 0; step < 3; step++) {
        await new Promise(resolve =>
          setTimeout(() => {
            setLoadingStep(step);
            resolve(true);
          }, loadingDurations[step])
        );
      }

      setLoadingStep(3);

      const response = await codeGenerationPromise;

      setSessionState(prev => ({
        ...prev,
        isLoading: false,
        generatedCode: response.output_data.generated_files["src/App.tsx"] || "",
        componentTree: response.componentTree,
        available_components: response.output_data.detailed_components || [],
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
      setView('chat');
    } catch (error) {
      setSessionState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to generate code. Please try again.'
      }));
      setView('upload');
    }
  }, [sessionState.image]);

  const handleSendMessage = useCallback(async (message: string) => {
    if (!sessionState.image) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: 'user',
      timestamp: new Date()
    };
    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '...',
      role: 'assistant',
      timestamp: new Date()
    };
    const updatedMessages = [...sessionState.messages, newMessage, loadingMessage];
    const newMessages = [...sessionState.messages, newMessage];
    setSessionState(prev => ({
      ...prev,
      messages: updatedMessages
    }));

    // setSessionState(prev => ({
    //   ...prev,
    //   messages: newMessages
    // }));

    try {
      const response = await modifyCode(
        newMessages,
        { 'src/App.tsx': sessionState.generatedCode || '' },
        sessionState.available_components
      );
      
      setSessionState(prev => ({
        ...prev,
        generatedCode: response.modified_files['src/App.tsx'],
        componentTree: response.changes,
        messages: [
          ...prev.messages.filter(msg => msg.id !== loadingMessage.id),
          {
            id: (Date.now() + 1).toString(),
            content: response.explanation || 'I\'ve updated the code based on your request.',
            role: 'assistant',
            timestamp: new Date()
          }
        ]
      }));
    } catch (error) {
      setSessionState(prev => ({
        ...prev,
        error: 'Failed to modify code. Please try again.'
      }));
    }
  }, [sessionState.image, sessionState.messages, sessionState.generatedCode, sessionState.available_components]);

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
      error: null,
      available_components: []
    });
    setUploadedImage(null);
    setView('upload');
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ height: '100vh', py: 1, overflow: 'hidden' }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: sessionState.image ? 'flex-start' : 'center',
          mb: 1,
          position: 'relative',
          width: '100%'
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            mb: 1,
            position: 'relative',
            p: 2,
            borderRadius: 4,
            background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 203, 243, 0.1) 100%)',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              borderRadius: 4,
              padding: '2px',
              background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.3) 0%, rgba(33, 203, 243, 0.3) 100%)',
              WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
              WebkitMaskComposite: 'xor',
              maskComposite: 'exclude',
            },
            ml: sessionState.image ? 2 : 0
          }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2,
              width: '100%',
              justifyContent: 'center'
            }}>
              <AutoFixHighIcon sx={{ 
                fontSize: 40, 
                color: 'primary.main',
                filter: 'drop-shadow(0 2px 4px rgba(33, 150, 243, 0.3))'
              }} />
              <Typography 
                variant="h3" 
                component="h1" 
                sx={{ 
                  textAlign: 'center',
                  fontWeight: 'bold',
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 2px 4px rgba(33, 150, 243, 0.2)'
                }}
              >
                Spice UI
              </Typography>
              <CodeIcon sx={{ 
                fontSize: 40, 
                color: 'primary.main',
                filter: 'drop-shadow(0 2px 4px rgba(33, 150, 243, 0.3))'
              }} />
            </Box>
          </Box>
          {!sessionState.image && (
            <Typography 
              variant="subtitle1" 
              color="textSecondary"
              sx={{ 
                textAlign: 'center',
                maxWidth: '600px',
                mb: 4,
                position: 'relative',
                zIndex: 1
              }}
            >
              Transform your UI designs into production-ready code. Upload your UI image and get instant React components.
            </Typography>
          )}
          {sessionState.image && !sessionState.isLoading && (
            <IconButton 
              onClick={handleReset} 
              color="primary"
              sx={{ position: 'absolute', right: 16, top: 16 }}
            >
              <RefreshIcon />
            </IconButton>
          )}
        </Box>

        {view === 'upload' ? (
          <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            {!uploadedImage ? (
              <ImageUploader
                onImageUpload={handleImageUpload}
                isLoading={sessionState.isLoading}
              />
            ) : (
              <Box sx={{ mt: 2, textAlign: 'center', position: 'relative', display: 'inline-block' }}>
                <img
                  src={uploadedImage}
                  alt="Uploaded preview"
                  style={{
                    maxWidth: '100%',
                    maxHeight: 300,
                    borderRadius: 8,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                  }}
                />
                <IconButton
                  size="small"
                  onClick={() => {
                    setUploadedImage(null);
                    setSessionState(prev => ({
                      ...prev,
                      image: null
                    }));
                  }}
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    background: 'rgba(255,255,255,0.8)',
                    '&:hover': { background: 'rgba(255,255,255,1)' }
                  }}
                >
                  <CloseIcon />
                </IconButton>
                <Box sx={{ mt: 2 }}>
                  <button
                    onClick={handleGenerateCode}
                    style={{
                      padding: '10px 24px',
                      fontSize: '1rem',
                      background: '#2196f3',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer'
                    }}
                  >
                    Generate Code
                  </button>
                </Box>
              </Box>
            )}
          </Box>
        ) : view === 'loading' ? (
          <LoadingSteps currentStep={loadingStep} />
        ) : (
          <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 103px)' }}>
            <Grid container spacing={2} sx={{ height: '100%' }}>
              <Grid item xs={12} sm={6} sx={{ height: '100%' }}>
                <Chat
                  messages={sessionState.messages}
                  onSendMessage={handleSendMessage}
                  isLoading={sessionState.isLoading}
                  uploadedImage={sessionState.image}
                />
              </Grid>
              <Grid item xs={12} sm={6} sx={{ height: '100%' }}>
                <SimpleCodePreview
                  code={sessionState.generatedCode || ""}
                  onDownload={handleDownload}
                />
              </Grid>
            </Grid>
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