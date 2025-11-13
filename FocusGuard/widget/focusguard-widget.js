const state = {
  isMonitoring: false,
  currentScore: 100,
  frameInterval: null,
  statsInterval: null
};
(function(window) {

// =========================================================================
// Initialization
// =========================================================================
function init(config) {
  state.config = config;
  createWidgetUI();
  startCamera();
  createSession().then((sessionId) => {
    state.sessionId = sessionId;
    updateStatus('✅ Monitoring started');
    if (config.onSessionStart) config.onSessionStart(sessionId);
    startMonitoring();
  }).catch((err) => {
    let msg = '❌ Initialization failed';
    if (err && err.message) msg += ': ' + err.message;
    updateStatus(msg);
    console.error('❌ FocusGuard: Initialization failed:', err);
  });
}

  // =========================================================================
  // Widget UI
  // =========================================================================

  function createWidgetUI() {
    const widget = document.createElement('div');
    widget.id = 'focusguard-widget';
    widget.style.cssText = `
      position: fixed;
      top: 20px;
      width: 280px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: white;
      z-index: 999999;
      transition: all 0.3s ease;
    `;

    widget.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
          🛡️ FocusGuard
        </h3>
        <button id="fg-minimize" style="
          background: rgba(255,255,255,0.2);
          border: none;
          color: white;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 16px;
          transition: background 0.2s;
        ">−</button>
      </div>
      
      <div id="fg-content">
        <div style="text-align: center; margin-bottom: 15px;">
          <div style="font-size: 48px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            <span id="fg-score">100</span>
          </div>
          <div style="font-size: 12px; opacity: 0.9; margin-top: -5px;">
            Focus Score
          </div>
        </div>

        <div style="
          background: rgba(255,255,255,0.15);
          backdrop-filter: blur(10px);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 12px;
        ">
          <div id="fg-status" style="font-size: 13px; text-align: center;">
            🔵 Initializing...
          </div>
        </div>

        <div style="
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
          font-size: 11px;
        ">
          <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-weight: bold; font-size: 16px;" id="fg-frames">0</div>
            <div style="opacity: 0.8;">Frames</div>
          </div>
          <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-weight: bold; font-size: 16px;" id="fg-duration">0:00</div>
            <div style="opacity: 0.8;">Duration</div>
          </div>
          <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; text-align: center;">
            <div style="font-weight: bold; font-size: 16px;" id="fg-alerts">0</div>
            <div style="opacity: 0.8;">Alerts</div>
          </div>
        </div>

        <button id="fg-end-session" style="
          width: 100%;
          margin-top: 15px;
          padding: 10px;
          background: rgba(255,255,255,0.2);
          border: 1px solid rgba(255,255,255,0.3);
          color: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
          transition: all 0.2s;
        " onmouseover="this.style.background='rgba(255,255,255,0.3)'" 
           onmouseout="this.style.background='rgba(255,255,255,0.2)'">
          End Session & Download Report
        </button>
      </div>
    `;

    document.body.appendChild(widget);

    // Minimize/maximize functionality
    const minimizeBtn = document.getElementById('fg-minimize');
    const content = document.getElementById('fg-content');
    let isMinimized = false;

    minimizeBtn.addEventListener('click', () => {
      isMinimized = !isMinimized;
      content.style.display = isMinimized ? 'none' : 'block';
      minimizeBtn.textContent = isMinimized ? '+' : '−';
      widget.style.width = isMinimized ? '160px' : '280px';
    });

    // End session button
    document.getElementById('fg-end-session').addEventListener('click', endSession);
  }

  // =========================================================================
  // Camera & Frame Capture
  // =========================================================================


    async function startCamera() {
        try {
            state.videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            return true;
        } catch (err) {
            updateStatus(`❌ Camera access denied: ${err.message}`);
            console.error('Camera access denied:', err);
            return false;
        }

        function captureFrame() {
            if (!state.videoStream) return null;

            const video = document.createElement('video');
            video.srcObject = state.videoStream;
            video.play();

            return new Promise((resolve) => {
                video.addEventListener('loadeddata', () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 640;
                    canvas.height = 480;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, 640, 480);
        
                    canvas.toBlob((blob) => {
                        video.srcObject = null;
                        resolve(blob);
                    }, 'image/jpeg', 0.8);
                });
            });
        }

        // =========================================================================
        // API Communication
        // =========================================================================

        ; (function (window) {
            async function createSession() {
                const response = await fetch(`${state.config.apiUrl}/api/v1/session/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        institution_id: state.config.institutionId,
                        exam_id: state.config.examId,
                        student_id: state.config.studentId,
                        metadata: state.config.metadata || {}
                    })
                });

                if (!response.ok) {
                    throw new Error(`Failed to create session: ${response.statusText}`);
                }

                const data = await response.json();
                return data.session_id;
            }

            async function analyzeFrame(frameBlob) {
                const formData = new FormData();
                formData.append('frame', frameBlob, 'frame.jpg');
                formData.append('timestamp', Date.now() / 1000);

                const response = await fetch(
                    `${state.config.apiUrl}/api/v1/session/${state.sessionId}/analyze`,
                    {
                        method: 'POST',
                        body: formData
                    }
                );

                if (!response.ok) {
                    console.error('Frame analysis failed:', response.statusText);
                    return null;
                }

                const data = await response.json();
                return data.analysis;
            }

            async function getStats() {
                const response = await fetch(
                    `${state.config.apiUrl}/api/v1/session/${state.sessionId}/stats`
                );

                if (!response.ok) {
                    console.error('Failed to get stats:', response.statusText);
                    return null;
                }

                return await response.json();
            }

            async function endSessionAPI() {
                const response = await fetch(
                    `${state.config.apiUrl}/api/v1/session/${state.sessionId}/end`,
                    { method: 'POST' }
                );

                if (!response.ok) {
                    throw new Error(`Failed to end session: ${response.statusText}`);
                }

                // Generate report
                await fetch(
                    `${state.config.apiUrl}/api/v1/session/${state.sessionId}/generate`,
                    { method: 'POST' }
                );

                return `${state.config.apiUrl}/api/v1/session/${state.sessionId}/report/download`;
            }

            // =========================================================================
            // UI Updates
            // =========================================================================

            function updateStatus(message) {
                const statusEl = document.getElementById('fg-status');
                if (statusEl) statusEl.textContent = message;
            }

            function updateScore(score) {
                const scoreEl = document.getElementById('fg-score');
                if (scoreEl) {
                    scoreEl.textContent = Math.round(score);
      
                    // Color based on score
                    if (score >= 80) {
                        scoreEl.style.color = '#4ade80';
                    } else if (score >= 60) {
                        scoreEl.style.color = '#fbbf24';
                    } else {
                        scoreEl.style.color = '#f87171';
                    }
                }

                state.currentScore = score;
    
                if (state.config.onScoreUpdate) {
                    state.config.onScoreUpdate(score);
                }
            }

            function updateStats(stats) {
                document.getElementById('fg-frames').textContent = stats.frames_processed;
    
                const duration = Math.floor(stats.duration_seconds);
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                document.getElementById('fg-duration').textContent =
                    `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
                const totalAlerts = stats.alerts.device_detected +
                    stats.alerts.voice_detected +
                    stats.alerts.person_detected;
                document.getElementById('fg-alerts').textContent = totalAlerts;
            }

            // =========================================================================
            // Monitoring Loop
            // =========================================================================

            async function startMonitoring() {
                updateStatus('📹 Capturing frames...');

                // Capture and analyze frame every 2 seconds
                state.frameInterval = setInterval(async () => {
                    if (!state.isMonitoring) return;

                    const frameBlob = await captureFrame();
                    if (!frameBlob) return;

                    const analysis = await analyzeFrame(frameBlob);
                    if (analysis) {
                        // Placeholder for analysis logic
                    }
                }, 2000);
            }

            function stopMonitoring() {
                clearInterval(state.frameInterval);
                state.frameInterval = null;
            }

            // Start the stats fetching interval
            state.statsInterval = setInterval(async () => {
                if (!state.isMonitoring) return;

                const stats = await getStats();
                if (stats) {
                    updateStats(stats);
                }
            }, 5000);

            // =========================================================================
            // Public API
            // =========================================================================

            window.FocusGuard = {
                init,
                start,
                stop,
                endSession,
                onSessionStart: null,
                onScoreUpdate: null
            };
        })(window);
    }

    window.FocusGuard = {
      init
    };
  })(window);