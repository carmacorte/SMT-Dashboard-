# YieldFlowLoader Component

A premium, reusable React component for file uploads with animated geometric raven silhouettes, pulsing shield, and smooth progress tracking.

## Features

✨ **Premium Design**
- Geometric raven silhouettes with orbital animations
- Pulsing shield with glow effects
- Dark theme with gradient accents
- Smooth 60fps animations

📦 **Fully Configurable**
- Custom animation speeds (default: 3s)
- Customizable accent colors (blue/green)
- Status text control
- Upload progress tracking (0-100%)
- Loading state management

🚀 **Upload Integration**
- Drag-and-drop file upload
- Click-to-upload support
- Real-time progress tracking via XMLHttpRequest
- Error handling and completion states
- Responsive design

🎯 **TypeScript Support**
- Fully typed React component
- TypeScript props interface
- CSS module typing

## Installation

```bash
# Copy the component files to your project
cp -r components/ your-project/src/
cp -r examples/ your-project/
```

## Basic Usage

```tsx
import { YieldFlowLoader } from './components';

function App() {
  return (
    <YieldFlowLoader
      statusText="YIELD FLOW"
      animationSpeed={3}
      accentColor="#1E90FF"
      secondaryColor="#24C3A2"
      enableUpload={true}
      uploadEndpoint="/api/upload"
    />
  );
}
```

## Props

### YieldFlowLoaderProps

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `animationSpeed` | number | 3 | Animation duration in seconds (range: 1-10) |
| `accentColor` | string | "#1E90FF" | Primary accent color (blue) |
| `secondaryColor` | string | "#24C3A2" | Secondary accent color (green) |
| `statusText` | string | "YIELD FLOW" | Main status text displayed |
| `uploadProgress` | number | 0 | Upload progress 0-100% |
| `isLoading` | boolean | false | Loading state flag |
| `onUploadComplete` | function | - | Callback when upload completes |
| `onProgressChange` | function | - | Callback for progress updates |
| `enableUpload` | boolean | true | Enable file upload zone |
| `uploadEndpoint` | string | "/api/upload" | Upload API endpoint |

## Usage Examples

### Basic Loader (No Upload)

```tsx
<YieldFlowLoader
  statusText="PROCESSING"
  animationSpeed={3}
  enableUpload={false}
/>
```

### With Upload Progress

```tsx
import { useState } from 'react';
import { YieldFlowLoader } from './components';

function UploadComponent() {
  const [progress, setProgress] = useState(0);

  return (
    <YieldFlowLoader
      statusText="UPLOADING"
      uploadProgress={progress}
      onProgressChange={setProgress}
      onUploadComplete={(result) => {
        if (result.success) {
          console.log('Upload successful');
        }
      }}
    />
  );
}
```

### Custom Colors & Animation Speed

```tsx
<YieldFlowLoader
  statusText="CUSTOM"
  animationSpeed={2.5}
  accentColor="#FF6B35"
  secondaryColor="#F7931E"
/>
```

### Complete Workflow

```tsx
const [phase, setPhase] = useState('idle');
const [progress, setProgress] = useState(0);

<YieldFlowLoader
  statusText={phase === 'idle' ? 'READY' : 'UPLOADING'}
  uploadProgress={progress}
  isLoading={phase !== 'idle'}
  onProgressChange={setProgress}
  onUploadComplete={() => setPhase('complete')}
/>
```

## Styling

The component uses CSS modules (`YieldFlowLoader.module.css`) for scoped styling. The following CSS custom properties can be configured:

```css
--accent-color: #1e90ff;
--secondary-color: #24c3a2;
--animation-speed: 3s;
```

### Dark Theme
The component automatically adapts to dark mode using `prefers-color-scheme: dark`.

### Responsive Design
- Mobile: 280px max-width
- Tablet: 320px max-width
- Desktop: 500px max-width

## Upload Integration

The component uses XMLHttpRequest for file uploads with progress tracking:

```typescript
// POST to uploadEndpoint with FormData
const formData = new FormData();
formData.append('file', file);

xhr.open('POST', uploadEndpoint);
xhr.send(formData);
```

### Expected Server Response

**Success (200-299):**
```javascript
// Any 2xx status code indicates success
```

**Error:**
```javascript
// Any other status code indicates failure
```

## Events & Callbacks

### onProgressChange
Fired during upload with current progress percentage:
```typescript
onProgressChange={(progress: number) => {
  console.log(`Upload ${progress}% complete`);
}}
```

### onUploadComplete
Fired when upload finishes (success or failure):
```typescript
onUploadComplete={(result: { success: boolean; message?: string }) => {
  if (result.success) {
    console.log('Upload successful');
  } else {
    console.log('Upload failed:', result.message);
  }
}}
```

## Animations

The component features multiple synchronized animations:

1. **Orbital Animations** - Ravens orbit around the shield
2. **Pulsing Shield** - Central shield pulses with glow
3. **Eye Glow** - Raven eyes pulse with intensity
4. **Beak Flutter** - Subtle beak movement
5. **Glow Rings** - Expanding rings around orbits
6. **Progress Fill** - Smooth gradient progress bar

All animations are GPU-accelerated using CSS transforms and opacity changes for smooth 60fps performance.

## Accessibility

- Semantic HTML structure
- ARIA-compliant upload zone
- High contrast colors (tested WCAG AA)
- Keyboard navigable file input
- Clear loading states and error messages

## Performance

- CSS-based animations (GPU accelerated)
- Optimized SVG rendering
- Minimal re-renders with React hooks
- CSS `will-change` and `backface-visibility` for optimization
- Responsive images with proper aspect ratios

## Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## TypeScript

Full TypeScript support with exported types:

```typescript
import { YieldFlowLoader, type YieldFlowLoaderProps } from './components';

const props: YieldFlowLoaderProps = {
  statusText: 'UPLOAD',
  animationSpeed: 3,
  accentColor: '#1E90FF',
};
```

## Error Handling

The component handles the following error cases:

- **Upload Failed** - Network errors, server errors (non-2xx status)
- **Upload Cancelled** - User aborted the upload
- **File Not Selected** - No file provided
- **Upload Error** - Generic error during processing

All errors display user-friendly messages in an error state overlay.

## Completion State

When upload completes successfully, the component shows:
- Checkmark animation
- "Upload Complete" message
- Auto-dismisses after 3 seconds
- Resets to ready state for next upload

## API Example

```typescript
// Backend Express example
app.post('/api/upload', (req, res) => {
  const file = req.files.file;
  
  // Process file...
  if (fileProcessed) {
    return res.status(200).json({ success: true });
  }
  
  return res.status(500).json({ error: 'Processing failed' });
});
```

## Troubleshooting

### Animations not smooth
- Ensure GPU acceleration is enabled
- Check browser hardware acceleration settings
- Verify CSS module import path

### Upload not working
- Verify `uploadEndpoint` is correct
- Check CORS settings on your server
- Ensure FormData is properly handled on backend

### Colors not applying
- Verify hex color format: `#RRGGBB`
- Check CSS module imports
- Clear browser cache

## License

This component is part of the TraceOps / SMT Dashboard project.
