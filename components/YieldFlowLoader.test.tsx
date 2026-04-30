import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { YieldFlowLoader, YieldFlowLoaderProps } from './YieldFlowLoader';

/**
 * Test suite for YieldFlowLoader component
 */

describe('YieldFlowLoader', () => {
  const defaultProps: YieldFlowLoaderProps = {
    statusText: 'TEST LOADER',
    animationSpeed: 3,
    accentColor: '#1E90FF',
    secondaryColor: '#24C3A2',
    enableUpload: true,
  };

  describe('Rendering', () => {
    it('should render the component', () => {
      render(<YieldFlowLoader {...defaultProps} />);
      expect(screen.getByText('TEST LOADER')).toBeInTheDocument();
    });

    it('should render status text', () => {
      render(<YieldFlowLoader {...defaultProps} statusText="CUSTOM STATUS" />);
      expect(screen.getByText('CUSTOM STATUS')).toBeInTheDocument();
    });

    it('should render processing subtext when loading', () => {
      render(<YieldFlowLoader {...defaultProps} isLoading={true} />);
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should render upload zone when enabled', () => {
      const { container } = render(<YieldFlowLoader {...defaultProps} enableUpload={true} />);
      const uploadZone = container.querySelector('[class*="uploadZone"]');
      expect(uploadZone).toBeInTheDocument();
    });

    it('should not render upload zone when disabled', () => {
      const { container } = render(<YieldFlowLoader {...defaultProps} enableUpload={false} />);
      const uploadZone = container.querySelector('[class*="uploadZone"]');
      expect(uploadZone).not.toBeInTheDocument();
    });

    it('should render SVG animation canvas', () => {
      const { container } = render(<YieldFlowLoader {...defaultProps} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Props', () => {
    it('should accept custom animation speed', () => {
      const { container } = render(
        <YieldFlowLoader {...defaultProps} animationSpeed={5} />
      );
      const style = container.querySelector('[style*="--animation-speed"]')?.getAttribute('style');
      expect(style).toContain('--animation-speed: 5s');
    });

    it('should accept custom colors', () => {
      const customAccent = '#FF0000';
      const customSecondary = '#00FF00';
      const { container } = render(
        <YieldFlowLoader
          {...defaultProps}
          accentColor={customAccent}
          secondaryColor={customSecondary}
        />
      );
      const style = container.querySelector('[style*="--accent-color"]')?.getAttribute('style');
      expect(style).toContain(`--accent-color: ${customAccent}`);
      expect(style).toContain(`--secondary-color: ${customSecondary}`);
    });

    it('should update progress when uploadProgress prop changes', () => {
      const { rerender } = render(<YieldFlowLoader {...defaultProps} uploadProgress={0} />);
      let progressText = screen.getByText('0%');
      expect(progressText).toBeInTheDocument();

      rerender(<YieldFlowLoader {...defaultProps} uploadProgress={50} />);
      progressText = screen.getByText('50%');
      expect(progressText).toBeInTheDocument();

      rerender(<YieldFlowLoader {...defaultProps} uploadProgress={100} />);
      progressText = screen.getByText('100%');
      expect(progressText).toBeInTheDocument();
    });
  });

  describe('File Upload', () => {
    it('should handle file selection', async () => {
      const onProgressChange = jest.fn();
      const onUploadComplete = jest.fn();

      render(
        <YieldFlowLoader
          {...defaultProps}
          onProgressChange={onProgressChange}
          onUploadComplete={onUploadComplete}
          uploadEndpoint="/api/test"
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(onProgressChange).toHaveBeenCalled();
      });
    });

    it('should handle drag and drop', async () => {
      const { container } = render(
        <YieldFlowLoader {...defaultProps} enableUpload={true} />
      );

      const uploadZone = container.querySelector('[class*="uploadZone"]') as HTMLElement;
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });

      const dragEvent = new DragEvent('dragover', {
        dataTransfer: new DataTransfer(),
      });

      fireEvent.dragOver(uploadZone, dragEvent);
      expect(uploadZone.className).toContain('dragActive');

      fireEvent.dragLeave(uploadZone);
      expect(uploadZone.className).not.toContain('dragActive');
    });

    it('should call onUploadComplete callback', async () => {
      const onUploadComplete = jest.fn();
      const mockFetch = jest.fn().mockResolvedValue({ ok: true });
      global.fetch = mockFetch;

      render(
        <YieldFlowLoader
          {...defaultProps}
          onUploadComplete={onUploadComplete}
          uploadEndpoint="/api/test"
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(onUploadComplete).toHaveBeenCalled();
      });
    });

    it('should handle upload errors gracefully', async () => {
      const onUploadComplete = jest.fn();

      render(
        <YieldFlowLoader
          {...defaultProps}
          onUploadComplete={onUploadComplete}
          uploadEndpoint="/api/test"
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });

      // Simulate error by setting invalid endpoint
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(onUploadComplete).toHaveBeenCalledWith({
          success: false,
          message: expect.any(String),
        });
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state', () => {
      render(<YieldFlowLoader {...defaultProps} isLoading={true} />);
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should hide loading state', () => {
      render(<YieldFlowLoader {...defaultProps} isLoading={false} />);
      expect(screen.queryByText('Processing...')).not.toBeInTheDocument();
    });

    it('should disable upload zone during loading', () => {
      const { container } = render(
        <YieldFlowLoader
          {...defaultProps}
          isLoading={true}
          uploadProgress={50}
          enableUpload={true}
        />
      );
      const uploadZone = container.querySelector('[class*="uploadZone"]');
      expect(uploadZone).toHaveClass('uploadDisabled');
    });
  });

  describe('Callbacks', () => {
    it('should call onProgressChange on progress update', async () => {
      const onProgressChange = jest.fn();

      const { rerender } = render(
        <YieldFlowLoader {...defaultProps} uploadProgress={0} onProgressChange={onProgressChange} />
      );

      rerender(
        <YieldFlowLoader {...defaultProps} uploadProgress={50} onProgressChange={onProgressChange} />
      );

      expect(onProgressChange).toHaveBeenCalledWith(50);
    });

    it('should call onUploadComplete with success', async () => {
      const onUploadComplete = jest.fn();

      const { rerender } = render(
        <YieldFlowLoader
          {...defaultProps}
          uploadProgress={0}
          onUploadComplete={onUploadComplete}
        />
      );

      rerender(
        <YieldFlowLoader
          {...defaultProps}
          uploadProgress={100}
          onUploadComplete={onUploadComplete}
        />
      );

      // Completion happens after 3s delay
      await waitFor(
        () => {
          expect(onUploadComplete).toHaveBeenCalled();
        },
        { timeout: 4000 }
      );
    });
  });

  describe('CSS Animations', () => {
    it('should apply correct animation speed to canvas', () => {
      const { container } = render(
        <YieldFlowLoader {...defaultProps} animationSpeed={2.5} />
      );
      const canvas = container.querySelector('svg');
      const style = canvas?.parentElement?.getAttribute('style');
      expect(style).toContain('--animation-speed: 2.5s');
    });

    it('should apply color variables to SVG', () => {
      const { container } = render(
        <YieldFlowLoader
          {...defaultProps}
          accentColor="#FF0000"
          secondaryColor="#00FF00"
        />
      );
      const style = container.querySelector('[style*="--accent-color"]')?.getAttribute('style');
      expect(style).toContain('--accent-color: #FF0000');
      expect(style).toContain('--secondary-color: #00FF00');
    });
  });

  describe('Responsive Design', () => {
    it('should render with responsive classes', () => {
      const { container } = render(<YieldFlowLoader {...defaultProps} />);
      const wrapper = container.querySelector('[class*="loaderWrapper"]');
      expect(wrapper).toBeInTheDocument();
    });

    it('should handle small screens', () => {
      global.innerWidth = 320;
      const { container } = render(<YieldFlowLoader {...defaultProps} />);
      expect(container.querySelector('[class*="container"]')).toBeInTheDocument();
    });
  });
});
