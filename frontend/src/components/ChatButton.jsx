import React, { useState } from 'react'
import { MessageCircle } from 'lucide-react'

export default function ChatButton(){
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    {from:'bot', text:'Hello! Ask me about your report or request interpretation.'}
  ])
  const [input, setInput] = useState('')

  function send(){
    if(!input.trim()) return
    const user = {from:'user', text:input}
    setMessages(m=>[...m, user])
    setInput('')
    // Mock bot reply (replace with API call to LLM agent)
    setTimeout(()=>{
      setMessages(m=>[...m, {from:'bot', text: 'This is a mock reply to: "'+user.text+'". Replace with real LLM integration.'}])
    },600)
  }

  return (
    <div className="floating-chat">
      <button onClick={()=>setOpen(s=>!s)} style={{background:'#0ea5a4', color:'#fff', border:'none', padding:12, borderRadius:999}}>
        <MessageCircle color="#fff" />
      </button>

      {open && (
        <div className="card" style={{width:320, marginTop:8}}>
          <div style={{height:260, overflow:'auto', display:'flex', flexDirection:'column', gap:8}}>
            {messages.map((m,i)=> (
              <div key={i} style={{textAlign: m.from==='bot'? 'left':'right'}}>
                <small style={{color:'#6b7280'}}>{m.from}</small>
                <div style={{background: m.from==='bot'? '#f1f5f9':'#e6fffa', padding:8, borderRadius:6}}>{m.text}</div>
              </div>
            ))}
          </div>
          <div style={{display:'flex', gap:8, marginTop:8}}>
            <input value={input} onChange={e=>setInput(e.target.value)} className="input" placeholder="Ask about your report..." />
            <button onClick={send} className="card">Send</button>
          </div>
        </div>
      )}
    </div>
  )
}
