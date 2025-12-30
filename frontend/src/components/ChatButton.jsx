import React, { useState } from 'react'
import { MessageCircle, Loader2 } from 'lucide-react'
import { useAuth } from '../auth/useAuth'

export default function ChatButton() {
    const { user } = useAuth()
    const [open, setOpen] = useState(false)
    const [messages, setMessages] = useState([
        { from: 'bot', text: 'Hello! Ask me about your report or request interpretation.' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    async function send() {
        if (!input.trim() || loading || !user) return

        const userMessage = { from: 'user', text: input }
        setMessages(m => [...m, userMessage])
        setInput('')
        setLoading(true)
        setError('')

        try {
            const token = await user.getIdToken()

            // Get conversation history format
            const conversationHistory = messages
                .filter(m => m.from !== 'bot' || m.text !== 'Hello! Ask me about your report or request interpretation.')
                .map(m => ({
                    role: m.from === 'bot' ? 'assistant' : 'user',
                    content: m.text
                }))

            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMessage.text,
                    user_id: user.uid,
                    conversation_history: conversationHistory,
                    report_id: 'default' // You may need to customize this
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

            setMessages(m => [...m, botMessage])

        } catch (err) {
            console.error('Chat error:', err)
            setError(err.message || 'Failed to send message')

            // Fallback message
            setMessages(m => [...m, {
                from: 'bot',
                text: 'Sorry, I encountered an error. Please try again.'
            }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="floating-chat">
            <button onClick={() => setOpen(s => !s)} style={{ background: '#0ea5a4', color: '#fff', border: 'none', padding: 12, borderRadius: 999 }}>
                <MessageCircle color="#fff" />
            </button>

            {open && (
                <div className="card" style={{ width: 320, marginTop: 8 }}>
                    <div style={{ height: 260, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {messages.map((m, i) => (
                            <div key={i} style={{ textAlign: m.from === 'bot' ? 'left' : 'right' }}>
                                <small style={{ color: '#6b7280' }}>{m.from}</small>
                                <div style={{ background: m.from === 'bot' ? '#f1f5f9' : '#e6fffa', padding: 8, borderRadius: 6 }}>{m.text}</div>
                            </div>
                        ))}
                        {loading && (
                            <div style={{ textAlign: 'left' }}>
                                <small style={{ color: '#6b7280' }}>bot</small>
                                <div style={{ background: '#f1f5f9', padding: 8, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Loader2 size={16} className="animate-spin" />
                                    Thinking...
                                </div>
                            </div>
                        )}
                        {error && (
                            <div style={{ color: '#dc2626', fontSize: 12, textAlign: 'center' }}>
                                {error}
                            </div>
                        )}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            className="input"
                            placeholder="Ask about your report..."
                            disabled={loading}
                            onKeyDown={e => e.key === 'Enter' && send()}
                        />
                        <button
                            onClick={send}
                            className="card"
                            disabled={loading || !input.trim() || !user}
                        >
                            {loading ? <Loader2 size={16} className="animate-spin" /> : 'Send'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
