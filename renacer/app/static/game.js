/**
 * Beatstar 120 FPS High-Performance Canvas Rhythm Engine
 * Fixed 3-Lane Rhythm Game with Direct Audio Playback & Sub-Millisecond Synchronization
 * Features: Upper-Screen Judgements & Canvas Background FX Engine (Auras, Ocean Waves, Synthwave, Aurora)
 */

const SFX_MISS_BASE64 = 'data:audio/wav;base64,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';

class HighFidelityAudioPlayer {
  constructor() {
    this.missAudio = new Audio(SFX_MISS_BASE64);
    this.missAudio.volume = 0.85;
    this.audioCtx = null;
  }

  ensureContext() {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  playPunchyArcadeMiss() {
    try {
      this.missAudio.currentTime = 0;
      this.missAudio.play().catch(() => {});
    } catch (e) {}
  }

  playAnalogTapeRewind() {
    try {
      const ctx = this.ensureContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const now = ctx.currentTime;
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.55);
      gain.gain.setValueAtTime(0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.55);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.55);
    } catch (e) {}
  }

  playPianoChime(scheduledTime = null, freq = 523.25) {
    try {
      const ctx = this.ensureContext();
      if (!ctx) return;
      const t = scheduledTime !== null ? scheduledTime : ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.4);
    } catch (e) {}
  }

  playClick(scheduledTime = null) {
    try {
      const ctx = this.ensureContext();
      if (!ctx) return;
      const t = scheduledTime !== null ? scheduledTime : ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, t);
      osc.frequency.exponentialRampToValueAtTime(300, t + 0.05);
      gain.gain.setValueAtTime(0.3, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.05);
    } catch (e) {}
  }
}

// ==========================================
// DIRECT HIGH-FIDELITY AUDIO SYNC ENGINE
// ==========================================

class DirectAudioSync {
  constructor(onReady, onEnded, onError) {
    this.audioElement = new Audio();
    this.audioElement.preload = 'auto';
    this.audioElement.volume = 1.0;
    
    this.onReady = onReady;
    this.onEnded = onEnded;
    this.onError = onError;

    this.isPlaying = false;
    this.isLoaded = false;
    this.duration = 0;
    
    // High-resolution clock anchor
    this.baseTimeMs = 0;
    this.basePerfNow = performance.now();

    this.audioElement.addEventListener('canplaythrough', () => {
      this.isLoaded = true;
      this.duration = this.audioElement.duration || 0;
      if (this.onReady) this.onReady();
    });

    this.audioElement.addEventListener('playing', () => {
      this.isPlaying = true;
      this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
      this.basePerfNow = performance.now();
    });

    this.audioElement.addEventListener('pause', () => {
      this.isPlaying = false;
      this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
      this.basePerfNow = performance.now();
    });

    this.audioElement.addEventListener('seeking', () => {
      this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
      this.basePerfNow = performance.now();
    });

    this.audioElement.addEventListener('seeked', () => {
      this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
      this.basePerfNow = performance.now();
    });

    this.audioElement.addEventListener('ended', () => {
      this.isPlaying = false;
      if (this.onEnded) this.onEnded();
    });

    this.audioElement.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      if (this.onError) this.onError('Error en la reproducción de audio.');
    });

    this.audioElement.addEventListener('timeupdate', () => {
      if (this.isPlaying) {
        const audioCurrent = this.audioElement.currentTime;
        const now = performance.now();
        const actual = audioCurrent * 1000;
        this.baseTimeMs = actual;
        this.basePerfNow = now;
      }
    });
  }

  loadAudioBlob(blob) {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    this.loadAudioUrl(url);
  }

  loadAudioUrl(url) {
    this.isLoaded = false;
    this.isPlaying = false;
    this.audioElement.src = url;
    this.audioElement.load();
    this.baseTimeMs = 0;
    this.basePerfNow = performance.now();
  }

  play() {
    if (!this.audioElement.src) return Promise.resolve();
    return this.audioElement.play().then(() => {
      this.isPlaying = true;
      this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
      this.basePerfNow = performance.now();
    }).catch(err => {
      console.warn('Audio play request interrupted:', err);
    });
  }

  pause() {
    this.isPlaying = false;
    try {
      this.audioElement.pause();
    } catch (e) {}
    this.baseTimeMs = (this.audioElement.currentTime || 0) * 1000;
    this.basePerfNow = performance.now();
  }

  seekTo(seconds) {
    const sec = Math.max(0, seconds);
    this.audioElement.currentTime = sec;
    this.baseTimeMs = sec * 1000;
    this.basePerfNow = performance.now();
  }

  getCurrentTimeMs() {
    if (!this.isPlaying) {
      return (this.audioElement.currentTime || 0) * 1000;
    }
    const elapsed = performance.now() - this.basePerfNow;
    return Math.max(0, this.baseTimeMs + elapsed);
  }
}

// ==========================================
// HIGH PERFORMANCE PARTICLE SYSTEM
// ==========================================

class ParticleSystem {
  constructor() {
    this.particles = [];
    this.shockwaves = [];
  }

  emitHit(x, y, color = '#00f2fe', count = 22) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 70 + Math.random() * 220;
      this.particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 40,
        radius: 2 + Math.random() * 3.5,
        color,
        alpha: 1.0,
        decay: 1.6 + Math.random() * 1.8
      });
    }

    this.shockwaves.push({
      x, y,
      radius: 8,
      maxRadius: 65,
      color,
      alpha: 0.9,
      decay: 3.5
    });
  }

  emitSwipeBurst(x, y, direction = 'up', color = '#ffd700', count = 30) {
    for (let i = 0; i < count; i++) {
      let baseAngle = -Math.PI / 2;
      if (direction === 'down') baseAngle = Math.PI / 2;
      else if (direction === 'left') baseAngle = Math.PI;
      else if (direction === 'right') baseAngle = 0;

      const angle = baseAngle + (Math.random() - 0.5) * 1.2;
      const speed = 120 + Math.random() * 300;

      this.particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        radius: 3 + Math.random() * 4,
        color,
        alpha: 1.0,
        decay: 1.8 + Math.random() * 2.0
      });
    }

    this.shockwaves.push({
      x, y,
      radius: 12,
      maxRadius: 85,
      color,
      alpha: 1.0,
      decay: 4.0
    });
  }

  emitHoldSpark(x, y, color = '#00ff88') {
    for (let i = 0; i < 3; i++) {
      const angle = (Math.random() - 0.5) * Math.PI - Math.PI / 2;
      const speed = 40 + Math.random() * 100;
      this.particles.push({
        x: x + (Math.random() - 0.5) * 20,
        y: y + (Math.random() - 0.5) * 8,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        radius: 1.5 + Math.random() * 2.5,
        color,
        alpha: 0.9,
        decay: 3.0
      });
    }
  }

  update(dt) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.alpha -= p.decay * dt;
      if (p.alpha <= 0) this.particles.splice(i, 1);
    }

    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const s = this.shockwaves[i];
      s.radius += (s.maxRadius - s.radius) * 12 * dt;
      s.alpha -= s.decay * dt;
      if (s.alpha <= 0) this.shockwaves.splice(i, 1);
    }
  }

  render(ctx) {
    ctx.save();
    for (const p of this.particles) {
      ctx.globalAlpha = Math.max(0, p.alpha);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();
    }

    for (const s of this.shockwaves) {
      ctx.globalAlpha = Math.max(0, s.alpha);
      ctx.strokeStyle = s.color;
      ctx.shadowColor = s.color;
      ctx.shadowBlur = 15;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }
}

// ==========================================
// 3-LANE FIXED BEATSTAR ENGINE
// ==========================================

class BeatstarEngine {
  constructor(canvas, uiCallbacks) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: true });
    this.ui = uiCallbacks;

    this.dpr = window.devicePixelRatio || 1;
    this.width = 0;
    this.height = 0;
    this.numLanes = 3; // Fixed strictly to 3 vertical lanes
    this.laneWidth = 0;
    this.hitLineY = 0;
    this.scrollDurationMs = 1000;

    this.notes = [];
    this.activeHolds = new Map();
    this.activeTouches = new Map();
    this.laneGlows = [0, 0, 0];
    this.fxRipples = [];

    // Background FX Theme
    this.activeEffect = localStorage.getItem('beatstar_active_effect') || 'neon_aura';

    // Scoring & Multiplier
    this.score = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.streakCount = 0;
    this.multiplier = 1;
    this.stars = 0;
    this.targetScore = 100000;
    this.missCount = 0;
    this.invulnerableUntil = 0;
    this.isInitialLaunch = true;
    this.isRewinding = false;
    this.judgements = [];
    this.stats = { perfectPlus: 0, perfect: 0, great: 0, miss: 0 };

    // Anti-Double-Miss Guard
    this.lastMissTimePerf = 0;
    this.isProcessingMiss = false;
    this.lastFailSongTimeSec = 0;

    this.latencyOffsetMs = parseInt(localStorage.getItem('beatstar_offset') || '0', 10);
    this.continueMode = localStorage.getItem('beatstar_continue_mode') === 'true';
    this.noteSpeedMultiplier = parseFloat(localStorage.getItem('beatstar_note_speed') || '1.0') || 1.0;
    this.isRunning = false;
    this.isPaused = false;
    this.isGameOver = false;
    this.animFrameId = null;

    // Visual Calibration
    this.isCalibrating = false;
    this.calibrationStartTime = 0;
    this.calibrationIntervalMs = 2000;
    this.nextCalibNoteTime = 0;
    this.synth = new HighFidelityAudioPlayer();

    this.particles = new ParticleSystem();
    this.sync = new DirectAudioSync(
      () => this.onAudioReady(),
      () => this.onAudioEnded(),
      (msg) => this.onAudioError(msg)
    );

    this.initCanvasSize();
    this.bindEvents();
  }

  setActiveEffect(effectId) {
    this.activeEffect = effectId || 'neon_aura';
    localStorage.setItem('beatstar_active_effect', this.activeEffect);
  }

  setLatencyOffset(offsetMs) {
    this.latencyOffsetMs = parseInt(offsetMs, 10) || 0;
    localStorage.setItem('beatstar_offset', this.latencyOffsetMs.toString());
  }

  setContinueMode(enabled) {
    this.continueMode = !!enabled;
    localStorage.setItem('beatstar_continue_mode', this.continueMode.toString());
  }

  setNoteSpeedMultiplier(multiplier) {
    this.noteSpeedMultiplier = parseFloat(multiplier) || 1.0;
    localStorage.setItem('beatstar_note_speed', this.noteSpeedMultiplier.toString());
    if (this.beatmapData) {
      this.scrollDurationMs = this.computeDynamicScrollDuration(this.beatmapData.metadata?.stars, this.notes);
    }
  }

  initCanvasSize() {
    const rect = this.canvas.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    this.numLanes = 3;
    this.laneWidth = this.width / 3;
    this.hitLineY = this.height * 0.82;

    this.canvas.width = this.width * this.dpr;
    this.canvas.height = this.height * this.dpr;
    this.ctx.scale(this.dpr, this.dpr);
  }

  bindEvents() {
    window.addEventListener('resize', () => this.initCanvasSize());

    this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
    this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
    this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
    this.canvas.addEventListener('touchcancel', (e) => this.handleTouchEnd(e), { passive: false });

    this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));

    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      if (e.key === 'Escape' || e.key === 'p' || e.key === 'P') {
        if (!this.isCalibrating && this.beatmapData) {
          if (this.isPaused) {
            if (this.ui.onResume) this.ui.onResume();
          } else {
            if (this.ui.onTogglePause) this.ui.onTogglePause();
          }
          return;
        }
      }
      if (this.isPaused || this.isRewinding) return;

      if (e.key === 'a' || e.key === 'A' || e.key === '1') this.triggerLaneInput(0, 'tap');
      if (e.key === 's' || e.key === 'S' || e.key === 'f' || e.key === 'F' || e.key === ' ' || e.key === '2') this.triggerLaneInput(1, 'tap');
      if (e.key === 'd' || e.key === 'D' || e.key === 'j' || e.key === 'J' || e.key === 'k' || e.key === 'K' || e.key === '3') this.triggerLaneInput(2, 'tap');

      if (e.key === 'ArrowLeft') this.triggerLaneInput(0, 'swipe', 'left');
      if (e.key === 'ArrowRight') this.triggerLaneInput(2, 'swipe', 'right');
      if (e.key === 'ArrowUp') this.triggerLaneInput(1, 'swipe', 'up');
      if (e.key === 'ArrowDown') this.triggerLaneInput(1, 'swipe', 'down');
    });

    window.addEventListener('keyup', (e) => {
      if (this.isPaused || this.isRewinding) return;
      if (e.key === 'a' || e.key === 'A' || e.key === '1') this.releaseLaneHold(0);
      if (e.key === 's' || e.key === 'S' || e.key === 'f' || e.key === 'F' || e.key === ' ' || e.key === '2') this.releaseLaneHold(1);
      if (e.key === 'd' || e.key === 'D' || e.key === 'j' || e.key === 'J' || e.key === 'k' || e.key === 'K' || e.key === '3') this.releaseLaneHold(2);
    });
  }

  /**
   * Calculates optimal scroll duration (ms) based on difficulty stars and note density.
   * Adjusted to a slower, comfortable and readable speed curve.
   */
  computeDynamicScrollDuration(stars, rawNotes = []) {
    const s = Math.max(1.0, Math.min(10.0, parseFloat(stars) || 3.0));
    
    // Comfortable, readable scroll duration curve (ms):
    // 1★: 1750ms (Easy / Very Relaxed)
    // 3★: 1450ms (Normal)
    // 5★: 1200ms (Hard)
    // 7★: 950ms  (Expert)
    // 9★: 750ms  (Insane)
    // 10★: 620ms (Master)
    let duration = 1750 - (s - 1.0) * 150;
    if (s >= 4.0) {
      duration = 1300 - (s - 4.0) * 125;
    }
    if (s >= 7.0) {
      duration = 925 - (s - 7.0) * 100;
    }

    if (rawNotes && rawNotes.length > 5) {
      const laneLastTime = [-Infinity, -Infinity, -Infinity];
      let minGapSameLane = Infinity;

      for (const n of rawNotes) {
        const l = Math.max(0, Math.min(2, n.lane ?? 1));
        const prev = laneLastTime[l];
        if (prev >= 0) {
          const gap = n.timestamp_ms - prev;
          if (gap > 15 && gap < minGapSameLane) {
            minGapSameLane = gap;
          }
        }
        laneLastTime[l] = n.timestamp_ms;
      }

      if (minGapSameLane < 250 && minGapSameLane > 0) {
        const hitY = this.hitLineY || 600;
        const maxAllowedDuration = (minGapSameLane * hitY) / 38;
        if (duration > maxAllowedDuration) {
          duration = maxAllowedDuration;
        }
      }
    }

    const mult = Math.max(0.5, Math.min(2.5, this.noteSpeedMultiplier || 1.0));
    duration = duration / mult;

    return Math.round(Math.max(480, Math.min(2200, duration)));
  }

  loadBeatmap(beatmapData, audioBlob = null) {
    this.isCalibrating = false;
    this.beatmapData = beatmapData;
    this.numLanes = 3;
    this.laneGlows = [0, 0, 0];
    this.fxRipples = [];
    this.initCanvasSize();

    // Extract real BPM and Beat Grid Offset
    this.bpm = beatmapData.metadata?.bpm || beatmapData.bpm || 120;
    const beatDurationMs = 60000 / (this.bpm || 120);
    this.firstBeatOffsetMs = (beatmapData.notes && beatmapData.notes.length > 0) 
      ? (((beatmapData.notes[0].timestamp_ms % beatDurationMs) + beatDurationMs) % beatDurationMs) 
      : 0;

    // Explicitly reset all game state flags
    this.isRunning = false;
    this.isPaused = false;
    this.isGameOver = false;
    this.isInitialLaunch = true;
    this.isRewinding = false;
    this.isProcessingMiss = false;
    this.lastMissTimePerf = 0;
    this.lastFailSongTimeSec = 0;

    const diffStars = beatmapData.metadata?.stars || 3.0;

    // Pass notes through LaneRemapper.sanitizeForTwoFingers to guarantee 2-finger compliance & density limit
    const rawNotes = (beatmapData && beatmapData.notes) ? beatmapData.notes : [];
    const sanitizedNotes = (typeof LaneRemapper !== 'undefined' && LaneRemapper.sanitizeForTwoFingers)
      ? LaneRemapper.sanitizeForTwoFingers(rawNotes, this.bpm, diffStars)
      : rawNotes;

    // Set dynamic scroll duration based on difficulty
    this.scrollDurationMs = this.computeDynamicScrollDuration(diffStars, sanitizedNotes);

    this.notes = sanitizedNotes.map(n => ({
      ...n,
      hit: false,
      holding: false,
      holdCompleted: false,
      missed: false,
      processed: false
    }));

    this.activeHolds.clear();
    this.activeTouches.clear();
    this.judgements = [];
    this.score = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.streakCount = 0;
    this.multiplier = 1;
    this.stars = 0;
    this.missCount = 0;
    this.invulnerableUntil = 0;
    this.stats = { perfectPlus: 0, perfect: 0, great: 0, miss: 0 };
    this.targetScore = Math.max(20000, this.notes.length * 450 * 3.5);

    // Load audio track
    if (audioBlob) {
      this.sync.loadAudioBlob(audioBlob);
    } else if (beatmapData.audio_blob_url) {
      this.sync.loadAudioUrl(beatmapData.audio_blob_url);
    }

    this.ui.onScoreUpdate(this.score, this.combo, this.stars, this.multiplier);
    this.ui.onSongLoaded(beatmapData.metadata);

    // Start 3-2-1 countdown then start playback and rendering loop
    if (this.ui && this.ui.onStartCountdown) {
      this.ui.onStartCountdown(() => {
        this.isPaused = false;
        this.sync.play();
        this.startLoop();
      });
    } else {
      this.isPaused = false;
      this.sync.play();
      this.startLoop();
    }
  }

  startNativeCalibration() {
    this.isCalibrating = true;
    this.scrollDurationMs = 1200;
    this.isPaused = false;
    this.isGameOver = false;
    this.isRewinding = false;
    this.sync.pause();
    this.notes = [];
    this.activeHolds.clear();
    this.activeTouches.clear();
    this.judgements = [];

    this.synth.ensureContext();
    this.calibrationStartTime = performance.now();
    this.nextCalibNoteTime = this.calibrationStartTime + 400;
    this.startLoop();
  }

  stopNativeCalibration() {
    this.isCalibrating = false;
    this.notes = [];
    this.activeHolds.clear();
    this.judgements = [];
    this.stop();
  }

  pause() {
    this.isPaused = true;
    this.sync.pause();
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
  }

  resume() {
    this.isPaused = false;
    this.isRewinding = false;
    this.isProcessingMiss = false;
    this.lastMissTimePerf = performance.now();
    this.sync.play();
    if (!this.animFrameId) {
      this.startLoop();
    }
  }

  animateRewind(fromTimeMs, toTimeMs, durationMs = 600, onComplete = null) {
    this.isRewinding = true;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }

    const startPerf = performance.now();

    const rewindStep = (now) => {
      const elapsed = now - startPerf;
      const progress = Math.min(1.0, elapsed / durationMs);

      const eased = progress < 0.5 
        ? 2 * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;

      const currentRenderTime = fromTimeMs + (toTimeMs - fromTimeMs) * eased;

      this.ctx.clearRect(0, 0, this.width, this.height);
      this.renderBackgroundFX(currentRenderTime);
      this.renderLanes();
      this.renderNotes(currentRenderTime);
      this.renderHitLine();

      if (progress < 1.0) {
        requestAnimationFrame(rewindStep);
      } else {
        this.isRewinding = false;
        if (onComplete) onComplete();
      }
    };

    requestAnimationFrame(rewindStep);
  }

  reviveAndResume() {
    this.synth.playAnalogTapeRewind();

    const currentSongTime = (this.sync.getCurrentTimeMs() || 0) / 1000;
    const targetTimeSec = Math.max(0, currentSongTime - 2.0);
    const targetTimeMs = targetTimeSec * 1000;
    const clearThresholdMs = (currentSongTime + 1.0) * 1000;

    this.sync.seekTo(targetTimeSec);
    this.sync.play();
    this.isPaused = false;
    this.isGameOver = false;

    // Reset notes
    this.notes.forEach(note => {
      const noteTime = note.timestamp_ms || 0;
      if (noteTime <= clearThresholdMs) {
        note.hit = true;
        note.missed = false;
        note.processed = true;
        note.holding = false;
        note.holdCompleted = true;
      } else {
        note.hit = false;
        note.missed = false;
        note.processed = false;
        note.holding = false;
        note.holdCompleted = false;
      }
    });

    this.particles.particles = [];
    this.particles.shockwaves = [];
    this.activeHolds.clear();
    this.activeTouches.clear();
    this.judgements = [];

    this.isProcessingMiss = false;
    this.lastMissTimePerf = performance.now();
    this.invulnerableUntil = clearThresholdMs + this.latencyOffsetMs + 800;

    if (this.ui.onShowRewindBadge) {
      this.ui.onShowRewindBadge();
    }

    const fromRenderTime = (currentSongTime * 1000) + this.latencyOffsetMs;
    const toRenderTime = targetTimeMs + this.latencyOffsetMs;

    this.animateRewind(fromRenderTime, toRenderTime, 600, () => {
      this.resume();
    });
  }

  restart() {
    if (!this.beatmapData) return;
    this.loadBeatmap(this.beatmapData, this.sync.audioElement.src);
    this.sync.seekTo(0);
    this.sync.play();
  }

  stop() {
    this.isPaused = true;
    this.isRunning = false;
    this.isRewinding = false;
    this.isProcessingMiss = false;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.sync.pause();
    this.activeHolds.clear();
    this.activeTouches.clear();
    this.notes = [];
    this.judgements = [];
    this.fxRipples = [];
  }

  getLaneFromX(clientX) {
    const rect = this.canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const lane = Math.floor(x / (rect.width / 3));
    return Math.max(0, Math.min(2, lane));
  }

  handleTouchStart(e) {
    e.preventDefault();
    if (this.isPaused || this.isRewinding) return;

    const rect = this.canvas.getBoundingClientRect();
    const now = performance.now();

    for (let i = 0; i < e.changedTouches.length; i++) {
      const touch = e.changedTouches[i];
      const x = touch.clientX - rect.left;
      const y = touch.clientY - rect.top;
      const lane = this.getLaneFromX(touch.clientX);

      this.activeTouches.set(touch.identifier, {
        x0: x, y0: y, t0: now, lane, swiped: false
      });

      this.triggerLaneInput(lane, 'tap', null, touch.identifier);
    }
  }

  handleTouchMove(e) {
    e.preventDefault();
    if (this.isPaused || this.isRewinding) return;

    const rect = this.canvas.getBoundingClientRect();
    const now = performance.now();

    for (let i = 0; i < e.changedTouches.length; i++) {
      const touch = e.changedTouches[i];
      const touchData = this.activeTouches.get(touch.identifier);
      if (!touchData || touchData.swiped) continue;

      const currentX = touch.clientX - rect.left;
      const currentY = touch.clientY - rect.top;
      const dx = currentX - touchData.x0;
      const dy = currentY - touchData.y0;
      const dist = Math.hypot(dx, dy);
      const elapsed = now - touchData.t0;

      if (dist > 20 && elapsed < 350) {
        let direction = 'up';
        if (Math.abs(dx) > Math.abs(dy)) {
          direction = dx > 0 ? 'right' : 'left';
        } else {
          direction = dy > 0 ? 'down' : 'up';
        }

        touchData.swiped = true;
        this.triggerLaneInput(touchData.lane, 'swipe', direction, touch.identifier);
      }
    }
  }

  handleTouchEnd(e) {
    e.preventDefault();
    for (let i = 0; i < e.changedTouches.length; i++) {
      const touch = e.changedTouches[i];
      const touchData = this.activeTouches.get(touch.identifier);
      if (touchData) {
        this.releaseLaneHold(touchData.lane, touch.identifier);
        this.activeTouches.delete(touch.identifier);
      }
    }
  }

  handleMouseDown(e) {
    if (this.isPaused || this.isRewinding) return;
    const lane = this.getLaneFromX(e.clientX);
    const rect = this.canvas.getBoundingClientRect();
    this.mouseTouch = {
      x0: e.clientX - rect.left,
      y0: e.clientY - rect.top,
      t0: performance.now(),
      lane: lane,
      swiped: false
    };
    this.triggerLaneInput(lane, 'tap', null, 'mouse');
  }

  handleMouseMove(e) {
    if (!this.mouseTouch || this.mouseTouch.swiped || this.isPaused || this.isRewinding) return;
    const rect = this.canvas.getBoundingClientRect();
    const dx = (e.clientX - rect.left) - this.mouseTouch.x0;
    const dy = (e.clientY - rect.top) - this.mouseTouch.y0;
    const dist = Math.hypot(dx, dy);

    if (dist > 20) {
      let direction = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
      this.mouseTouch.swiped = true;
      this.triggerLaneInput(this.mouseTouch.lane, 'swipe', direction, 'mouse');
    }
  }

  handleMouseUp() {
    if (this.mouseTouch) {
      this.releaseLaneHold(this.mouseTouch.lane, 'mouse');
      this.mouseTouch = null;
    }
  }

  triggerLaneInput(lane, inputType = 'tap', swipeDirection = null, touchId = null) {
    this.laneGlows[lane] = 1.0;
    const currentTime = this.isCalibrating 
      ? (performance.now() - this.calibrationStartTime) + this.latencyOffsetMs
      : this.sync.getCurrentTimeMs() + this.latencyOffsetMs;

    const hitX = (lane + 0.5) * this.laneWidth;
    const hitY = this.hitLineY;

    // Trigger visual background ripple/wave
    this.fxRipples.push({
      lane,
      x: hitX,
      y: hitY,
      radius: 12,
      maxRadius: 180,
      alpha: 0.85,
      decay: 2.2,
      color: lane === 0 ? '#00f2fe' : (lane === 1 ? '#00ff88' : '#ff007f')
    });

    let closestNote = null;
    let minDiff = Infinity;

    for (const note of this.notes) {
      if ((!this.isCalibrating && note.lane !== lane) || note.hit || note.missed || note.holdCompleted) continue;
      const diff = Math.abs(note.timestamp_ms - currentTime);
      if (diff < 260 && diff < minDiff) {
        minDiff = diff;
        closestNote = note;
      }
    }

    if (!closestNote) {
      if (this.isCalibrating) {
        this.synth.playClick();
        return;
      }
      
      const nowPerf = performance.now();
      if (this.beatmapData && this.sync.isPlaying && currentTime > this.invulnerableUntil && !this.isProcessingMiss && (nowPerf - this.lastMissTimePerf >= 750)) {
        this.synth.playPunchyArcadeMiss();
        this.addJudgement('GHOST TAP', '#ff4d4d');
        this.handleMiss();
      }
      return;
    }

    if (this.isCalibrating) {
      this.judgeHit(closestNote, minDiff, hitX, hitY, 'CALIB');
      closestNote.hit = true;
      this.particles.emitHit(hitX, hitY, '#00f2fe');
      this.synth.playPianoChime();
      return;
    }

    if (closestNote.type === 'tap' && inputType === 'tap') {
      this.judgeHit(closestNote, minDiff, hitX, hitY);
      closestNote.hit = true;
      this.particles.emitHit(hitX, hitY, '#00f2fe');
    } 
    else if (closestNote.type === 'swipe' && inputType === 'swipe') {
      const targetDir = closestNote.direction || 'up';
      if (swipeDirection === targetDir || !closestNote.direction) {
        this.judgeHit(closestNote, minDiff, hitX, hitY, 'SWIPE');
        closestNote.hit = true;
        this.particles.emitSwipeBurst(hitX, hitY, targetDir, '#ffd700', 32);
      }
    } 
    else if (closestNote.type === 'hold' && inputType === 'tap') {
      this.judgeHit(closestNote, minDiff, hitX, hitY);
      closestNote.holding = true;
      closestNote.missed = false;
      this.activeHolds.set(lane, {
        note: closestNote,
        touchId: touchId,
        startTime: currentTime,
        initialTime: closestNote.timestamp_ms
      });
      this.particles.emitHit(hitX, hitY, '#00ff88', 22);
    }
  }

  releaseLaneHold(lane, touchId = null) {
    const active = this.activeHolds.get(lane);
    if (!active) return;
    if (touchId !== null && active.touchId !== touchId) return;

    const currentTime = this.sync.getCurrentTimeMs() + this.latencyOffsetMs;
    const note = active.note;
    const endT = note.end_timestamp_ms || (note.timestamp_ms + (note.duration_ms || 700));

    if (currentTime >= endT - 160) {
      note.holdCompleted = true;
      note.hit = true;
      note.holding = false;
      this.addScore(450 * this.multiplier);
      const hitX = (lane + 0.5) * this.laneWidth;
      this.particles.emitHit(hitX, this.hitLineY, '#00ff88', 30);
    } else {
      note.missed = true;
      note.holding = false;
      const nowPerf = performance.now();
      if (!this.isProcessingMiss && (nowPerf - this.lastMissTimePerf >= 750)) {
        this.synth.playPunchyArcadeMiss();
        this.addJudgement('HOLD DROP', '#ff4d4d');
        this.handleMiss();
      }
    }
    this.activeHolds.delete(lane);
  }

  judgeHit(note, diffMs, x, y, customLabel = null) {
    let text = 'GREAT';
    let color = '#ffd166';
    let points = 150;

    if (diffMs <= 45) {
      text = customLabel ? `PERFECT+ ${customLabel}` : 'PERFECT+';
      color = '#00f2fe';
      points = 450;
      this.stats.perfectPlus++;
      this.streakCount++;
    } else if (diffMs <= 90) {
      text = customLabel ? `PERFECT ${customLabel}` : 'PERFECT';
      color = '#06d6a0';
      points = 300;
      this.stats.perfect++;
      this.streakCount++;
    } else if (diffMs <= 170) {
      text = customLabel ? `GREAT ${customLabel}` : 'GREAT';
      color = '#ffd166';
      points = 150;
      this.stats.great++;
      this.streakCount = Math.max(0, this.streakCount - 1);
    } else {
      text = customLabel ? `GOOD ${customLabel}` : 'GOOD';
      color = '#a0aec0';
      points = 75;
      this.streakCount = 0;
    }

    if (this.streakCount >= 15) {
      this.multiplier = 5;
    } else if (this.streakCount >= 10) {
      this.multiplier = 3;
    } else if (this.streakCount >= 5) {
      this.multiplier = 2;
    } else {
      this.multiplier = 1;
    }

    this.combo++;
    if (this.combo > this.maxCombo) this.maxCombo = this.combo;
    
    this.addScore(points * this.multiplier);
    this.addJudgement(text, color);
  }

  addScore(pts) {
    this.score += pts;
    const target90 = this.targetScore * 0.90;
    this.stars = Math.min(5, Math.floor((this.score / target90) * 5));
    this.ui.onScoreUpdate(this.score, this.combo, this.stars, this.multiplier);
  }

  handleMiss() {
    const nowPerf = performance.now();
    if (this.isProcessingMiss || (nowPerf - this.lastMissTimePerf < 750)) {
      return;
    }

    this.isProcessingMiss = true;
    this.lastMissTimePerf = nowPerf;
    this.lastFailSongTimeSec = (this.sync.getCurrentTimeMs() || 0) / 1000;

    this.combo = 0;
    this.streakCount = 0;
    this.multiplier = 1;
    this.stats.miss++;
    this.ui.onScoreUpdate(this.score, this.combo, this.stars, this.multiplier);

    if (!this.continueMode && !this.isCalibrating && this.beatmapData) {
      const penaltyCost = Math.pow(2, this.missCount);
      this.missCount++;
      this.pause();
      if (this.ui.onMissPenalty) {
        this.ui.onMissPenalty(penaltyCost, this.missCount);
      }
    }
  }

  /**
   * Judgements rendered in upper screen area (below HUD) to prevent blocking incoming notes
   */
  addJudgement(text, color) {
    this.judgements.push({
      text: text,
      color: color,
      y: this.height * 0.20,
      alpha: 1.0,
      scale: 1.25,
      decay: 2.0
    });
  }

  update(dt) {
    if (this.isPaused || this.isRewinding) return;

    if (this.isCalibrating) {
      const now = performance.now();
      const currentCalibTime = (now - this.calibrationStartTime) + this.latencyOffsetMs;

      if (now >= this.nextCalibNoteTime) {
        const targetHitTime = currentCalibTime + this.scrollDurationMs;
        const audioCtx = this.synth.ensureContext();
        const delaySec = Math.max(0, (this.scrollDurationMs - this.latencyOffsetMs) / 1000);
        this.synth.playPianoChime(audioCtx.currentTime + delaySec);

        this.notes.push({
          id: this.notes.length + 1,
          lane: 1,
          type: 'tap',
          timestamp_ms: targetHitTime,
          hit: false,
          missed: false,
          flashed: false
        });

        this.nextCalibNoteTime = now + this.calibrationIntervalMs;
      }

      for (const note of this.notes) {
        if (!note.flashed && currentCalibTime >= note.timestamp_ms) {
          note.flashed = true;
          const hitX = (1 + 0.5) * this.laneWidth;
          this.laneGlows[1] = 1.0;
          this.particles.emitHit(hitX, this.hitLineY, '#00f2fe', 18);

          if (this.ui.onMetronomeBeat) {
            this.ui.onMetronomeBeat();
          }
        }
      }

      if (this.notes.length > 20) {
        this.notes.splice(0, 8);
      }

      this.updateVisualEffects(dt);
      return;
    }

    const currentTime = this.sync.getCurrentTimeMs() + this.latencyOffsetMs;
    const nowPerf = performance.now();
    const canTriggerMiss = !this.isProcessingMiss && (nowPerf - this.lastMissTimePerf >= 750);

    for (const note of this.notes) {
      if (!note.hit && !note.missed && !note.holding && !note.processed && !note.holdCompleted) {
        if (currentTime - note.timestamp_ms > 240) {
          note.missed = true;
          note.processed = true;
          if (currentTime > this.invulnerableUntil && canTriggerMiss) {
            this.synth.playPunchyArcadeMiss();
            this.addJudgement('MISS', '#ff4d4d');
            this.handleMiss();
            break;
          }
        }
      }
    }

    for (const [lane, active] of this.activeHolds.entries()) {
      const note = active.note;
      const endT = note.end_timestamp_ms || (note.timestamp_ms + (note.duration_ms || 700));
      const hitX = (lane + 0.5) * this.laneWidth;
      
      this.particles.emitHoldSpark(hitX, this.hitLineY, '#00ff88');
      this.addScore(Math.round(260 * dt * this.multiplier));

      if (currentTime >= endT) {
        note.holdCompleted = true;
        note.hit = true;
        note.holding = false;
        this.activeHolds.delete(lane);
        this.particles.emitHit(hitX, this.hitLineY, '#00ff88', 35);
        this.addJudgement('HOLD CLEAR!', '#00ff88');
      }
    }

    this.updateVisualEffects(dt);

    if (this.beatmapData && this.notes.length > 0) {
      const lastNoteTime = Math.max(...this.notes.map(n => n.end_timestamp_ms || n.timestamp_ms));
      if (currentTime > lastNoteTime + 2000 && !this.isGameOver) {
        this.isGameOver = true;
        
        const diffStars = this.beatmapData.metadata?.stars || 3.0;
        let diffMultiplier = diffStars < 2.5 ? 1 : (diffStars < 4.5 ? 2 : (diffStars < 6.5 ? 3 : 4));
        const earnedClefs = this.stars * diffMultiplier;

        this.ui.onGameEnd(this.score, this.maxCombo, this.stars, this.stats, earnedClefs);
      }
    }
  }

  updateVisualEffects(dt) {
    for (let l = 0; l < 3; l++) {
      this.laneGlows[l] = Math.max(0, (this.laneGlows[l] || 0) - dt * 4.0);
    }

    for (let i = this.judgements.length - 1; i >= 0; i--) {
      const j = this.judgements[i];
      j.alpha -= j.decay * dt;
      j.y -= 15 * dt;
      j.scale = Math.max(1.0, j.scale - dt * 1.2);
      if (j.alpha <= 0) this.judgements.splice(i, 1);
    }

    for (let i = this.fxRipples.length - 1; i >= 0; i--) {
      const r = this.fxRipples[i];
      r.radius += (r.maxRadius - r.radius) * 7.5 * dt;
      r.alpha -= r.decay * dt;
      if (r.alpha <= 0) this.fxRipples.splice(i, 1);
    }

    this.particles.update(dt);
  }

  /**
   * Canvas Background Effects:
   * - 'black' (Pitch black)
   * - 'neon_aura' (Aura Neón Rítmica - subtle pulsing light & ripples)
   * - 'ocean_waves' (Mareas del Océano - animated fluid rolling waves & splash surges)
   * - 'synthwave_grid' (Ciberespacio Retro 80s - perspective grid)
   * - 'cosmic_aurora' (Aurora Boreal - shimmering flowing plasma)
   */
  /**
   * Canvas Background Effects:
   * Syncs breathing light auras, ocean swells and neon glows directly to the song's BPM and beat grid!
   */
  renderBackgroundFX(currentTime) {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const effect = this.activeEffect || 'neon_aura';

    if (effect === 'black') {
      ctx.fillStyle = '#06040a';
      ctx.fillRect(0, 0, w, h);
      return;
    }

    // Compute real musical beat pulse (1:1 with song BPM)
    const bpm = this.bpm || 120;
    const beatDurationMs = 60000 / bpm;
    const songTime = currentTime || 0;
    const beatProgress = (((songTime - (this.firstBeatOffsetMs || 0)) % beatDurationMs) + beatDurationMs) % beatDurationMs;
    const beatNorm = beatProgress / beatDurationMs; // 0.0 at kick strike -> 1.0 before next beat
    // Punchy exponential attack-decay beat envelope (like a real audio bass pump)
    const beatPulse = Math.pow(Math.max(0, 1 - beatNorm * 1.7), 2.2);

    if (effect === 'neon_aura') {
      // 1. Deep black base
      ctx.fillStyle = '#06040c';
      ctx.fillRect(0, 0, w, h);

      // 2. Real BPM Rhythmic Aura Breathing behind lanes
      const auraAlpha = 0.08 + 0.18 * beatPulse;
      const auraRadius = w * 0.70 + 45 * beatPulse;

      const auraGrad = ctx.createRadialGradient(w / 2, this.hitLineY * 0.65, 10, w / 2, this.hitLineY * 0.65, auraRadius);
      auraGrad.addColorStop(0, `rgba(0, 242, 254, ${auraAlpha * 1.6})`);
      auraGrad.addColorStop(0.5, `rgba(255, 0, 127, ${auraAlpha * 0.9})`);
      auraGrad.addColorStop(1, 'rgba(6, 4, 12, 0)');
      
      ctx.save();
      ctx.fillStyle = auraGrad;
      ctx.fillRect(0, 0, w, h);

      // 3. Subtle ambient neon ripples on tap
      for (const r of this.fxRipples) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, r.alpha * 0.4);
        ctx.strokeStyle = r.color || '#00f2fe';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = r.color || '#00f2fe';
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }
      ctx.restore();
      return;
    }

    if (effect === 'ocean_waves') {
      // 1. Deep oceanic gradient
      const oceanGrad = ctx.createLinearGradient(0, 0, 0, h);
      oceanGrad.addColorStop(0, '#020914');
      oceanGrad.addColorStop(0.6, '#041628');
      oceanGrad.addColorStop(1, '#062d48');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, w, h);

      // 2. Multi-layer animated undulating ocean sine waves pulsing with the rhythm
      ctx.save();
      const t = songTime * 0.0018;
      const waveSwell = 1.0 + 0.45 * beatPulse;

      // Back wave (Deep teal)
      ctx.fillStyle = `rgba(0, 180, 216, ${0.10 + 0.08 * beatPulse})`;
      ctx.beginPath();
      ctx.moveTo(0, h);
      for (let x = 0; x <= w; x += 8) {
        const y = h * 0.68 + (Math.sin(x * 0.015 + t) * 18 + Math.cos(x * 0.03 - t * 0.8) * 10) * waveSwell;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(w, h);
      ctx.closePath();
      ctx.fill();

      // Mid wave (Ocean cyan)
      ctx.fillStyle = `rgba(0, 242, 254, ${0.14 + 0.10 * beatPulse})`;
      ctx.beginPath();
      ctx.moveTo(0, h);
      for (let x = 0; x <= w; x += 8) {
        const y = h * 0.75 + (Math.sin(x * 0.02 - t * 1.2) * 15 + Math.cos(x * 0.01 + t * 0.6) * 12) * waveSwell;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(w, h);
      ctx.closePath();
      ctx.fill();

      // Front wave (Seafoam crest)
      ctx.fillStyle = `rgba(72, 202, 228, ${0.18 + 0.12 * beatPulse})`;
      ctx.beginPath();
      ctx.moveTo(0, h);
      for (let x = 0; x <= w; x += 8) {
        const y = h * 0.82 + (Math.sin(x * 0.025 + t * 1.5) * 12) * waveSwell;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(w, h);
      ctx.closePath();
      ctx.fill();

      // 3. Dynamic Wave Surges on Key Press
      for (const r of this.fxRipples) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, r.alpha * 0.5);
        ctx.fillStyle = 'rgba(0, 242, 254, 0.35)';
        ctx.shadowColor = '#00f2fe';
        ctx.shadowBlur = 20;

        const surgeW = this.laneWidth * 0.85;
        const surgeH = r.radius * 2.2;
        ctx.beginPath();
        ctx.ellipse(r.x, this.hitLineY - surgeH * 0.4, surgeW / 2, surgeH / 2, 0, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.0;
        ctx.stroke();
        ctx.restore();
      }
      ctx.restore();
      return;
    }

    if (effect === 'synthwave_grid') {
      const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
      bgGrad.addColorStop(0, '#0a0014');
      bgGrad.addColorStop(0.55, '#1a002c');
      bgGrad.addColorStop(1, '#2c004a');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, w, h);

      const sunY = h * 0.55;
      const sunRadius = w * 0.42 + 35 * beatPulse;
      const sunGrad = ctx.createRadialGradient(w / 2, sunY, 5, w / 2, sunY, sunRadius);
      sunGrad.addColorStop(0, `rgba(255, 0, 127, ${0.35 + 0.25 * beatPulse})`);
      sunGrad.addColorStop(0.6, `rgba(255, 110, 0, ${0.15 + 0.15 * beatPulse})`);
      sunGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = sunGrad;
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.strokeStyle = `rgba(255, 0, 127, ${0.20 + 0.15 * beatPulse})`;
      ctx.lineWidth = 1.5;
      const gridOffset = (songTime * 0.06) % 30;

      for (let y = sunY + gridOffset; y < h; y += 28 * ((y - sunY) / 150)) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      for (let vx = -w * 0.5; vx <= w * 1.5; vx += w * 0.25) {
        ctx.beginPath();
        ctx.moveTo(w / 2, sunY);
        ctx.lineTo(vx, h);
        ctx.stroke();
      }
      ctx.restore();
      return;
    }

    if (effect === 'cosmic_aurora') {
      ctx.fillStyle = '#04020a';
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      const t = songTime * 0.0012;
      const auroraPulse = 1.0 + 0.4 * beatPulse;
      
      for (let layer = 0; layer < 3; layer++) {
        const ribbonAlpha = (layer === 0 ? 0.16 : (layer === 1 ? 0.14 : 0.12)) * auroraPulse;
        const ribbonColor = layer === 0 
          ? `rgba(0, 255, 136, ${ribbonAlpha})` 
          : (layer === 1 ? `rgba(0, 242, 254, ${ribbonAlpha})` : `rgba(177, 66, 255, ${ribbonAlpha})`);
        ctx.fillStyle = ribbonColor;
        ctx.beginPath();
        ctx.moveTo(0, 0);

        for (let x = 0; x <= w; x += 12) {
          const y = (h * (0.3 + layer * 0.15) + Math.sin(x * 0.01 + t + layer) * 45 + Math.cos(x * 0.02 - t * 0.7) * 25) * (0.9 + 0.1 * beatPulse);
          ctx.lineTo(x, y);
        }
        ctx.lineTo(w, 0);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
      return;
    }
  }

  render() {
    this.ctx.clearRect(0, 0, this.width, this.height);
    const currentTime = this.isCalibrating 
      ? (performance.now() - this.calibrationStartTime) + this.latencyOffsetMs
      : this.sync.getCurrentTimeMs() + this.latencyOffsetMs;

    this.renderBackgroundFX(currentTime);
    this.renderLanes();
    this.renderNotes(currentTime);
    this.particles.render(this.ctx);
    this.renderHitLine();
    this.renderJudgements();
  }

  renderLanes() {
    const ctx = this.ctx;

    for (let l = 0; l < 3; l++) {
      const x0 = l * this.laneWidth;

      const isHolding = this.activeHolds.has(l);
      if (isHolding) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 255, 136, 0.22)';
        ctx.fillRect(x0, 0, this.laneWidth, this.height);
        ctx.restore();
      } else if (this.laneGlows[l] > 0) {
        ctx.save();
        ctx.fillStyle = `#00f2fe${Math.round(this.laneGlows[l] * 50).toString(16).padStart(2, '0')}`;
        ctx.fillRect(x0, 0, this.laneWidth, this.height);
        ctx.restore();
      }

      if (l > 0) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x0, 0);
        ctx.lineTo(x0, this.height);
        ctx.stroke();
      }
    }
  }

  renderHitLine() {
    const ctx = this.ctx;
    const y = this.hitLineY;

    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.shadowColor = '#00f2fe';
    ctx.shadowBlur = 16;
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(this.width, y);
    ctx.stroke();

    const baseRadius = 28;
    const pressedRadius = 33;
    const holdingRadius = 36;
    const ringRadius = 42;

    for (let l = 0; l < 3; l++) {
      const cx = (l + 0.5) * this.laneWidth;
      const isHolding = this.activeHolds.has(l);
      const isPressed = this.laneGlows[l] > 0.4 || isHolding;

      ctx.beginPath();
      ctx.arc(cx, y, isHolding ? holdingRadius : (isPressed ? pressedRadius : baseRadius), 0, Math.PI * 2);
      ctx.fillStyle = isHolding 
        ? 'rgba(0, 255, 136, 0.45)' 
        : (isPressed ? 'rgba(0, 242, 254, 0.35)' : 'rgba(255, 255, 255, 0.08)');
      ctx.fill();
      ctx.strokeStyle = isHolding ? '#00ff88' : (isPressed ? '#00f2fe' : 'rgba(255, 255, 255, 0.3)');
      ctx.lineWidth = isHolding ? 4 : (isPressed ? 3 : 2);
      ctx.stroke();

      if (isHolding) {
        const active = this.activeHolds.get(l);
        const startT = active.startTime;
        const endT = active.note.end_timestamp_ms || (startT + (active.note.duration_ms || 700));
        const currT = this.sync.getCurrentTimeMs() + this.latencyOffsetMs;
        const progress = Math.min(1.0, Math.max(0, (currT - startT) / (endT - startT)));

        ctx.beginPath();
        ctx.arc(cx, y, ringRadius, -Math.PI / 2, -Math.PI / 2 + progress * Math.PI * 2);
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 3.5;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  renderVectorChevron(ctx, x, y, direction, size = 32, strokeColor = '#ffffff') {
    ctx.save();
    ctx.translate(x, y);

    let angle = 0;
    if (direction === 'down') angle = Math.PI;
    else if (direction === 'left') angle = -Math.PI / 2;
    else if (direction === 'right') angle = Math.PI / 2;

    ctx.rotate(angle);

    const w = size * 1.35;
    const h = size * 0.70;
    const thickness = size * 0.38;

    ctx.beginPath();
    ctx.moveTo(0, -h);
    ctx.lineTo(w, 0);
    ctx.lineTo(w, thickness);
    ctx.lineTo(0, -h + thickness);
    ctx.lineTo(-w, thickness);
    ctx.lineTo(-w, 0);
    ctx.closePath();

    ctx.fillStyle = strokeColor;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(0, -h + thickness * 1.3);
    ctx.lineTo(w * 0.75, thickness * 1.3);
    ctx.lineTo(w * 0.75, thickness * 1.9);
    ctx.lineTo(0, -h + thickness * 1.9);
    ctx.lineTo(-w * 0.75, thickness * 1.9);
    ctx.lineTo(-w * 0.75, thickness * 1.3);
    ctx.closePath();

    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fill();

    ctx.restore();
  }

  renderNotes(currentTime) {
    const ctx = this.ctx;

    for (const note of this.notes) {
      if (note.holdCompleted) continue;
      if (note.hit && note.type !== 'hold') continue;
      if (note.missed && !note.holding) continue;

      const isBeingHeld = note.holding && !note.holdCompleted;
      const timeUntilHit = note.timestamp_ms - currentTime;
      const x = (note.lane + 0.5) * this.laneWidth;
      const w = this.laneWidth * 0.78;
      const h = 28;

      if (note.type === 'hold') {
        const holdDuration = note.duration_ms || 700;
        const fullTailLength = (holdDuration / this.scrollDurationMs) * this.hitLineY;
        const endT = note.end_timestamp_ms || (note.timestamp_ms + holdDuration);
        
        let headY = this.hitLineY - (timeUntilHit / this.scrollDurationMs) * this.hitLineY;
        let tailLength = fullTailLength;

        if (isBeingHeld) {
          headY = this.hitLineY;
          const remainingMs = Math.max(0, endT - currentTime);
          tailLength = (remainingMs / this.scrollDurationMs) * this.hitLineY;
        }

        const endY = headY - tailLength;
        if (endY > this.height + 100 || headY < -300) continue;

        ctx.save();
        const grad = ctx.createLinearGradient(0, endY, 0, headY);
        if (isBeingHeld) {
          grad.addColorStop(0, 'rgba(0, 255, 136, 0.25)');
          grad.addColorStop(1, 'rgba(0, 255, 136, 0.95)');
          ctx.shadowColor = '#00ff88';
          ctx.shadowBlur = 22;
        } else {
          grad.addColorStop(0, 'rgba(240, 147, 251, 0.2)');
          grad.addColorStop(1, 'rgba(245, 87, 108, 0.85)');
          ctx.shadowColor = '#f5576c';
          ctx.shadowBlur = 14;
        }

        ctx.fillStyle = grad;
        ctx.fillRect(x - w * 0.4, endY, w * 0.8, tailLength);
        
        ctx.strokeStyle = isBeingHeld ? '#00ff88' : '#f5576c';
        ctx.lineWidth = isBeingHeld ? 3.5 : 2.5;
        ctx.strokeRect(x - w * 0.4, endY, w * 0.8, tailLength);

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x - w * 0.45, endY - 4, w * 0.9, 8);

        ctx.fillStyle = isBeingHeld ? '#00ff88' : '#ffffff';
        ctx.beginPath();
        ctx.roundRect(x - w / 2, headY - h / 2, w, h, 12);
        ctx.fill();
        ctx.restore();

      } else if (note.type === 'swipe') {
        const giantW = this.laneWidth * 0.92;
        const giantH = 58;
        const y = this.hitLineY - (timeUntilHit / this.scrollDurationMs) * this.hitLineY;
        if (y < -300 || y > this.height + 100) continue;

        ctx.save();
        const dir = note.direction || 'up';
        
        let neonGlow = '#00f2fe';
        let grad1 = '#00f2fe';
        let grad2 = '#0066ff';

        if (dir === 'up') {
          neonGlow = '#ffd700';
          grad1 = '#ffd700';
          grad2 = '#ff007f';
        } else if (dir === 'down') {
          neonGlow = '#00ff88';
          grad1 = '#00ff88';
          grad2 = '#00b4d8';
        }

        ctx.shadowColor = neonGlow;
        ctx.shadowBlur = 28;
        
        const grad = ctx.createLinearGradient(x - giantW / 2, y, x + giantW / 2, y);
        grad.addColorStop(0, grad1);
        grad.addColorStop(1, grad2);
        ctx.fillStyle = grad;

        ctx.beginPath();
        ctx.roundRect(x - giantW / 2, y - giantH / 2, giantW, giantH, 18);
        ctx.fill();

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3.0;
        ctx.stroke();

        this.renderVectorChevron(ctx, x, y, dir, 28, '#ffffff');
        ctx.restore();

      } else {
        const y = this.hitLineY - (timeUntilHit / this.scrollDurationMs) * this.hitLineY;
        if (y < -300 || y > this.height + 100) continue;

        ctx.save();
        ctx.shadowColor = '#00f2fe';
        ctx.shadowBlur = 14;

        const grad = ctx.createLinearGradient(x - w / 2, y, x + w / 2, y);
        grad.addColorStop(0, '#00f2fe');
        grad.addColorStop(1, '#4facfe');
        ctx.fillStyle = grad;

        ctx.beginPath();
        ctx.roundRect(x - w / 2, y - h / 2, w, h, 12);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.roundRect(x - w / 4, y - h / 4, w / 2, h / 2, 6);
        ctx.fill();
        ctx.restore();
      }
    }
  }

  renderJudgements() {
    const ctx = this.ctx;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (const j of this.judgements) {
      ctx.globalAlpha = Math.max(0, j.alpha);
      ctx.font = `900 ${23 * j.scale}px Outfit, sans-serif`;
      ctx.shadowColor = j.color;
      ctx.shadowBlur = 20;
      ctx.fillStyle = j.color;
      ctx.fillText(j.text, this.width / 2, j.y);
    }
    ctx.restore();
  }

  startLoop() {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.isRunning = true;
    let lastTime = performance.now();

    const loop = (now) => {
      if (!this.isRunning || this.isPaused || this.isRewinding) {
        this.animFrameId = null;
        return;
      }
      const dt = Math.min(0.05, (now - lastTime) / 1000);
      lastTime = now;

      this.update(dt);
      this.render();

      this.animFrameId = requestAnimationFrame(loop);
    };
    this.animFrameId = requestAnimationFrame(loop);
  }

  onAudioReady() {
    console.log("Audio track ready and buffered.");
  }

  onAudioEnded() {
    console.log("Audio track finished.");
  }

  onAudioError(msg) {
    console.error("Audio error:", msg);
    this.stop();
    if (this.ui && this.ui.onAudioError) {
      this.ui.onAudioError(msg);
    }
  }
}

window.BeatstarEngine = BeatstarEngine;
window.DirectAudioSync = DirectAudioSync;
window.ParticleSystem = ParticleSystem;
window.HighFidelityAudioPlayer = HighFidelityAudioPlayer;
