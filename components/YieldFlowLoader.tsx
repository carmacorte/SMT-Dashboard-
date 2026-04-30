import React, { useState, useEffect, useCallback } from 'react';
import styles from './YieldFlowLoader.module.css';

export interface YieldFlowLoaderProps {
  animationSpeed?: number;
  accentColor?: string;
  secondaryColor?: string;
  statusText?: string;
  uploadProgress?: number;
  isLoading?: boolean;
  onUploadComplete?: (data: { success: boolean; message?: string }) => void;
  onProgressChange?: (progress: number) => void;
  enableUpload?: boolean;
  uploadEndpoint?: string;
}

export const YieldFlowLoader: React.FC<YieldFlowLoaderProps> = ({
  animationSpeed = 3,
  accentColor = '#1E90FF',
  secondaryColor = '#24C3A2',
  statusText = 'YIELD FLOW',
  uploadProgress = 0,
  isLoading = false,
  onUploadComplete,
  onProgressChange,
  enableUpload = true,
  uploadEndpoint = '/api/upload',
}) => {
  const [progress, setProgress] = useState(uploadProgress);
  const [loading, setLoading] = useState(isLoading);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  useEffect(() => {
    setProgress(uploadProgress);
  }, [uploadProgress]);

  useEffect(() => {
    setLoading(isLoading);
  }, [isLoading]);

  useEffect(() => {
    onProgressChange?.(progress);
  }, [progress, onProgressChange]);

  const handleFileSelect = useCallback(async (file: File) => {
    if (!file) return;

    setError(null);
    setLoading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setProgress(Math.min(percentComplete, 99));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          setProgress(100);
          setCompleted(true);
          setLoading(false);
          onUploadComplete?.({ success: true });
          setTimeout(() => setCompleted(false), 3000);
        } else {
          throw new Error(`Upload failed with status ${xhr.status}`);
        }
      });

      xhr.addEventListener('error', () => {
        setError('Upload failed. Please try again.');
        setLoading(false);
        onUploadComplete?.({ success: false, message: 'Upload failed' });
      });

      xhr.addEventListener('abort', () => {
        setError('Upload cancelled.');
        setLoading(false);
      });

      xhr.open('POST', uploadEndpoint);
      xhr.send(formData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      setLoading(false);
      onUploadComplete?.({ success: false, message });
    }
  }, [uploadEndpoint, onUploadComplete]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.add(styles.dragActive);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove(styles.dragActive);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove(styles.dragActive);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <div
      className={styles.container}
      style={{
        '--accent-color': accentColor,
        '--secondary-color': secondaryColor,
        '--animation-speed': `${animationSpeed}s`,
      } as React.CSSProperties}
    >
      <div className={styles.loaderWrapper}>
        <svg className={styles.animationCanvas} viewBox="0 0 300 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dual cyber ravens orbiting security core">
          <defs>
            <radialGradient id="eyeCyan" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#D2F8FF"/><stop offset="55%" stopColor="#22D3EE"/><stop offset="100%" stopColor="#22D3EE" stopOpacity="0"/></radialGradient>
            <radialGradient id="eyeBlue" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#D7EAFF"/><stop offset="55%" stopColor="#1E90FF"/><stop offset="100%" stopColor="#1E90FF" stopOpacity="0"/></radialGradient>
            <linearGradient id="shieldStroke" x1="150" y1="78" x2="150" y2="170"><stop offset="0" stopColor="#22D3EE"/><stop offset="0.5" stopColor="#1E90FF"/><stop offset="1" stopColor="#22B573"/></linearGradient>
            <filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.8"/></filter>
          </defs>

          <ellipse cx="150" cy="120" rx="102" ry="76" fill="none" stroke="#1F2937" strokeWidth="1.2" strokeDasharray="5 6" opacity="0.45" className={styles.orbitRing}/>
          <ellipse cx="150" cy="120" rx="88" ry="64" fill="none" stroke="#334155" strokeWidth="1" opacity="0.3" className={styles.orbitRing}/>

          <g className={styles.shield}>
            <path d="M150 82 L172 92 L172 126 C172 144 160 158 150 164 C140 158 128 144 128 126 L128 92 Z" fill="#08101E" stroke="url(#shieldStroke)" strokeWidth="1.8" className={styles.shieldOutline}/>
            <path d="M150 94 L162 100 L162 124 C162 135 155 144 150 147 C145 144 138 135 138 124 L138 100 Z" fill="none" stroke="#22D3EE" strokeOpacity="0.6" strokeWidth="1"/>
            <circle cx="150" cy="120" r="10" fill="#0D1B2A" stroke="#22B573" strokeWidth="1" className={styles.shieldCore}/>
            <circle cx="150" cy="120" r="5" fill="#22B573" filter="url(#softGlow)" opacity="0.8" className={styles.shieldCore}/>
          </g>

          <g className={styles.ravenLeft}>
            <g transform="translate(70 80)">
              <path d="M9 29 C4 22 4 14 11 9 C18 5 31 5 40 11 C48 15 53 23 52 30 C49 39 39 45 26 45 C16 44 11 38 9 29 Z" fill="#02060D"/>
              <path d="M34 18 L46 20 L40 28" fill="none" stroke="#22D3EE" strokeWidth="1.2" strokeLinecap="round"/>
              <path d="M18 20 L28 16 L36 20 L26 24 Z" fill="none" stroke="#22D3EE" strokeWidth="1"/>
              <path d="M16 29 L26 25 L34 30 L24 35 Z" fill="none" stroke="#22D3EE" strokeWidth="0.9"/>
              <path d="M12 16 L5 14 L11 20" fill="#02060D" stroke="#22D3EE" strokeWidth="0.8"/>
              <circle cx="18" cy="16" r="2.2" fill="url(#eyeCyan)" className={styles.ravenEye}/>
              <circle cx="18" cy="16" r="4" fill="#22D3EE" opacity="0.3" filter="url(#softGlow)" className={styles.ravenEye}/>
            </g>
          </g>

          <g className={styles.ravenRight}>
            <g transform="translate(178 112) scale(-1 1)">
              <path d="M9 29 C4 22 4 14 11 9 C18 5 31 5 40 11 C48 15 53 23 52 30 C49 39 39 45 26 45 C16 44 11 38 9 29 Z" fill="#001a33"/>
              <path d="M34 18 L46 20 L40 28" fill="none" stroke="#1E90FF" strokeWidth="1.2" strokeLinecap="round"/>
              <path d="M18 20 L28 16 L36 20 L26 24 Z" fill="none" stroke="#1E90FF" strokeWidth="1"/>
              <path d="M16 29 L26 25 L34 30 L24 35 Z" fill="none" stroke="#1E90FF" strokeWidth="0.9"/>
              <path d="M12 16 L5 14 L11 20" fill="#001a33" stroke="#1E90FF" strokeWidth="0.8"/>
              <circle cx="18" cy="16" r="2.2" fill="url(#eyeBlue)" className={styles.ravenEye}/>
              <circle cx="18" cy="16" r="4" fill="#1E90FF" opacity="0.32" filter="url(#softGlow)" className={styles.ravenEye}/>
            </g>
          </g>

          <g className={styles.glowRing} opacity="0.82">
            <rect x="16" y="198" width="12" height="12" rx="2" fill="#22D3EE"/>
            <rect x="32" y="198" width="12" height="12" rx="2" fill="#1E90FF"/>
            <rect x="48" y="198" width="12" height="12" rx="2" fill="#22B573"/>
          </g>
        </svg>

        <div className={styles.statusContainer}>
          <h2 className={styles.statusText}>{statusText}</h2>
          {loading && <p className={styles.statusSubtext}>Processing...</p>}
        </div>

        {enableUpload && (
          <div className={styles.progressWrapper}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progress}%`, backgroundColor: progress >= 100 ? secondaryColor : accentColor }} />
            </div>
            <p className={styles.progressText}>{Math.round(progress)}%</p>
          </div>
        )}

        {completed && (<div className={styles.completionState}><svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="2" style={{ color: secondaryColor }} /><path d="M15 24L21 30L33 18" stroke="currentColor" strokeWidth="2" fill="none" style={{ color: secondaryColor }} /></svg><p className={styles.completionText}>Upload Complete</p></div>)}

        {error && !loading && (<div className={styles.errorState}><p className={styles.errorText}>⚠ {error}</p></div>)}

        {enableUpload && !completed && (
          <div className={`${styles.uploadZone} ${loading ? styles.uploadDisabled : ''}`} onClick={handleClick} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
            {!loading && <p className={styles.uploadText}>Drag files here or click to upload</p>}
            <input ref={fileInputRef} type="file" onChange={handleFileChange} className={styles.fileInput} disabled={loading} />
          </div>
        )}
      </div>
    </div>
  );
};

export default YieldFlowLoader;
