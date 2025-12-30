import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, MessageCircle, Trash2, FileText, ChevronDown, Plus } from 'lucide-react'
import { useAuth } from '../auth/useAuth'
import ReactMarkdown from 'react-markdown'

export default function AIChatbot() {
    const { user } = useAuth()
    const [messages, setMessages] = useState([
        {
            from: 'bot',
            text: "Hello! I'm your AI health assistant. I can help you understand your medical reports, explain biomarkers, and answer questions about your health data. How can I assist you today?",
            timestamp: new Date().toISOString()
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    // Report selection state
    const [reports, setReports] = useState([])
    const [selectedReportId, setSelectedReportId] = useState(null)
    const [loadingReports, setLoadingReports] = useState(true)
    const [showReportSelector, setShowReportSelector] = useState(false)

    // Fetch available reports on mount
    useEffect(() => {
        if (user) {
            fetchReports()
        }
    }, [user])

    const fetchReports = async () => {
        try {
            setLoadingReports(true)
            const token = await user.getIdToken()

            const response = await fetch(`/api/LLMReportsPatientList/${user.uid}`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            if (response.ok) {
                const data = await response.json()
                setReports(data)
                // Default to latest report (first one since sorted by time desc)
                if (data.length > 0) {
                    setSelectedReportId(data[0]._id.$oid || data[0]._id)
                }
            }
        } catch (err) {
            console.error('Failed to fetch reports:', err)
        } finally {
            setLoadingReports(false)
        }
    }

    const getReportId = (report) => {
        return report._id.$oid || report._id
    }

    const formatReportDate = (timeStr) => {
        try {
            const date = new Date(timeStr)
            return date.toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            })
        } catch {
            return 'Unknown date'
        }
    }

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input on mount
    useEffect(() => {
        inputRef.current?.focus()
    }, [])

    // Convert messages to conversation history format for API
    const getConversationHistory = () => {
        return messages.map(msg => ({
            role: msg.from === 'bot' ? 'assistant' : 'user',
            content: msg.text
        }))
    }

    const sendMessage = async () => {
        if (!input.trim() || loading) return

        const userMessage = {
            from: 'user',
            text: input.trim(),
            timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)
        setError('')

        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMessage.text,
                    user_id: user.uid,
                    conversation_history: getConversationHistory(),
                    report_id: selectedReportId
                })
            })

            if (!response.ok) {
                const errorData = await response.text()
                throw new Error(errorData || 'Failed to get response')
            }

            const data = await response.json()

            const botMessage = {
                from: 'bot',
                text: data.response,
                timestamp: data.timestamp
            }

            setMessages(prev => [...prev, botMessage])
        } catch (err) {
            console.error('Chat error:', err)
            setError(err.message || 'Failed to send message. Please try again.')

            // Add error message to chat
            setMessages(prev => [
                ...prev,
                {
                    from: 'bot',
                    text: "I'm sorry, I encountered an error processing your request. Please try again.",
                    timestamp: new Date().toISOString(),
                    isError: true
                }
            ])
        } finally {
            setLoading(false)
            inputRef.current?.focus()
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    const clearConversation = () => {
        setMessages([
            {
                from: 'bot',
                text: "Hello! I'm your AI health assistant. I can help you understand your medical reports, explain biomarkers, and answer questions about your health data. How can I assist you today?",
                timestamp: new Date().toISOString()
            }
        ])
        setError('')
        setShowReportSelector(false)
    }

    const formatTime = (timestamp) => {
        try {
            return new Date(timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
            })
        } catch {
            return ''
        }
    }

    const suggestedQuestions = [
        "What does my vitamin D level mean?",
        "Explain my hemoglobin results",
        "What is a normal blood glucose range?",
        "How can I improve my biomarkers?",
        "What diet changes do you recommend?"
    ]

    const handleSuggestedQuestion = (question) => {
        setInput(question)
        inputRef.current?.focus()
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
                <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <MessageCircle size={28} color="#0ea5a4" />
                    AI Health Assistant
                </h2>
                <div style={{ display: 'flex', gap: 10 }}>
                    {/* Report Selector */}
                    <div style={{ position: 'relative' }}>
                        <button
                            onClick={() => setShowReportSelector(!showReportSelector)}
                            className="btn-secondary"
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 6,
                                minWidth: 180
                            }}
                            disabled={loadingReports}
                        >
                            <FileText size={16} />
                            {loadingReports ? (
                                'Loading...'
                            ) : selectedReportId ? (
                                <span style={{
                                    maxWidth: 120,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                }}>
                                    {reports.find(r => getReportId(r) === selectedReportId)
                                        ? formatReportDate(reports.find(r => getReportId(r) === selectedReportId).time)
                                        : 'Select Report'}
                                </span>
                            ) : (
                                'No Reports'
                            )}
                            <ChevronDown size={14} style={{ marginLeft: 'auto' }} />
                        </button>

                        {/* Dropdown */}
                        {showReportSelector && reports.length > 0 && (
                            <div
                                style={{
                                    position: 'absolute',
                                    top: '100%',
                                    right: 0,
                                    marginTop: 4,
                                    background: '#fff',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: 8,
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    zIndex: 100,
                                    minWidth: 240,
                                    maxHeight: 300,
                                    overflowY: 'auto'
                                }}
                            >
                                <div style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', fontSize: 12, color: '#64748b' }}>
                                    Select a report to chat about
                                </div>
                                {reports.map((report, idx) => (
                                    <button
                                        key={getReportId(report)}
                                        onClick={() => {
                                            setSelectedReportId(getReportId(report))
                                            setShowReportSelector(false)
                                        }}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 10,
                                            width: '100%',
                                            padding: '10px 12px',
                                            border: 'none',
                                            background: selectedReportId === getReportId(report) ? '#f0fdfa' : 'transparent',
                                            borderLeft: selectedReportId === getReportId(report) ? '3px solid #0ea5a4' : '3px solid transparent',
                                            cursor: 'pointer',
                                            textAlign: 'left',
                                            transition: 'all 0.15s ease'
                                        }}
                                        onMouseOver={(e) => {
                                            if (selectedReportId !== getReportId(report)) {
                                                e.currentTarget.style.background = '#f8fafc'
                                            }
                                        }}
                                        onMouseOut={(e) => {
                                            if (selectedReportId !== getReportId(report)) {
                                                e.currentTarget.style.background = 'transparent'
                                            }
                                        }}
                                    >
                                        <FileText size={16} color={selectedReportId === getReportId(report) ? '#0ea5a4' : '#64748b'} />
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 500, color: '#1e293b' }}>
                                                Report {idx + 1}
                                                {idx === 0 && (
                                                    <span style={{
                                                        marginLeft: 6,
                                                        fontSize: 10,
                                                        background: '#0ea5a4',
                                                        color: '#fff',
                                                        padding: '2px 6px',
                                                        borderRadius: 10
                                                    }}>
                                                        Latest
                                                    </span>
                                                )}
                                            </div>
                                            <div style={{ fontSize: 11, color: '#64748b' }}>
                                                {formatReportDate(report.time)}
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={clearConversation}
                        className="btn-secondary"
                        style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                        <Trash2 size={16} />
                        Clear Chat
                    </button>
                </div>
            </div>

            {/* No reports warning */}
            {!loadingReports && reports.length === 0 && (
                <div style={{
                    background: '#fef3c7',
                    border: '1px solid #fcd34d',
                    borderRadius: 8,
                    padding: '12px 16px',
                    marginBottom: 16,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    fontSize: 14,
                    color: '#92400e'
                }}>
                    <FileText size={18} />
                    You don't have any analyzed reports yet. Upload and analyze a report first to get personalized responses.
                </div>
            )}

            <div className="card" style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
                {/* Chat Messages Area */}
                <div
                    style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 16
                    }}
                >
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            style={{
                                display: 'flex',
                                justifyContent: msg.from === 'bot' ? 'flex-start' : 'flex-end',
                                gap: 10
                            }}
                        >
                            {msg.from === 'bot' && (
                                <div
                                    style={{
                                        width: 36,
                                        height: 36,
                                        borderRadius: '50%',
                                        background: 'linear-gradient(180deg, #0ea5a4, #059e95)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0
                                    }}
                                >
                                    <Bot size={20} color="#fff" />
                                </div>
                            )}

                            <div style={{ maxWidth: '70%' }}>
                                <div
                                    style={{
                                        background: msg.from === 'bot'
                                            ? (msg.isError ? '#fef2f2' : '#f8fafc')
                                            : 'linear-gradient(180deg, #0ea5a4, #059e95)',
                                        color: msg.from === 'bot'
                                            ? (msg.isError ? '#dc2626' : '#1e293b')
                                            : '#fff',
                                        padding: '12px 16px',
                                        borderRadius: msg.from === 'bot'
                                            ? '4px 16px 16px 16px'
                                            : '16px 4px 16px 16px',
                                        border: msg.from === 'bot' && !msg.isError ? '1px solid #e2e8f0' : 'none',
                                        lineHeight: 1.5,
                                        whiteSpace: 'pre-wrap'
                                    }}
                                >
                                    {msg.from === 'bot' ? (
                                        <div className="markdown-content">
                                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                                        </div>
                                    ) : (
                                        msg.text
                                    )}
                                </div>
                                <div
                                    style={{
                                        fontSize: 11,
                                        color: '#94a3b8',
                                        marginTop: 4,
                                        textAlign: msg.from === 'bot' ? 'left' : 'right'
                                    }}
                                >
                                    {formatTime(msg.timestamp)}
                                </div>
                            </div>

                            {msg.from === 'user' && (
                                <div
                                    style={{
                                        width: 36,
                                        height: 36,
                                        borderRadius: '50%',
                                        background: '#e2e8f0',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0
                                    }}
                                >
                                    <User size={20} color="#64748b" />
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Loading indicator */}
                    {loading && (
                        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                            <div
                                style={{
                                    width: 36,
                                    height: 36,
                                    borderRadius: '50%',
                                    background: 'linear-gradient(180deg, #0ea5a4, #059e95)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0
                                }}
                            >
                                <Bot size={20} color="#fff" />
                            </div>
                            <div
                                style={{
                                    background: '#f8fafc',
                                    padding: '12px 16px',
                                    borderRadius: '4px 16px 16px 16px',
                                    border: '1px solid #e2e8f0',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8
                                }}
                            >
                                <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                                <span style={{ color: '#64748b' }}>Thinking...</span>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Suggested Questions (show only when few messages) */}
                {messages.length <= 2 && (
                    <div style={{ padding: '0 16px 12px', borderTop: '1px solid #f1f5f9' }}>
                        <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, marginTop: 12 }}>
                            Suggested questions:
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                            {suggestedQuestions.map((question, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleSuggestedQuestion(question)}
                                    style={{
                                        background: '#f1f5f9',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: 20,
                                        padding: '6px 12px',
                                        fontSize: 13,
                                        color: '#475569',
                                        cursor: 'pointer',
                                        transition: 'all 0.15s ease'
                                    }}
                                    onMouseOver={(e) => {
                                        e.target.style.background = '#e2e8f0'
                                        e.target.style.borderColor = '#cbd5e1'
                                    }}
                                    onMouseOut={(e) => {
                                        e.target.style.background = '#f1f5f9'
                                        e.target.style.borderColor = '#e2e8f0'
                                    }}
                                >
                                    {question}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Error message */}
                {error && (
                    <div style={{
                        padding: '8px 16px',
                        background: '#fef2f2',
                        color: '#dc2626',
                        fontSize: 13,
                        borderTop: '1px solid #fecaca'
                    }}>
                        {error}
                    </div>
                )}

                {/* Input Area */}
                <div
                    style={{
                        padding: 16,
                        borderTop: '1px solid #e2e8f0',
                        background: '#fafbfc'
                    }}
                >
                    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about your health reports, biomarkers, or get health advice..."
                            className="input"
                            style={{
                                flex: 1,
                                resize: 'none',
                                minHeight: 44,
                                maxHeight: 120,
                                padding: '12px 16px',
                                fontSize: 14,
                                lineHeight: 1.4
                            }}
                            rows={1}
                            disabled={loading}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || loading}
                            style={{
                                background: input.trim() && !loading
                                    ? 'linear-gradient(180deg, #0ea5a4, #059e95)'
                                    : '#e2e8f0',
                                color: input.trim() && !loading ? '#fff' : '#94a3b8',
                                border: 'none',
                                borderRadius: 10,
                                padding: '12px 20px',
                                cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                fontWeight: 500,
                                transition: 'all 0.15s ease'
                            }}
                        >
                            {loading ? (
                                <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            ) : (
                                <Send size={18} />
                            )}
                            Send
                        </button>
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 8 }}>
                        Press Enter to send • Shift + Enter for new line
                    </div>
                </div>
            </div>

            {/* Inline styles for spinner animation */}
            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .markdown-content {
          font-size: 14px;
        }
        .markdown-content p {
          margin: 0 0 8px 0;
        }
        .markdown-content p:last-child {
          margin-bottom: 0;
        }
        .markdown-content ul, .markdown-content ol {
          margin: 8px 0;
          padding-left: 20px;
        }
        .markdown-content li {
          margin: 4px 0;
        }
        .markdown-content h1, .markdown-content h2, .markdown-content h3, 
        .markdown-content h4, .markdown-content h5, .markdown-content h6 {
          margin: 12px 0 8px 0;
          font-weight: 600;
        }
        .markdown-content h1 { font-size: 1.4em; }
        .markdown-content h2 { font-size: 1.25em; }
        .markdown-content h3 { font-size: 1.1em; }
        .markdown-content code {
          background: #e2e8f0;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 13px;
          font-family: 'Monaco', 'Menlo', monospace;
        }
        .markdown-content pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 12px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 8px 0;
        }
        .markdown-content pre code {
          background: transparent;
          padding: 0;
          color: inherit;
        }
        .markdown-content blockquote {
          border-left: 3px solid #0ea5a4;
          margin: 8px 0;
          padding-left: 12px;
          color: #64748b;
        }
        .markdown-content strong {
          font-weight: 600;
        }
        .markdown-content a {
          color: #0ea5a4;
          text-decoration: underline;
        }
        .markdown-content table {
          border-collapse: collapse;
          margin: 8px 0;
          width: 100%;
        }
        .markdown-content th, .markdown-content td {
          border: 1px solid #e2e8f0;
          padding: 8px;
          text-align: left;
        }
        .markdown-content th {
          background: #f8fafc;
          font-weight: 600;
        }
      `}</style>
        </div>
    )
}
