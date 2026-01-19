import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import './CustomerContext.css';

const DEFAULT_CONTEXT = {
    plan: "Ahorro",
    scoring: 3.5,
    motivo: "exceso_agua",
    stops_ultimo_ano: 1,
    albaran_descargado: false,
    tipo_cliente: "residencial",
    canal: "Telefono"
};

export default function CustomerContext({ context, onContextChange, onUpdate }) {
    const [editorValue, setEditorValue] = useState(
        JSON.stringify(context || DEFAULT_CONTEXT, null, 2)
    );
    const [error, setError] = useState(null);

    // Sincronizar el editor cuando el contexto cambia desde fuera (Auto-fill)
    React.useEffect(() => {
        setEditorValue(JSON.stringify(context, null, 2));
    }, [context]);

    const handleEditorChange = (value) => {
        setEditorValue(value);
        setError(null);

        // Try to parse and validate JSON
        try {
            const parsed = JSON.parse(value);
            onContextChange(parsed);
        } catch (e) {
            setError("JSON inválido");
        }
    };

    const handleUpdate = () => {
        try {
            const parsed = JSON.parse(editorValue);
            onContextChange(parsed);
            onUpdate();
            setError(null);
        } catch (e) {
            setError("JSON inválido. Por favor, corrige los errores antes de actualizar.");
        }
    };

    return (
        <div className="customer-context card">
            <h2>👤 Contexto del Cliente</h2>
            <p className="subtitle">Editable en tiempo real</p>

            <div className="editor-container">
                <Editor
                    height="400px"
                    defaultLanguage="json"
                    value={editorValue}
                    onChange={handleEditorChange}
                    theme="vs-light"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 13,
                        lineNumbers: 'on',
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 2,
                        formatOnPaste: true,
                        formatOnType: true
                    }}
                />
            </div>

            {error && (
                <div className="error-message">
                    ⚠️ {error}
                </div>
            )}

            <button
                onClick={handleUpdate}
                className="update-button"
                disabled={!!error}
            >
                🔄 Actualizar Contexto
            </button>

            <div className="help-section">
                <h4>📚 Campos disponibles:</h4>
                <ul>
                    <li><code>plan</code>: Plan contratado (Ahorro, Planocho)</li>
                    <li><code>scoring</code>: Puntuación del cliente (0-5)</li>
                    <li><code>motivo</code>: Motivo (exceso_agua, ausencia_vacaciones, null)</li>
                    <li><code>stops_ultimo_ano</code>: Número de stops previos</li>
                    <li><code>albaran_descargado</code>: true si es el mismo día de ruta</li>
                    <li><code>tipo_cliente</code>: residencial, residencial_user, residencial_ma</li>
                    <li><code>canal</code>: Chat o Telefono (afecta al formato del speech)</li>
                </ul>
            </div>
        </div>
    );
}
