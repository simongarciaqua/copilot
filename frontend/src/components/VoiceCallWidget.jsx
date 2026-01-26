
import React, { useState, useEffect, useRef } from 'react';
import './VoiceCallWidget.css';

export default function VoiceCallWidget({ onSendMessage }) {
    const [isActive, setIsActive] = useState(false);
    const [status, setStatus] = useState('idle'); // idle, listening, processing, speaking
    const recognitionRef = useRef(null);

    useEffect(() => {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new window.webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'es-ES';

            recognition.onstart = () => {
                setStatus('listening');
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                setStatus('processing');
                onSendMessage(text, { isVoice: true });
                setIsActive(false); // End call cycle for this turn (or keep open if continuous?)
                // For this POC, let's close it after getting input, or reset to idle?
                // Ideally, auto-close visual state or switch to 'speaking' if we could track it.
            };

            recognition.onerror = (event) => {
                console.error("Speech error", event);
                setStatus('error');
                setTimeout(() => {
                    setIsActive(false);
                    setStatus('idle');
                }, 2000);
            };

            recognition.onend = () => {
                if (status === 'listening') {
                    setIsActive(false);
                    setStatus('idle');
                }
            };

            recognitionRef.current = recognition;
        }
    }, [onSendMessage, status]);

    const handleToggleCall = () => {
        if (!recognitionRef.current) {
            alert("Tu navegador no soporta llamadas de voz (Usa Chrome).");
            return;
        }

        if (isActive) {
            recognitionRef.current.stop();
            setIsActive(false);
            setStatus('idle');
        } else {
            setIsActive(true);
            recognitionRef.current.start();
        }
    };

    return (
        <div className={`voice-widget-container ${isActive ? 'active' : ''}`}>
            {isActive && (
                <div className="voice-status-indicator">
                    <div className="waves">
                        <span></span><span></span><span></span>
                    </div>
                    <p>
                        {status === 'listening' && "Escuchando..."}
                        {status === 'processing' && "Procesando..."}
                        {status === 'speaking' && "Hablando..."}
                        {status === 'error' && "Error de conexión"}
                    </p>
                </div>
            )}

            <button
                className={`voice-fab ${isActive ? 'active' : ''}`}
                onClick={handleToggleCall}
                title="Llamar al Agente"
            >
                {isActive ? '📞' : '☎️'}
                <span className="tooltip">Llamar al Agente</span>
            </button>
        </div>
    );
}
