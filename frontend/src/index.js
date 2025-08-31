import React from 'react';
import ReactDOM from 'react-dom/client';
import '../styles/globals.css';
import App from './src';

// Create root and render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);