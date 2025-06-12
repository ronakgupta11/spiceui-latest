import React from 'react';
import { Paper, Box, Typography, Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

interface SimpleCodePreviewProps {
  imageUrl: string;
  onDownload: () => void;
}

const SimpleCodePreview: React.FC<SimpleCodePreviewProps> = ({ imageUrl, onDownload }) => {
  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">Generated Code</Typography>
      </Box>
      <Box sx={{ 
        position: 'relative',
        flex: 1,
        minHeight: 0 // Important for flex child
      }}>
        <Box
          component="img"
          src={imageUrl}
          alt="Uploaded UI"
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            padding: 2
          }}
        />
      </Box>
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={onDownload}
          startIcon={<DownloadIcon />}
          fullWidth
        >
          Download Code
        </Button>
      </Box>
    </Paper>
  );
};

export default SimpleCodePreview; 