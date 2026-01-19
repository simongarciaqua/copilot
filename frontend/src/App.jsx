import React, { useState } from 'react';
import ClientSimulation from './components/ClientSimulation';
import Recommendation from './components/Recommendation';
import CustomerContext from './components/CustomerContext';
import './App.css';

const DEFAULT_CONTEXT = {
    plan: "Ahorro",
    scoring: 3.5,
    motivo: null,
    stops_ultimo_ano: 1,
    albaran_descargado: false,
    tipo_cliente: "residencial",
    canal: "Telefono"
};

function App() {
    const [messages, setMessages] = useState([]);
    const [customerContext, setCustomerContext] = useState(DEFAULT_CONTEXT);
    const [recommendation, setRecommendation] = useState(null);
    const [rulesDecision, setRulesDecision] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const analyzeConversation = async (messagesToAnalyze = null) => {
        const messagesArray = messagesToAnalyze || messages;

        if (messagesArray.length === 0) {
            setError("Envía al menos un mensaje del cliente primero");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: messagesArray,
                    customer_context: customerContext
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error en el análisis');
            }

            const data = await response.json();
            setRecommendation(data.recommendation);
            setRulesDecision(data.rules_decision);

            // AUTO-FILL: Si el backend ha extraído datos, actualizamos el contexto local
            if (data.enriched_context) {
                setCustomerContext(data.enriched_context);
            }
        } catch (err) {
            if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
                setError("No se pudo conectar con el servidor (Backend). Asegúrate de que esté ejecutándose en el puerto 8000.");
            } else {
                setError(err.message);
            }
            console.error('Error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = (message) => {
        const newMessages = [...messages, message];
        setMessages(newMessages);
        // Analyze with the new messages immediately
        analyzeConversation(newMessages);
    };

    const handleContextUpdate = () => {
        setMessages([]);
        setRecommendation(null);
        setRulesDecision(null);
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
        </div>
    );
}

export default App;
