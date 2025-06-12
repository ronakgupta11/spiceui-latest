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
      setLoadingStep(0);

      try {
        // Start code generation in parallel
        const codeGenerationPromise = generateCode(base64Image);
        
        // Handle the first three steps with 10-second intervals
        for (let step = 0; step < 3; step++) {
          await new Promise(resolve => 
            setTimeout(() => {
              setLoadingStep(step);
              resolve(true);
            }, 10000)
          );
        }
        
        // Move to the final step
        setLoadingStep(3);
        
        // Wait for code generation to complete
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
      messages: [...prev.messages, newMessage]
    }));

    try {
      const response = await modifyCode(
        sessionState.messages,
        { 'src/App.tsx': sessionState.generatedCode || '' },
        sessionState.available_components
      );
      
      setSessionState(prev => ({
        ...prev,
        generatedCode: response.modified_files['src/App.tsx'],
        componentTree: response.changes,
        messages: [
          ...prev.messages,
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

        {!sessionState.image ? (
          <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            <ImageUploader
              onImageUpload={handleImageUpload}
              isLoading={sessionState.isLoading}
            />
          </Box>
        ) : sessionState.isLoading ? (
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