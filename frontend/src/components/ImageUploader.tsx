import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Typography, Paper, CircularProgress, Box } from '@mui/material';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import { ImageUploaderProps } from '../types';

const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageUpload, isLoading }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      onImageUpload(file);
    }
  }, [onImageUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    multiple: false
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 4,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        bgcolor: isDragActive ? 'action.hover' : 'background.paper',
        minHeight: 300,
        position: 'relative',
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: 'primary.main',
          bgcolor: 'action.hover'
        }
      }}
    >
      <input {...getInputProps()} />
      {isLoading ? (
        <CircularProgress />
      ) : (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3
          }}
        >
          <Typography 
            variant="h5" 
            sx={{ 
              fontWeight: 'medium',
              mb: 2
            }}
          >
            Upload UI Image
          </Typography>
          
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1
            }}
          >
            <Box
              sx={{
                width: 100,
                height: 100,
                borderRadius: '50%',
                bgcolor: '#F5F7FA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}
            >
              <AddPhotoAlternateIcon 
                sx={{ 
                  fontSize: 48, 
                  color: '#64748B',
                  position: 'relative',
                  zIndex: 1
                }} 
              />
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  right: 0,
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid white',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                <Typography
                  sx={{
                    color: 'white',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    lineHeight: 1
                  }}
                >
                  +
                </Typography>
              </Box>
            </Box>

            <Typography 
              variant="h6" 
              color="primary"
              sx={{ 
                fontWeight: 'medium'
              }}
            >
              Salt Image
            </Typography>
          </Box>

          <Typography 
            variant="body2" 
            color="textSecondary"
            sx={{ 
              textAlign: 'center',
              maxWidth: '400px'
            }}
          >
            Drag and drop your image here or click to browse
          </Typography>

          <Typography 
            variant="caption" 
            color="textSecondary"
            sx={{ 
              mt: 1
            }}
          >
            Supported formats: PNG, JPG, JPEG
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ImageUploader; 