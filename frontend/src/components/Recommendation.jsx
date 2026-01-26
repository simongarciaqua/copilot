import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Recommendation.css';

export default function Recommendation({ recommendation, loading, rulesDecision, process }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        if (recommendation?.speech_sugerido) {
            navigator.clipboard.writeText(recommendation.speech_sugerido);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const getReasonText = (reason) => {
        const reasonMap = {
            'reconduccion_obligatoria_previa': 'Reconducción obligatoria requerida antes de permitir stop',
            'reconduccion_obligatoria': 'El cliente debe intentar otras opciones primero',
            'ausencia_temporal': 'El cliente estará ausente temporalmente',
            'reconduccion_obligatoria': 'El cliente debe intentar otras opciones primero',
            'ausencia_temporal': 'El cliente estará ausente temporalmente',
            'scoring_alto': 'Cliente con scoring alto tiene beneficios',
            'no_rules_matched': 'No se encontraron reglas aplicables',
            // Aviso Urgente Reasons
            'es_dia_reparto': 'Hoy es día de reparto',
            'albaran_usual_pendiente': 'Ya tiene un albarán USUAL pendiente',
            'albaran_crm_pendiente': 'Ya tiene un albarán CRM pendiente',
            'albaran_crm_en_plazo': 'Albarán CRM en plazo (<= 48h)',
            'albaran_crm_retraso': 'Albarán CRM con retraso (> 48h)',
            'zona_no_permitida': 'Zona no habilitada para urgentes',
            'proximo_reparto_48h': 'Próximo reparto en < 48h',
            'cumple_requisitos': 'Cumple todos los requisitos'
        };
        return reasonMap[reason] || reason;
    };

    if (loading) {
        return (
            <div className="recommendation card">
                <h2>🎯 Recomendación al Agente</h2>
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Analizando conversación...</p>
                </div>
            </div>
        );
    }

    // Caso A: Falta información (NEED_INFO)
    if (rulesDecision?.status === 'NEED_INFO') {
        const questionData = rulesDecision.question_data;
        return (
            <div className="recommendation card status-need-info">
                <div className="status-header">
                    <span className="state-badge warning">SOLICITAR INFORMACIÓN</span>
                </div>
                <h2>❓ Falta Información Clave</h2>
                <p className="description">
                    El motor de reglas requiere más datos para poder recomendar una acción segura.
                </p>

                <div className="question-box">
                    <p className="question-label">Pregunta sugerida para el cliente:</p>
                    <p className="question-text">"{questionData?.question}"</p>

                    {questionData?.options && (
                        <div className="options-hint">
                            <p>Opciones posibles:</p>
                            <ul>
                                {questionData.options.map(opt => (
                                    <li key={opt.value}>{opt.label}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                <div className="instruction-info">
                    <p>ℹ️ Actualiza el <strong>Contexto del Cliente</strong> una vez obtengas la respuesta.</p>
                </div>
            </div>
        );
    }

    // Caso B: Charla Social o Desconocida (Smalltalk)
    if (rulesDecision?.status === 'SOCIAL' || rulesDecision?.status === 'UNKNOWN') {
        return (
            <div className="recommendation card status-social">
                <div className="status-header">
                    <span className="state-badge neutral">A LA ESCUCHA</span>
                </div>
                <h2>🧤 Conversación Social</h2>
                <div className="social-state">
                    <div className="wave">👋</div>
                    <p>El cliente está realizando una consulta social o saludo.</p>
                    <p className="hint">
                        {rulesDecision?.status === 'SOCIAL'
                            ? "El sistema no intervendrá hasta que detecte una intención de negocio."
                            : "Continúa la charla. Detectaré el proceso cuando el cliente lo solicite."}
                    </p>
                </div>
            </div>
        );
    }

    if (recommendation?.gestion_finalizada) {
        return (
            <div className="recommendation card status-success">
                <div className="status-header">
                    <span className="state-badge success">GUESTIÓN COMPLETADA (FCR)</span>
                </div>
                <h2>🏆 ¡Objetivo Conseguido!</h2>
                <div className="success-state">
                    <p className="success-msg">La gestión se ha resuelto positivamente siguiendo el manual.</p>

                    <div className="final-speech">
                        <label>📝 Speech de Cierre:</label>
                        <div className="speech-content">
                            <ReactMarkdown>{recommendation.speech_sugerido}</ReactMarkdown>
                        </div>
                    </div>

                    <div className="final-steps">
                        <label>✅ Pasos Finales en CRM:</label>
                        <div className="next-step-content success">
                            {recommendation.siguiente_paso}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!recommendation) {
        return (
            <div className="recommendation card">
                <h2>🎯 Recomendación al Agente</h2>
                <div className="empty-state">
                    <p>No hay recomendación todavía.</p>
                    <p className="hint">Envía un mensaje del cliente para obtener una recomendación.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="recommendation card">
            <h2>🎯 Recomendación al Agente</h2>

            <div className="recommendation-header">
                <h3 className="title">{recommendation.titulo}</h3>
                <span className={`badge ${getBadgeClass(recommendation.objetivo)}`}>
                    {recommendation.objetivo}
                </span>
            </div>

            <div className="info-grid">
                <div className="info-item">
                    <label>{process === 'AVISO_URGENTE' ? 'Aviso Permitido' : 'Stop Permitido'}</label>
                    <div className="stop-indicator">
                        {process === 'AVISO_URGENTE' ? (
                            // Lógica para AVISO URGENTE
                            recommendation.aviso_permitido ? (
                                <span className="status-yes">✓ Sí - Generar</span>
                            ) : (
                                <>
                                    <span className="status-no">✗ No Permitido</span>
                                    {rulesDecision?.reason && (
                                        <div className="reason-badge">
                                            {getReasonText(rulesDecision.reason)}
                                        </div>
                                    )}
                                </>
                            )
                        ) : (
                            // Lógica para STOP REPARTO
                            recommendation.stop_permitido ? (
                                <span className="status-yes">✓ Sí</span>
                            ) : rulesDecision?.decision === 'reconduccion' ? (
                                <>
                                    <span className="status-reconduction">⚠ Permitido con Reconducción</span>
                                    {rulesDecision?.reason && (
                                        <div className="reason-badge reconduction">
                                            {getReasonText(rulesDecision.reason)}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <>
                                    <span className="status-no">✗ No</span>
                                    {rulesDecision?.reason && (
                                        <div className="reason-badge">
                                            {getReasonText(rulesDecision.reason)}
                                        </div>
                                    )}
                                </>
                            )
                        )}
                    </div>
                </div>
            </div>

            <div className="speech-section">
                <div className="section-header">
                    <label>📝 Speech Sugerido</label>
                    <button
                        onClick={handleCopy}
                        className="copy-button"
                        title="Copiar al portapapeles"
                    >
                        {copied ? '✓ Copiado' : '📋 Copiar'}
                    </button>
                </div>
                <div className="speech-content">
                    <ReactMarkdown>{recommendation.speech_sugerido}</ReactMarkdown>
                </div>
            </div>

            <div className="next-step-section">
                <label>⏭️ Siguiente Paso si Rechaza</label>
                <p className="next-step-content">
                    {recommendation.siguiente_paso}
                </p>
            </div>
        </div>
    );
}

function getBadgeClass(objetivo) {
    const lower = objetivo?.toLowerCase() || '';
    if (lower.includes('reconducción') || lower.includes('reconduccion')) return 'badge-warning';
    if (lower.includes('retención') || lower.includes('retencion')) return 'badge-info';
    if (lower.includes('fcr')) return 'badge-success';
    return 'badge-info';
}
