import axios from 'axios';
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import ScryfallSearch from './components/ScryfallSearch';
import BoardBuilder from './components/BoardBuilder';
import PsychographicAssessment from './components/PsychographicAssessment';

type Conversation = {
  id: number;
  title: string;
  created_at: string;
};

type ThinkingStep = {
  label: string;
  detail: string;
};

type Message = {
  sender: string;
  content: string;
  created_at: string;
  thinking?: ThinkingStep[];
};

type AccountRequest = {
  id: number;
  username: string;
  status: string;
  created_at: string;
};

type ProfileSummary = {
  primary_type_label: string;
  primary_score: number;
  description: string;
  play_style_summary: string;
  conversation_guidance: string;
  preference_breakdown: Record<string, number>;
};

type TabKey = 'chat' | 'tools' | 'profile' | 'settings';

const api = axios.create({ baseURL: '/api' });

const decodeToken = (token: string) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch (err) {
    return null;
  }
};

function App() {
  const tokenStorageKey = 'melvin_token';
  const tabNav: { key: TabKey; label: string }[] = [
    { key: 'chat', label: 'Chat' },
    { key: 'tools', label: 'Tools' },
    { key: 'profile', label: 'Profile' },
    { key: 'settings', label: 'Settings' },
  ];
  const [requestUsername, setRequestUsername] = useState('');
  const [requestPassword, setRequestPassword] = useState('');
  const [requestStatus, setRequestStatus] = useState<string | null>(null);
  const [authView, setAuthView] = useState<'login' | 'request'>('login');

  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(tokenStorageKey));
  const [isAdmin, setIsAdmin] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  const authHeaders = useMemo(() => ({ headers: { Authorization: token ? `Bearer ${token}` : '' } }), [token]);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newConversationTitle, setNewConversationTitle] = useState('New Conversation');
  const [question, setQuestion] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingPreview, setThinkingPreview] = useState<ThinkingStep[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>('chat');
  const [tonePreference, setTonePreference] = useState('Helpful and friendly');
  const [detailPreference, setDetailPreference] = useState('Balanced');

  const [pendingRequests, setPendingRequests] = useState<AccountRequest[]>([]);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);
  const [profileSummary, setProfileSummary] = useState<ProfileSummary | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [showAssessment, setShowAssessment] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  type AuthShellProps = {
    children: ReactNode;
    onRequestLink?: () => void;
    onLoginLink?: () => void;
    heading: string;
    subheading?: string;
    ctaLabel?: string;
  };

  const AuthShell = ({ children, heading, subheading, onRequestLink, onLoginLink, ctaLabel }: AuthShellProps) => (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-50">
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-12">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-sm tracking-wide text-blue-400">MELVIN</p>
            <h1 className="text-3xl font-bold text-white">{heading}</h1>
            {subheading && <p className="text-slate-400 mt-2">{subheading}</p>}
          </div>
          {onRequestLink && (
            <button onClick={onRequestLink} className="rounded-full border border-blue-500 px-4 py-2 text-sm hover:bg-blue-500/10 transition">
              {ctaLabel ?? 'Request Access'}
            </button>
          )}
          {onLoginLink && (
            <button onClick={onLoginLink} className="rounded-full border border-blue-500 px-4 py-2 text-sm hover:bg-blue-500/10 transition">
              Back to Login
            </button>
          )}
        </header>
        {children}
      </div>
    </div>
  );

  const resetSession = useCallback((message?: string) => {
    setToken(null);
    setIsAdmin(false);
    setUserName(null);
    localStorage.removeItem(tokenStorageKey);
    setConversations([]);
    setMessages([]);
    setSelectedConversation(null);
    setPendingRequests([]);
    setProfileSummary(null);
    setActiveTab('chat');
    if (message) {
      setAdminStatus(message);
    } else {
      setAdminStatus(null);
    }
  }, [tokenStorageKey]);

  const handleAuthError = useCallback((error: unknown, fallbackMessage?: string) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      resetSession('Please log in again to continue.');
      return true;
    }
    if (fallbackMessage) {
      alert(fallbackMessage);
    }
    console.error(error);
    return false;
  }, [resetSession]);

  const loadProfileSummary = useCallback(async () => {
    if (!token) return;
    setProfileLoading(true);
    setProfileError(null);
    try {
      const response = await api.get<ProfileSummary>('/profiles/me/summary', authHeaders);
      setProfileSummary(response.data);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        setProfileSummary(null);
      } else if (!handleAuthError(error)) {
        setProfileError('Failed to load profile summary');
      }
    } finally {
      setProfileLoading(false);
    }
  }, [authHeaders, handleAuthError, token]);

  useEffect(() => {
    if (token) {
      const payload = decodeToken(token);
      setIsAdmin(payload?.admin ?? false);
      setUserName(payload?.username ?? null);
      loadConversations();
      if (payload?.admin) {
        loadPendingRequests();
      }
    } else {
      setUserName(null);
    }
  }, [token]);

  useEffect(() => {
    if (token && activeTab === 'profile') {
      loadProfileSummary();
    }
  }, [token, activeTab, loadProfileSummary]);

  useEffect(() => {
    if (activeTab === 'chat') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking, activeTab]);

  const handleAssessmentComplete = async () => {
    await loadProfileSummary();
    setShowAssessment(false);
  };

  const loadConversations = async () => {
    if (!token) return;
    try {
      const response = await api.get<Conversation[]>('/conversations/', authHeaders);
      setConversations(response.data);
      if (response.data.length && !selectedConversation) {
        selectConversation(response.data[0]);
      }
    } catch (error) {
      handleAuthError(error);
    }
  };

  const selectConversation = async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    try {
      const response = await api.get(`/conversations/${conversation.id}`, authHeaders);
      setMessages(response.data.messages ?? []);
    } catch (error) {
      handleAuthError(error);
    }
  };

  const handleRequestAccount = async () => {
    try {
      await api.post('/auth/request', {
        username: requestUsername,
        password: requestPassword,
      });
      setRequestStatus('Request submitted. Please wait for approval and try logging in later.');
      setRequestUsername('');
      setRequestPassword('');
    } catch (error: any) {
      setRequestStatus(error.response?.data?.detail ?? 'Failed to submit request.');
    }
  };

  const handleLogin = async () => {
    try {
      const response = await api.post('/auth/login', {
        username: loginUsername,
        password: loginPassword,
      });
      const receivedToken = response.data.access_token;
      setToken(receivedToken);
      localStorage.setItem(tokenStorageKey, receivedToken);
      setLoginPassword('');
      setLoginUsername('');
      loadConversations();
    } catch (error: any) {
      alert(error.response?.data?.detail ?? 'Login failed');
    }
  };

  const handleCreateConversation = async () => {
    if (!newConversationTitle.trim()) return;
    try {
      const response = await api.post('/conversations/', {
        title: newConversationTitle,
      }, authHeaders);
      setNewConversationTitle('New Conversation');
      loadConversations();
      selectConversation(response.data);
    } catch (error) {
      handleAuthError(error, 'Failed to create conversation');
    }
  };

  const handleSendQuestion = async () => {
    if (!selectedConversation || !question.trim()) return;
    const convoId = selectedConversation.id;
    const userMessage: Message = { sender: 'user', content: question, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setIsThinking(true);
    setThinkingPreview([{ label: 'Analyzing', detail: 'Collecting rules, cards, and rulings context.' }]);
    try {
      const response = await api.post(`/conversations/${convoId}/chat`, {
        question: userMessage.content,
        tone: tonePreference,
        detail_level: detailPreference,
      }, authHeaders);
      setMessages(prev => [...prev, response.data]);
      setThinkingPreview(response.data.thinking ?? []);
    } catch (error) {
      if (!handleAuthError(error, 'Failed to send message')) {
        console.error(error);
      }
    }
    setIsThinking(false);
  };

  const loadPendingRequests = async () => {
    if (!token) return;
    try {
      const response = await api.get<AccountRequest[]>('/auth/requests', authHeaders);
      setPendingRequests(response.data);
    } catch (error) {
      handleAuthError(error);
    }
  };

  const handleApprove = async (requestId: number) => {
    try {
      await api.post(`/auth/requests/${requestId}/approve`, {}, authHeaders);
      setAdminStatus('Request approved');
      loadPendingRequests();
    } catch (error) {
      if (!handleAuthError(error)) {
        setAdminStatus('Failed to approve request');
      }
    }
  };

  const handleDeny = async (requestId: number) => {
    try {
      await api.post(`/auth/requests/${requestId}/deny`, {}, authHeaders);
      setAdminStatus('Request denied');
      loadPendingRequests();
    } catch (error) {
      if (!handleAuthError(error)) {
        setAdminStatus('Failed to deny request');
      }
    }
  };

  const handleLogout = () => {
    resetSession();
    setAuthView('login');
  };

  if (!token) {
    if (authView === 'request') {
      return (
        <AuthShell
          heading="Request an account"
          subheading="Tell us who you are and we’ll notify an administrator to approve your access."
          onLoginLink={() => setAuthView('login')}
        >
          <div className="grid md:grid-cols-2 gap-8 items-start">
            <div className="space-y-4">
              <h2 className="text-2xl font-semibold">Your credentials</h2>
              <p className="text-slate-400">
                Choose a username and password. After approval, you’ll use these to sign in.
              </p>
              <div className="space-y-2">
                <label className="text-sm text-slate-300">Username</label>
                <input className="w-full p-3 rounded bg-slate-900 border border-slate-800" value={requestUsername} onChange={(e) => setRequestUsername(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-slate-300">Password</label>
                <input type="password" className="w-full p-3 rounded bg-slate-900 border border-slate-800" value={requestPassword} onChange={(e) => setRequestPassword(e.target.value)} />
              </div>
              <button className="mt-2 w-full bg-blue-600 hover:bg-blue-500 transition px-4 py-3 rounded font-semibold" onClick={handleRequestAccount}>
                Submit request
              </button>
              {requestStatus && <p className="text-sm text-green-400">{requestStatus}</p>}
            </div>
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-lg font-semibold">What happens next?</h3>
              <ul className="space-y-3 text-slate-300 text-sm">
                <li>• An admin reviews your request.</li>
                <li>• Once approved, log in from the landing page.</li>
                <li>• Need to adjust details? Submit a new request.</li>
              </ul>
              <div className="text-xs text-slate-500">
                Questions? Reach out to your Melvin administrator.
              </div>
            </div>
          </div>
        </AuthShell>
      );
    }

    return (
      <AuthShell
        heading="Magic: the Gathering AI Assistant"
        subheading="Ask rules questions, explore rulings, and collaborate with Melvin."
        onRequestLink={() => setAuthView('request')}
        ctaLabel="Request an account"
      >
        <div className="grid md:grid-cols-2 gap-10 items-start">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-200 px-3 py-1 rounded-full text-xs font-semibold">
              <span>Play smarter</span>
            </div>
            <h2 className="text-3xl font-bold text-white leading-tight">Sign in to chat with Melvin</h2>
            <p className="text-slate-400 max-w-xl">
              Log in to manage conversations, ask for rulings, and share boards. Don&apos;t have access yet? Request an account and we&apos;ll approve you shortly.
            </p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <h3 className="text-xl font-semibold">Login</h3>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Username</label>
              <input className="w-full p-3 rounded bg-slate-900 border border-slate-800" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Password</label>
              <input type="password" className="w-full p-3 rounded bg-slate-900 border border-slate-800" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
            </div>
            <button className="w-full bg-green-600 hover:bg-green-500 transition px-4 py-3 rounded font-semibold" onClick={handleLogin}>
              Enter Melvin
            </button>
            <button className="w-full text-sm text-blue-300 underline" onClick={() => setAuthView('request')}>
              Need an account? Request access
            </button>
          </div>
        </div>
      </AuthShell>
    );
  }

  const toneOptions = [
    'Helpful and friendly',
    'Neutral and concise',
    'Judge-like and formal',
    'Energetic coach',
  ];
  const detailOptions = ['Balanced', 'High detail', 'Quick summary'];
  const formatPreferenceLabel = (key: string) => {
    if (key === 'big_plays') return 'Big Plays';
    if (key === 'originality') return 'Originality';
    if (key === 'optimization') return 'Optimization';
    if (key === 'mechanics') return 'Mechanical Curiosity';
    return key.charAt(0).toUpperCase() + key.slice(1);
  };

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 space-y-8">
      <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Melvin</h1>
          <p className="text-slate-400">Magic: The Gathering rules assistant</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-sm text-slate-300">
            <p>
              Signed in as{' '}
              <span className="font-semibold text-white">{userName ?? 'Planeswalker'}</span>
            </p>
            <p className="text-slate-500">Tone: {tonePreference} · Detail: {detailPreference}</p>
          </div>
          <button className="bg-red-600 px-4 py-2 rounded" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="flex flex-wrap gap-2 bg-slate-900/60 border border-slate-800 rounded-full p-1">
        {tabNav.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-full text-sm transition ${
              activeTab === tab.key ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === 'chat' && (
        <div className="grid md:grid-cols-3 gap-6">
          <section className="bg-slate-900 p-4 rounded-lg shadow md:col-span-1 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <input className="flex-1 p-2 rounded bg-slate-800" value={newConversationTitle} onChange={(e) => setNewConversationTitle(e.target.value)} />
              <button className="bg-blue-600 px-3 py-2 rounded" onClick={handleCreateConversation}>+</button>
            </div>
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => selectConversation(conversation)}
                  className={`w-full text-left p-3 rounded ${selectedConversation?.id === conversation.id ? 'bg-blue-600/30 border border-blue-500' : 'bg-slate-800'}`}
                >
                  <p className="font-semibold">{conversation.title}</p>
                  <p className="text-xs text-slate-400">{new Date(conversation.created_at).toLocaleString()}</p>
                </button>
              ))}
            </div>
          </section>

          <section className="bg-slate-900 p-4 rounded-lg shadow md:col-span-2 flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2 max-h-[60vh]">
              {messages.map((message, idx) => (
                <div key={idx} className={`p-3 rounded ${message.sender === 'user' ? 'bg-blue-900/40' : 'bg-slate-800'}`}>
                  <p className="text-sm text-slate-400 mb-1">{message.sender} — {new Date(message.created_at).toLocaleTimeString()}</p>
                  <p>{message.content}</p>
                  {message.sender !== 'user' && message.thinking && message.thinking.length > 0 && (
                    <details className="mt-2 text-xs text-slate-300/80">
                      <summary className="cursor-pointer text-blue-200">View Melvin&apos;s reasoning</summary>
                      <ul className="mt-2 space-y-1">
                        {message.thinking.map((step, stepIdx) => (
                          <li key={`${idx}-${stepIdx}`} className="border-l border-blue-500/40 pl-2">
                            <span className="font-semibold text-slate-100">{step.label}:</span> {step.detail}
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              ))}
              {isThinking && (
                <div className="p-3 rounded bg-blue-900/20 border border-blue-500/50 animate-pulse">
                  <p className="text-sm text-blue-200 mb-1">Melvin is preparing a response…</p>
                  <ul className="text-xs text-slate-300 space-y-1">
                    {thinkingPreview.map((step, idx) => (
                      <li key={`${step.label}-${idx}`} className="border-l border-blue-400/40 pl-2">
                        <span className="font-semibold">{step.label}:</span> {step.detail}
                      </li>
                    ))}
                    {thinkingPreview.length === 0 && <li>Gathering knowledge...</li>}
                  </ul>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="flex gap-3">
              <textarea className="flex-1 rounded bg-slate-800 p-3" rows={3} placeholder="Ask Melvin..." value={question} onChange={(e) => setQuestion(e.target.value)} />
              <button className="bg-green-600 px-4 rounded" onClick={handleSendQuestion}>
                Send
              </button>
            </div>
          </section>
        </div>
      )}

      {activeTab === 'tools' && (
        <section className="space-y-6">
          <div className="bg-slate-900 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-2">Tools hub</h2>
            <p className="text-slate-400">Search cards, sketch boards, and test ideas alongside your conversations.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <ScryfallSearch />
            <BoardBuilder />
          </div>
        </section>
      )}

      {activeTab === 'profile' && (
        <section className="bg-slate-900 p-6 rounded-lg shadow space-y-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold">Your Player Profile</h2>
              <p className="text-slate-400">Share how you like to play so Melvin can tailor explanations and suggestions.</p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <button className="px-4 py-2 rounded bg-blue-600 text-white" onClick={() => setShowAssessment(true)}>
                {profileSummary ? 'Retake Assessment' : 'Start Assessment'}
              </button>
              <button className="px-4 py-2 rounded border border-slate-600 text-slate-200" onClick={loadProfileSummary}>
                Refresh Summary
              </button>
            </div>
          </div>
          {profileLoading && <p className="text-slate-300">Loading your profile summary...</p>}
          {profileError && <p className="text-red-400">{profileError}</p>}
          {!profileLoading && !profileSummary && !profileError && (
            <p className="text-slate-300">You haven&apos;t completed the assessment yet. Click &quot;Start Assessment&quot; to begin.</p>
          )}
          {profileSummary && (
            <div className="space-y-4">
              <div className="bg-slate-800 p-4 rounded-lg space-y-2">
                <p className="text-lg font-semibold text-white">{profileSummary.primary_type_label}</p>
                <p className="text-slate-300">{Math.round(profileSummary.primary_score * 100)}% alignment</p>
                <p className="text-slate-200">{profileSummary.description}</p>
                <p className="text-sm text-slate-400">{profileSummary.play_style_summary}</p>
              </div>
              <div className="bg-slate-800 p-4 rounded-lg space-y-2">
                <h3 className="font-semibold text-white">How Melvin will respond</h3>
                <p className="text-slate-300">{profileSummary.conversation_guidance}</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {Object.entries(profileSummary.preference_breakdown).map(([key, value]) => (
                  <div key={key} className="bg-slate-900/60 p-4 rounded-lg">
                    <div className="flex items-center justify-between text-sm text-slate-300 mb-2">
                      <span>{formatPreferenceLabel(key)}</span>
                      <span>{Math.round(value * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded">
                      <div className="bg-blue-500 h-2 rounded" style={{ width: `${value * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {showAssessment && (
            <div className="border border-slate-700 rounded-lg overflow-hidden">
              <PsychographicAssessment authToken={token} onAssessmentComplete={handleAssessmentComplete} onClose={() => setShowAssessment(false)} />
            </div>
          )}
        </section>
      )}

      {activeTab === 'settings' && (
        <section className="space-y-6">
          <div className="bg-slate-900 p-6 rounded-lg shadow space-y-4">
            <h2 className="text-xl font-semibold">Conversation Preferences</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm text-slate-300">
                Melvin&apos;s tone
                <select className="p-3 rounded bg-slate-800 text-white" value={tonePreference} onChange={(e) => setTonePreference(e.target.value)}>
                  {toneOptions.map((tone) => (
                    <option key={tone} value={tone}>{tone}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-2 text-sm text-slate-300">
                Detail level
                <select className="p-3 rounded bg-slate-800 text-white" value={detailPreference} onChange={(e) => setDetailPreference(e.target.value)}>
                  {detailOptions.map((detail) => (
                    <option key={detail} value={detail}>{detail}</option>
                  ))}
                </select>
              </label>
            </div>
            <p className="text-sm text-slate-400">These preferences are attached to your future Melvin conversations.</p>
          </div>

          {isAdmin && (
            <section className="bg-slate-900 p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Admin Queue</h2>
                <button className="text-sm underline" onClick={loadPendingRequests}>Refresh</button>
              </div>
              {adminStatus && <p className="text-sm text-slate-300 mb-4">{adminStatus}</p>}
              <div className="space-y-3">
                {pendingRequests.length === 0 && <p className="text-slate-400">No pending requests</p>}
                {pendingRequests.map((request) => (
                  <div key={request.id} className="bg-slate-800 p-4 rounded flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{request.username}</p>
                      <p className="text-xs text-slate-400">Requested {new Date(request.created_at).toLocaleString()}</p>
                    </div>
                    <div className="flex gap-2">
                      <button className="bg-green-600 px-3 py-1 rounded" onClick={() => handleApprove(request.id)}>Approve</button>
                      <button className="bg-red-600 px-3 py-1 rounded" onClick={() => handleDeny(request.id)}>Deny</button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </section>
      )}
    </div>
  );
}

export default App;
