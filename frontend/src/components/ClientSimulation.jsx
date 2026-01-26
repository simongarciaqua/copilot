
import React, { useState } from 'react';
import './ClientSimulation.css';

export default function ClientSimulation({ messages, onSendMessage }) {
    const [input, setInput] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    return (
        <div className="client-simulation card">
            <h2>💬 Cliente (Simulación)</h2>
            <p className="subtitle">Simula lo que escribe el cliente</p>

            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <p>No hay mensajes del cliente aún.</p>
                        <p className="hint">Escribe un mensaje abajo para comenzar.</p>
                    </div>
                ) : (
                    messages.map((msg, index) => (
                        <div key={index} className="message">
                            <div className="message-bubble">
                                {msg}
                            </div>
                            <div className="message-time">
                                {new Date().toLocaleTimeString('es-ES', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                        </div>
                    ))
                )}
            </div>

            <form onSubmit={handleSubmit} className="input-form">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ej: Me sobra agua y quiero parar el reparto..."
                    className="message-input"
                />
                <button type="submit" className="send-button">
                    Enviar
                </button>
            </form>
        </div>
    );
}
