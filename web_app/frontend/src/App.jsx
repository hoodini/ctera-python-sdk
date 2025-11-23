import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Book, Settings, Code, Home as HomeIcon, MessageCircle } from 'lucide-react'
import DocsViewer from './components/DocsViewer'
import ConfigEditor from './components/ConfigEditor'
import ScriptBuilder from './components/ScriptBuilder'
import Home from './components/Home'
import Chat from './components/Chat'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#050B14] text-white selection:bg-ctera-cyan selection:text-ctera-navy overflow-x-hidden font-sans">
      {/* Global Ambient Lighting */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[40%] h-[40%] bg-ctera-purple/20 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[20%] w-[40%] h-[40%] bg-ctera-cyan/10 blur-[150px] rounded-full" />
      </div>

      {/* Navigation */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-500 ${scrolled ? 'bg-[#0A1628]/80 backdrop-blur-xl border-b border-white/5 py-4' : 'bg-transparent py-8'}`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <div 
            className="flex items-center gap-3 cursor-pointer group" 
            onClick={() => setActiveTab('home')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-ctera-cyan to-ctera-purple flex items-center justify-center shadow-lg shadow-ctera-cyan/20 group-hover:shadow-ctera-cyan/40 transition-all duration-300">
              <span className="font-display font-bold text-xl text-white">C</span>
            </div>
            <span className="font-display font-bold text-xl tracking-tight text-white">CTERA <span className="text-ctera-cyan">SDK</span></span>
          </div>
          
          {/* Center Tabs */}
          <div className="hidden md:flex items-center p-1.5 bg-white/5 rounded-full border border-white/10 backdrop-blur-md">
            {[
              { id: 'home', label: 'Home', icon: HomeIcon },
              { id: 'builder', label: 'Builder', icon: Code },
              { id: 'chat', label: 'Chat', icon: MessageCircle },
              { id: 'config', label: 'Config', icon: Settings },
              { id: 'docs', label: 'Docs', icon: Book },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative px-5 py-2 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                  activeTab === tab.id 
                    ? 'text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-white/10 rounded-full border border-white/10 shadow-inner"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <span className="relative z-10 flex items-center gap-2">
                  <tab.icon size={16} className={activeTab === tab.id ? 'text-ctera-cyan' : ''} />
                  {tab.label}
                </span>
              </button>
            ))}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/ctera/ctera-python-sdk" 
              target="_blank" 
              rel="noreferrer"
              className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white transition-colors"
            >
              <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.05-.015-2.055-3.33.72-4.035-1.605-4.035-1.605-.54-1.38-1.335-1.755-1.335-1.755-1.087-.735.084-.72.084-.72 1.2.075 1.83 1.23 1.83 1.23 1.065 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.475-1.335-5.475-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.225 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405 1.02 0 2.04.135 3 .405 2.295-1.56 3.3-1.23 3.3-1.23.66 1.695.24 2.925.12 3.225.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.285 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"></path></svg>
              <span>Star on GitHub</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-32 pb-20 px-6 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <AnimatePresence mode="wait">
            
            {activeTab === 'home' && (
              <motion.div
                key="home"
                initial={{ opacity: 0, filter: 'blur(10px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                exit={{ opacity: 0, filter: 'blur(10px)' }}
                transition={{ duration: 0.4 }}
              >
                <Home onChangeTab={setActiveTab} />
              </motion.div>
            )}

            {activeTab === 'docs' && (
              <motion.div
                key="docs"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                 <div className="mb-10">
                    <h2 className="text-3xl font-display font-bold mb-4">Documentation</h2>
                    <p className="text-gray-400">Comprehensive guides and API references for the Python SDK.</p>
                 </div>
                <DocsViewer />
              </motion.div>
            )}

            {activeTab === 'builder' && (
              <motion.div
                key="builder"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="h-full"
              >
                <div className="mb-10 text-center md:text-left">
                    <h2 className="text-3xl font-display font-bold mb-2">Script Builder</h2>
                    <p className="text-gray-400">Generate production-ready automation scripts instantly.</p>
                </div>
                <ScriptBuilder />
              </motion.div>
            )}

            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                <div className="mb-10 text-center md:text-left">
                    <h2 className="text-3xl font-display font-bold mb-2">AI Agent</h2>
                    <p className="text-gray-400">Chat with the CTERA SDK repository.</p>
                </div>
                <Chat />
              </motion.div>
            )}

            {activeTab === 'config' && (
              <motion.div
                key="config"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                <div className="mb-10">
                    <h2 className="text-3xl font-display font-bold mb-4">Configuration</h2>
                    <p className="text-gray-400">Manage global SDK settings.</p>
                </div>
                <ConfigEditor />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

    </div>
  )
}

export default App
