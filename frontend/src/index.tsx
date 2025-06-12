import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { SaltProvider } from "@salt-ds/core";

// Import theme CSS
import "@salt-ds/theme/index.css";
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);


root.render(
  <React.StrictMode>
     <SaltProvider>
      <App />
     </SaltProvider>

  </React.StrictMode>
); 