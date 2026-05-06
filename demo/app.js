/* SMTinel IO - Interactive Cinematic Demo */

// Canvas setup for binary rain
const canvas = document.getElementById('binaryCanvas');
const ctx = canvas.getContext('2d');

// Set canvas size
function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Binary characters
const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
const charArray = chars.split('');
const fontSize = 14;
const columns = canvas.width / fontSize;
const drops = [];

// Initialize drops
for (let i = 0; i < columns; i++) {
    drops[i] = Math.random() * canvas.height;
}

// Draw binary rain
function drawBinaryRain() {
    ctx.fillStyle = 'rgba(5, 10, 15, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'rgba(0, 210, 255, 0.8)';
    ctx.font = `${fontSize}px 'Courier New'`;

    for (let i = 0; i < drops.length; i++) {
        const text = charArray[Math.floor(Math.random() * charArray.length)];
        ctx.fillText(text, i * fontSize, drops[i]);

        if (drops[i] > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }
        drops[i] += fontSize * 0.7;
    }
}

// Animation loop for binary rain
function animateBinaryRain() {
    drawBinaryRain();
    requestAnimationFrame(animateBinaryRain);
}
animateBinaryRain();

// Boot Sequence Controller
class BootSequence {
    constructor() {
        this.bootOverlay = document.getElementById('bootSequence');
        this.bootPercent = document.getElementById('bootPercent');
        this.bootStatus = document.getElementById('bootStatus');
        this.progressFill = document.querySelector('.progress-fill');
        this.mainDashboard = document.getElementById('mainDashboard');
        this.currentPercent = 0;
        this.bootMessages = [
            'SYSTEM BOOT...',
            'LOADING INTELLIGENCE PROTOCOLS...',
            'INITIALIZING TRACE ENGINES...',
            'SYNCHRONIZING DATA STREAMS...',
            'ESTABLISHING CONNECTIONS...',
            'BOOTING SMTinelito GUARDIAN...',
            'ACTIVATING YIELD PREDICTION CORE...',
            'SYSTEM READY...',
            'ENGAGING CINEMATIC MODE...'
        ];
        this.currentMessageIndex = 0;
    }

    async start() {
        this.animateProgress();
        await this.runBootSequence();
        this.transitionToDashboard();
    }

    animateProgress() {
        const interval = setInterval(() => {
            if (this.currentPercent < 100) {
                const increment = Math.random() * (15 - 3) + 3;
                this.currentPercent = Math.min(this.currentPercent + increment, 99);
                this.updateProgress();
            } else {
                clearInterval(interval);
            }
        }, 300);
    }

    updateProgress() {
        this.bootPercent.textContent = Math.floor(this.currentPercent);
        this.progressFill.style.width = this.currentPercent + '%';
    }

    async runBootSequence() {
        for (let i = 0; i < this.bootMessages.length; i++) {
            this.bootStatus.textContent = this.bootMessages[i];
            await this.sleep(600);
        }
        this.currentPercent = 100;
        this.updateProgress();
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    transitionToDashboard() {
        gsap.to(this.bootOverlay, {
            opacity: 0,
            duration: 1,
            ease: 'power2.inOut',
            onComplete: () => {
                this.bootOverlay.classList.add('hidden');
                this.mainDashboard.classList.remove('hidden');
                this.initializeDashboard();
            }
        });
    }

    initializeDashboard() {
        // Trigger staggered animations for dashboard elements
        const sections = document.querySelectorAll('.panel-section, .avatar-section, .puzzle-section');
        sections.forEach((section, index) => {
            gsap.from(section, {
                opacity: 0,
                y: 20,
                duration: 0.6,
                delay: index * 0.1,
                ease: 'power2.out'
            });
        });

        // Initialize puzzle interactions
        initializePuzzle();
    }
}

// Puzzle System
function initializePuzzle() {
    const nodes = document.querySelectorAll('.puzzle-node:not(.locked)');
    const resolveBtn = document.getElementById('resolveBtn');
    const selectedNodes = new Set();

    nodes.forEach(node => {
        node.addEventListener('click', function() {
            if (!this.classList.contains('locked')) {
                this.classList.toggle('active');

                if (this.classList.contains('active')) {
                    selectedNodes.add(this.dataset.node);
                } else {
                    selectedNodes.delete(this.dataset.node);
                }

                // Visual feedback
                gsap.to(this, {
                    scale: this.classList.contains('active') ? 1.05 : 1,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            }
        });
    });

    resolveBtn.addEventListener('click', function() {
        // Check if correct combination is selected
        const correctNodes = ['ICT', 'AOI', 'REFLOW'];
        const selectedArray = Array.from(selectedNodes);

        const isCorrect = correctNodes.every(node => selectedNodes.has(node));

        if (isCorrect && selectedArray.length <= correctNodes.length) {
            triggerPuzzleSolution();
        } else {
            showPuzzleError();
        }
    });
}

function triggerPuzzleSolution() {
    // Animate button click
    const resolveBtn = document.getElementById('resolveBtn');

    gsap.to(resolveBtn, {
        scale: 0.95,
        duration: 0.1,
        ease: 'power2.out'
    });

    gsap.to(resolveBtn, {
        scale: 1,
        duration: 0.2,
        delay: 0.1,
        ease: 'back.out'
    });

    // Puzzle success animation
    const nodes = document.querySelectorAll('.puzzle-node.active');
    nodes.forEach((node, index) => {
        gsap.to(node, {
            background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.3), rgba(0, 210, 255, 0.2))',
            borderColor: '#00FF88',
            duration: 0.5,
            delay: index * 0.1,
            ease: 'power2.out'
        });
    });

    // Recover plant health
    setTimeout(() => {
        recoverPlantHealth();
    }, 800);
}

function showPuzzleError() {
    const resolveBtn = document.getElementById('resolveBtn');

    gsap.to(resolveBtn, {
        x: -5,
        duration: 0.1,
        repeat: 3,
        yoyo: true,
        ease: 'power2.out'
    });
}

function recoverPlantHealth() {
    const healthNumber = document.querySelector('.health-number');
    const healthFill = document.querySelector('.xp-fill');
    let currentHealth = 68;
    const targetHealth = 100;

    // Animate health number
    const healthInterval = setInterval(() => {
        currentHealth += 4;
        if (currentHealth >= targetHealth) {
            currentHealth = targetHealth;
            clearInterval(healthInterval);
            healthNumber.style.color = '#00FF88';
            gsap.to(healthNumber, {
                textShadow: '0 0 20px #00FF88',
                duration: 0.3
            });
        }

        healthNumber.textContent = currentHealth + '%';
    }, 30);

    // Animate health bar
    gsap.to(healthFill, {
        width: '100%',
        duration: 2,
        ease: 'power2.out'
    });

    // Celebrate with particles
    createSuccessParticles();

    // Update mission status
    setTimeout(() => {
        const missionItems = document.querySelectorAll('.mission-item');
        if (missionItems.length > 0) {
            const lastMission = missionItems[missionItems.length - 1];
            lastMission.classList.add('completed');
            lastMission.querySelector('.mission-check').textContent = '✓';
        }
    }, 1000);
}

function createSuccessParticles() {
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    const particleCount = 30;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'fixed';
        particle.style.left = centerX + 'px';
        particle.style.top = centerY + 'px';
        particle.style.width = '4px';
        particle.style.height = '4px';
        particle.style.background = '#00FF88';
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        particle.style.zIndex = '99';
        particle.style.boxShadow = '0 0 8px #00FF88';
        document.body.appendChild(particle);

        const angle = (Math.PI * 2 * i) / particleCount;
        const velocity = 3 + Math.random() * 5;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        let x = centerX;
        let y = centerY;

        function animateParticle() {
            x += vx;
            y += vy;
            particle.style.left = x + 'px';
            particle.style.top = y + 'px';
            particle.style.opacity = 1 - (Math.abs(x - centerX) / 500);

            if (Math.abs(x - centerX) < 500 && Math.abs(y - centerY) < 500) {
                requestAnimationFrame(animateParticle);
            } else {
                particle.remove();
            }
        }
        animateParticle();
    }
}

// SMTinelito Interactive Hover Effects
function initializeSMTinelito() {
    const smtinelito = document.getElementById('smtinelito');
    const svg = smtinelito.querySelector('svg');

    smtinelito.addEventListener('mouseenter', function() {
        gsap.to(svg, {
            filter: 'drop-shadow(0 0 30px #00D2FF)',
            duration: 0.3,
            ease: 'power2.out'
        });
    });

    smtinelito.addEventListener('mouseleave', function() {
        gsap.to(svg, {
            filter: 'drop-shadow(0 0 20px #00D2FF)',
            duration: 0.3,
            ease: 'power2.out'
        });
    });

    // Add eye tracking
    document.addEventListener('mousemove', function(e) {
        const rect = smtinelito.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
        const eyeGlow = svg.querySelector('.eye-glow');

        if (eyeGlow) {
            gsap.to(eyeGlow, {
                opacity: 0.3 + Math.sin(angle) * 0.3,
                duration: 0.1
            });
        }
    });
}

// Sidebar Navigation
function initializeSidebarNavigation() {
    const sidebarItems = document.querySelectorAll('.sidebar-item');

    sidebarItems.forEach(item => {
        item.addEventListener('click', function() {
            sidebarItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            gsap.to(this, {
                scale: 1.02,
                duration: 0.2,
                ease: 'power2.out'
            });

            setTimeout(() => {
                gsap.to(this, {
                    scale: 1,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }, 200);
        });
    });
}

// Initialize everything
function initialize() {
    const boot = new BootSequence();
    boot.start();
}

// Add event listener for when boot completes
window.addEventListener('load', () => {
    setTimeout(() => {
        initialize();
    }, 100);
});

// Export functions for console debugging
window.debugAPI = {
    skipBoot: () => {
        document.getElementById('bootSequence').classList.add('hidden');
        document.getElementById('mainDashboard').classList.remove('hidden');
        initializeDashboard();
    },
    completeHealthBar: () => {
        recoverPlantHealth();
    },
    triggerParticles: () => {
        createSuccessParticles();
    }
};

console.log('%cSMTinel IO - Demo Ready', 'color: #00D2FF; font-size: 16px; font-weight: bold;');
console.log('%cDebug API available: window.debugAPI', 'color: #FFB800; font-size: 12px;');
