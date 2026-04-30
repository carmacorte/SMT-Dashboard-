# YieldFlowLoader Integration Guide

This guide explains how to integrate the new YieldFlowLoader component into the existing SMT Dashboard and TraceOps systems.

## Overview

The YieldFlowLoader is a reusable React component designed to handle file uploads with beautiful animations. It can be integrated into:

1. **Dashboard Applications** - File import/upload flows
2. **Configuration Workflows** - Settings and setup flows
3. **Batch Processing** - Large file processing with progress tracking
4. **Data Migration** - Transferring data between systems

## Project Structure

```
SMT-Dashboard-/
├── components/
│   ├── YieldFlowLoader.tsx          # Main component
│   ├── YieldFlowLoader.module.css   # Styles
│   ├── YieldFlowLoader.test.tsx     # Tests
│   ├── index.ts                     # Exports
│   └── README.md                    # Component docs
├── examples/
│   └── YieldFlowLoaderExample.tsx   # Usage examples
├── INTEGRATION_GUIDE.md             # This file
├── index.html                       # Existing dashboard
└── SMTWADASH.html                   # Existing SMT dashboard
```

## Installation Steps

### 1. React Setup (If Not Already Present)

The component requires React 18+ and TypeScript. If your project doesn't have these:

```bash
npm install react react-dom react-dom/client
npm install --save-dev typescript @types/react @types/react-dom
```

### 2. CSS Modules Support

Ensure your build tool supports CSS modules:

```bash
# For Create React App
npm install

# For Vite
npm install

# For Next.js
# CSS modules are built-in
```

### 3. Copy Component Files

```bash
# Copy the component directory
cp -r components/ your-project/src/components/

# Copy examples for reference
cp -r examples/ your-project/docs/examples/
```

## Integration Patterns

### Pattern 1: Simple Upload Dialog

```typescript
import { YieldFlowLoader } from './components';
import { useState } from 'react';

export function FileUploadDialog() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Upload File</button>
      {isOpen && (
        <div className="modal">
          <YieldFlowLoader
            statusText="IMPORT DATA"
            uploadEndpoint="/api/import"
            onUploadComplete={(result) => {
              if (result.success) {
                setIsOpen(false);
                // Refresh data
              }
            }}
          />
        </div>
      )}
    </>
  );
}
```

### Pattern 2: Multi-Step Workflow

```typescript
import { YieldFlowLoader } from './components';
import { useState } from 'react';

export function DataMigration() {
  const [step, setStep] = useState<'upload' | 'validate' | 'complete'>('upload');

  return (
    <div>
      {step === 'upload' && (
        <YieldFlowLoader
          statusText="STEP 1: UPLOAD"
          uploadEndpoint="/api/validate"
          onUploadComplete={(result) => {
            if (result.success) setStep('validate');
          }}
        />
      )}
      {step === 'validate' && (
        <YieldFlowLoader
          statusText="STEP 2: VALIDATE"
          isLoading={true}
          enableUpload={false}
          onUploadComplete={() => setStep('complete')}
        />
      )}
    </div>
  );
}
```

### Pattern 3: With Progress Tracking

```typescript
import { YieldFlowLoader } from './components';
import { useState } from 'react';

export function TrackingUpload() {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready');

  return (
    <YieldFlowLoader
      statusText={status}
      uploadProgress={progress}
      isLoading={progress > 0 && progress < 100}
      onProgressChange={(p) => {
        setProgress(p);
        if (p < 33) setStatus('Reading...');
        else if (p < 66) setStatus('Processing...');
        else setStatus('Finalizing...');
      }}
      onUploadComplete={(result) => {
        setStatus(result.success ? 'Complete!' : 'Failed');
      }}
    />
  );
}
```

### Pattern 4: Integration with Existing SMTWADASH

To integrate into the existing SMTWADASH.html:

```typescript
// In your React component
import { YieldFlowLoader } from './components';

function SMTDashboardWithLoader() {
  return (
    <>
      <div className="hdr">
        {/* Existing header */}
      </div>

      {/* Add YieldFlowLoader as upload option */}
      <div className="upload-section">
        <YieldFlowLoader
          statusText="MANUFACTURING DATA"
          uploadEndpoint="/api/smt/upload"
          accentColor="#E8621A"  // Match SMT colors
          secondaryColor="#2563EB"
          onUploadComplete={async (result) => {
            if (result.success) {
              // Trigger data refresh
              location.reload();
            }
          }}
        />
      </div>

      {/* Rest of dashboard */}
    </>
  );
}
```

## Backend Integration

### Express.js Example

```typescript
import express from 'express';
import multer from 'multer';
import { processYieldFlowFile } from './processors';

const router = express.Router();
const upload = multer({ dest: 'uploads/' });

// Upload endpoint for YieldFlowLoader
router.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Process the file
    const result = await processYieldFlowFile(req.file.path);

    // Success response (any 2xx status)
    res.status(200).json({
      success: true,
      message: 'File processed successfully',
      data: result,
    });
  } catch (error) {
    // Error response (any non-2xx status)
    res.status(500).json({
      error: 'Processing failed',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
```

### Fastify Example

```typescript
import fastify from 'fastify';
import fastifyMultipart from '@fastify/multipart';
import { processYieldFlowFile } from './processors';

const app = fastify();
app.register(fastifyMultipart);

app.post('/api/upload', async (request, reply) => {
  try {
    const data = await request.file();
    const buffer = await data.toBuffer();

    // Process the file
    const result = await processYieldFlowFile(buffer);

    // Success response
    return { success: true, data: result };
  } catch (error) {
    // Error response - automatic 500 status
    throw new Error('Processing failed');
  }
});
```

### Django/Flask Example

```python
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400

        file = request.files['file']
        filename = secure_filename(file.filename)

        # Process the file
        result = process_yield_flow_file(file.stream)

        # Success response
        return {'success': True, 'data': result}, 200

    except Exception as e:
        # Error response
        return {'error': str(e)}, 500
```

## Styling Integration

### Customize Colors for Your Brand

```typescript
<YieldFlowLoader
  accentColor="#FF6B35"      // Orange
  secondaryColor="#F7931E"   // Gold
  statusText="CUSTOM BRAND"
/>
```

### Match Existing Dashboard Palette

```typescript
// For SMTWADASH (Orange theme)
<YieldFlowLoader
  accentColor="#E8621A"      // SMT orange
  secondaryColor="#2563EB"   // SMT blue
/>

// For TraceOps (Blue/Green theme)
<YieldFlowLoader
  accentColor="#1E90FF"      // TraceOps blue
  secondaryColor="#15966B"   // TraceOps green
/>
```

### CSS Customization

Override component styles using CSS modules:

```css
/* YieldFlowLoaderCustom.module.css */
.container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px;
}

.statusText {
  font-family: 'Segoe UI', sans-serif;
  letter-spacing: 0.12em;
}
```

## Data Flow Integration

### Upload → Processing → Display

```
┌─────────────────────────────────────────────┐
│  YieldFlowLoader (Upload Component)         │
│  - File selection                           │
│  - Progress tracking                        │
└─────────────────┬───────────────────────────┘
                  │ POST /api/upload
                  ▼
┌─────────────────────────────────────────────┐
│  Backend API                                │
│  - File validation                          │
│  - Data processing                          │
│  - Database storage                         │
└─────────────────┬───────────────────────────┘
                  │ Response
                  ▼
┌─────────────────────────────────────────────┐
│  Application State                          │
│  - Update results                           │
│  - Refresh dashboard                        │
│  - Show completion                          │
└─────────────────────────────────────────────┘
```

## Error Handling

### Common Error Scenarios

```typescript
<YieldFlowLoader
  onUploadComplete={(result) => {
    if (!result.success) {
      switch (result.message) {
        case 'Network error':
          console.error('Check your connection');
          break;
        case 'Invalid file format':
          console.error('Only CSV and Excel supported');
          break;
        case 'File too large':
          console.error('Maximum 50MB');
          break;
        default:
          console.error('Unknown error:', result.message);
      }
    }
  }}
/>
```

### Error Recovery

```typescript
const [error, setError] = useState<string | null>(null);
const [retryCount, setRetryCount] = useState(0);

const handleUploadComplete = (result) => {
  if (!result.success) {
    setError(result.message);
    if (retryCount < 3) {
      setTimeout(() => {
        setRetryCount(retryCount + 1);
        // Retry logic here
      }, 2000 * (retryCount + 1));
    }
  }
};
```

## Performance Optimization

### Code Splitting

```typescript
import { lazy, Suspense } from 'react';

const YieldFlowLoader = lazy(() =>
  import('./components').then(m => ({ default: m.YieldFlowLoader }))
);

export function LazyUpload() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <YieldFlowLoader />
    </Suspense>
  );
}
```

### Memoization

```typescript
import { memo } from 'react';
import { YieldFlowLoader } from './components';

export const MemoizedLoader = memo(YieldFlowLoader);
```

## Testing Integration

### Unit Tests

```typescript
import { render, screen } from '@testing-library/react';
import { YieldFlowLoader } from './components';

test('renders with custom props', () => {
  render(
    <YieldFlowLoader
      statusText="TEST"
      uploadEndpoint="/test"
    />
  );
  expect(screen.getByText('TEST')).toBeInTheDocument();
});
```

### Integration Tests

```typescript
test('completes upload workflow', async () => {
  const mockUpload = jest.fn().mockResolvedValue({ success: true });

  const { getByText } = render(
    <YieldFlowLoader
      onUploadComplete={mockUpload}
      uploadEndpoint="/api/test"
    />
  );

  // Simulate upload
  await userEvent.upload(document.querySelector('input[type="file"]'), new File(['test'], 'test.txt'));

  // Wait for completion
  await waitFor(() => {
    expect(mockUpload).toHaveBeenCalledWith({ success: true });
  });
});
```

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 90+ | ✅ Full support |
| Firefox | 88+ | ✅ Full support |
| Safari | 14+ | ✅ Full support |
| Edge | 90+ | ✅ Full support |
| IE11 | - | ❌ Not supported |

## Troubleshooting

### Animations Not Smooth

1. Check GPU acceleration in browser
2. Verify CSS module compilation
3. Clear browser cache
4. Check for CSS conflicts

### Upload Not Working

1. Verify endpoint path: `/api/upload`
2. Check CORS headers on backend
3. Verify FormData handling
4. Check browser console for errors

### Colors Not Applying

1. Verify hex format: `#RRGGBB`
2. Check CSS variable scoping
3. Ensure CSS module imports
4. Clear browser cache

## Support & Contributing

For issues, feature requests, or contributions:

1. Check existing documentation
2. Review component examples
3. Check test cases
4. Create issue with reproduction case

## Version History

- **v1.0.0** (Initial Release)
  - Core loader component
  - Upload integration
  - Customizable props
  - TypeScript support
  - CSS module styling
  - Responsive design
  - Error handling
  - Progress tracking

## Future Enhancements

- [ ] Drag-and-drop zones
- [ ] Multiple file uploads
- [ ] Pause/resume functionality
- [ ] Network retry strategies
- [ ] File validation
- [ ] Custom animations
- [ ] Analytics integration
- [ ] Accessibility improvements
