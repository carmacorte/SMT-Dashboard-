// SMTinel Cinematic Demo - Button Injector
// Non-invasive navbar button injection

(function() {
  'use strict';

  // Wait for DOM to be ready
  function waitForElement(selector, maxAttempts = 50) {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      const interval = setInterval(() => {
        const element = document.querySelector(selector);
        if (element) {
          clearInterval(interval);
          resolve(element);
        } else if (++attempts >= maxAttempts) {
          clearInterval(interval);
          reject(new Error(`Element ${selector} not found after ${maxAttempts} attempts`));
        }
      }, 100);
    });
  }

  // Create demo button
  function createDemoButton() {
    const button = document.createElement('a');
    button.href = 'demo.html';
    button.target = '_blank';
    button.rel = 'noopener noreferrer';
    button.className = 'smtinel-demo-btn';
    button.innerHTML = '▶ DEMO CINEMATIC';
    button.title = 'Abrir experiencia cinematográfica de SMTinel';

    // Add inline styles
    Object.assign(button.style, {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      padding: '10px 16px',
      borderRadius: '8px',
      border: 'none',
      background: 'linear-gradient(135deg, #00D2FF, #147CFF)',
      color: '#050A0F',
      fontSize: '11px',
      fontWeight: '700',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      boxShadow: '0 0 15px rgba(0, 210, 255, 0.5)',
      textDecoration: 'none',
      whiteSpace: 'nowrap'
    });

    // Add hover effect
    button.addEventListener('mouseenter', function() {
      this.style.boxShadow = '0 0 25px rgba(0, 210, 255, 0.8)';
      this.style.transform = 'translateY(-2px)';
    });

    button.addEventListener('mouseleave', function() {
      this.style.boxShadow = '0 0 15px rgba(0, 210, 255, 0.5)';
      this.style.transform = 'translateY(0)';
    });

    return button;
  }

  // Inject button into navbar
  async function injectButton() {
    try {
      // Try to find the topbar/navbar container
      // Look for various possible selectors
      const selectors = [
        '.saas-topbar-actions',
        '.ic-nav',
        '[role="navigation"]',
        'header nav',
        '.navbar-buttons',
        '.topbar-actions'
      ];

      let container = null;
      for (const selector of selectors) {
        const el = document.querySelector(selector);
        if (el) {
          container = el;
          break;
        }
      }

      // If no container found, try waiting for it
      if (!container) {
        container = await waitForElement('.saas-topbar-actions');
      }

      const demoButton = createDemoButton();
      container.appendChild(demoButton);

      console.log('✅ SMTinel Demo button injected successfully');
    } catch (error) {
      console.warn('⚠️ Could not inject demo button:', error.message);
      // Fallback: Add button to body if navbar not found
      const demoButton = createDemoButton();
      Object.assign(demoButton.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: '9999',
        padding: '12px 20px'
      });
      document.body.appendChild(demoButton);
      console.log('✅ Demo button added as floating button');
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }

  // Also try injecting after a short delay in case of dynamic content
  setTimeout(injectButton, 2000);
})();
