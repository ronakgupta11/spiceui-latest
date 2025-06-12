import React from 'react';
import { Box, Typography, CircularProgress, Paper, LinearProgress } from '@mui/material';

interface LoadingStepsProps {
  currentStep: number;
}

const steps = [
  'Analyzing UI Design...',
  'Generating Component Tree...',
  'Mapping Components...',
  'Generating Code...'
];

const LoadingSteps: React.FC<LoadingStepsProps> = ({ currentStep }) => {
  return (
    <Paper sx={{ p: 4, maxWidth: 400, mx: 'auto', mt: 4 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <CircularProgress />
        <Typography variant="h6" align="center" color="primary" sx={{ fontWeight: 'bold' }}>
          {steps[currentStep]}
        </Typography>
        <Box sx={{ width: '100%', mt: 2 }}>
          {steps.map((step, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                mb: 2,
                opacity: index <= currentStep ? 1 : 0.5,
                transition: 'opacity 0.3s ease'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="body1"
                  sx={{
                    color: index === currentStep ? 'primary.main' : 
                           index < currentStep ? 'success.main' : 'text.primary',
                    fontWeight: index === currentStep ? 'bold' : 'normal'
                  }}
                >
                  {step}
                </Typography>
              </Box>
              {index === currentStep && (
                <LinearProgress 
                  sx={{ 
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: 'primary.main'
                    }
                  }} 
                />
              )}
            </Box>
          ))}
        </Box>
      </Box>
    </Paper>
  );
};

export default LoadingSteps; 