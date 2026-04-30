import React, { useState } from 'react';
import { YieldFlowLoader } from '../components';

/**
 * Example implementations of the YieldFlowLoader component
 * showing different configurations and use cases
 */

export const BasicExample: React.FC = () => {
  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="YIELD FLOW"
        animationSpeed={3}
        accentColor="#1E90FF"
        secondaryColor="#24C3A2"
      />
    </div>
  );
};

export const UploadWithProgressExample: React.FC = () => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready');

  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="UPLOAD PROCESSING"
        uploadProgress={progress}
        isLoading={progress > 0 && progress < 100}
        animationSpeed={2.5}
        accentColor="#FF6B35"
        secondaryColor="#F7931E"
        onProgressChange={(p) => setProgress(p)}
        onUploadComplete={(result) => {
          setStatus(result.success ? 'Upload Complete' : 'Upload Failed');
        }}
        enableUpload={true}
        uploadEndpoint="/api/upload"
      />
    </div>
  );
};

export const CustomColorsExample: React.FC = () => {
  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="CUSTOM THEME"
        animationSpeed={3.5}
        accentColor="#9D4EDD"
        secondaryColor="#3A86FF"
      />
    </div>
  );
};

export const FastAnimationExample: React.FC = () => {
  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="FAST MODE"
        animationSpeed={1.5}
        accentColor="#00D9FF"
        secondaryColor="#FF006E"
      />
    </div>
  );
};

export const SlowAnimationExample: React.FC = () => {
  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="SLOW MODE"
        animationSpeed={5}
        accentColor="#06FFA5"
        secondaryColor="#0099FF"
      />
    </div>
  );
};

export const LoadingStateExample: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="LOADING DATA"
        isLoading={isLoading}
        uploadProgress={50}
        animationSpeed={3}
        accentColor="#1E90FF"
        secondaryColor="#24C3A2"
        onUploadComplete={() => setIsLoading(false)}
      />
    </div>
  );
};

export const CompleteWorkflowExample: React.FC = () => {
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing' | 'complete'>('idle');
  const [progress, setProgress] = useState(0);

  const handleUploadStart = () => {
    setPhase('uploading');
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setPhase('processing');
          setTimeout(() => setPhase('complete'), 2000);
          return 100;
        }
        return prev + Math.random() * 30;
      });
    }, 500);
  };

  return (
    <div style={{ width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <YieldFlowLoader
        statusText={
          phase === 'idle' ? 'YIELD FLOW' :
          phase === 'uploading' ? 'UPLOADING' :
          phase === 'processing' ? 'PROCESSING' :
          'COMPLETE'
        }
        uploadProgress={progress}
        isLoading={phase === 'uploading' || phase === 'processing'}
        animationSpeed={3}
        accentColor="#1E90FF"
        secondaryColor="#24C3A2"
        onUploadComplete={() => {
          setPhase('idle');
          setProgress(0);
        }}
        enableUpload={phase === 'idle'}
      />
      {phase === 'idle' && (
        <button
          onClick={handleUploadStart}
          style={{
            marginTop: '40px',
            padding: '12px 24px',
            fontSize: '14px',
            fontWeight: '600',
            backgroundColor: '#1E90FF',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          Start Upload Simulation
        </button>
      )}
    </div>
  );
};

/**
 * Integration example for use within a larger application
 * Shows how to integrate with error handling and state management
 */
export const IntegratedExample: React.FC = () => {
  const [uploadState, setUploadState] = useState<{
    progress: number;
    loading: boolean;
    error: string | null;
  }>({ progress: 0, loading: false, error: null });

  const handleProgressChange = (progress: number) => {
    setUploadState((prev) => ({ ...prev, progress }));
  };

  const handleUploadComplete = (result: { success: boolean; message?: string }) => {
    setUploadState((prev) => ({
      ...prev,
      loading: false,
      error: result.success ? null : result.message || 'Unknown error',
    }));
  };

  return (
    <div style={{ width: '100%', minHeight: '100vh' }}>
      <YieldFlowLoader
        statusText="INTEGRATED WORKFLOW"
        uploadProgress={uploadState.progress}
        isLoading={uploadState.loading}
        animationSpeed={3}
        accentColor="#1E90FF"
        secondaryColor="#24C3A2"
        onProgressChange={handleProgressChange}
        onUploadComplete={handleUploadComplete}
        enableUpload={true}
        uploadEndpoint="/api/uploads/yield-flow"
      />
    </div>
  );
};
