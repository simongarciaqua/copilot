import React, { useState } from 'react';
import ClientSimulation from './components/ClientSimulation';
import Recommendation from './components/Recommendation';
import CustomerContext from './components/CustomerContext';
import VoiceCallWidget from './components/VoiceCallWidget';
import './App.css';

const DEFAULT_CONTEXT = {
    plan: "Ahorro",
    scoring: 3.5,
    motivo: null,
    stops_ultimo_ano: 1,
    albaran_descargado: false,
    tipo_cliente: "residencial",
    canal: "Telefono",
    // Aviso Urgente Fields
    is_delivery_day: false,
    has_pending_usual_delivery: false,
    has_pending_crm_delivery: false,
    urgent_notice_allowed_zone: true,
    next_delivery_hours: 72,
    route_type: "Normal", // Normal | Megaruta
    pending_crm_hours: 24 // Horas desde creación del albarán CRM
};

function App() {
    const [messages, setMessages] = useState([]);
    const [customerContext, setCustomerContext] = useState(DEFAULT_CONTEXT);
    const [recommendation, setRecommendation] = useState(null);
    const [rulesDecision, setRulesDecision] = useState(null);
    const [process, setProcess] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const playAudioResponse = async (text) => {
        try {
            const apiBase = import.meta.env.VITE_API_URL || '';
            const response = await fetch(`${apiBase}/api/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    // voice_id: "JBFqnCBsd6RMkjVDRZzb" // You can omit to use backend default
                })
            });
            if (response.ok) {
                const blob = await response.blob();
                const audio = new Audio(URL.createObjectURL(blob));
                audio.play();
            }
        } catch (e) {
            console.error("Audio playback error:", e);
        }
    };

    const analyzeConversation = async (messagesToAnalyze = null, contextOverride = {}) => {
        const messagesArray = messagesToAnalyze || messages;

        if (messagesArray.length === 0) {
            setError("Envía al menos un mensaje del cliente primero");
            return;
        }

        setLoading(true);
        setError(null);

        // Merge current context with overrides (e.g. force channel: 'Chat' for voice)
        const activeContext = { ...customerContext, ...contextOverride };

        try {
            const apiBase = import.meta.env.VITE_API_URL || '';
            const response = await fetch(`${apiBase}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: messagesArray,
                    customer_context: activeContext // Use the potentially overridden context
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error en el análisis');
            }

            const data = await response.json();
            setRecommendation(data.recommendation);
            setRulesDecision(data.rules_decision);
            setProcess(data.process);

            if (data.enriched_context) {
                // Determine if we should update global context or just keep it local
                setCustomerContext(data.enriched_context);
            }

            // AUTO-PLAY VOICE RESPONSE - DISABLED
            /*
            if (data.recommendation && data.recommendation.speech_sugerido) {
                console.log("Playing audio for:", data.recommendation.speech_sugerido);
                playAudioResponse(data.recommendation.speech_sugerido);
            }
            */

        } catch (err) {
            // ... error handling
            setError(err.message);
            console.error('Error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = (message, meta = {}) => {
        const newMessages = [...messages, message];
        setMessages(newMessages);

        // If message comes from voice, force 'Chat' context to get conversational speech
        const contextOverride = meta.isVoice ? { canal: 'Chat' } : {};

        analyzeConversation(newMessages, contextOverride);
    };

    const handleContextUpdate = () => {
        setMessages([]);
        setRecommendation(null);
        setRulesDecision(null);
        setProcess(null);
        setError(null);
    };

    return (
        <div className="app">
            <header className="app-header">
                <h1>🤖 Copiloto de Atención al Cliente</h1>
                <p className="tagline">Sistema de recomendaciones para agentes internos</p>
            </header>

            {error && (
                <div className="error-banner">
                    <span>⚠️ {error}</span>
                    <button onClick={() => setError(null)}>✕</button>
                </div>
            )}

            <div className="panels-container">
                <div className="panel">
                    <ClientSimulation
                        messages={messages}
                        onSendMessage={handleSendMessage}
                    />
                </div>

                <div className="panel">
                    <Recommendation
                        recommendation={recommendation}
                        loading={loading}
                        rulesDecision={rulesDecision}
                        process={process}
                    />
                </div>

                <div className="panel">
                    <CustomerContext
                        context={customerContext}
                        onContextChange={setCustomerContext}
                        onUpdate={handleContextUpdate}
                    />
                </div>
            </div>

            <footer className="app-footer">
                <p>
                    POC - Sistema Multi-Agente |
                    <span className="status">
                        {loading ? ' 🔄 Analizando...' : ' ✓ Listo'}
                    </span>
                </p>
            </footer>

            <VoiceCallWidget onSendMessage={handleSendMessage} />
        </div>
    );
}

export default App;
