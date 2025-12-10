"use client";

import { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, FileText, X, Loader2, Menu } from 'lucide-react';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
};

type DocumentInfo = {
  filename: string;
  size: number;
  type: string;
  created_at: number;
  last_modified: number;
};

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

// Use environment variable for API URL, fallback to relative path for production
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://127.0.0.1:8000/api' 
  : '/api';

// Utility functions (currently unused but kept for future use)
// const formatFileSize = (bytes: number): string => {
//   if (bytes === 0) return '0 Bytes';
//   const k = 1024;
//   const sizes = ['Bytes', 'KB', 'MB', 'GB'];
//   const i = Math.floor(Math.log(bytes) / Math.log(k));
//   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
// };

// const formatDate = (timestamp: number): string => {
//   return new Date(timestamp * 1000).toLocaleDateString('en-US', {
//     year: 'numeric',
//     month: 'short',
//     day: 'numeric',
//   });
// };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const fetchDocuments = useCallback(async () => {
    try {
      console.log('Fetching documents from:', `${API_BASE_URL}/documents`);
      const response = await fetch(`${API_BASE_URL}/documents`, {
        headers: {
          'Accept': 'application/json',
        },
      });
      
      console.log('Documents response status:', response.status);
      
      if (!response.ok) {
        let errorMsg = `Failed to fetch documents: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || JSON.stringify(errorData);
        } catch {
          const text = await response.text();
          if (text) errorMsg = text;
        }
        throw new Error(errorMsg);
      }
      
      const data = await response.json();
      console.log('Documents data:', data);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError(error instanceof Error ? error.message : 'Failed to load documents');
      setDocuments([]); // Clear documents on error
    }
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          history: messages,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response,
        source: data.source
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadFile = useCallback(async (file: File) => {
    if (!file) return;

    console.log(`Starting upload of ${file.name} (${file.size} bytes)`);
    setUploadStatus('uploading');
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', file.name);

    try {
      console.log(`Sending request to: ${API_BASE_URL}/upload_document`);
      const response = await fetch(`${API_BASE_URL}/upload_document`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let the browser set it with the boundary
        headers: {
          'Accept': 'application/json',
        },
      });

      console.log('Upload response status:', response.status);
      
      if (!response.ok) {
        let errorMsg = `Server error: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || JSON.stringify(errorData);
        } catch {
          const text = await response.text();
          if (text) errorMsg = text;
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      
      // Refresh documents list
      await fetchDocuments();
      
      setUploadStatus('success');
      setTimeout(() => setUploadStatus('idle'), 3000);
      return result;
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      const errorMsg = error instanceof Error ? error.message : 'Failed to upload document. Please check the console for details.';
      setError(errorMsg);
      throw error;
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [fetchDocuments]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      await uploadFile(file);
    } catch {
      // Error handling is done in uploadFile
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || 
          file.type === 'text/plain' || 
          file.name.endsWith('.pdf') || 
          file.name.endsWith('.txt')) {
        try {
          await uploadFile(file);
        } catch {
          // Error handling is done in uploadFile
        }
      } else {
        setError('Only PDF and text files are allowed');
      }
    }
  }, [uploadFile]);

  const handleDeleteDocument = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete document');
      }

      await fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete document');
    }
  };

  // Rest of your component JSX...
  // [Previous JSX content remains the same]
  // ...

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white shadow-lg transform ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:relative md:translate-x-0 transition-transform duration-300 ease-in-out`}
      >
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">Documents</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {documents.length === 0 ? (
              <p className="text-gray-500 text-sm">No documents uploaded yet</p>
            ) : (
              <ul className="space-y-2">
                {documents.map((doc) => (
                  <li 
                    key={doc.filename}
                    className="flex items-center justify-between p-2 hover:bg-gray-100 rounded"
                  >
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="text-sm truncate max-w-[160px]">{doc.filename}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.filename)}
                      className="text-red-500 hover:text-red-700"
                      title="Delete document"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="p-4 border-t border-gray-200">
            <div
              ref={dropZoneRef}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
              }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept=".pdf,.txt"
              />
              <Upload className="h-8 w-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-600">
                {dragActive ? 'Drop the file here' : 'Drag & drop files here or click to browse'}
              </p>
              <p className="text-xs text-gray-400 mt-1">Supports: .pdf, .txt</p>
              {uploadStatus === 'uploading' && (
                <div className="mt-2 flex items-center justify-center">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  <span className="ml-2 text-sm text-gray-500">Uploading...</span>
                </div>
              )}
              {uploadStatus === 'success' && (
                <p className="mt-2 text-sm text-green-600">Upload successful!</p>
              )}
              {error && (
                <p className="mt-2 text-sm text-red-600">{error}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm z-10">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="md:hidden text-gray-500 hover:text-gray-700"
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="text-xl font-semibold text-gray-800">RAG Chat</h1>
            <div className="w-6"></div> {/* For alignment */}
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.source && message.role === 'assistant' && (
                    <p className="text-xs mt-1 opacity-70">Source: {message.source}</p>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 rounded-lg px-4 py-2">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}
    </div>
  );
}