// WebSocket & HUD State Controller
let ws = null;
const feedContainer = document.getElementById('terminal-feed');
const badgeIdle = document.getElementById('badge-idle');
const badgeListening = document.getElementById('badge-listening');
const badgeThinking = document.getElementById('badge-thinking');
const badgeSpeaking = document.getElementById('badge-speaking');
const waveform = document.getElementById('waveform');
const connStatus = document.getElementById('conn-status');
const ambientGlow = document.getElementById('ambient-glow');

// Shutdown Button DOM Element
const btnShutdown = document.getElementById('btn-shutdown');

// Telemetry DOM Elements
const cpuVal = document.getElementById('cpu-val');
const cpuBar = document.getElementById('cpu-bar');
const cpuTempVal = document.getElementById('cpu-temp-val');
const cpuTempBar = document.getElementById('cpu-temp-bar');
const ramVal = document.getElementById('ram-val');
const ramBar = document.getElementById('ram-bar');
const netRx = document.getElementById('net-rx');
const netTx = document.getElementById('net-tx');
const statLatency = document.getElementById('stat-latency');
const statQueries = document.getElementById('stat-queries');
const digitalClock = document.getElementById('digital-clock');

// Google Weather DOM Elements
const weatherDayHeader = document.getElementById('weather-day-header');
const weatherMainIcon = document.getElementById('weather-main-icon');
const weatherTemp = document.getElementById('weather-temp');
const weatherCond = document.getElementById('weather-cond');
const weatherDetails = document.getElementById('weather-details');
const hourlyTimeline = document.getElementById('hourly-timeline');
const btnToggleUnit = document.getElementById('btn-toggle-unit');

let currentState = 'IDLE';
let activeDevices = [];
let weatherDataCache = null;
let useFahrenheit = false;
let currentSpeakingAmplitude = 0;

// Persona cycling state
const PERSONAS = ['JARVIS', 'SCI-FI', 'FRIENDLY'];
const PERSONA_COLORS = { 'JARVIS': 'blue', 'SCI-FI': 'purple', 'FRIENDLY': 'green' };
let currentPersonaIdx = 0;

// Persona chip click handler
const personaVal = document.getElementById('persona-val');
if (personaVal) {
    personaVal.style.cursor = 'pointer';
    personaVal.title = 'Click to switch EVE personality';
    personaVal.addEventListener('click', () => {
        currentPersonaIdx = (currentPersonaIdx + 1) % PERSONAS.length;
        const newPersona = PERSONAS[currentPersonaIdx];
        personaVal.textContent = newPersona;
        personaVal.className = 'chip-val';
        const colorClass = PERSONA_COLORS[newPersona] || 'blue';
        personaVal.classList.add(colorClass);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'set_persona', persona: newPersona }));
        }
        appendFeedLine(`[SYSTEM] Persona switched to ${newPersona}.`, 'system');
    });
}

// Digital Clock Updater
function updateClock() {
    if (digitalClock) {
        const now = new Date();
        digitalClock.textContent = now.toLocaleTimeString('en-US', { hour12: true });
    }
}
setInterval(updateClock, 1000);
updateClock();

// Smooth Counter Interpolation (requestAnimationFrame)
const currentValues = { cpu: 0, ram: 0, temp: 0 };
function animateCounter(element, start, end, duration = 400, suffix = '') {
    if (!element) return;
    let startTime = null;
    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const val = (start + (end - start) * progress).toFixed(1);
        element.textContent = `${val}${suffix}`;
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}

// Web Audio SFX
let audioCtx = null;
function getAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function playWakeChime() {
    try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.06, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
    } catch (e) {}
}

function playThinkingTone() {
    try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        gain.gain.setValueAtTime(0.03, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.2);
    } catch (e) {}
}

function playToolChime() {
    try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1200, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(2400, ctx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.04, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.1);
    } catch (e) {}
}

// Typewriter Terminal Feed
function appendFeedLine(text, type = 'system') {
    if (!feedContainer) return;
    const line = document.createElement('div');
    line.className = `feed-line ${type}`;
    feedContainer.appendChild(line);

    let idx = 0;
    function typeChar() {
        if (idx < text.length) {
            line.textContent += text.charAt(idx);
            idx++;
            feedContainer.scrollTop = feedContainer.scrollHeight;
            setTimeout(typeChar, 12);
        }
    }
    typeChar();
}

// State Manager with Ambient Glow Sync
function setHUDState(state) {
    if (currentState !== state) {
        if (state === 'LISTENING') playWakeChime();
        else if (state === 'THINKING') playThinkingTone();
    }

    currentState = state;
    if (badgeIdle) badgeIdle.classList.remove('active');
    if (badgeListening) badgeListening.classList.remove('active');
    if (badgeThinking) badgeThinking.classList.remove('active');
    if (badgeSpeaking) badgeSpeaking.classList.remove('active');
    if (waveform) waveform.classList.remove('active');
    if (ambientGlow) ambientGlow.className = 'orb-ambient-glow';

    if (state === 'IDLE') {
        if (badgeIdle) badgeIdle.classList.add('active');
        if (ambientGlow) ambientGlow.classList.add('glow-idle');
    } else if (state === 'LISTENING') {
        if (badgeListening) badgeListening.classList.add('active');
        if (waveform) waveform.classList.add('active');
        if (ambientGlow) ambientGlow.classList.add('glow-listening');
    } else if (state === 'THINKING') {
        if (badgeThinking) badgeThinking.classList.add('active');
        if (ambientGlow) ambientGlow.classList.add('glow-thinking');
    } else if (state === 'SPEAKING') {
        if (badgeSpeaking) badgeSpeaking.classList.add('active');
        if (ambientGlow) ambientGlow.classList.add('glow-speaking');
    }
}

// Render 7-Column Google Weather Timeline Cards
function renderHourlyTimeline(hourly) {
    if (!hourlyTimeline) return;
    hourlyTimeline.innerHTML = '';

    if (!hourly || !hourly.length) {
        hourlyTimeline.innerHTML = '<div class="timeline-pill text-dim">Timeline unavailable</div>';
        return;
    }

    hourly.forEach((item, idx) => {
        const pill = document.createElement('div');
        pill.className = 'timeline-pill';
        pill.style.animationDelay = `${idx * 0.06}s`;

        const displayTemp = useFahrenheit ? Math.round((item.temp * 9/5) + 32) : item.temp;
        const precipStr = item.precip.toString().includes('%') ? item.precip : `${item.precip}%`;

        pill.innerHTML = `
            <span class="pill-time">${item.time}</span>
            <span class="pill-icon">${item.icon}</span>
            <span class="pill-precip">${precipStr}</span>
            <span class="pill-temp">${displayTemp}°</span>
        `;
        hourlyTimeline.appendChild(pill);
    });
}

// Weather °C / °F Unit Toggle Handler
function toggleWeatherUnit() {
    useFahrenheit = !useFahrenheit;
    if (weatherDataCache) {
        updateWeatherUI(weatherDataCache);
    }
}

if (weatherTemp) weatherTemp.addEventListener('click', toggleWeatherUnit);
if (btnToggleUnit) btnToggleUnit.addEventListener('click', toggleWeatherUnit);

function updateWeatherUI(data) {
    if (!data) return;
    weatherDataCache = data;
    if (data.day_header && weatherDayHeader) weatherDayHeader.textContent = data.day_header;
    if (data.icon && weatherMainIcon) weatherMainIcon.textContent = data.icon;

    const rawTemp = (data.temp_c !== undefined && data.temp_c !== null) ? Number(data.temp_c) : 23;
    const rawHigh = (data.today_max !== undefined && data.today_max !== null) ? Number(data.today_max) : (rawTemp + 3);
    const rawLow = (data.today_min !== undefined && data.today_min !== null) ? Number(data.today_min) : (rawTemp - 4);

    const displayTemp = useFahrenheit ? Math.round((rawTemp * 9/5) + 32) : Math.round(rawTemp);
    const displayHigh = useFahrenheit ? Math.round((rawHigh * 9/5) + 32) : Math.round(rawHigh);
    const displayLow = useFahrenheit ? Math.round((rawLow * 9/5) + 32) : Math.round(rawLow);

    if (weatherTemp) weatherTemp.textContent = `${displayTemp}`;
    if (btnToggleUnit) btnToggleUnit.textContent = useFahrenheit ? '°F | °C' : '°C | °F';
    if (weatherCond) weatherCond.textContent = data.condition || 'Partly cloudy';
    if (weatherDetails) weatherDetails.textContent = `High: ${displayHigh}°  Low: ${displayLow}°  Precip: ${data.precip_pct || '0%'}`;

    renderHourlyTimeline(data.hourly);
}

// Shutdown Button Handler
if (btnShutdown) {
    btnShutdown.addEventListener('click', () => {
        appendFeedLine('[SYSTEM] Initiating EVE Shutdown...', 'system');
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'shutdown' }));
        }
        fetch('/api/shutdown', { method: 'POST' }).catch(() => {});
        setTimeout(() => {
            window.close();
        }, 800);
    });
}

// WebSocket Connection - Connects IMMEDIATELY on load
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        if (connStatus) {
            connStatus.textContent = 'ONLINE';
            connStatus.className = 'status-online';
        }
        appendFeedLine('[SYSTEM] Connected to EVE.', 'system');
        ws.send(JSON.stringify({ action: 'get_weather' }));
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'state') {
                setHUDState(data.value);
            } else if (data.type === 'speaking_amplitude') {
                currentSpeakingAmplitude = data.value || 0;
            } else if (data.type === 'telemetry') {
                if (cpuVal) {
                    animateCounter(cpuVal, currentValues.cpu, data.cpu, 300, '%');
                    currentValues.cpu = data.cpu;
                }
                if (cpuBar) cpuBar.style.width = `${data.cpu}%`;

                if (ramVal) {
                    animateCounter(ramVal, currentValues.ram, data.ram, 300, '%');
                    currentValues.ram = data.ram;
                }
                if (ramBar) ramBar.style.width = `${data.ram}%`;

                if (netRx) netRx.textContent = `${data.rx_kb} KB/s`;
                if (netTx) netTx.textContent = `${data.tx_kb} KB/s`;

                if (data.cpu_temp !== undefined && cpuTempVal) {
                    if (typeof data.cpu_temp === 'number') {
                        animateCounter(cpuTempVal, currentValues.temp, data.cpu_temp, 300, '°C');
                        currentValues.temp = data.cpu_temp;
                        if (cpuTempBar) cpuTempBar.style.width = `${Math.min(100, (data.cpu_temp / 100) * 100)}%`;
                    } else {
                        cpuTempVal.textContent = 'N/A';
                        if (cpuTempBar) cpuTempBar.style.width = '0%';
                    }
                }
            } else if (data.type === 'weather') {
                updateWeatherUI(data);
            } else if (data.type === 'latency') {
                if (statLatency) statLatency.textContent = `${data.ms} ms`;
                if (statQueries) statQueries.textContent = `${data.queries}`;
            } else if (data.type === 'persona_changed') {
                const pName = (data.value || 'JARVIS').toUpperCase();
                if (personaVal) {
                    personaVal.textContent = pName;
                    personaVal.className = 'chip-val';
                    const colorClass = PERSONA_COLORS[pName] || 'blue';
                    personaVal.classList.add(colorClass);
                    const idx = PERSONAS.indexOf(pName);
                    if (idx >= 0) currentPersonaIdx = idx;
                }
            } else if (data.type === 'user_speech') {
                appendFeedLine(`[USER] "${data.value}"`, 'user');
            } else if (data.type === 'eve_speech') {
                appendFeedLine(`[EVE] ${data.value}`, 'eve');
            } else if (data.type === 'tool_call') {
                appendFeedLine(`[TOOL EXECUTION] ${data.value}`, 'tool');
                playToolChime();
            } else if (data.type === 'system') {
                appendFeedLine(`[SYSTEM] ${data.value}`, 'system');
            }
        } catch (err) {
            console.error('Failed to parse WebSocket payload:', err);
        }
    };

    ws.onclose = () => {
        if (connStatus) {
            connStatus.textContent = 'OFFLINE';
            connStatus.className = 'text-dim';
        }
        appendFeedLine('[SYSTEM] Connection lost. Reconnecting...', 'system');
        setTimeout(connectWebSocket, 3000);
    };
}

// Connect WebSocket IMMEDIATELY
connectWebSocket();

// ==========================================
// THREE.JS PERFECT ROUND PARTICLE SPHERICAL ORB (SAFELY ENCLOSED)
// ==========================================
function initThreeParticleOrb() {
    const container = document.getElementById('three-container');
    if (!container || typeof THREE === 'undefined') {
        console.warn('Three.js or container not available.');
        return;
    }

    const scene = new THREE.Scene();

    let containerW = (container.clientWidth > 0) ? container.clientWidth : (window.innerWidth || 500);
    let containerH = (container.clientHeight > 0) ? container.clientHeight : (window.innerHeight || 450);

    const camera = new THREE.PerspectiveCamera(60, containerW / containerH, 0.1, 1000);
    camera.position.z = 180;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(containerW, containerH);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    function onWindowResize() {
        if (!container) return;
        containerW = (container.clientWidth > 0) ? container.clientWidth : (window.innerWidth || 500);
        containerH = (container.clientHeight > 0) ? container.clientHeight : (window.innerHeight || 450);
        camera.aspect = containerW / containerH;
        camera.updateProjectionMatrix();
        renderer.setSize(containerW, containerH);
    }
    window.addEventListener('resize', onWindowResize);
    setTimeout(onWindowResize, 100);
    setTimeout(onWindowResize, 500);

    // Create Dynamic Canvas Circle Texture for Round Dots
    const circleCanvas = document.createElement('canvas');
    circleCanvas.width = 32;
    circleCanvas.height = 32;
    const circleCtx = circleCanvas.getContext('2d');
    circleCtx.beginPath();
    circleCtx.arc(16, 16, 15, 0, Math.PI * 2);
    circleCtx.fillStyle = '#ffffff';
    circleCtx.fill();
    const circleTexture = new THREE.CanvasTexture(circleCanvas);

    const particleCount = 1000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const initialPositions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const radius = 60.0;
    let i = 0;
    while (i < particleCount) {
        const x = Math.random() * 2 - 1;
        const y = Math.random() * 2 - 1;
        const z = Math.random() * 2 - 1;

        if (x * x + y * y + z * z <= 1.0) {
            const px = x * radius;
            const py = y * radius;
            const pz = z * radius;

            positions[i * 3] = px;
            positions[i * 3 + 1] = py;
            positions[i * 3 + 2] = pz;

            initialPositions[i * 3] = px;
            initialPositions[i * 3 + 1] = py;
            initialPositions[i * 3 + 2] = pz;

            colors[i * 3] = 0.23;
            colors[i * 3 + 1] = 0.51;
            colors[i * 3 + 2] = 0.96;

            i++;
        }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
        size: 8.0,
        map: circleTexture,
        vertexColors: true,
        transparent: true,
        opacity: 0.95,
        alphaTest: 0.01,
        blending: THREE.AdditiveBlending
    });

    const particleSystem = new THREE.Points(geometry, particleMaterial);
    scene.add(particleSystem);

    let shockwaveActive = false;
    let shockwaveProgress = 0;

    function triggerParticleShockwave() {
        shockwaveActive = true;
        shockwaveProgress = 0;
        playWakeChime();
        appendFeedLine('[TOUCH] Orb tapped. Triggering shockwave & LISTENING mode.', 'system');
        setHUDState('LISTENING');
    }

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    container.addEventListener('pointerdown', (e) => {
        isDragging = true;
        previousMousePosition = { x: e.clientX, y: e.clientY };

        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObject(particleSystem);
        if (intersects.length > 0 || Math.hypot(e.clientX - (rect.left + rect.width / 2), e.clientY - (rect.top + rect.height / 2)) < 100) {
            triggerParticleShockwave();
        }
    });

    window.addEventListener('pointermove', (e) => {
        if (!isDragging) return;
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;

        particleSystem.rotation.y += deltaX * 0.008;
        particleSystem.rotation.x += deltaY * 0.008;

        previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('pointerup', () => { isDragging = false; });

    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        camera.position.z += e.deltaY * 0.12;
        camera.position.z = Math.max(40, Math.min(600, camera.position.z));
    }, { passive: false });

    const clock = new THREE.Clock();
    let timeVal = 0;

    function animateThree() {
        requestAnimationFrame(animateThree);
        timeVal += 0.015;

        let targetSpeed = 0.004;
        let targetScale = 1.0;
        let targetColor = new THREE.Color(0x3b82f6);

        if (currentState === 'LISTENING') {
            targetSpeed = 0.008;
            targetScale = 1.0 + Math.sin(timeVal * 4) * 0.08;
            targetColor = new THREE.Color(0x00ffcc);
        } else if (currentState === 'THINKING') {
            targetSpeed = 0.035;
            targetScale = 1.15;
            targetColor = new THREE.Color(0xb026ff);
        } else if (currentState === 'SPEAKING') {
            targetSpeed = 0.012 + (currentSpeakingAmplitude * 0.025);
            targetScale = 1.05 + (currentSpeakingAmplitude * 0.55);
            targetColor = new THREE.Color(0x10b981);
        }

        const time = clock.getElapsedTime();
        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;
            let scale = 1.0 + Math.sin(time * 2.0 + i) * 0.05;

            if (shockwaveActive) {
                scale += Math.sin(shockwaveProgress * Math.PI) * 0.5;
            }

            positions[i3] = initialPositions[i3] * scale;
            positions[i3 + 1] = initialPositions[i3 + 1] * scale;
            positions[i3 + 2] = initialPositions[i3 + 2] * scale;
        }
        geometry.attributes.position.needsUpdate = true;

        if (shockwaveActive) {
            shockwaveProgress += 0.05;
            if (shockwaveProgress >= 1.0) {
                shockwaveActive = false;
            }
        }

        if (!isDragging) {
            particleSystem.rotation.y += targetSpeed;
            particleSystem.rotation.x += targetSpeed * 0.5;
        }

        particleSystem.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.05);
        particleMaterial.color.lerp(targetColor, 0.06);

        renderer.render(scene, camera);
    }
    animateThree();
}

// Safely initialize 3D particle orb
try {
    initThreeParticleOrb();
} catch (orbErr) {
    console.warn("WebGL / Three.js orb initialization error:", orbErr);
}
