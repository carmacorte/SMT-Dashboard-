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
        <svg
          className={styles.animationCanvas}
          viewBox="0 0 400 400"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Outer orbit rings */}
          <circle
            cx="200"
            cy="200"
            r="140"
            className={styles.orbitRing}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            opacity="0.3"
          />
          <circle
            cx="200"
            cy="200"
            r="100"
            className={styles.orbitRing}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.2"
            opacity="0.2"
          />

          {/* Left Raven (Blue) */}
          <g className={styles.ravenLeft} style={{ color: accentColor }}>
            <g className={styles.ravenBody}>
              <path
                d="M 80 180 Q 75 170 80 160 L 85 155 Q 90 160 85 175 Z"
                fill="currentColor"
              />
              <circle cx="82" cy="158" r="3" fill="currentColor" className={styles.ravenEye} />
              <path d="M 85 160 L 95 158 L 93 165 Z" fill="currentColor" className={styles.ravenBeak} />
            </g>
          </g>

          {/* Right Raven (Green) */}
          <g className={styles.ravenRight} style={{ color: secondaryColor }}>
            <g className={styles.ravenBody}>
              <path
                d="M 320 180 Q 325 170 320 160 L 315 155 Q 310 160 315 175 Z"
                fill="currentColor"
              />
              <circle cx="318" cy="158" r="3" fill="currentColor" className={styles.ravenEye} />
              <path d="M 315 160 L 305 158 L 307 165 Z" fill="currentColor" className={styles.ravenBeak} />
            </g>
          </g>

          {/* Central Shield */}
          <g className={styles.shield}>
            <path
              d="M 200 120 L 240 140 L 240 220 Q 200 260 160 220 L 160 140 Z"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.6"
              className={styles.shieldOutline}
            />
            {/* Pulsing shield core */}
            <circle cx="200" cy="180" r="30" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4" className={styles.shieldCore} />
            <circle cx="200" cy="180" r="20" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3" className={styles.shieldCore} />
          </g>

          {/* Glow rings */}
          <circle
            cx="200"
            cy="200"
            r="160"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.15"
            className={styles.glowRing}
          />
          <circle
            cx="200"
            cy="200"
            r="180"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.08"
            className={styles.glowRing}
          />
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
