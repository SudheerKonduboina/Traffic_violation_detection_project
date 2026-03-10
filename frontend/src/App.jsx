import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Shield, User, Eye, Settings, AlertTriangle, CheckCircle, XCircle,
  BarChart3, Camera, Moon, Sun, ChevronRight, CreditCard,
  Bike, ChevronDown, Clock, Zap, Bot, Maximize, RefreshCw, LogOut,
  Star, MessageSquare, Send, X, ClipboardList, ArrowLeft
} from 'lucide-react';

/**
 * AI-Based Traffic Violation Monitoring Using AI
 * FINALIZED VERSION - Total Violations: 7
 * Fix: Updated project title & justified Officer Review buttons.
 * Region: Andhra Pradesh (AP)
 */

// ==========================================
// 1. SHARED DATA & COMPONENTS
// ==========================================
const API_BASE = 'http://localhost:8000';

const StatusBadge = ({ status, payment }) => {
  if (payment === 'Paid') return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">Paid</span>;
  const styles = { 'Approved': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', 'Under Review': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', 'Declined': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' };
  return <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-700'}`}>{status}</span>;
};

const Card = ({ children, className = "", onClick = null }) => (
  <div onClick={onClick} className={`bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm transition-all ${onClick ? 'cursor-pointer hover:shadow-md hover:-translate-y-1 active:scale-[0.98]' : ''} ${className}`}>{children}</div>
);

// --- Feedback Submission Modal ---
const FeedbackModal = ({ onClose, user, onSave }) => {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ id: Date.now(), user: user.id, role: user.role, rating, comment: feedback, date: new Date().toLocaleString() });
    setSubmitted(true);
    setTimeout(onClose, 2000);
  };

  if (submitted) {
    return (
      <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
        <Card className="p-8 max-w-sm w-full text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} />
          </div>
          <h3 className="text-xl font-black text-slate-950 dark:text-white mb-2 uppercase tracking-tighter tracking-widest">Success</h3>
          <p className="text-slate-500 text-sm italic text-nowrap">Feedback successfully logged.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
      <Card className="p-0 max-w-md w-full overflow-hidden shadow-2xl ring-1 ring-slate-200 dark:ring-slate-700">
        <div className="bg-indigo-600 p-6 text-white flex justify-between items-center">
          <div className="flex items-center gap-3 text-white">
            <MessageSquare size={24} />
            <div><h3 className="font-black uppercase tracking-tight leading-none text-white font-sans">System Feedback</h3><p className="text-[10px] text-white/70 mt-1 uppercase font-bold tracking-widest">ID: {user.id}</p></div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-full transition-colors cursor-pointer"><X size={20} className="text-white" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 font-sans">Rate Overall System</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button key={star} type="button" onClick={() => setRating(star)} onMouseEnter={() => setHover(star)} onMouseLeave={() => setHover(0)} className="transition-transform active:scale-90 cursor-pointer">
                  <Star size={32} className={`${(hover || rating) >= star ? 'fill-amber-400 text-amber-400' : 'text-slate-300 dark:text-slate-600'}`} />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 font-sans">Detailed Comments</label>
            <textarea required value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="Share your experience..." className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 min-h-[120px] text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-950 dark:text-white font-sans" />
          </div>
          <button type="submit" disabled={!rating} className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-black uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer font-sans">
            <Send size={18} /> Send Feedback
          </button>
        </form>
      </Card>
    </div>
  );
};

// --- AI Detection Feed Modal ---
const DetectionCameraModal = ({ onClose }) => {
  const [ocrLogs, setOcrLogs] = useState(["[SYSTEM] AI Engine Initialized...", "[SYSTEM] Loading YOLOv8 Weights..."]);
  useEffect(() => {
    const logs = ["AP12 AB 1234", "AP14 XY 9009", "AP12 KL 5566", "AP09 CD 7788", "AP12 PQ 1122"];
    const interval = setInterval(() => { setOcrLogs(prev => [`[OCR] Detected Plate: ${logs[Math.floor(Math.random() * logs.length)]}`, ...prev].slice(0, 10)); }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-8 bg-slate-900/90 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-black w-full max-w-5xl rounded-3xl border border-slate-700 shadow-2xl overflow-hidden flex flex-col md:flex-row h-full max-h-[700px]">
        <div className="flex-1 relative bg-slate-950 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center z-10 bg-gradient-to-b from-black/80 to-transparent">
            <div className="flex items-center gap-2 text-white">
              <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
              <span className="font-mono text-xs font-bold uppercase tracking-widest">LIVE AI FEED: Vizag_CAM_01</span>
            </div>
          </div>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="absolute border-2 border-red-500 w-32 h-32 rounded-sm" style={{ top: '30%', left: '25%' }}><div className="absolute -top-6 left-0 bg-red-500 text-white text-[10px] px-1 font-bold uppercase">VIOLATION: NO_HELMET</div></div>
            <div className="absolute border-2 border-green-500 w-48 h-32 rounded-sm" style={{ top: '55%', left: '50%' }}><div className="absolute -top-6 left-0 bg-green-500 text-white text-[10px] px-1 font-bold uppercase">VEHICLE: TWO_WHEELER</div></div>
            <div className="w-full h-1 bg-indigo-500/30 absolute top-1/2 animate-bounce blur-sm shadow-[0_0_15px_rgba(99,102,241,0.5)]" />
          </div>
          <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center z-10">
            <div className="flex gap-2">
              <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors cursor-pointer"><Maximize size={18} /></button>
              <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors cursor-pointer"><RefreshCw size={18} /></button>
            </div>
            <button onClick={onClose} className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold uppercase tracking-widest transition-all cursor-pointer">Stop Detection</button>
          </div>
        </div>
        <div className="w-full md:w-80 bg-slate-900 border-l border-slate-700 flex flex-col">
          <div className="p-4 border-b border-slate-800 bg-slate-800/50"><h4 className="text-white font-bold text-sm flex items-center gap-2 uppercase tracking-tighter font-black"><Bot size={16} className="text-indigo-400" /> AI LIVE LOGS</h4></div>
          <div className="flex-1 p-4 font-mono text-[10px] overflow-y-auto space-y-2 bg-black/30">{ocrLogs.map((log, i) => (<div key={i} className={`p-1.5 rounded ${log.includes('Detected') ? 'bg-indigo-900/30 text-indigo-300' : 'text-slate-500'}`}>{log}</div>))}</div>
          <div className="p-4 border-t border-slate-800 bg-slate-900 text-white"><div className="p-3 bg-indigo-600/10 border border-indigo-500/30 rounded-xl"><p className="text-indigo-400 font-bold text-[10px] uppercase mb-1">OCR ACTIVE BUFFER</p><p className="text-lg font-mono font-black tracking-widest uppercase">AP12 AB 1234</p></div></div>
        </div>
      </div>
    </div>
  );
};

// --- Login Page ---
const LoginPage = ({ onLogin, isDarkMode, toggleDarkMode }) => {
  const [role, setRole] = useState('user');
  const [id, setId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!id || !password) return;

    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: id, password })
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      onLogin({
        role: data.role.toLowerCase(),
        id: data.user_id,
        name: data.full_name,
        rawRole: data.role
      });
    } catch (err) {
      setError("Invalid credentials. Try generic ones for demo (e.g. admin@test.com)");
    }
  };
  const roleConfigs = { user: { title: 'User Login', icon: Bike, label: 'Vehicle Number', placeholder: 'e.g. AP12 AB 1234' }, officer: { title: 'Officer Login', icon: Shield, label: 'Officer ID', placeholder: 'e.g. POL-8821' }, admin: { title: 'Admin Login', icon: Settings, label: 'Admin ID / Email', placeholder: 'e.g. admin@traffic.gov' } };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950 p-6 transition-colors duration-300 font-sans">
      <button onClick={toggleDarkMode} className="absolute top-8 right-8 p-3 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 shadow-sm hover:shadow-md transition-all cursor-pointer">{isDarkMode ? <Sun size={20} className="text-amber-500" /> : <Moon size={20} className="text-indigo-500" />}</button>
      <div className="w-full max-w-xl">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-white font-black text-2xl mx-auto mb-4 shadow-xl shadow-indigo-600/20"><Bot size={32} /></div>
          {/* UPDATED PROJECT TITLE */}
          <h1 className="text-3xl font-black text-slate-950 dark:text-white tracking-tight uppercase">Traffic Violation Monitoring Using AI</h1>
          <p className="text-slate-600 text-sm mt-1 uppercase font-bold tracking-widest opacity-70">Automated AI-Based Law Enforcement</p>
        </div>
        <Card className="p-8 max-w-md mx-auto">
          <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl mb-8">
            {['user', 'officer', 'admin'].map((r) => (
              <button key={r} onClick={() => setRole(r)} className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all cursor-pointer ${role === r ? 'bg-white dark:bg-slate-800 text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}>{r}</button>
            ))}
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <h2 className="text-lg font-bold text-slate-950 dark:text-white flex items-center gap-2 uppercase tracking-tighter font-black">{React.createElement(roleConfigs[role].icon, { size: 20, className: "text-indigo-600" })}{roleConfigs[role].title}</h2>
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 font-black">Login Credentials</label>
              <div className="relative"><input type="text" required placeholder={roleConfigs[role].placeholder} className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm text-slate-950 dark:text-white uppercase font-mono tracking-widest" value={id} onChange={(e) => setId(e.target.value)} /></div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 font-black">Password</label>
              <div className="relative"><input type="password" required placeholder="••••••••" className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm text-slate-950 dark:text-white" value={password} onChange={(e) => setPassword(e.target.value)} /></div>
            </div>
            {error && <p className="text-red-500 text-xs font-bold font-sans">{error}</p>}
            <button type="submit" className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black uppercase tracking-widest text-xs shadow-lg shadow-indigo-600/20 transition-all cursor-pointer flex items-center justify-center gap-2">
              Sign In <ChevronRight size={18} />
            </button>
          </form>
        </Card>
      </div>
    </div>
  );
};

// --- Admin Dashboard (Integrated Actions Grid) ---
const AdminDashboard = ({ user, feedbacks }) => {
  const [listType, setListType] = useState('AI');
  const [showDetection, setShowDetection] = useState(false);
  const [showFeedbackList, setShowFeedbackList] = useState(false);

  const [stats, setStats] = useState({ ai: 0, officer: 0, total: 0 });
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const headers = { 'X-Role': user.rawRole, 'X-User-Id': user.id };
        const [statsRes, violRes] = await Promise.all([
          fetch(`${API_BASE}/admin/dashboard`, { headers }),
          fetch(`${API_BASE}/violations`, { headers })
        ]);

        if (statsRes.ok && violRes.ok) {
          const statsData = await statsRes.json();
          const violData = await violRes.json();

          setStats({
            ai: statsData.approved_challans, // simplify for demo
            officer: statsData.pending_review,
            total: statsData.total_violations
          });
          setViolations(violData);
        }
      } catch (err) {
        console.error("Failed to fetch admin dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [user]);

  const filteredViolations = useMemo(() => {
    // Basic filter for demo purposes
    return violations.filter(v => listType === 'AI' ? !v.is_uncertain : v.is_uncertain).slice(0, 5);
  }, [listType, violations]);

  const counts = stats;

  if (showFeedbackList) {
    return (
      <div className="space-y-6 font-sans">
        <div className="flex justify-between items-center">
          <button onClick={() => setShowFeedbackList(false)} className="flex items-center gap-2 text-slate-500 hover:text-indigo-600 font-black uppercase tracking-widest text-[10px] transition-colors cursor-pointer border border-slate-200 dark:border-slate-700 px-3 py-2 rounded-lg bg-white dark:bg-slate-800"><ArrowLeft size={14} /> Back to Dashboard</button>
          <div className="text-right"><h2 className="text-2xl font-black text-slate-950 dark:text-white uppercase tracking-tight font-sans">System Feedback Forms</h2><p className="text-slate-600 text-sm italic font-black uppercase tracking-widest">"Reviewing submitted entries"</p></div>
        </div>
        <Card className="overflow-hidden border-2 border-indigo-500/10 shadow-xl">
          <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center"><h3 className="font-bold text-slate-950 dark:text-white flex items-center gap-2 uppercase tracking-widest text-xs font-sans font-black"><MessageSquare size={16} className="text-indigo-600" /> FEEDBACK RECORDS</h3></div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-100/50 dark:bg-slate-900/50 text-slate-500 text-[10px] font-black uppercase tracking-widest"><tr><th className="px-6 py-4">ID/PLATE</th><th className="px-6 py-4 text-center">ROLE</th><th className="px-6 py-4">RATING</th><th className="px-6 py-4">COMMENTS</th><th className="px-6 py-4 text-right">DATE</th></tr></thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {feedbacks.length === 0 ? (<tr><td colSpan="5" className="px-6 py-24 text-center text-slate-400 italic font-black uppercase tracking-tighter">No feedback entries found. User/Officer feedback will appear here once submitted.</td></tr>) : (
                  feedbacks.map((f) => (
                    <tr key={f.id} className="text-sm hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                      <td className="px-6 py-4 font-mono font-black text-indigo-600 uppercase tracking-widest">{f.user}</td>
                      <td className="px-6 py-4 text-center"><span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tighter ${f.role === 'officer' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'}`}>{f.role}</span></td>
                      <td className="px-6 py-4"><div className="flex gap-0.5 text-amber-400">{[...Array(f.rating)].map((_, i) => <Star key={i} size={14} className="fill-current" />)}</div></td>
                      <td className="px-6 py-4 text-slate-900 dark:text-slate-300 max-w-xs">{f.comment}</td>
                      <td className="px-6 py-4 text-right text-[10px] text-slate-400 font-mono tracking-tighter uppercase font-black">{f.date}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8 font-sans">
      {showDetection && <DetectionCameraModal onClose={() => setShowDetection(false)} />}

      <div>
        <h2 className="text-2xl font-black text-slate-950 dark:text-white uppercase font-mono tracking-tight text-indigo-600 dark:text-indigo-400">Admin ID: {user.id}</h2>
        <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">Global System Monitoring Dashboard</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* 1. AI APPROVED STAT */}
        <Card onClick={() => setListType('AI')} className={`p-8 border-b-4 cursor-pointer transition-all hover:scale-[1.02] ${listType === 'AI' ? 'border-b-indigo-600 ring-2 ring-indigo-500/20 bg-indigo-50/10' : 'border-b-indigo-400 shadow-lg shadow-indigo-600/5'}`}>
          <div className="flex items-center gap-6">
            <div className={`p-4 rounded-xl transition-colors ${listType === 'AI' ? 'bg-indigo-600 text-white' : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600'}`}><Zap size={32} /></div>
            <div>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 font-black">AI APPROVED</p>
              <h3 className="text-3xl font-black text-slate-950 dark:text-white leading-none">0{counts.ai}</h3>
            </div>
          </div>
        </Card>

        {/* 2. AI DETECTION ACTION */}
        <Card onClick={() => setShowDetection(true)} className="p-8 border-b-4 border-b-indigo-600 bg-white dark:bg-slate-800 cursor-pointer transition-all hover:scale-[1.02] shadow-xl hover:ring-4 ring-indigo-500/10">
          <div className="flex items-center gap-6">
            <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 rounded-xl"><Camera size={32} /></div>
            <div>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 font-black">SYSTEM ACTION</p>
              <h3 className="text-2xl font-black uppercase leading-none text-nowrap text-slate-950 dark:text-white">AI DETECTION</h3>
            </div>
          </div>
        </Card>

        {/* 3. OFFICER APPROVED STAT */}
        <Card onClick={() => setListType('OFFICER')} className={`p-8 border-b-4 cursor-pointer transition-all hover:scale-[1.02] ${listType === 'OFFICER' ? 'border-b-blue-600 ring-2 ring-blue-500/20 bg-blue-50/10' : 'border-b-blue-400 shadow-lg shadow-blue-600/5'}`}>
          <div className="flex items-center gap-6">
            <div className={`p-4 rounded-xl transition-colors ${listType === 'OFFICER' ? 'bg-blue-600 text-white' : 'bg-indigo-900/30 text-blue-600'}`}><Shield size={32} /></div>
            <div>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 font-black">OFFICER APPROVED</p>
              <h3 className="text-3xl font-black text-slate-950 dark:text-white leading-none">0{counts.officer}</h3>
            </div>
          </div>
        </Card>

        {/* 4. TODAY TOTAL VIOLATIONS */}
        <Card className="p-8 border-b-4 border-b-green-500 transition-all hover:scale-[1.02] shadow-lg shadow-green-600/5">
          <div className="flex items-center gap-6">
            <div className="p-4 bg-green-50 dark:bg-green-900/30 text-green-600 rounded-xl"><BarChart3 size={32} /></div>
            <div>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 text-nowrap font-black">TOTAL VIOLATIONS</p>
              <h3 className="text-3xl font-black text-slate-950 dark:text-white leading-none text-nowrap">{counts.total}</h3>
            </div>
          </div>
        </Card>

        {/* 5. ACTIVE AI CAMERAS */}
        <Card className="p-8 border-b-4 border-b-amber-500 transition-all hover:scale-[1.02] shadow-lg shadow-amber-600/5">
          <div className="flex items-center gap-6">
            <div className="p-4 bg-amber-50 dark:bg-amber-900/30 text-amber-600 rounded-xl"><Bot size={32} /></div>
            <div>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 text-nowrap font-black">ACTIVE CAMERAS</p>
              <h3 className="text-3xl font-black text-slate-950 dark:text-white leading-none text-nowrap font-sans">48 / 50</h3>
            </div>
          </div>
        </Card>

        {/* 6. FEEDBACK FORMS ACTION */}
        <Card onClick={() => setShowFeedbackList(true)} className="p-8 border-b-4 border-b-slate-700 bg-white dark:bg-slate-800 cursor-pointer transition-all hover:scale-[1.02] shadow-xl hover:ring-4 ring-slate-500/10 font-sans">
          <div className="flex items-center gap-6 font-sans">
            <div className="p-4 bg-slate-50 dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 rounded-xl font-sans"><ClipboardList size={32} /></div>
            <div className="font-sans">
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1 font-sans font-black">ADMIN ACTION</p>
              <h3 className="text-2xl font-black uppercase leading-none text-nowrap text-slate-950 dark:text-white font-sans">FEEDBACK FORMS</h3>
            </div>
          </div>
        </Card>

      </div>

      <Card className="overflow-hidden border-2 border-indigo-500/10 shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex justify-between bg-slate-50 dark:bg-slate-800/50 items-center font-sans">
          <h3 className="font-black text-slate-950 dark:text-white flex items-center gap-2 uppercase tracking-tight font-sans">
            {listType === 'AI' ? <Zap size={18} className="text-indigo-600" /> : <Shield size={18} className="text-blue-600" />}
            LATEST {listType === 'AI' ? 'AI' : 'OFFICER'} APPROVED VIOLATIONS
          </h3>
        </div>
        <div className="p-0 overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-100/50 dark:bg-slate-900/50 text-slate-500 text-[10px] font-black uppercase tracking-widest">
              <tr><th className="px-6 py-4">CHALLAN ID</th><th className="px-6 py-4 text-nowrap">VIOLATION TYPE</th><th className="px-6 py-4 text-nowrap text-indigo-500">AP PLATE NUMBER</th><th className="px-6 py-4 text-right">CONFIDENCE</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {loading ? (
                <tr><td colSpan="4" className="px-6 py-8 text-center text-slate-500 text-xs">Loading data...</td></tr>
              ) : filteredViolations.length === 0 ? (
                <tr><td colSpan="4" className="px-6 py-8 text-center text-slate-500 text-xs">No violations found</td></tr>
              ) : filteredViolations.map((v) => (
                <tr key={v.id} className="text-sm hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                  <td className="px-6 py-4 font-mono text-xs font-black text-slate-950 dark:text-slate-400 group-hover:text-indigo-600 uppercase tracking-widest">{v.id.split('-')[0]}</td>
                  <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">{v.violation_type}</td>
                  <td className="px-6 py-4 font-mono uppercase text-indigo-600 dark:text-indigo-400 font-black tracking-widest">{v.plate_text_norm || 'UNKNOWN'}</td>
                  <td className="px-6 py-4 text-right text-xs font-bold text-green-600 font-black">{Math.round(v.detection_confidence * 100)}% AI</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

// --- Officer Module ---
const OfficerReviewModule = ({ user }) => {
  const [selectedChallan, setSelectedChallan] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API_BASE}/officer/review-queue`, {
        headers: { 'X-Role': user.rawRole, 'X-User-Id': user.id }
      });
      if (res.ok) setReviews(await res.json());
    } catch (err) {
      console.error("Failed to load queue", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [user]);

  const handleAction = async (challanId, action) => {
    try {
      const res = await fetch(`${API_BASE}/officer/challans/${challanId}/${action}`, {
        method: 'POST',
        headers: { 'X-Role': user.rawRole, 'X-User-Id': user.id }
      });
      if (res.ok) {
        setReviews(prev => prev.filter(r => r.challan_id !== challanId));
        if (selectedChallan?.challan_id === challanId) setSelectedChallan(null);
      }
    } catch (err) {
      console.error(`Failed to ${action} challan`, err);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex justify-between items-center"><div><h2 className="text-2xl font-black text-slate-950 dark:text-white uppercase font-mono tracking-tight text-indigo-600 dark:text-indigo-400 font-sans">Officer ID: {user.id}</h2><p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">Verify AI-flagged uncertain cases</p></div><div className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider">{reviews.length} Pending Cases</div></div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden h-[600px] flex flex-col bg-white dark:bg-slate-800">
          <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 z-10 sticky top-0"><h3 className="font-black text-xs uppercase tracking-widest">Review Queue</h3></div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans">
            {loading ? <p className="text-center text-xs text-slate-400">Loading queue...</p> : reviews.length === 0 ? <p className="text-center text-xs text-slate-400">No pending reviews</p> : reviews.map(item => (<Card key={item.challan_id} className={`p-4 cursor-pointer transition-all ${selectedChallan?.challan_id === item.challan_id ? 'ring-2 ring-indigo-500 bg-indigo-50 dark:bg-indigo-900/10' : 'hover:bg-slate-50 dark:hover:bg-slate-700/50 font-sans'}`} onClick={() => setSelectedChallan(item)}><div className="flex justify-between items-start mb-2"><p className="text-xs font-mono text-slate-500 uppercase tracking-widest">{item.challan_id.split('-')[0]}</p><span className="text-xs font-bold text-indigo-600 bg-white dark:bg-slate-800 px-1.5 rounded">{Math.round(item.detection_confidence * 100)}% Conf.</span></div><p className="font-black text-slate-950 dark:text-white uppercase tracking-tighter">{item.violation_type}</p><p className="text-[10px] text-slate-600 mt-1 font-mono uppercase tracking-widest">{item.plate_text_norm || 'UNKNOWN'}</p></Card>))}
          </div>
        </div>
        <div className="lg:col-span-2 font-sans">{selectedChallan ? (
          <Card className="p-6 shadow-xl border-2 border-indigo-500/10 font-sans"><div className="flex justify-between items-start mb-6 font-sans"><div><h3 className="text-xl font-black text-slate-950 dark:text-white uppercase tracking-tight">{selectedChallan.violation_type}</h3><p className="text-slate-600 text-xs font-mono uppercase tracking-widest font-black">{new Date(selectedChallan.occurred_at).toLocaleString()} • VIZAG CAM-02</p></div><div className="text-right"><p className="text-[10px] text-slate-400 font-black uppercase tracking-widest leading-none">AI Confidence</p><p className="text-3xl font-black text-amber-500">{Math.round(selectedChallan.detection_confidence * 100)}%</p></div></div><div className="relative aspect-video bg-slate-900 rounded-xl overflow-hidden mb-6 flex items-center justify-center text-slate-500 border border-slate-200 dark:border-slate-700 font-black uppercase tracking-widest text-[10px] font-sans">[ AI EVIDENCE CAPTURE: {selectedChallan.plate_text_norm || 'UNKNOWN'} ]</div><div className="flex gap-4 font-sans">
            {/* JUSTIFIED ACTION BUTTONS */}
            <button onClick={() => handleAction(selectedChallan.challan_id, 'decline')} className="flex-1 py-4 bg-red-100 hover:bg-red-200 text-red-700 rounded-xl font-black uppercase tracking-widest text-xs transition-all cursor-pointer flex items-center justify-center gap-2"><XCircle size={18} /> Decline</button>
            <button onClick={() => handleAction(selectedChallan.challan_id, 'approve')} className="flex-1 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-black uppercase tracking-widest text-xs transition-all cursor-pointer flex items-center justify-center gap-2"><CheckCircle size={18} /> Approve</button>
          </div></Card>) : (<div className="h-[600px] border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl flex items-center justify-center text-slate-400 font-sans"><div className="text-center font-sans"><Eye size={48} className="mx-auto mb-4 opacity-20 font-sans" /><p className="font-black uppercase tracking-widest text-xs font-sans">Select a case for review</p></div></div>)}</div>
      </div>
    </div>
  );
};

// --- User Module ---
const UserDashboard = ({ user }) => {
  const [activeFilter, setActiveFilter] = useState('Paid');
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(null);
  const [challans, setChallans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchChallans = async () => {
      try {
        const res = await fetch(`${API_BASE}/user/challans`, {
          headers: { 'X-Role': user.rawRole, 'X-User-Id': user.id }
        });
        if (res.ok) setChallans(await res.json());
      } catch (err) {
        console.error("Failed to load user challans", err);
      } finally {
        setLoading(false);
      }
    };
    fetchChallans();
  }, [user]);

  // For demo, distribute statuses since backend currently only returns actual "amount" and "due_date" as 0/None.
  // In a real app, `v.status` and `v.amount` would drive this. Let's mock the "payment" state randomly for UI display.
  const mappedChallans = useMemo(() => {
    return challans.map(c => ({
      ...c,
      payment: c.challan_id.charCodeAt(0) % 2 === 0 ? 'Paid' : 'Unpaid' // pseudo-random split
    }));
  }, [challans]);

  const filteredList = useMemo(() => {
    return mappedChallans.filter(v => {
      if (activeFilter === 'Paid') return v.payment === 'Paid';
      if (activeFilter === 'Unpaid') return v.payment === 'Unpaid';
      if (activeFilter === 'Pending') return v.status === 'Under Review';
      return false;
    });
  }, [activeFilter, mappedChallans]);

  const getCount = (type) => {
    if (type === 'Paid') return mappedChallans.filter(v => v.payment === 'Paid').length;
    if (type === 'Unpaid') return mappedChallans.filter(v => v.payment === 'Unpaid').length;
    if (type === 'Pending') return mappedChallans.filter(v => v.status === 'Under Review').length;
    return 0;
  };

  const handlePayment = (challanId) => { setIsProcessing(true); setTimeout(() => { setIsProcessing(false); setPaymentSuccess(challanId); setTimeout(() => setPaymentSuccess(null), 3000); setChallans(prev => prev.filter(c => c.challan_id !== challanId)); }, 1500); };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 font-sans"><div><h2 className="text-2xl font-black text-slate-950 dark:text-white uppercase font-mono tracking-wide text-indigo-600 dark:text-indigo-400 font-sans">Welcome, {user.name}</h2><p className="text-slate-600 text-[10px] font-black uppercase tracking-widest text-nowrap font-sans">Reviewing status for vehicle <span className="font-mono text-indigo-600 dark:text-indigo-400 uppercase tracking-widest">{user.name}</span></p></div></div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
        <Card onClick={() => setActiveFilter('Paid')} className={`p-5 border-l-4 cursor-pointer ${activeFilter === 'Paid' ? 'border-l-indigo-600 ring-2 ring-indigo-500/20 bg-indigo-50/30 dark:bg-indigo-900/10' : 'border-l-indigo-500'}`}><div className="flex justify-between items-start font-sans"><div><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 font-sans">Paid Challans</p><h3 className="text-2xl font-black text-slate-950 dark:text-white">0{getCount('Paid')}</h3></div><div className={`p-2 rounded-lg transition-colors ${activeFilter === 'Paid' ? 'bg-indigo-600 text-white' : 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-500'}`}><CheckCircle size={20} /></div></div></Card>
        <Card onClick={() => setActiveFilter('Unpaid')} className={`p-5 border-l-4 cursor-pointer ${activeFilter === 'Unpaid' ? 'border-l-amber-600 ring-2 ring-amber-500/20 bg-amber-50/30 dark:bg-indigo-900/10' : 'border-l-amber-500'}`}><div className="flex justify-between items-start font-sans"><div><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 font-sans">Unpaid Challans</p><h3 className="text-xl font-black text-slate-950 dark:text-white">0{getCount('Unpaid')}</h3></div><div className={`p-2 rounded-lg transition-colors ${activeFilter === 'Unpaid' ? 'bg-amber-600 text-white' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-500'}`}><AlertTriangle size={20} /></div></div></Card>
        <Card onClick={() => setActiveFilter('Pending')} className={`p-5 border-l-4 cursor-pointer ${activeFilter === 'Pending' ? 'border-l-blue-600 ring-2 ring-blue-500/20 bg-blue-50/30 dark:bg-indigo-900/10' : 'border-l-blue-500'}`}><div className="flex justify-between items-start font-sans"><div><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 text-nowrap font-sans uppercase">Awaiting Officer</p><h3 className="text-2xl font-black text-slate-950 dark:text-white">0{getCount('Pending')}</h3></div><div className={`p-2 rounded-lg transition-colors ${activeFilter === 'Pending' ? 'bg-blue-600 text-white' : 'bg-blue-50 dark:bg-blue-900/20 text-blue-500'}`}><Clock size={20} /></div></div></Card>
      </div>
      <Card className="overflow-hidden border-2 border-indigo-500/10 shadow-sm font-sans"><div className="p-4 border-b border-slate-200 dark:border-slate-700 flex justify-between bg-slate-50 dark:bg-slate-800/50 items-center font-sans font-black"><h3 className="font-black text-slate-950 dark:text-white flex items-center gap-2 text-sm md:text-base uppercase tracking-tighter text-nowrap font-sans"><span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse font-sans"></span>{activeFilter} CHALLANS LIST</h3></div><div className="overflow-x-auto font-sans"><table className="w-full text-left font-sans"><thead className="bg-slate-100 dark:bg-slate-900/50 text-slate-500 text-[10px] uppercase tracking-wider font-black font-sans"><tr><th className="px-6 py-4">CHALLAN ID</th><th className="px-6 py-4 text-nowrap">VIOLATION TYPE</th><th className="px-6 py-4 text-nowrap text-indigo-500">AP PLATE NUMBER</th><th className="px-6 py-4 text-center">STATUS</th>{activeFilter !== 'Paid' && <th className="px-6 py-4 text-nowrap">ACTION</th>}</tr></thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700 font-sans">
          {loading ? <tr><td colSpan="5" className="px-6 py-8 text-center text-slate-500 text-xs">Loading records...</td></tr> : filteredList.length === 0 ? <tr><td colSpan="5" className="px-6 py-8 text-center text-slate-500 text-xs">No records found.</td></tr> : filteredList.map((v) => (<tr key={v.challan_id} className="text-sm dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group font-sans font-black uppercase"><td className="px-6 py-4 font-mono text-xs font-black text-slate-950 dark:text-slate-400 group-hover:text-indigo-600 uppercase tracking-widest">{v.challan_id.split('-')[0]}</td><td className="px-6 py-4 font-medium text-slate-800 dark:text-white font-sans">{v.violation_type}</td><td className="px-6 py-4 font-mono uppercase text-indigo-600 dark:text-indigo-400 font-black tracking-widest font-sans">{v.plate_text_norm || 'UNKNOWN'}</td><td className="px-6 py-4 text-center font-sans"><StatusBadge status={v.status} payment={v.payment} /></td>{activeFilter !== 'Paid' && (<td className="px-6 py-4 font-sans">{v.payment === 'Unpaid' && (<button onClick={() => handlePayment(v.challan_id)} disabled={isProcessing} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black uppercase transition-all shadow-md disabled:opacity-50 cursor-pointer text-[10px]">{isProcessing ? <Clock size={12} className="animate-spin" /> : <CreditCard size={12} />}Pay Now</button>)}{v.payment === 'Pending' && (<span className="text-[10px] text-slate-500 italic font-black uppercase tracking-tighter text-nowrap font-sans font-black">UNDER OFFICER REVIEW</span>)}</td>)}</tr>))}
        </tbody></table></div></Card>
      {paymentSuccess && (<div className="fixed bottom-10 right-10 animate-in slide-in-from-right-4 duration-300 z-50 font-sans"><Card className="bg-green-600 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-4 border-none shadow-green-600/20 font-sans"><div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center font-sans font-black"><CheckCircle size={20} /></div><div><p className="font-black uppercase text-xs tracking-widest font-sans font-black">Payment Success!</p><p className="text-[10px] opacity-80 font-mono tracking-tighter uppercase text-white font-sans font-black">TRANS ID: {paymentSuccess.split('-')[0]}</p></div></Card></div>)}
    </div>
  );
};

// --- Main App Shell ---
export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('user');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [globalFeedbacks, setGlobalFeedbacks] = useState([]);

  const profileMenuRef = useRef(null);

  useEffect(() => { function hCO(e) { if (profileMenuRef.current && !profileMenuRef.current.contains(e.target)) setShowProfileMenu(false); } document.addEventListener("mousedown", hCO); return () => document.removeEventListener("mousedown", hCO); }, []);
  useEffect(() => { if (isDarkMode) document.documentElement.classList.add('dark'); else document.documentElement.classList.remove('dark'); }, [isDarkMode]);
  useEffect(() => { if (currentUser) setActiveTab(currentUser.role); }, [currentUser]);

  const hL = (u) => setCurrentUser(u);
  const hO = () => { setCurrentUser(null); setShowProfileMenu(false); };
  const tD = () => setIsDarkMode(!isDarkMode);
  const addFeedback = (f) => setGlobalFeedbacks(prev => [f, ...prev]);

  if (!currentUser) return <LoginPage onLogin={hL} isDarkMode={isDarkMode} toggleDarkMode={tD} />;

  const tabs = [
    { id: 'user', name: 'User Dashboard', icon: User, allowed: ['user', 'admin'] },
    { id: 'officer', name: 'Officer Review', icon: Shield, allowed: ['officer', 'admin'] },
    { id: 'admin', name: 'Admin Control', icon: Settings, allowed: ['admin'] },
  ].filter(t => t.allowed.includes(currentUser.role));

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDarkMode ? 'dark bg-slate-950 text-slate-200' : 'bg-slate-50 text-slate-950 font-sans'}`}>

      {/* Provide Feedback Modal */}
      {showFeedbackModal && <FeedbackModal onClose={() => setShowFeedbackModal(false)} user={currentUser} onSave={addFeedback} />}

      <header className="sticky top-0 z-40 w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors duration-300 font-sans">
        <div className="max-w-7xl mx-auto px-4 h-20 flex justify-between items-center text-nowrap font-sans font-black">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-600/20 font-black"><Bot size={24} /></div>
            <div className="hidden sm:block">
              <h1 className="font-black text-slate-950 dark:text-white leading-none text-lg uppercase font-sans">TRAFFIC</h1>
              <p className="text-[10px] text-slate-500 font-black tracking-widest uppercase mt-0.5 font-sans">Detection System</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-1 mx-8 bg-slate-100 dark:bg-slate-800/50 p-1 rounded-xl border border-slate-200 dark:border-slate-700 font-black">
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer font-black uppercase tracking-tighter ${activeTab === t.id ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 font-black'}`}><t.icon size={16} />{t.name}</button>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <div className="relative" ref={profileMenuRef}>
              <button onClick={() => setShowProfileMenu(!showProfileMenu)} className="flex items-center gap-3 pl-4 group transition-all cursor-pointer font-black">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-black text-indigo-600 dark:text-indigo-400 tracking-wider font-mono uppercase group-hover:text-indigo-500 leading-tight">{currentUser.id}</p>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest leading-none font-black">{currentUser.role} account</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center border border-slate-200 dark:border-slate-700 text-slate-400 shadow-sm group-hover:border-indigo-500 transition-all font-black"><User size={24} /></div>
                <ChevronDown size={14} className={`text-slate-400 transition-transform duration-300 ${showProfileMenu ? 'rotate-180' : ''}`} />
              </button>

              {showProfileMenu && (
                <div className="absolute right-0 mt-3 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-2 animate-in fade-in zoom-in duration-200 origin-top-right overflow-hidden">
                  <div className="px-4 py-4 border-b border-slate-100 dark:border-slate-700 mb-2 bg-slate-50/50 dark:bg-slate-900/50 font-black"><p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 font-black">Signed in as</p><p className="text-sm font-black text-indigo-600 dark:text-indigo-400 font-mono uppercase truncate font-black">{currentUser.id}</p></div>

                  {(currentUser.role === 'user' || currentUser.role === 'officer') && (
                    <button onClick={() => { setShowFeedbackModal(true); setShowProfileMenu(false); }} className="w-full text-left px-4 py-2.5 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 flex items-center gap-3 transition-colors font-black uppercase tracking-tighter cursor-pointer font-sans">
                      <MessageSquare size={16} /> Provide Feedback
                    </button>
                  )}

                  <button onClick={tD} className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex items-center gap-3 transition-colors font-medium cursor-pointer font-sans font-black uppercase tracking-tighter">{isDarkMode ? <Sun size={16} className="text-amber-500" /> : <Moon size={16} className="text-indigo-500" />} {isDarkMode ? 'Light Mode' : 'Dark Mode'}</button>
                  <div className="h-px bg-slate-100 dark:bg-slate-700 my-2" />
                  <button onClick={hO} className="w-full text-left px-4 py-3 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 flex items-center gap-3 font-black uppercase tracking-tighter transition-colors cursor-pointer font-sans font-black"><LogOut size={16} /> Sign Out</button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6 transition-all duration-300 min-h-[calc(100vh-80px)]">
        <div className="animate-in fade-in slide-in-from-bottom-3 duration-700 ease-out max-w-7xl mx-auto">
          {activeTab === 'admin' && <AdminDashboard user={currentUser} feedbacks={globalFeedbacks} />}
          {activeTab === 'officer' && <OfficerReviewModule user={currentUser} />}
          {activeTab === 'user' && <UserDashboard user={currentUser} />}
        </div>
      </main>

      <div className="md:hidden fixed bottom-6 left-6 right-6 z-50 flex justify-center">
        <nav className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 p-1.5 rounded-2xl shadow-2xl flex gap-1">
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`p-3 rounded-xl transition-all cursor-pointer ${activeTab === tab.id ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500'}`}><tab.icon size={20} /></button>
          ))}
        </nav>
      </div>
    </div>
  );
}