import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Mic, Paperclip, MoreVertical, Phone, Video, Search, ArrowLeft } from 'lucide-react'

function Chat() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hi there! I'm your CTERA SDK AI Assistant. Ask me anything about the repository.", isUser: false, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMsg = { 
      id: Date.now(), 
      text: input, 
      isUser: true, 
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    }
    
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    // Create a placeholder for the AI response
    const aiMsgId = Date.now() + 1
    setMessages(prev => [...prev, { 
      id: aiMsgId, 
      text: "", 
      isUser: false, 
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    }])

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userMsg.text }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiResponseText = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            aiResponseText += chunk;

            setMessages(prev => prev.map(msg => 
                msg.id === aiMsgId ? { ...msg, text: aiResponseText } : msg
            ));
        }

    } catch (error) {
        console.error("Error fetching chat response:", error);
        setMessages(prev => prev.map(msg => 
            msg.id === aiMsgId ? { ...msg, text: "Sorry, I encountered an error while processing your request. Please make sure the COHERE_API_KEY environment variable is set in the backend." } : msg
        ));
    } finally {
        setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[600px] w-full max-w-4xl mx-auto bg-[#0b141a] rounded-2xl overflow-hidden shadow-2xl border border-white/5 font-sans">
      {/* Header */}
      <div className="bg-[#202c33] p-4 flex items-center justify-between border-b border-[#2a3942]">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-ctera-cyan to-ctera-purple p-[2px]">
             <div className="w-full h-full rounded-full bg-[#202c33] flex items-center justify-center">
               <span className="text-ctera-cyan font-bold">AI</span>
             </div>
          </div>
          <div>
            <h3 className="text-[#e9edef] font-medium">CTERA Agent</h3>
            <p className="text-[#8696a0] text-xs">online</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-[#aebac1]">
          <Video size={20} className="cursor-pointer hover:text-white transition-colors" />
          <Phone size={20} className="cursor-pointer hover:text-white transition-colors" />
          <div className="w-[1px] h-6 bg-[#2a3942]" />
          <Search size={20} className="cursor-pointer hover:text-white transition-colors" />
          <MoreVertical size={20} className="cursor-pointer hover:text-white transition-colors" />
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-[#0b141a] relative">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-[0.06]" 
             style={{ 
               backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23ffffff' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E")` 
             }} 
        />

        <div className="space-y-2 relative z-10">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 relative group shadow-sm ${
                  msg.isUser 
                    ? 'bg-[#005c4b] text-[#e9edef] rounded-tr-none' 
                    : 'bg-[#202c33] text-[#e9edef] rounded-tl-none'
                }`}
              >
                {/* Tail */}
                <div className={`absolute top-0 w-3 h-3 ${
                    msg.isUser 
                    ? '-right-2 bg-[#005c4b] [clip-path:polygon(0_0,0%_100%,100%_0)]' 
                    : '-left-2 bg-[#202c33] [clip-path:polygon(0_0,100%_0,100%_100%)]'
                }`} />
                
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words font-normal">
                    {msg.text}
                </p>
                <div className="flex items-center justify-end gap-1 mt-1 select-none">
                  <span className="text-[11px] text-[#8696a0]">{msg.timestamp}</span>
                  {msg.isUser && (
                    <span className="text-[#53bdeb]">
                        <svg viewBox="0 0 16 15" width="16" height="15" className="fill-current">
                            <path d="M15.01 3.316l-.478-.372a.365.365 0 0 0-.51.063L8.666 9.879a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l6.272-7.655a.426.426 0 0 0-.063-.51zm-3.275-.07l-.422-.506a.365.365 0 0 0-.51-.063L4.533 9.023a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l4.376-6.558a.426.426 0 0 0-.063-.51z"></path>
                        </svg>
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
          {isLoading && !messages.some(m => m.id > Date.now()) && (
             <div className="flex justify-start">
                <div className="bg-[#202c33] p-3 rounded-lg rounded-tl-none">
                    <div className="flex gap-1">
                        <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-[#202c33] p-3 flex items-end gap-4 border-t border-[#2a3942]">
        <div className="pb-3 text-[#8696a0] hover:text-white cursor-pointer transition-colors">
           <Paperclip size={24} />
        </div>
        <form onSubmit={handleSubmit} className="flex-1 bg-[#2a3942] rounded-lg flex items-center">
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message"
                className="w-full bg-transparent text-[#d1d7db] placeholder-[#8696a0] px-4 py-3 outline-none text-sm"
            />
        </form>
        <div className="pb-3">
            {input.trim() ? (
                 <button 
                 onClick={handleSubmit}
                 className="text-[#8696a0] hover:text-ctera-cyan transition-colors"
               >
                 <Send size={24} />
               </button>
            ) : (
                <button className="text-[#8696a0] hover:text-white transition-colors">
                    <Mic size={24} />
                </button>
            )}
         
        </div>
      </div>
    </div>
  )
}

export default Chat

