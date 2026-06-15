import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  Clock,
  History,
} from 'lucide-react';
import { uploadContract, triggerAnalysis, getContracts } from '../lib/api';
import { cn } from '../lib/utils';
import { toastSuccess, toastError, toastInfo } from '../components/ui/Toast';

export function UploadPage() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const { data: contracts } = useQuery({
    queryKey: ['contracts'],
    queryFn: getContracts,
  });

  const recentUploads = contracts?.slice(0, 3) || [];



  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const contract = await uploadContract(file);
      toastSuccess('Upload successful');
      toastInfo('Analysis started...');
      // Auto-trigger analysis after upload
      await triggerAnalysis(contract.id);
      return contract;
    },
    onSuccess: (contract) => {
      setTimeout(() => {
        navigate(`/contracts/${contract.id}`);
      }, 1200);
    },
    onError: (err: any) => {
      setIsTransitioning(false);
      const msg = err.response?.data?.detail || 'Upload failed. Please try again.';
      toastError(msg);
      setError(msg);
    },
  });

  const validateFile = (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const validExts = ['.pdf', '.docx'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
      setError('Invalid file type. Only PDF and DOCX files are supported.');
      return false;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError('File too large. Maximum size is 20MB.');
      return false;
    }

    setError(null);
    return true;
  };

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleUpload = () => {
    if (selectedFile) {
      setIsTransitioning(true);
      uploadMutation.mutate(selectedFile);
    }
  };

  const isUploading = uploadMutation.isPending || isTransitioning;

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isUploading && !uploadMutation.isSuccess) {
      setUploadProgress(0);
      interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) return prev;
          return prev + 5;
        });
      }, 300);
    } else if (uploadMutation.isSuccess) {
      setUploadProgress(100);
    }
    return () => clearInterval(interval);
  }, [isUploading, uploadMutation.isSuccess]);

  return (
    <div className="p-4 md:p-8 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-foreground)]">
          Upload Contract
        </h1>
        <p className="text-[var(--color-muted-foreground)] mt-1">
          Upload a PDF or DOCX contract for AI-powered analysis
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'glass-card rounded-xl p-12 text-center transition-all duration-300 cursor-pointer',
          dragActive && 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 scale-[1.01]',
          !dragActive && 'hover:border-[var(--color-muted-foreground)]/30',
        )}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx"
          onChange={handleInputChange}
          className="hidden"
        />

        {!selectedFile ? (
          <>
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--color-primary)]/10 flex items-center justify-center">
              <Upload className={cn('h-8 w-8', dragActive ? 'text-[var(--color-primary)]' : 'text-[var(--color-muted-foreground)]')} />
            </div>
            <p className="text-lg font-medium text-[var(--color-foreground)] mb-2">
              {dragActive ? 'Drop your file here' : 'Drag and drop your contract'}
            </p>
            <p className="text-sm text-[var(--color-muted-foreground)] mb-4">
              or click to browse files
            </p>
            <p className="text-xs text-[var(--color-muted-foreground)]">
              Supports PDF and DOCX (max 20MB)
            </p>
          </>
        ) : (
          <div className="flex items-center justify-center gap-4 animate-fade-in transition-all duration-300">
            <div className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300",
              selectedFile.name.toLowerCase().endsWith('.pdf') ? "bg-red-500/10" : "bg-blue-500/10"
            )}>
              <FileText className={cn(
                "h-6 w-6",
                selectedFile.name.toLowerCase().endsWith('.pdf') ? "text-red-500" : "text-blue-500"
              )} />
            </div>
            <div className="text-left flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--color-foreground)] truncate" title={selectedFile.name}>
                {selectedFile.name}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={cn(
                  "text-[10px] font-bold px-1.5 py-0.5 rounded",
                  selectedFile.name.toLowerCase().endsWith('.pdf') ? "bg-red-500/10 text-red-500" : "bg-blue-500/10 text-blue-500"
                )}>
                  {selectedFile.name.toLowerCase().endsWith('.pdf') ? 'PDF' : 'DOCX'}
                </span>
                <p className="text-xs text-[var(--color-muted-foreground)]">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                setError(null);
              }}
              className="p-1.5 rounded-lg hover:bg-[var(--color-secondary)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-all duration-200 cursor-pointer hover:scale-110 active:scale-90 ml-2"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Upload Button */}
      {selectedFile && (
        <div className="mt-6 animate-fade-in">
          <button
            onClick={handleUpload}
            disabled={isUploading}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 relative overflow-hidden cursor-pointer active:scale-[0.98]',
              isUploading
                ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)] cursor-not-allowed'
                : 'bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary)]/90 hover:-translate-y-1 hover:shadow-xl shadow-[var(--color-primary)]/20',
            )}
          >
            {isUploading && (
              <div 
                className="absolute left-0 top-0 bottom-0 bg-[var(--color-primary)]/20 transition-all duration-1000 ease-out" 
                style={{ width: `${uploadProgress}%` }} 
              />
            )}
            
            <div className="relative flex items-center gap-2">
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading and starting analysis... {uploadProgress}%
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  Upload and Analyze
                </>
              )}
            </div>
          </button>
          
          {isUploading && (
            <div className="mt-3 flex items-center justify-center gap-2 text-sm text-[var(--color-muted-foreground)] animate-fade-in">
              <Clock className="h-4 w-4" />
              <span>Estimated analysis time: 15-30 seconds</span>
            </div>
          )}
        </div>
      )}

      {/* What happens next */}
      <div className="mt-8 glass-card rounded-xl p-6">
        <h3 className="text-sm font-semibold text-[var(--color-foreground)] mb-4">
          What happens after upload?
        </h3>
        <div className="space-y-3">
          {[
            { step: '1', label: 'Document parsed and structured (sections, headings, tables)' },
            { step: '2', label: 'AI extracts and classifies all contract clauses' },
            { step: '3', label: 'Each clause scored for risk against market standards' },
            { step: '4', label: 'Plain-English executive summary generated' },
          ].map((item) => (
            <div key={item.step} className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-xs font-bold text-[var(--color-primary)]">
                  {item.step}
                </span>
              </div>
              <p className="text-sm text-[var(--color-muted-foreground)]">{item.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Uploads */}
      <div className="mt-8 glass-card rounded-xl p-6 animate-fade-in">
        <div className="flex items-center gap-2 mb-4">
          <History className="h-4 w-4 text-[var(--color-primary)]" />
          <h3 className="text-sm font-semibold text-[var(--color-foreground)]">
            Recent Uploads
          </h3>
        </div>
        
        {recentUploads.length > 0 ? (
          <div className="space-y-3">
            {recentUploads.map((contract) => (
              <div 
                key={contract.id} 
                className="flex items-center justify-between p-3 rounded-lg hover:bg-[var(--color-secondary)]/50 transition-colors cursor-pointer border border-transparent hover:border-[var(--color-border)]"
                onClick={() => navigate(`/contracts/${contract.id}`)}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0 pr-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                    contract.filename.toLowerCase().endsWith('.pdf') ? "bg-red-500/10" : "bg-blue-500/10"
                  )}>
                    <FileText className={cn(
                      "h-4 w-4",
                      contract.filename.toLowerCase().endsWith('.pdf') ? "text-red-500" : "text-blue-500"
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--color-foreground)] truncate">
                      {contract.filename}
                    </p>
                    <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">
                      {new Date(contract.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {contract.status === 'analyzed' && (
                    <span className="text-[10px] px-2 py-1 rounded-full bg-green-500/10 text-green-500 font-medium border border-green-500/20">
                      Analyzed
                    </span>
                  )}
                  {contract.status === 'processing' && (
                    <span className="text-[10px] px-2 py-1 rounded-full bg-blue-500/10 text-blue-500 font-medium border border-blue-500/20">
                      Processing
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center border border-dashed border-[var(--color-border)] rounded-lg bg-[var(--color-background)]/50">
            <History className="h-8 w-8 text-[var(--color-muted-foreground)] opacity-30 mb-3" />
            <p className="text-sm font-medium text-[var(--color-foreground)] mb-1">No recent uploads</p>
            <p className="text-xs text-[var(--color-muted-foreground)] max-w-xs">
              Contracts you upload will appear here for quick access.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
