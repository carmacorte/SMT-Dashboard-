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
        {/* SVG Canvas */}
        <svg className={styles.animationCanvas} viewBox="0 0 300 240" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="leftEyeGlow" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stopColor="#b7f7ff" />
              <stop offset="55%" stopColor="#22D3EE" />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="rightEyeGlow" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stopColor="#cbe6ff" />
              <stop offset="55%" stopColor="#1E90FF" />
              <stop offset="100%" stopColor="#1E90FF" stopOpacity="0" />
            </radialGradient>
          </defs>

          <ellipse cx="150" cy="120" rx="108" ry="78" className={styles.orbitRing} />
          <ellipse cx="150" cy="120" rx="88" ry="62" className={styles.orbitRingSoft} />

          <g className={styles.ravenLeft}>
            <g transform="translate(82 120) scale(1.02)">
              <path d="M-27 0 C-24 -12 -16 -19 -6 -19 C5 -19 15 -12 17 -2 C11 4 2 7 -11 8 C-18 8 -24 6 -27 0Z" fill="#020305" />
              <path d="M11 -4 L23 -8 L13 2 Z" fill="#0b141d" className={styles.ravenBeak} />
              <path d="M-24 -2 C-13 6 3 7 16 0" fill="none" stroke="#22D3EE" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M-20 -11 L-10 -16 L0 -13 L8 -7" fill="none" stroke="#22D3EE" strokeWidth="1.2" strokeLinecap="round" opacity="0.95" />
              <path d="M-17 3 L-6 -1 L4 2 L13 -1" fill="none" stroke="#22D3EE" strokeWidth="1" strokeLinecap="round" opacity="0.7" />
              <circle cx="8" cy="-8" r="2.6" fill="url(#leftEyeGlow)" className={styles.ravenEye} />
            </g>
          </g>

          <g className={styles.ravenRight}>
            <g transform="translate(218 120) scale(1.02, -1.02)">
              <path d="M-27 0 C-24 -12 -16 -19 -6 -19 C5 -19 15 -12 17 -2 C11 4 2 7 -11 8 C-18 8 -24 6 -27 0Z" fill="#001a33" />
              <path d="M11 -4 L23 -8 L13 2 Z" fill="#0c2442" className={styles.ravenBeak} />
              <path d="M-24 -2 C-13 6 3 7 16 0" fill="none" stroke="#1E90FF" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M-20 -11 L-10 -16 L0 -13 L8 -7" fill="none" stroke="#1E90FF" strokeWidth="1.2" strokeLinecap="round" opacity="0.95" />
              <path d="M-17 3 L-6 -1 L4 2 L13 -1" fill="none" stroke="#22B573" strokeWidth="0.95" strokeLinecap="round" opacity="0.8" />
              <circle cx="8" cy="-8" r="2.6" fill="url(#rightEyeGlow)" className={styles.ravenEye} />
            </g>
          </g>

          {/* Central Shield */}
          <g className={styles.shield}>
            <path
              d="M 150 72 L 182 90 L 182 142 Q 150 171 118 142 L 118 90 Z"
              fill="none"
              stroke="#22D3EE"
              strokeWidth="1.8"
              opacity="0.6"
              className={styles.shieldOutline}
            />
            <path d="M 150 92 L 166 100 L 166 133 Q 150 148 134 133 L 134 100 Z" fill="#061321" opacity="0.9" />
            <circle cx="150" cy="118" r="15" fill="none" stroke="#1E90FF" strokeWidth="1.2" opacity="0.5" className={styles.shieldCore} />
            <circle cx="150" cy="118" r="9" fill="none" stroke="#22B573" strokeWidth="1" opacity="0.5" className={styles.shieldCore} />
          </g>
          <ellipse cx="150" cy="120" rx="120" ry="86" className={styles.glowRing} />
        </svg>

        {/* Status Text */}
        <div className={styles.statusContainer}>
          <h2 className={styles.statusText}>{statusText}</h2>
          {loading && <p className={styles.statusSubtext}>Processing...</p>}
        </div>

        {/* Progress Bar */}
        {enableUpload && (
          <div className={styles.progressWrapper}>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{
                  width: `${progress}%`,
                  backgroundColor: progress >= 100 ? secondaryColor : accentColor,
                }}
              />
            </div>
            <p className={styles.progressText}>{Math.round(progress)}%</p>
          </div>
        )}

        {/* Completion State */}
        {completed && (
          <div className={styles.completionState}>
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="2" style={{ color: secondaryColor }} />
              <path d="M15 24L21 30L33 18" stroke="currentColor" strokeWidth="2" fill="none" style={{ color: secondaryColor }} />
            </svg>
            <p className={styles.completionText}>Upload Complete</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className={styles.errorState}>
            <p className={styles.errorText}>⚠ {error}</p>
          </div>
        )}

        {/* Upload Zone */}
        {enableUpload && !completed && (
          <div
            className={`${styles.uploadZone} ${loading ? styles.uploadDisabled : ''}`}
            onClick={handleClick}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {!loading && <p className={styles.uploadText}>Drag files here or click to upload</p>}
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              className={styles.fileInput}
              disabled={loading}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default YieldFlowLoader;
