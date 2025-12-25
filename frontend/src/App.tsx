import axios from 'axios';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  context?: MessageContext | null;
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

type ModelOptions = {
  current: string;
  available: string[];
};

type ModelPreference = {
  preferred_model: string | null;
  effective_model: string;
};

type UserModelPreference = {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
  preferred_model: string | null;
  effective_model: string;
};

type TabKey = 'chat' | 'tools' | 'profile' | 'settings';
type MessageContext = {
  rules?: string;
  cards?: string;
  rulings?: string;
  references?: string;
  player_guidance?: string;
  state?: any;
  tools?: string;
  external_cards?: string;
};
type CardSearchResult = {
  name: string;
  type_line?: string | null;
  oracle_text?: string | null;
};
type CardSearchResponse = {
  results: CardSearchResult[];
};

const api = axios.create({ baseURL: '/api' });

const formatError = (error: any): string => {
  const detail = error?.response?.data?.detail ?? error?.message ?? error;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        const loc = item?.loc ? `[${item.loc.join('.')}] ` : '';
        return `${loc}${item?.msg ?? JSON.stringify(item)}`;
      })
      .join(' | ');
  }
  if (detail && typeof detail === 'object') {
    if (detail.msg) return detail.msg;
    return JSON.stringify(detail);
  }
  return 'Unexpected error';
};

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
  const [selectedCards, setSelectedCards] = useState<string[]>([]);
  const [cardPickerOpen, setCardPickerOpen] = useState(false);
  const [cardSearchTerm, setCardSearchTerm] = useState('');
  const [cardSearchResults, setCardSearchResults] = useState<CardSearchResult[]>([]);
  const [cardSearchLoading, setCardSearchLoading] = useState(false);
  const [cardSearchError, setCardSearchError] = useState<string | null>(null);
  const [insightOpen, setInsightOpen] = useState(false);
  const [insightMessage, setInsightMessage] = useState<Message | null>(null);

  const [pendingRequests, setPendingRequests] = useState<AccountRequest[]>([]);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);
  const [modelOptions, setModelOptions] = useState<ModelOptions | null>(null);
  const [modelStatus, setModelStatus] = useState<string | null>(null);
  const [modelPreference, setModelPreference] = useState<ModelPreference | null>(null);
  const [modelPreferenceStatus, setModelPreferenceStatus] = useState<string | null>(null);
  const [userModelPrefs, setUserModelPrefs] = useState<UserModelPreference[]>([]);
  const [userModelPrefsStatus, setUserModelPrefsStatus] = useState<string | null>(null);
  const [updatingUserModelId, setUpdatingUserModelId] = useState<number | null>(null);
  const [profileSummary, setProfileSummary] = useState<ProfileSummary | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [showAssessment, setShowAssessment] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const defaultModelOptionValue = '__DEFAULT_MODEL_OPTION__';

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
    setSelectedCards([]);
    setCardPickerOpen(false);
    setCardSearchTerm('');
    setCardSearchResults([]);
    setCardSearchError(null);
    setCardSearchLoading(false);
    setInsightOpen(false);
    setInsightMessage(null);
    setModelPreference(null);
    setModelPreferenceStatus(null);
    setUserModelPrefs([]);
    setUserModelPrefsStatus(null);
    setUpdatingUserModelId(null);
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

  const loadModelOptions = useCallback(async () => {
    if (!token) return;
    setModelStatus(null);
    try {
      const response = await api.get<ModelOptions>('/models/ollama', authHeaders);
      setModelOptions(response.data);
    } catch (error) {
      if (!handleAuthError(error, 'Failed to load model list')) {
        setModelStatus('Could not load available models from Ollama.');
      }
    }
  }, [authHeaders, handleAuthError, token]);

  const loadModelPreference = useCallback(async () => {
    if (!token) return;
    try {
      const response = await api.get<ModelPreference>('/models/preferences/me', authHeaders);
      setModelPreference(response.data);
      setModelPreferenceStatus(null);
    } catch (error) {
      if (!handleAuthError(error)) {
        setModelPreferenceStatus('Failed to load model preference.');
      }
    }
  }, [authHeaders, handleAuthError, token]);

  const saveModelPreference = useCallback(async (value: string | null) => {
    if (!token) return;
    setModelPreferenceStatus('Saving preference...');
    try {
      const response = await api.post<ModelPreference>('/models/preferences/me', { model: value }, authHeaders);
      setModelPreference(response.data);
      setModelPreferenceStatus(value ? `Preference saved (${value}).` : 'Preference cleared. Using default model.');
    } catch (error) {
      if (!handleAuthError(error, 'Failed to save preference')) {
        setModelPreferenceStatus('Failed to save preference.');
      }
    }
  }, [authHeaders, handleAuthError, token]);

  const loadUserModelPrefs = useCallback(async () => {
    if (!token || !isAdmin) return;
    try {
      const response = await api.get<UserModelPreference[]>('/models/preferences/users', authHeaders);
      setUserModelPrefs(response.data);
      setUserModelPrefsStatus(null);
    } catch (error) {
      if (!handleAuthError(error, 'Failed to load user model preferences')) {
        setUserModelPrefsStatus('Failed to load user preferences.');
      }
    }
  }, [authHeaders, handleAuthError, isAdmin, token]);

  const updateUserModelPreference = useCallback(async (userId: number, value: string | null) => {
    if (!token || !isAdmin) return;
    setUpdatingUserModelId(userId);
    try {
      const response = await api.post<UserModelPreference>(`/models/preferences/users/${userId}`, { model: value }, authHeaders);
      setUserModelPrefs((prev) => prev.map((entry) => (entry.id === userId ? response.data : entry)));
      setUserModelPrefsStatus(value ? 'Updated user preference.' : 'Cleared user preference.');
    } catch (error) {
      if (!handleAuthError(error, 'Failed to update user model preference')) {
        setUserModelPrefsStatus('Failed to update user preference.');
      }
    } finally {
      setUpdatingUserModelId(null);
    }
  }, [authHeaders, handleAuthError, isAdmin, token]);

  const selectConversation = useCallback(async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    try {
      const response = await api.get(`/conversations/${conversation.id}`, authHeaders);
      setMessages(response.data.messages ?? []);
    } catch (error) {
      handleAuthError(error);
    }
  }, [authHeaders, handleAuthError]);

  const loadConversations = useCallback(async () => {
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
  }, [authHeaders, handleAuthError, selectConversation, selectedConversation, token]);

  const loadPendingRequests = useCallback(async () => {
    if (!token) return;
    try {
      const response = await api.get<AccountRequest[]>('/auth/requests', authHeaders);
      setPendingRequests(response.data);
    } catch (error) {
      handleAuthError(error);
    }
  }, [authHeaders, handleAuthError, token]);

  useEffect(() => {
    if (token) {
      const payload = decodeToken(token);
      const adminFlag = payload?.admin ?? false;
      setIsAdmin(adminFlag);
      setUserName(payload?.username ?? null);
      loadConversations();
      loadModelOptions();
      loadModelPreference();
      if (adminFlag) {
        loadPendingRequests();
        loadUserModelPrefs();
      } else {
        setPendingRequests([]);
        setUserModelPrefs([]);
      }
    } else {
      setUserName(null);
      setIsAdmin(false);
      setModelPreference(null);
      setUserModelPrefs([]);
    }
  }, [
    loadConversations,
    loadModelOptions,
    loadModelPreference,
    loadPendingRequests,
    loadUserModelPrefs,
    token,
  ]);

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

  useEffect(() => {
    setSelectedCards([]);
    setCardPickerOpen(false);
    setCardSearchTerm('');
    setCardSearchResults([]);
    setCardSearchError(null);
    setInsightOpen(false);
    setInsightMessage(null);
  }, [selectedConversation?.id]);

  useEffect(() => {
    if (!cardPickerOpen) {
      setCardSearchLoading(false);
      return;
    }
    const term = cardSearchTerm.trim();
    if (term.length < 2) {
      setCardSearchResults([]);
      setCardSearchError(null);
      setCardSearchLoading(false);
      return;
    }
    const controller = new AbortController();
    setCardSearchLoading(true);
    setCardSearchError(null);
    api.get<CardSearchResponse>('/cards/search', {
      ...authHeaders,
      params: { q: term, limit: 8 },
      signal: controller.signal,
    }).then((response) => {
      setCardSearchResults(response.data.results);
    }).catch((error) => {
      if (axios.isCancel(error)) {
        return;
      }
      if (axios.isAxiosError(error) && error.code === 'ERR_CANCELED') {
        return;
      }
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }
      setCardSearchError('Failed to search cards. Try again.');
    }).finally(() => {
      setCardSearchLoading(false);
    });
    return () => controller.abort();
  }, [cardPickerOpen, cardSearchTerm, authHeaders]);

  useEffect(() => {
    if (!cardPickerOpen) {
      setCardSearchTerm('');
      setCardSearchResults([]);
      setCardSearchError(null);
    }
  }, [cardPickerOpen]);

  const handleAssessmentComplete = async () => {
    await loadProfileSummary();
    setShowAssessment(false);
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
      setRequestStatus(formatError(error));
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
      alert(formatError(error));
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

  const handleAddCard = (name: string) => {
    setSelectedCards((prev) => (prev.includes(name) ? prev : [...prev, name]));
    setCardSearchTerm('');
    setCardSearchResults([]);
  };

  const handleRemoveCard = (name: string) => {
    setSelectedCards((prev) => prev.filter((card) => card !== name));
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
        card_names: selectedCards,
      }, authHeaders);
      setMessages(prev => [...prev, response.data]);
      setInsightMessage(response.data);
      setThinkingPreview(response.data.thinking ?? []);
    } catch (error) {
      if (!handleAuthError(error, 'Failed to send message')) {
        console.error(error);
      }
    }
    setIsThinking(false);
  };

  const handleModelPreferenceSelect = (value: string) => {
    const normalized = value === defaultModelOptionValue ? null : value;
    saveModelPreference(normalized);
  };

  const handleAdminModelPreferenceSelect = (userId: number, value: string) => {
    const normalized = value === defaultModelOptionValue ? null : value;
    updateUserModelPreference(userId, normalized);
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
  };

  const [showRequestForm, setShowRequestForm] = useState(false);

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
        <div className="max-w-xl mx-auto px-6 py-16 space-y-8">
          <header className="space-y-3 text-center">
            <p className="uppercase tracking-[0.3em] text-xs text-blue-300">Melvin</p>
            <h1 className="text-4xl font-bold">Magic: The Gathering rules partner</h1>
            <p className="text-slate-300">
              Log in to access judge-grade rulings, Commander insights, and your personalized Melvin workspace.
            </p>
          </header>

          {!showRequestForm ? (
            <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-white text-center">Log in</h2>
              </div>
              <div className="space-y-3">
                <label className="text-sm text-slate-300">Username</label>
                <input className="w-full p-3 rounded-xl bg-slate-950/60 border border-slate-800 focus:outline-none focus:border-blue-500" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} />
              </div>
              <div className="space-y-3">
                <label className="text-sm text-slate-300">Password</label>
                <input type="password" className="w-full p-3 rounded-xl bg-slate-950/60 border border-slate-800 focus:outline-none focus:border-blue-500" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
              </div>
              <button className="w-full bg-blue-600 hover:bg-blue-500 transition px-4 py-3 rounded-xl font-semibold" onClick={handleLogin}>
                Enter Melvin
              </button>
              <p className="text-center text-xs text-slate-500">
                Need access?{' '}
                <button className="underline text-blue-300" onClick={() => { setShowRequestForm(true); setRequestStatus(null); }}>
                  Request an account
                </button>
              </p>
            </section>
          ) : (
            <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-white">Request access</h2>
                <button className="text-sm text-blue-300 underline" onClick={() => setShowRequestForm(false)}>
                  Back to login
                </button>
              </div>
              <p className="text-sm text-slate-400">
                Submit a username and password. An admin will approve you, then you can log in from the main page.
              </p>
              <div className="space-y-3">
                <label className="text-sm text-slate-300">Desired username</label>
                <input className="w-full p-3 rounded-xl bg-slate-950/60 border border-slate-800 focus:outline-none focus:border-blue-500" value={requestUsername} onChange={(e) => setRequestUsername(e.target.value)} />
              </div>
              <div className="space-y-3">
                <label className="text-sm text-slate-300">Password</label>
                <input type="password" className="w-full p-3 rounded-xl bg-slate-950/60 border border-slate-800 focus:outline-none focus:border-blue-500" value={requestPassword} onChange={(e) => setRequestPassword(e.target.value)} />
              </div>
              <button className="w-full bg-emerald-600 hover:bg-emerald-500 transition px-4 py-3 rounded-xl font-semibold" onClick={handleRequestAccount}>
                Submit request
              </button>
              {requestStatus && <p className="text-sm text-emerald-300 text-center">{requestStatus}</p>}
            </section>
          )}
        </div>
      </div>
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
                  <p className="text-xs text-slate-400 flex flex-wrap gap-2 justify-between">
                    <span>ID #{conversation.id}</span>
                    <span>{new Date(conversation.created_at).toLocaleString()}</span>
                  </p>
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
                  {message.sender !== 'user' && message.context && (
                    <button
                      className="mt-2 text-xs text-blue-300 hover:text-blue-200 underline"
                      onClick={() => {
                        setInsightMessage(message);
                        setInsightOpen(true);
                      }}
                    >
                      Inspect context & reasoning
                    </button>
                  )}
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
            <div className="border-t border-slate-800 pt-3 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs sm:text-sm text-slate-400">
                <span>Give Melvin optional card context. You can also type card names inside brackets, e.g. [Sol Ring].</span>
                <button className="text-blue-300 hover:text-blue-200" onClick={() => setCardPickerOpen((prev) => !prev)}>
                  {cardPickerOpen ? 'Close card selector' : 'Add cards for relevance'}
                </button>
              </div>
              {selectedCards.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedCards.map((card) => (
                    <span key={card} className="bg-slate-800 border border-slate-700 rounded-full px-3 py-1 text-xs text-slate-200 flex items-center gap-2">
                      {card}
                      <button className="text-slate-400 hover:text-white" onClick={() => handleRemoveCard(card)} aria-label={`Remove ${card}`}>
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
              {cardPickerOpen && (
                <div className="bg-slate-800/80 border border-slate-700 rounded-lg p-3 space-y-2">
                  <div className="flex gap-2">
                    <input
                      className="flex-1 rounded bg-slate-900/80 border border-slate-700 px-3 py-2 text-sm"
                      placeholder="Search local Oracle data..."
                      value={cardSearchTerm}
                      onChange={(e) => setCardSearchTerm(e.target.value)}
                    />
                    <button className="px-3 py-2 text-sm rounded border border-slate-600 text-slate-200" onClick={() => setCardPickerOpen(false)}>
                      Done
                    </button>
                  </div>
                  <p className="text-xs text-slate-400">Select matches from the ingested Oracle database. Only exact matches will be sent with your prompt.</p>
                  {cardSearchError && <p className="text-xs text-red-400">{cardSearchError}</p>}
                  <div className="max-h-48 overflow-y-auto space-y-2">
                    {cardSearchLoading && <p className="text-sm text-slate-300">Searching...</p>}
                    {!cardSearchLoading && cardSearchTerm.trim().length < 2 && (
                      <p className="text-xs text-slate-500">Type at least two characters to search.</p>
                    )}
                    {!cardSearchLoading && cardSearchTerm.trim().length >= 2 && cardSearchResults.length === 0 && !cardSearchError && (
                      <p className="text-xs text-slate-500">No matches yet.</p>
                    )}
                    {!cardSearchLoading && cardSearchResults.map((result) => (
                      <button
                        key={result.name}
                        className="w-full text-left bg-slate-900/70 hover:bg-slate-700/70 transition rounded p-2 text-sm"
                        onClick={() => handleAddCard(result.name)}
                      >
                        <p className="font-semibold text-white">{result.name}</p>
                        {result.type_line && <p className="text-xs text-slate-300">{result.type_line}</p>}
                        {result.oracle_text && <p className="text-xs text-slate-400 mt-1 overflow-hidden text-ellipsis whitespace-nowrap">{result.oracle_text}</p>}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex gap-3">
                <textarea className="flex-1 rounded bg-slate-800 p-3" rows={3} placeholder="Ask Melvin..." value={question} onChange={(e) => setQuestion(e.target.value)} />
                <button className="bg-green-600 px-4 rounded" onClick={handleSendQuestion}>
                  Send
                </button>
              </div>
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

          <div className="bg-slate-900 p-6 rounded-lg shadow space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Model Preference</h2>
              <button className="text-sm underline" onClick={() => { loadModelOptions(); loadModelPreference(); }}>
                Refresh
              </button>
            </div>
            <p className="text-sm text-slate-400">
              Choose which Ollama model Melvin should use for your conversations. Selecting &quot;Use Melvin default&quot; honors the global configuration.
            </p>
            <div className="grid gap-3 md:grid-cols-2 items-end">
              <label className="flex flex-col gap-2 text-sm text-slate-300">
                Model for my chats
                <select
                  className="p-3 rounded bg-slate-800 text-white"
                  value={modelPreference?.preferred_model ?? defaultModelOptionValue}
                  onChange={(e) => handleModelPreferenceSelect(e.target.value)}
                  disabled={!modelOptions}
                >
                  <option value={defaultModelOptionValue}>
                    Use Melvin default {modelOptions ? `(${modelOptions.current})` : ''}
                  </option>
                  {modelOptions?.available.map((name) => (
                    <option key={`self-${name}`} value={name}>{name}</option>
                  ))}
                </select>
              </label>
              <div className="space-y-2 text-sm text-slate-300">
                <p>
                  Effective model:{' '}
                  <span className="font-semibold">{modelPreference?.effective_model ?? modelOptions?.current ?? '...'}</span>
                </p>
                <button
                  className="text-slate-400 underline disabled:opacity-50"
                  onClick={() => saveModelPreference(null)}
                  disabled={!modelPreference?.preferred_model}
                >
                  Reset to default
                </button>
              </div>
            </div>
            {modelPreferenceStatus && <p className="text-xs text-slate-400">{modelPreferenceStatus}</p>}
          </div>

          {isAdmin && (
            <>
              <div className="bg-slate-900 p-6 rounded-lg shadow space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Default Model (admins)</h2>
                  <button className="text-sm underline" onClick={loadModelOptions}>Refresh</button>
                </div>
                {modelStatus && <p className="text-sm text-red-300">{modelStatus}</p>}
                {modelOptions ? (
                  <div className="grid gap-3 md:grid-cols-2 items-end">
                    <label className="flex flex-col gap-2 text-sm text-slate-300">
                      Active model
                      <select
                        className="p-3 rounded bg-slate-800 text-white"
                        value={modelOptions.current}
                        onChange={async (e) => {
                          const next = e.target.value;
                          setModelStatus(null);
                          try {
                            const response = await api.post<ModelOptions>('/models/ollama', { model: next }, authHeaders);
                            setModelOptions(response.data);
                            setModelStatus(`Model switched to ${next}`);
                            await loadModelPreference();
                            await loadUserModelPrefs();
                          } catch (error) {
                            if (!handleAuthError(error, 'Failed to switch model')) {
                              setModelStatus('Model change failed.');
                            }
                          }
                        }}
                      >
                        {modelOptions.available.map((name) => (
                          <option key={`global-${name}`} value={name}>{name}</option>
                        ))}
                      </select>
                    </label>
                    <div className="text-sm text-slate-400">
                      <p>Models are fetched from the Ollama service configured for Melvin.</p>
                      <p>Ensure the selected model is pulled and available.</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-400 text-sm">Loading model list...</p>
                )}
              </div>

              <div className="bg-slate-900 p-6 rounded-lg shadow space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">User overrides</h2>
                  <button className="text-sm underline" onClick={loadUserModelPrefs}>Refresh</button>
                </div>
                {userModelPrefsStatus && <p className="text-sm text-slate-300">{userModelPrefsStatus}</p>}
                {userModelPrefs.length === 0 ? (
                  <p className="text-slate-400 text-sm">No users found.</p>
                ) : (
                  <div className="space-y-3">
                    {userModelPrefs.map((entry) => (
                      <div key={entry.id} className="bg-slate-800 p-4 rounded flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="font-semibold text-white flex items-center gap-2">
                            {entry.username}
                            {entry.is_admin && (
                              <span className="text-xs text-blue-300 border border-blue-500 rounded-full px-2 py-0.5">Admin</span>
                            )}
                          </p>
                          <p className="text-xs text-slate-400">Effective model: {entry.effective_model}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <select
                            className="p-2 rounded bg-slate-900 text-white text-sm"
                            value={entry.preferred_model ?? defaultModelOptionValue}
                            onChange={(e) => handleAdminModelPreferenceSelect(entry.id, e.target.value)}
                            disabled={!modelOptions || updatingUserModelId === entry.id}
                          >
                            <option value={defaultModelOptionValue}>
                              Use default {modelOptions ? `(${modelOptions.current})` : ''}
                            </option>
                            {modelOptions?.available.map((name) => (
                              <option key={`pref-${entry.id}-${name}`} value={name}>{name}</option>
                            ))}
                          </select>
                          {updatingUserModelId === entry.id && <span className="text-xs text-slate-400">Saving…</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-slate-900 p-6 rounded-lg shadow">
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
              </div>
            </>
          )}
        </section>
      )}

      {insightOpen && insightMessage && (
        <div className="fixed inset-0 z-40">
          <button className="absolute inset-0 bg-black/40" onClick={() => { setInsightOpen(false); setInsightMessage(null); }} aria-label="Close insights panel" />
          <div className="absolute right-0 top-0 h-full w-full max-w-md bg-slate-950 text-slate-100 shadow-2xl p-6 overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-blue-300">Conversation insights</p>
                <h2 className="text-2xl font-bold">Under the hood</h2>
                <p className="text-slate-400 text-sm">Inspect Melvin&apos;s reasoning chain and the exact context fed to the model.</p>
              </div>
              <button className="text-sm text-slate-400 hover:text-white" onClick={() => { setInsightOpen(false); setInsightMessage(null); }}>
                Close
              </button>
            </div>
            <div className="space-y-4">
              <div className="bg-slate-900/60 rounded-lg p-4">
                <p className="text-sm text-slate-400 mb-2">Response snapshot</p>
                <p className="text-slate-200">{insightMessage.content}</p>
                <p className="text-xs text-slate-500 mt-2">{new Date(insightMessage.created_at).toLocaleString()}</p>
              </div>
              {insightMessage.thinking && insightMessage.thinking.length > 0 && (
                <div className="bg-slate-900/60 rounded-lg p-4 space-y-2">
                  <p className="font-semibold text-white">Reasoning steps</p>
                  <ul className="space-y-2 text-sm">
                    {insightMessage.thinking.map((step, idx) => (
                      <li key={`${step.label}-${idx}`} className="border-l border-blue-500/40 pl-3">
                        <p className="text-slate-200 font-semibold">{step.label}</p>
                        <p className="text-slate-400">{step.detail}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {insightMessage.context && (
                <div className="space-y-3">
                  {[
                    { label: 'Rules context', key: 'rules' },
                    { label: 'Cards context', key: 'cards' },
                    { label: 'Rulings context', key: 'rulings' },
                    { label: 'Reference guides', key: 'references' },
                    { label: 'Player guidance', key: 'player_guidance' },
                    { label: 'State snapshot', key: 'state' },
                    { label: 'Rule-engine tools', key: 'tools' },
                    { label: 'External card notes', key: 'external_cards' },
                    { label: 'Model used', key: 'model' },
                  ].map((section) => {
                    const value = (insightMessage.context as Record<string, unknown>)[section.key];
                    const formatted = typeof value === 'string'
                      ? value.trim()
                      : value
                        ? JSON.stringify(value, null, 2)
                        : '';
                    return (
                      <div key={section.key} className="bg-slate-900/40 rounded-lg p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-400">{section.label}</p>
                        <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-200 max-h-48 overflow-y-auto">
                          {formatted || 'No data included for this section.'}
                        </pre>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
