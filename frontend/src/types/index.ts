export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface SessionState {
  image: string | null;
  messages: Message[];
  componentTree: any | null;
  generatedCode: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface ChatProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  uploadedImage?: string | null;
}

export interface CodePreviewProps {
  code: string | null;
  onDownload: () => void;
}

export interface ImageUploaderProps {
  onImageUpload: (file: File) => void;
  isLoading: boolean;
}

export interface PreviewProps {
  code: string | null;
} 