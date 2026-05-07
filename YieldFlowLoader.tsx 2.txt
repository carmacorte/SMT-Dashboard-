import React, { useState, useEffect, useCallback } from 'react';
import styles from './YieldFlowLoader.module.css';

export type YieldFlowLoaderVisual = 'ravens' | 'particle-spiral' | 'smtinel-orbit' | 'analytics-grid' | 'trace-network' | 'custom-image';

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
  /**
   * Selects the loader artwork. Use `custom-image` with `loaderImageSrc` to render
   * an uploaded SMTinel loader image without changing component internals.
   */
  visual?: YieldFlowLoaderVisual;
  /** Source URL/path for user-supplied loader images. */
  loaderImageSrc?: string;
  /** Accessible alt text for `loaderImageSrc`. */
  loaderImageAlt?: string;
}

const spiralDots = [
  [143, 121, 1.6], [153, 118, 1.8], [158, 126, 1.5], [151, 134, 1.4], [137, 132, 1.7],
  [129, 120, 1.5], [134, 104, 1.8], [154, 96, 1.6], [176, 105, 1.7], [187, 128, 1.6],
  [177, 156, 1.8], [146, 170, 1.5], [109, 158, 1.7], [91, 124, 1.6], [103, 82, 1.8],
  [148, 59, 1.7], [202, 72, 1.5], [232, 119, 1.8], [220, 181, 1.6], [163, 217, 1.8],
  [86, 205, 1.5], [36, 146, 1.7], [42, 58, 1.6], [122, 17, 1.8], [226, 37, 1.5],
];

const matrixCells = Array.from({ length: 64 }, (_, index) => {
  const row = Math.floor(index / 8);
  const col = index % 8;
  const value = row === col ? 0.95 : ((row * 17 + col * 11) % 10) / 18 + 0.12;
  return { col, row, value };
});

const boxPlots = [28, 45, 63, 84, 103, 122, 141, 160, 179, 198, 217, 236];

function renderRavenVisual(stylesRef: typeof styles) {
  return (
    <svg className={stylesRef.animationCanvas} viewBox="0 0 300 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dual cyber ravens orbiting security core">
      <defs>
        <radialGradient id="eyeCyan" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#D2F8FF"/><stop offset="55%" stopColor="#22D3EE"/><stop offset="100%" stopColor="#22D3EE" stopOpacity="0"/></radialGradient>
        <radialGradient id="eyeBlue" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#D7EAFF"/><stop offset="55%" stopColor="#1E90FF"/><stop offset="100%" stopColor="#1E90FF" stopOpacity="0"/></radialGradient>
        <linearGradient id="shieldStroke" x1="150" y1="78" x2="150" y2="170"><stop offset="0" stopColor="#22D3EE"/><stop offset="0.5" stopColor="#1E90FF"/><stop offset="1" stopColor="#22B573"/></linearGradient>
        <filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.8"/></filter>
      </defs>

      <ellipse cx="150" cy="120" rx="102" ry="76" fill="none" stroke="#1F2937" strokeWidth="1.2" strokeDasharray="5 6" opacity="0.45" className={stylesRef.orbitRing}/>
      <ellipse cx="150" cy="120" rx="88" ry="64" fill="none" stroke="#334155" strokeWidth="1" opacity="0.3" className={stylesRef.orbitRing}/>

      <g className={stylesRef.shield}>
        <path d="M150 82 L172 92 L172 126 C172 144 160 158 150 164 C140 158 128 144 128 126 L128 92 Z" fill="#08101E" stroke="url(#shieldStroke)" strokeWidth="1.8" className={stylesRef.shieldOutline}/>
        <path d="M150 94 L162 100 L162 124 C162 135 155 144 150 147 C145 144 138 135 138 124 L138 100 Z" fill="none" stroke="#22D3EE" strokeOpacity="0.6" strokeWidth="1"/>
        <circle cx="150" cy="120" r="10" fill="#0D1B2A" stroke="#22B573" strokeWidth="1" className={stylesRef.shieldCore}/>
        <circle cx="150" cy="120" r="5" fill="#22B573" filter="url(#softGlow)" opacity="0.8" className={stylesRef.shieldCore}/>
      </g>

      <g className={stylesRef.ravenLeft}>
        <g transform="translate(70 80)">
          <path d="M9 29 C4 22 4 14 11 9 C18 5 31 5 40 11 C48 15 53 23 52 30 C49 39 39 45 26 45 C16 44 11 38 9 29 Z" fill="#02060D"/>
          <path d="M34 18 L46 20 L40 28" fill="none" stroke="#22D3EE" strokeWidth="1.2" strokeLinecap="round"/>
          <path d="M18 20 L28 16 L36 20 L26 24 Z" fill="none" stroke="#22D3EE" strokeWidth="1"/>
          <path d="M16 29 L26 25 L34 30 L24 35 Z" fill="none" stroke="#22D3EE" strokeWidth="0.9"/>
          <path d="M12 16 L5 14 L11 20" fill="#02060D" stroke="#22D3EE" strokeWidth="0.8"/>
          <circle cx="18" cy="16" r="2.2" fill="url(#eyeCyan)" className={stylesRef.ravenEye}/>
          <circle cx="18" cy="16" r="4" fill="#22D3EE" opacity="0.3" filter="url(#softGlow)" className={stylesRef.ravenEye}/>
        </g>
      </g>

      <g className={stylesRef.ravenRight}>
        <g transform="translate(178 112) scale(-1 1)">
          <path d="M9 29 C4 22 4 14 11 9 C18 5 31 5 40 11 C48 15 53 23 52 30 C49 39 39 45 26 45 C16 44 11 38 9 29 Z" fill="#001a33"/>
          <path d="M34 18 L46 20 L40 28" fill="none" stroke="#1E90FF" strokeWidth="1.2" strokeLinecap="round"/>
          <path d="M18 20 L28 16 L36 20 L26 24 Z" fill="none" stroke="#1E90FF" strokeWidth="1"/>
          <path d="M16 29 L26 25 L34 30 L24 35 Z" fill="none" stroke="#1E90FF" strokeWidth="0.9"/>
          <path d="M12 16 L5 14 L11 20" fill="#001a33" stroke="#1E90FF" strokeWidth="0.8"/>
          <circle cx="18" cy="16" r="2.2" fill="url(#eyeBlue)" className={stylesRef.ravenEye}/>
          <circle cx="18" cy="16" r="4" fill="#1E90FF" opacity="0.32" filter="url(#softGlow)" className={stylesRef.ravenEye}/>
        </g>
      </g>

      <g className={stylesRef.glowRing} opacity="0.82">
        <rect x="16" y="198" width="12" height="12" rx="2" fill="#22D3EE"/>
        <rect x="32" y="198" width="12" height="12" rx="2" fill="#1E90FF"/>
        <rect x="48" y="198" width="12" height="12" rx="2" fill="#22B573"/>
      </g>
    </svg>
  );
}

function renderParticleSpiral(stylesRef: typeof styles) {
  return (
    <svg className={`${stylesRef.animationCanvas} ${stylesRef.posterCanvas}`} viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SMTinel particle spiral loader">
      <defs>
        <radialGradient id="loaderBg" cx="50%" cy="50%" r="70%"><stop offset="0%" stopColor="#081a23"/><stop offset="52%" stopColor="#02060d"/><stop offset="100%" stopColor="#000"/></radialGradient>
        <linearGradient id="spiralStroke" x1="45" y1="260" x2="245" y2="55"><stop stopColor="var(--accent-color)"/><stop offset="0.48" stopColor="#28f5ff"/><stop offset="1" stopColor="var(--secondary-color)"/></linearGradient>
        <filter id="particleGlow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect width="300" height="300" rx="26" fill="url(#loaderBg)"/>
      <g className={stylesRef.starField} opacity="0.52">
        {spiralDots.map(([cx, cy, r], index) => <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r={r} fill={index % 3 === 0 ? 'var(--secondary-color)' : 'var(--accent-color)'}/>) }
      </g>
      <path className={stylesRef.spiralPath} d="M149 151 C162 143 160 123 145 121 C126 118 118 142 134 157 C157 178 198 160 203 124 C210 76 157 43 107 60 C42 82 19 163 63 221 C111 284 211 276 263 210" fill="none" stroke="url(#spiralStroke)" strokeWidth="3.2" strokeLinecap="round" filter="url(#particleGlow)"/>
      <path d="M149 151 C162 143 160 123 145 121 C126 118 118 142 134 157 C157 178 198 160 203 124 C210 76 157 43 107 60 C42 82 19 163 63 221 C111 284 211 276 263 210" fill="none" stroke="#99fbff" strokeWidth="0.8" strokeLinecap="round" opacity="0.9"/>
      <g className={stylesRef.candles} opacity="0.35">
        {[34, 68, 232, 258].map((x, index) => <g key={x} transform={`translate(${x} ${50 + index * 42})`}><line x1="0" y1="-16" x2="0" y2="18" stroke="#22d3ee" strokeWidth="0.8"/><rect x="-5" y="-8" width="10" height="16" fill="none" stroke="#22d3ee" strokeWidth="0.8"/></g>)}
      </g>
    </svg>
  );
}

function renderSmtinelOrbit(stylesRef: typeof styles) {
  return (
    <svg className={`${stylesRef.animationCanvas} ${stylesRef.posterCanvas}`} viewBox="0 0 300 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SMTinel orbit brand loader">
      <rect width="300" height="380" rx="30" fill="#000"/>
      <g transform="translate(150 150)" className={stylesRef.rotatingRadar}>
        <circle r="106" fill="none" stroke="#123d4b" strokeWidth="1" strokeDasharray="2 7"/>
        <circle r="82" fill="none" stroke="#1a6c76" strokeWidth="0.8" opacity="0.58"/>
        <path d="M0 0 C18 -12 10 -38 -12 -35 C-46 -31 -44 17 -10 32 C42 56 91 11 80 -43 C64 -120 -45 -134 -103 -72" fill="none" stroke="#38f7ff" strokeWidth="3" strokeLinecap="round" filter="url(#smtinelGlow)"/>
      </g>
      <defs><filter id="smtinelGlow" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="3"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <g className={stylesRef.loaderNodes}>
        {[42, 82, 122, 178, 218, 258].map((x, index) => <g key={x} transform={`translate(${x} ${90 + (index % 2) * 72})`}><rect x="-17" y="-13" width="34" height="26" fill="#020a10" stroke="#20dceb" opacity="0.75"/><line x1="-11" y1="0" x2="11" y2="0" stroke="#22b573"/><line x1="-11" y1="-7" x2="11" y2="-7" stroke="#1e90ff" opacity="0.7"/></g>)}
      </g>
      <text x="150" y="317" textAnchor="middle" fill="#fff" fontFamily="Inter, Segoe UI, sans-serif" fontSize="44" fontWeight="300" letterSpacing="1">SMTinel</text>
    </svg>
  );
}

function renderAnalyticsGrid(stylesRef: typeof styles) {
  const tile = (x: number, y: number, children: React.ReactNode, label?: string) => (
    <g transform={`translate(${x} ${y})`}>
      <rect width="86" height="74" fill="#02050a" stroke="#173440" strokeWidth="1"/>
      {label && <text x="9" y="14" fill="#66f8ff" fontSize="7" fontFamily="monospace">{label}</text>}
      {children}
    </g>
  );

  return (
    <svg className={`${stylesRef.animationCanvas} ${stylesRef.wideCanvas}`} viewBox="0 0 300 225" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SMTinel analytics dashboard loader">
      <rect width="300" height="225" rx="18" fill="#010409"/>
      <g className={stylesRef.dashboardTiles}>
        {tile(6, 6, <><path d="M18 55 C35 14 64 18 73 8" fill="none" stroke="#27f3ff" strokeWidth="2"/><circle cx="39" cy="39" r="9" fill="#1ee6ff" opacity="0.22"/></>, 'Yield')}
        {tile(107, 6, <>{boxPlots.slice(0, 6).map((_, i) => <g key={i} transform={`translate(${14 + i * 11} 38)`}><line y1="-21" y2="24" stroke="#246fff"/><rect x="-4" y="-8" width="8" height="16" fill="none" stroke="#28f5ff"/><circle cy={-26 + (i % 3) * 8} r="1.8" fill="#22b573"/></g>)}</>, 'SPI')}
        {tile(208, 6, <g transform="translate(12 14)">{matrixCells.map(({ col, row, value }) => <rect key={`${col}-${row}`} x={col * 7} y={row * 6} width="7" height="6" fill={col === row ? '#29f2ff' : '#1fd06b'} opacity={value}/>)}</g>, 'Corr')}
        {tile(6, 82, <><path d="M12 46 C29 22 49 21 67 39" fill="none" stroke="#20e4ec" strokeWidth="2" strokeLinecap="round"/><text x="10" y="59" fill="#58f4ff" fontSize="8">AOI</text><text x="53" y="22" fill="#58f4ff" fontSize="8">SPI</text></>, 'Flow')}
        {tile(107, 82, <>{[13, 25, 37, 49, 61, 73].map((y, i) => <path key={y} d={`M7 ${y} C23 ${y - 12} 39 ${y + 12} 80 ${y - (i % 2) * 9}`} fill="none" stroke={i % 3 === 0 ? '#22b573' : i % 3 === 1 ? '#24e8ff' : '#1e90ff'} strokeWidth="1.1" opacity="0.8"/>)}</>, 'Signals')}
        {tile(208, 82, <><circle cx="43" cy="35" r="16" fill="none" stroke="#29f2ff" strokeWidth="2"/><text x="43" y="39" textAnchor="middle" fill="#fff" fontSize="11">MES</text><path d="M43 35 L15 18 M43 35 L75 21 M43 35 L21 61 M43 35 L70 57" stroke="#22b573" opacity="0.75"/></>, 'Net')}
        {tile(6, 158, <><path d="M17 57 C38 7 64 9 76 20" fill="none" stroke="#29f2ff" strokeWidth="2"/><circle cx="35" cy="44" r="11" fill="#22b573" opacity="0.35"/></>, 'Golden')}
        {tile(107, 158, <>{boxPlots.slice(0, 7).map((_, i) => <g key={i} transform={`translate(${11 + i * 11} 38)`}><line y1="-22" y2="23" stroke={i < 3 ? '#22b573' : '#ff5757'}/><rect x="-4" y="-7" width="8" height="15" fill="none" stroke={i < 3 ? '#22b573' : '#ff5757'}/></g>)}</>, 'Stable')}
        {tile(208, 158, <><path d="M13 42 C37 10 68 11 76 22 C85 35 61 49 50 37 C40 27 52 17 59 23" fill="none" stroke="#29f2ff" strokeWidth="2"/><text x="43" y="44" textAnchor="middle" fill="#fff" fontSize="16">SMT</text></>, 'SMTinel')}
      </g>
    </svg>
  );
}

function renderTraceNetwork(stylesRef: typeof styles) {
  const metrics = ['Yield', 'OEE', 'SPI', 'AOI', 'Cycle', 'FPY'];
  return (
    <svg className={`${stylesRef.animationCanvas} ${stylesRef.posterCanvas}`} viewBox="0 0 300 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SMTinel trace network loader">
      <rect width="300" height="420" rx="30" fill="#000"/>
      <path className={stylesRef.spiralPath} d="M150 28 C119 82 159 111 171 82 C182 55 141 51 135 79 C129 111 169 131 198 105" fill="none" stroke="#26f6ff" strokeWidth="2" opacity="0.8"/>
      <line x1="150" y1="44" x2="150" y2="386" stroke="#1de7ef" strokeWidth="1.2" opacity="0.8"/>
      {['Unit Created', 'Material Verified', 'Print Started', 'AOI Inspection', 'Trace Attached', 'Reflow Completed', 'ICT Tested', 'Functional Test', 'Repair Applied', 'Final Inspection', 'Unit Released'].map((label, index) => <g key={label} className={stylesRef.timelineNode} transform={`translate(150 ${54 + index * 31})`}><circle r="5" fill="#03151b" stroke="#28f5ff" strokeWidth="2"/><text x="14" y="4" fill="#8afaff" fontSize="8" fontFamily="Inter, sans-serif">{label}</text></g>)}
      <g className={stylesRef.networkCore} transform="translate(150 184)">
        {[[0,-40],[-58,5],[-38,62],[48,62],[60,2]].map(([x, y], i) => <g key={`${x}-${y}`}><line x1="0" y1="0" x2={x} y2={y} stroke="#20dceb" opacity="0.5"/><circle cx={x} cy={y} r={i === 0 ? 22 : 17} fill="#031520" stroke="#25eaff" strokeWidth="2"/><text x={x} y={y + 4} textAnchor="middle" fill="#e9feff" fontSize={i === 0 ? 14 : 10}>{['MES','Repair','Trace','FCT','ICT'][i]}</text></g>)}
      </g>
      {metrics.map((metric, index) => {
        const left = index % 2 === 0;
        const x = left ? 16 : 214;
        const y = 30 + index * 58;
        return <g key={metric} transform={`translate(${x} ${y})`}><text x="0" y="0" fill="#64f5ff" fontSize="8">{metric}</text>{[0, 1, 2, 3].map((item) => <g key={item} transform={`translate(${8 + item * 13} 24)`}><line y1="-20" y2="20" stroke="#1e90ff"/><rect x="-4" y="-7" width="8" height="14" fill="none" stroke={item % 2 ? '#22b573' : '#24e8ff'}/></g>)}</g>;
      })}
    </svg>
  );
}

function renderLoaderVisual(visual: YieldFlowLoaderVisual, loaderImageSrc: string | undefined, loaderImageAlt: string) {
  if ((visual === 'custom-image' || loaderImageSrc) && loaderImageSrc) {
    return <img className={`${styles.animationCanvas} ${styles.imageCanvas}`} src={loaderImageSrc} alt={loaderImageAlt} />;
  }

  switch (visual) {
    case 'particle-spiral':
      return renderParticleSpiral(styles);
    case 'smtinel-orbit':
      return renderSmtinelOrbit(styles);
    case 'analytics-grid':
      return renderAnalyticsGrid(styles);
    case 'trace-network':
      return renderTraceNetwork(styles);
    default:
      return renderRavenVisual(styles);
  }
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
  visual = 'ravens',
  loaderImageSrc,
  loaderImageAlt = 'SMTinel loader artwork',
}) => {
  const [progress, setProgress] = useState(uploadProgress);
  const [loading, setLoading] = useState(isLoading);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const [externalCompleteNotified, setExternalCompleteNotified] = useState(uploadProgress >= 100);
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

  useEffect(() => {
    if (uploadProgress < 100) {
      setExternalCompleteNotified(false);
      return undefined;
    }

    if (!externalCompleteNotified) {
      setExternalCompleteNotified(true);
      setCompleted(true);
      onUploadComplete?.({ success: true });
      const timer = window.setTimeout(() => setCompleted(false), 3000);
      return () => window.clearTimeout(timer);
    }

    return undefined;
  }, [externalCompleteNotified, onUploadComplete, uploadProgress]);

  const completeUpload = useCallback(() => {
    setProgress(100);
    setCompleted(true);
    setLoading(false);
    onUploadComplete?.({ success: true });
    window.setTimeout(() => setCompleted(false), 3000);
  }, [onUploadComplete]);

  const failUpload = useCallback((message: string) => {
    setError(message);
    setLoading(false);
    onUploadComplete?.({ success: false, message });
  }, [onUploadComplete]);

  const handleFileSelect = useCallback(async (file: File) => {
    if (!file) return;

    setError(null);
    setLoading(true);
    setProgress(0);

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
        completeUpload();
        return;
      }

      failUpload(`Upload failed with status ${xhr.status}`);
    });

    xhr.addEventListener('error', () => {
      failUpload('Upload failed. Please try again.');
    });

    xhr.addEventListener('abort', () => {
      failUpload('Upload cancelled.');
    });

    try {
      xhr.open('POST', uploadEndpoint);
      xhr.send(formData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      failUpload(message);
    }
  }, [completeUpload, failUpload, uploadEndpoint]);

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
    if (!loading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
      e.currentTarget.value = '';
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
      <div className={styles.loaderWrapper} data-loader-visual={visual}>
        {renderLoaderVisual(visual, loaderImageSrc, loaderImageAlt)}

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
