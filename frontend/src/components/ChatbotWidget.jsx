import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './ChatbotWidget.css';

const ChatbotWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState(() => {
        const saved = localStorage.getItem('chatbot_history');
        return saved ? JSON.parse(saved) : [
            { type: 'bot', text: '¡Hola! Soy tu asistente administrativo mejorado. 🤖\n\nPrueba comandos como:\n• "saldo hoy" - Balance actual\n• "afiliados activos" - Estadísticas\n• "top rutas" - Rutas rentables\n• "ir a [módulo]" - Navegación rápida\n\nEscribe "ayuda" para ver todos los comandos.' }
        ];
    });
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const navigate = useNavigate();

    // Comandos disponibles para sugerencias
    const availableCommands = [
        'saldo hoy', 'balance', 'afiliados activos', 'vehículos disponibles',
        'ingresos semana', 'próximas reuniones', 'top rutas', 'sanciones',
        'viajes mañana', 'morosos', 'ayuda', 'limpiar historial',
        'ir a pagos', 'ir a afiliados', 'ir a reportes', 'ir a hojas',
        'ir a vehiculos', 'ir a sanciones'
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Guardar historial en localStorage
    useEffect(() => {
        localStorage.setItem('chatbot_history', JSON.stringify(messages));
    }, [messages]);

    // Atajo de teclado Ctrl+K
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                setIsOpen(prev => !prev);
                if (!isOpen) {
                    setTimeout(() => inputRef.current?.focus(), 100);
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);

    // Sugerencias mientras escribe
    useEffect(() => {
        if (input.length > 1) {
            const matches = availableCommands.filter(cmd =>
                cmd.toLowerCase().includes(input.toLowerCase())
            ).slice(0, 3);
            setSuggestions(matches);
        } else {
            setSuggestions([]);
        }
    }, [input]);

    const processCommand = async (command) => {
        const cmd = command.toLowerCase().trim();

        // Comandos especiales
        if (cmd === 'ayuda' || cmd === 'help') {
            return {
                type: 'bot',
                text: `📚 **Comandos Disponibles**\n\n**Consultas:**\n• saldo hoy / balance\n• afiliados activos\n• vehículos disponibles\n• ingresos semana\n• próximas reuniones\n• top rutas\n• sanciones\n• viajes mañana\n• morosos\n\n**Navegación:**\n• ir a [pagos/afiliados/reportes/hojas/vehiculos/sanciones]\n\n**Utilidades:**\n• ayuda - Esta ayuda\n• limpiar historial - Borra el chat\n\n**Atajo:** Ctrl+K para abrir/cerrar`
            };
        }

        if (cmd === 'limpiar historial' || cmd === 'limpiar') {
            localStorage.removeItem('chatbot_history');
            setMessages([{ type: 'bot', text: '✅ Historial limpiado.' }]);
            return null;
        }

        // Navegación
        const navCommands = {
            'ir a pagos': '/pagos-y-egresos',
            'ir a afiliados': '/afiliados',
            'ir a reportes': '/reportes',
            'ir a hojas': '/hojas-ruta',
            'ir a vehiculos': '/vehiculos',
            'ir a vehículos': '/vehiculos',
            'ir a sanciones': '/sanciones-asistencia'
        };

        if (navCommands[cmd]) {
            navigate(navCommands[cmd]);
            return { type: 'bot', text: `✅ Navegando a ${cmd.replace('ir a ', '')}...` };
        }

        // Consultas de datos
        try {
            setIsTyping(true);

            // Saldo/Balance
            if (cmd.includes('saldo') || cmd.includes('balance')) {
                const res = await api.getReporteFinanzas();
                const saldo = res.data.saldo_mes || 0;
                const ingresos = res.data.ingresos_mes || 0;
                const egresos = res.data.egresos_mes || 0;
                const cambio = res.data.porcentaje_cambio_ingresos || 0;
                return {
                    type: 'bot',
                    text: `💰 **Balance del Mes**\n\n📊 Saldo: Bs. ${saldo.toLocaleString()}\n💵 Ingresos: Bs. ${ingresos.toLocaleString()}\n💸 Egresos: Bs. ${egresos.toLocaleString()}\n📈 Cambio: ${cambio > 0 ? '+' : ''}${cambio}% vs mes anterior`
                };
            }

            // Afiliados activos
            if (cmd.includes('afiliado') && cmd.includes('activo')) {
                const res = await api.getReportesOperativos();
                const total = res.data?.afiliados?.total || 0;
                const activos = res.data?.afiliados?.activos || 0;
                const pasivos = res.data?.afiliados?.pasivos || 0;
                return {
                    type: 'bot',
                    text: `👥 **Afiliados**\n\n✅ Activos: ${activos}\n⏸️ Pasivos: ${pasivos}\n📊 Total: ${total}`
                };
            }

            // Vehículos disponibles
            if (cmd.includes('vehiculo') || cmd.includes('vehículo')) {
                const res = await api.getVehiculos({ page_size: 100 });
                const vehiculos = res.data?.results || res.data || [];
                const disponibles = vehiculos.filter(v => v.estado === 'activo').length;
                return {
                    type: 'bot',
                    text: `🚗 **Vehículos**\n\n✅ Disponibles: ${disponibles}\n📊 Total: ${vehiculos.length}`
                };
            }

            // Ingresos semana
            if (cmd.includes('ingreso') && cmd.includes('semana')) {
                const hoy = new Date();
                const hace7dias = new Date(hoy);
                hace7dias.setDate(hoy.getDate() - 7);
                const res = await api.getReporteFinanzas();
                const ingresos7 = res.data.ingresos_7dias || 0;
                return {
                    type: 'bot',
                    text: `💵 **Ingresos de la Semana**\n\nÚltimos 7 días: Bs. ${ingresos7.toLocaleString()}\nPromedio diario: Bs. ${(ingresos7 / 7).toFixed(2)}`
                };
            }

            // Próximas reuniones
            if (cmd.includes('reunion') || cmd.includes('reunión')) {
                const hoy = new Date().toISOString().split('T')[0];
                const res = await api.getReuniones({ fecha__gte: hoy, page_size: 5 });
                const reuniones = res.data?.results || res.data || [];
                if (reuniones.length === 0) {
                    return { type: 'bot', text: '📅 No hay reuniones programadas próximamente.' };
                }
                const lista = reuniones.map(r => `• ${r.fecha} - ${r.asunto || 'Sin asunto'}`).join('\n');
                return { type: 'bot', text: `📅 **Próximas Reuniones**\n\n${lista}` };
            }

            // Top rutas
            if (cmd.includes('top') && cmd.includes('ruta')) {
                const res = await api.getRutasRentables({ meses: 3 });
                const rutas = res.data?.rutas || [];
                if (rutas.length === 0) {
                    return { type: 'bot', text: '📍 No hay datos de rutas disponibles.' };
                }
                const top3 = rutas.slice(0, 3).map((r, i) =>
                    `${i + 1}. ${r.ruta_nombre}: Bs. ${r.ingresos_totales?.toLocaleString() || 0}`
                ).join('\n');
                return { type: 'bot', text: `🏆 **Top 3 Rutas Rentables**\n\n${top3}` };
            }

            // Sanciones
            if (cmd.includes('sancion')) {
                const res = await api.getSanciones({ estado: 'pendiente', page_size: 5 });
                const sanciones = res.data?.results || res.data || [];
                if (sanciones.length === 0) {
                    return { type: 'bot', text: '✅ No hay sanciones pendientes.' };
                }
                const lista = sanciones.map(s => `• ${s.afiliado_nombre}: Bs. ${s.monto}`).join('\n');
                return { type: 'bot', text: `⚠️ **Sanciones Pendientes** (${sanciones.length}):\n\n${lista}` };
            }

            // Viajes mañana
            if (cmd.includes('viaje') || cmd.includes('hoja')) {
                const hoy = new Date();
                const manana = new Date(hoy);
                manana.setDate(hoy.getDate() + 1);
                const fechaStr = manana.toISOString().split('T')[0];
                const res = await api.getHojasRuta({ fecha_emision: fechaStr, page_size: 10 });
                const hojas = res.data?.results || res.data || [];
                if (hojas.length === 0) {
                    return { type: 'bot', text: '📋 No hay viajes programados para mañana.' };
                }
                return { type: 'bot', text: `🚌 **Viajes Mañana**: ${hojas.length} hojas de ruta programadas.` };
            }

            // Morosos
            if (cmd.includes('moros') || cmd.includes('deud')) {
                const res = await api.getAfiliadosMorosos({ page_size: 5 });
                const morosos = res.data?.morosos || [];
                if (morosos.length === 0) {
                    return { type: 'bot', text: '✅ No hay afiliados morosos críticos.' };
                }
                const lista = morosos.slice(0, 3).map(m => `• ${m.afiliado}: Bs. ${m.total_deuda}`).join('\n');
                return { type: 'bot', text: `🚨 **Morosos Críticos**:\n\n${lista}` };
            }

            return {
                type: 'bot',
                text: '🤔 No entendí tu consulta. Escribe "ayuda" para ver todos los comandos disponibles.'
            };

        } catch (error) {
            console.error('Error en chatbot:', error);
            return { type: 'bot', text: '❌ Error al procesar tu consulta. Intenta de nuevo.' };
        } finally {
            setIsTyping(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { type: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setSuggestions([]);

        const response = await processCommand(currentInput);
        if (response) {
            setTimeout(() => {
                setMessages(prev => [...prev, response]);
            }, 500);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInput(suggestion);
        setSuggestions([]);
        inputRef.current?.focus();
    };

    return (
        <>
            {/* Burbuja flotante */}
            {!isOpen && (
                <button
                    className="chatbot-bubble"
                    onClick={() => {
                        setIsOpen(true);
                        setTimeout(() => inputRef.current?.focus(), 100);
                    }}
                    title="Asistente Virtual (Ctrl+K)"
                >
                    💬
                    <span className="chatbot-badge">AI</span>
                </button>
            )}

            {/* Modal del chat */}
            {isOpen && (
                <div className="chatbot-modal">
                    <div className="chatbot-header">
                        <div className="chatbot-title">
                            <span className="chatbot-icon">🤖</span>
                            <div>
                                <span>Asistente Administrativo</span>
                                <small style={{ display: 'block', fontSize: '0.7rem', opacity: 0.8 }}>Ctrl+K para cerrar</small>
                            </div>
                        </div>
                        <button className="chatbot-close" onClick={() => setIsOpen(false)}>✕</button>
                    </div>

                    <div className="chatbot-messages">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`chatbot-message ${msg.type}`}>
                                <div className="message-bubble">
                                    {msg.text.split('\n').map((line, i) => (
                                        <p key={i}>{line}</p>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {isTyping && (
                            <div className="chatbot-message bot">
                                <div className="message-bubble typing">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Sugerencias */}
                    {suggestions.length > 0 && (
                        <div className="chatbot-suggestions">
                            {suggestions.map((sug, idx) => (
                                <button
                                    key={idx}
                                    className="suggestion-chip"
                                    onClick={() => handleSuggestionClick(sug)}
                                >
                                    {sug}
                                </button>
                            ))}
                        </div>
                    )}

                    <div className="chatbot-input-container">
                        <input
                            ref={inputRef}
                            type="text"
                            className="chatbot-input"
                            placeholder="Escribe tu consulta o 'ayuda'..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                        />
                        <button className="chatbot-send" onClick={handleSend}>
                            ➤
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default ChatbotWidget;
