// Jarvis Frontend Assistant Setup & Multi-lang initialization

function initJarvis() {
    // 1. Multi-lang Google Translate Widget Init
    const script = document.createElement("script");
    script.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    document.head.appendChild(script);

    window.googleTranslateElementInit = function () {
        new window.google.translate.TranslateElement({
            pageLanguage: 'en',
            includedLanguages: 'en,hi,ta,te,kn,ml,mr,bn,gu,pa', // Only the requested languages
            layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE
        }, 'google_translate_element');
    };

    // UI Elements
    const orb = document.createElement("div");
    orb.id = "jarvis-orb";
    orb.innerHTML = "<div class='orb-inner'>🎤</div>";

    const panel = document.createElement("div");
    panel.id = "jarvis-panel";
    panel.innerHTML = `
        <div id="google_translate_element" style="margin-bottom: 20px;"></div>
        <div class="jarvis-header">
            <strong>AGRI-JARVIS</strong>
            <button onclick="document.getElementById('jarvis-panel').classList.remove('open')">✕</button>
        </div>
        <div id="jarvis-transcript" aria-live="polite">Listening for commands... Try "zoom in"</div>
        <div id="jarvis-response"></div>
    `;

    document.body.appendChild(orb);
    document.body.appendChild(panel);

    // 2. Speech & Orb Logic
    let recognition;
    let isListening = false;

    // Feature detect
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
    } else {
        document.getElementById('jarvis-transcript').innerText = "Speech API not supported in this browser fallback.";
    }

    orb.addEventListener("click", () => {
        panel.classList.toggle("open");
        if (!recognition) return;

        if (isListening) {
            recognition.stop();
            orb.classList.remove('listening');
            isListening = false;
        } else {
            // Get current language from Google translate combo if possible, fallback to en-IN
            const langCombo = document.querySelector('.goog-te-combo');
            const lang = langCombo ? langCombo.value : 'en';
            // Map ISO 639-1 to BCP 47
            const langMap = { 'en': 'en-IN', 'hi': 'hi-IN', 'ta': 'ta-IN', 'te': 'te-IN', 'kn': 'kn-IN', 'ml': 'ml-IN', 'mr': 'mr-IN', 'bn': 'bn-IN', 'gu': 'gu-IN', 'pa': 'pa-IN' };
            recognition.lang = langMap[lang] || 'en-IN';

            recognition.start();
            orb.classList.add('listening');
            document.getElementById('jarvis-transcript').innerText = "Listening...";
            isListening = true;
        }
    });

    if (recognition) {
        recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript;
            document.getElementById('jarvis-transcript').innerText = transcript;

            if (event.results[event.results.length - 1].isFinal) {
                isListening = false;
                orb.classList.remove('listening');
                processCommand(transcript);
            }
        };
        recognition.onerror = () => {
            isListening = false;
            orb.classList.remove('listening');
            document.getElementById('jarvis-transcript').innerText = "Microphone error or stopped.";
        };
    }

    function processCommand(text) {
        const langCombo = document.querySelector('.goog-te-combo');
        const lang = langCombo ? langCombo.value : 'en';

        // Connect to FastAPI backend
        fetch("http://localhost:8000/api/assistant/chat", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, lang: lang })
        }).then(res => res.json())
            .then(data => {
                document.getElementById('jarvis-response').innerText = data.text;
                speak(data.text, lang);

                // Handle UI actions
                if (data.actions) {
                    data.actions.forEach(action => {
                        if (action.type === 'zoom_map' && window.map) {
                            window.map.zoomIn(action.level);
                        } else if (action.type === 'filter_by_risk') {
                            // Simple mock filtering text update if map handles filtering
                            document.getElementById('pac-input').value = 'High Risk View';
                        }
                    });
                }
            })
            .catch(e => {
                document.getElementById('jarvis-response').innerText = "Backend disconnected.";
            });
    }

    function speak(text, lang) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // barge-in
            const utterance = new SpeechSynthesisUtterance(text);
            const langMap = { 'en': 'en-IN', 'hi': 'hi-IN', 'ta': 'ta-IN', 'te': 'te-IN', 'kn': 'kn-IN' };
            utterance.lang = langMap[lang] || 'en-IN';
            window.speechSynthesis.speak(utterance);
        }
    }
}

// Inject styles for Orb & Multilingual
const styles = document.createElement('style');
styles.innerHTML = `
    #jarvis-orb {
        position: fixed;
        bottom: 30px;
        left: 30px; /* Instead of right to not block FAB */
        width: 60px;
        height: 60px;
        background: radial-gradient(circle, #0ea5e9, #0284c7);
        border-radius: 50%;
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.5);
        cursor: pointer;
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 24px;
        transition: all 0.3s;
    }
    #jarvis-orb.listening {
        animation: pulse-ring 1s infinite;
        background: radial-gradient(circle, #ef4444, #dc2626);
        box-shadow: 0 0 30px rgba(239, 68, 68, 0.8);
    }
    @keyframes pulse-ring {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    #jarvis-panel {
        position: fixed;
        bottom: -400px;
        left: 30px;
        width: 320px;
        background: rgba(10, 10, 10, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        z-index: 9999;
        transition: bottom 0.4s ease;
        color: white;
        font-family: var(--sans);
    }
    #jarvis-panel.open {
        bottom: 110px;
    }
    .jarvis-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
    }
    #jarvis-transcript { margin-top: 10px; font-style: italic; color: #aaa; font-size: 13px; }
    #jarvis-response { margin-top: 10px; font-weight: 500; font-size: 14px; }
    
    /* GTranslate Overrides */
    .goog-te-banner-frame, .goog-logo-link { display: none !important; }
    body { top: 0 !important; }
    .goog-te-gadget { color: transparent !important; font-size: 0px !important; }
    .goog-te-combo {
        background: #111; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 4px;
    }
    .skiptranslate.goog-te-gadget > span { display: none !important; }
`;
document.head.appendChild(styles);

// Wait for load to initialize
window.addEventListener('load', initJarvis);
