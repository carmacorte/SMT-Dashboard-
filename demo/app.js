/* ═══════════════════════════════════════════════════════════════ */
/* SMTINEL IO - PREMIUM CINEMATIC DASHBOARD - JAVASCRIPT ENGINE    */
/* ═══════════════════════════════════════════════════════════════ */

// ─────────────────────────────────────────────────────────────────
// BINARY RAIN EFFECT
// ─────────────────────────────────────────────────────────────────

const canvas = document.getElementById('binaryCanvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

const chars = '01アイウエオカキク';
const charArray = chars.split('');
const fontSize = 14;
const columns = Math.ceil(canvas.width / fontSize);
const drops = Array.from({ length: columns }, () => Math.random() * canvas.height);

function drawBinaryRain() {
    ctx.fillStyle = 'rgba(5, 10, 15, 0.02)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'rgba(0, 210, 255, 0.6)';
    ctx.font = `${fontSize}px 'JetBrains Mono', monospace`;
    ctx.textAlign = 'center';

    for (let i = 0; i < drops.length; i++) {
        const text = charArray[Math.floor(Math.random() * charArray.length)];
        ctx.fillText(text, i * fontSize + fontSize / 2, drops[i]);

        if (drops[i] > canvas.height && Math.random() > 0.98) {
            drops[i] = 0;
        }
        drops[i] += fontSize * 0.8;
    }
}

function animateBinaryRain() {
    drawBinaryRain();
    requestAnimationFrame(animateBinaryRain);
}
animateBinaryRain();

// ─────────────────────────────────────────────────────────────────
// BOOT SEQUENCE CONTROLLER
// ─────────────────────────────────────────────────────────────────

class BootController {
    constructor() {
        this.bootSequence = document.getElementById('bootSequence');
        this.mainDashboard = document.getElementById('mainDashboard');
        this.bootPercent = document.getElementById('bootPercent');
        this.bootStatus = document.getElementById('bootStatus');
        this.progressFill = document.querySelector('.progress-fill');
        this.subsystems = document.querySelectorAll('.subsystem');

        this.currentPercent = 0;
        this.bootMessages = [
            'CORE INITIALIZATION',
            'LOADING INTELLIGENCE CORE',
            'SYNCHRONIZING DATA LAYERS',
            'ESTABLISHING CONNECTIONS',
            'BOOTING GUARDIAN AI',
            'ACTIVATING TRACE ENGINES',
            'INITIALIZING YIELD PREDICTION',
            'SYSTEM STABILIZATION',
            'ENTERING CINEMATIC MODE'
        ];
        this.currentMessageIndex = 0;
    }

    async start() {
        this.startProgressAnimation();
        await this.runBootSequence();
        this.activateSubsystems();
        await this.sleep(1000);
        this.transitionToDashboard();
    }

    startProgressAnimation() {
        const interval = setInterval(() => {
            if (this.currentPercent < 95) {
                const increment = Math.random() * (12 - 2) + 2;
                this.currentPercent = Math.min(this.currentPercent + increment, 95);
                this.updateProgress();
            } else {
                clearInterval(interval);
            }
        }, 250);
    }

    updateProgress() {
        this.bootPercent.textContent = Math.floor(this.currentPercent);
        this.progressFill.style.width = this.currentPercent + '%';
    }

    async runBootSequence() {
        for (const message of this.bootMessages) {
            this.bootStatus.textContent = message;
            await this.sleep(500);
        }
        this.currentPercent = 100;
        this.updateProgress();
        this.bootStatus.textContent = 'SYSTEM READY';
    }

    activateSubsystems() {
        this.subsystems.forEach((subsystem, index) => {
            setTimeout(() => {
                subsystem.classList.add('active');
            }, index * 200);
        });
    }

    transitionToDashboard() {
        gsap.to(this.bootSequence, {
            opacity: 0,
            duration: 0.8,
            ease: 'power2.inOut',
            onComplete: () => {
                this.bootSequence.classList.add('hidden');
                this.mainDashboard.classList.remove('hidden');
                this.initializeDashboard();
            }
        });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    initializeDashboard() {
        // Stagger card animations
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });

        // Initialize sidebar items
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach((item, index) => {
            gsap.from(item, {
                opacity: 0,
                x: -20,
                duration: 0.5,
                delay: index * 0.05,
                ease: 'power2.out'
            });
        });

        // Initialize puzzle system
        initializePuzzle();
        initializeSidebarInteractions();
        initializeSMTineletoInteractions();
    }
}

// ─────────────────────────────────────────────────────────────────
// PUZZLE SYSTEM - HOLOGRAPHIC CORRELATION
// ─────────────────────────────────────────────────────────────────

function initializePuzzle() {
    const nodes = document.querySelectorAll('.puzzle-node:not(.locked)');
    const resolveBtn = document.getElementById('resolveBtn');
    const selectedNodes = new Set();

    nodes.forEach(node => {
        node.addEventListener('click', function() {
            if (!this.classList.contains('locked')) {
                const wasActive = this.classList.contains('active');

                this.classList.toggle('active');

                if (!wasActive) {
                    selectedNodes.add(this.dataset.node);
                    playNodeSelectSound();
                    gsap.to(this, {
                        scale: 1.05,
                        duration: 0.2,
                        ease: 'back.out'
                    });
                } else {
                    selectedNodes.delete(this.dataset.node);
                    gsap.to(this, {
                        scale: 1,
                        duration: 0.2,
                        ease: 'back.out'
                    });
                }
            }
        });

        node.addEventListener('mouseenter', function() {
            if (!this.classList.contains('locked')) {
                gsap.to(this, {
                    y: -4,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }
        });

        node.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                gsap.to(this, {
                    y: 0,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }
        });
    });

    resolveBtn.addEventListener('click', function() {
        const correctNodes = ['ICT', 'AOI', 'REFLOW'];
        const selectedArray = Array.from(selectedNodes);
        const isCorrect = correctNodes.every(node => selectedNodes.has(node));

        if (isCorrect && selectedArray.length <= correctNodes.length) {
            triggerPuzzleSolution();
        } else {
            triggerPuzzleError();
        }
    });

    resolveBtn.addEventListener('mouseenter', function() {
        gsap.to(this, {
            y: -3,
            duration: 0.2,
            ease: 'power2.out'
        });
    });

    resolveBtn.addEventListener('mouseleave', function() {
        gsap.to(this, {
            y: 0,
            duration: 0.2,
            ease: 'power2.out'
        });
    });
}

function triggerPuzzleSolution() {
    const resolveBtn = document.getElementById('resolveBtn');
    const activeNodes = document.querySelectorAll('.puzzle-node.active');

    // Button press animation
    gsap.to(resolveBtn, {
        scale: 0.95,
        duration: 0.1,
        ease: 'power2.out'
    });

    gsap.to(resolveBtn, {
        scale: 1,
        duration: 0.15,
        delay: 0.1,
        ease: 'back.out'
    });

    // Node success glow
    activeNodes.forEach((node, index) => {
        gsap.to(node.querySelector('.node-inner'), {
            boxShadow: '0 0 40px #00E5A8, inset 0 0 20px rgba(0, 229, 168, 0.2)',
            duration: 0.4,
            delay: index * 0.1
        });

        gsap.to(node.querySelector('.node-glow'), {
            background: 'radial-gradient(circle, var(--success), transparent)',
            opacity: 0.8,
            duration: 0.4,
            delay: index * 0.1
        });
    });

    setTimeout(() => {
        recoverPlantHealth();
        createSuccessParticles();
    }, 600);
}

function triggerPuzzleError() {
    const resolveBtn = document.getElementById('resolveBtn');

    gsap.to(resolveBtn, {
        x: -8,
        duration: 0.05,
        repeat: 4,
        yoyo: true,
        ease: 'power2.out'
    });
}

function recoverPlantHealth() {
    const healthValue = document.querySelector('.health-value');
    const healthChart = document.querySelector('.health-chart polyline:last-of-type');
    const healthFill = document.querySelector('.xp-fill');
    const missionItems = document.querySelectorAll('.mission-item');

    let currentHealth = 68;
    const targetHealth = 100;

    const healthInterval = setInterval(() => {
        currentHealth += 4;
        if (currentHealth >= targetHealth) {
            currentHealth = targetHealth;
            clearInterval(healthInterval);
            healthValue.textContent = '100%';
            healthValue.style.color = '#00E5A8';
            gsap.to(healthValue, {
                textShadow: '0 0 25px #00E5A8',
                duration: 0.3
            });
        } else {
            healthValue.textContent = currentHealth + '%';
        }
    }, 30);

    // Animate health bar
    if (healthFill) {
        gsap.to(healthFill, {
            width: '100%',
            duration: 2,
            ease: 'power2.out'
        });
    }

    // Update last mission
    if (missionItems.length > 0) {
        const lastMission = missionItems[missionItems.length - 1];
        setTimeout(() => {
            lastMission.classList.add('completed');
            lastMission.classList.remove('active');
            lastMission.querySelector('.mission-check').textContent = '✓';

            gsap.from(lastMission, {
                backgroundColor: 'rgba(0, 229, 168, 0.2)',
                duration: 0.5
            });
        }, 500);
    }
}

function createSuccessParticles() {
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    const particleCount = 40;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'fixed';
        particle.style.left = centerX + 'px';
        particle.style.top = centerY + 'px';
        particle.style.width = '6px';
        particle.style.height = '6px';
        particle.style.background = '#00E5A8';
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        particle.style.zIndex = '999';
        particle.style.boxShadow = '0 0 12px #00E5A8';
        document.body.appendChild(particle);

        const angle = (Math.PI * 2 * i) / particleCount;
        const velocity = 4 + Math.random() * 6;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        let x = centerX;
        let y = centerY;
        let life = 1;

        function animateParticle() {
            x += vx;
            y += vy;
            life -= 0.02;

            particle.style.left = x + 'px';
            particle.style.top = y + 'px';
            particle.style.opacity = Math.max(0, life);

            if (life > 0) {
                requestAnimationFrame(animateParticle);
            } else {
                particle.remove();
            }
        }

        animateParticle();
    }
}

// ─────────────────────────────────────────────────────────────────
// SMTINELITO INTERACTIONS
// ─────────────────────────────────────────────────────────────────

function initializeSMTineletoInteractions() {
    const smtinelito = document.querySelector('.smtinelito');
    const eyes = document.querySelectorAll('.eye');

    if (smtinelito) {
        smtinelito.addEventListener('mouseenter', function() {
            gsap.to(this, {
                filter: 'drop-shadow(0 0 40px #00D2FF)',
                duration: 0.3,
                ease: 'power2.out'
            });
        });

        smtinelito.addEventListener('mouseleave', function() {
            gsap.to(this, {
                filter: 'drop-shadow(0 0 20px #00D2FF)',
                duration: 0.3,
                ease: 'power2.out'
            });
        });

        // Eye tracking
        document.addEventListener('mousemove', function(e) {
            eyes.forEach(eye => {
                const rect = eye.getBoundingClientRect();
                const eyeX = rect.left + rect.width / 2;
                const eyeY = rect.top + rect.height / 2;

                const angle = Math.atan2(e.clientY - eyeY, e.clientX - eyeX);
                const distance = 4;

                const pupil = eye.querySelector('.pupil');
                if (pupil) {
                    gsap.to(pupil, {
                        x: Math.cos(angle) * distance,
                        y: Math.sin(angle) * distance,
                        duration: 0.1,
                        overwrite: 'auto'
                    });
                }
            });
        });
    }
}

// ─────────────────────────────────────────────────────────────────
// SIDEBAR INTERACTIONS
// ─────────────────────────────────────────────────────────────────

function initializeSidebarInteractions() {
    const menuItems = document.querySelectorAll('.menu-item');

    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            gsap.to(this, {
                scale: 1.02,
                duration: 0.15,
                ease: 'back.out'
            });

            setTimeout(() => {
                gsap.to(this, {
                    scale: 1,
                    duration: 0.15,
                    ease: 'back.out'
                });
            }, 150);
        });

        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                gsap.to(this, {
                    x: 4,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }
        });

        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                gsap.to(this, {
                    x: 0,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }
        });
    });
}

// ─────────────────────────────────────────────────────────────────
// NAVIGATION INTERACTIONS
// ─────────────────────────────────────────────────────────────────

function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// ─────────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────────

function playNodeSelectSound() {
    // Visual feedback instead of audio
    const audio = new Audio('data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA==');
    audio.volume = 0.1;
    audio.play().catch(() => {});
}

// ─────────────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────────────

window.addEventListener('load', () => {
    setTimeout(() => {
        const boot = new BootController();
        boot.start();
        initializeNavigation();
    }, 100);
});

// ─────────────────────────────────────────────────────────────────
// DEBUG API
// ─────────────────────────────────────────────────────────────────

window.debugAPI = {
    skipBoot: () => {
        document.getElementById('bootSequence').classList.add('hidden');
        document.getElementById('mainDashboard').classList.remove('hidden');
        const boot = new BootController();
        boot.initializeDashboard();
    },
    completeHealth: () => {
        recoverPlantHealth();
    },
    triggerParticles: () => {
        createSuccessParticles();
    },
    toggleBinary: () => {
        canvas.style.opacity = canvas.style.opacity === '0' ? '0.08' : '0';
    }
};

console.log('%c═══════════════════════════════════════════════════════════════', 'color: #00D2FF; font-weight: bold;');
console.log('%cSMTINEL IO - PREMIUM CINEMATIC DASHBOARD', 'color: #00D2FF; font-size: 16px; font-weight: bold;');
console.log('%cIntelligence Protocols Initialized', 'color: #FFB800; font-size: 12px;');
console.log('%cDebug API: window.debugAPI', 'color: #00E5A8; font-size: 11px;');
console.log('%c═══════════════════════════════════════════════════════════════', 'color: #00D2FF; font-weight: bold;');
