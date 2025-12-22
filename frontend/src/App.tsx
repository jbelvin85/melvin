import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';
import ScryfallSearch from './components/ScryfallSearch';
import BoardBuilder from './components/BoardBuilder';

type Conversation = {
  id: number;
  title: string;
  created_at: string;
};

type Message = {
  sender: string;
  content: string;
  created_at: string;
};

type AccountRequest = {
  id: number;
  username: string;
  status: string;
  created_at: string;
};

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
  const [requestUsername, setRequestUsername] = useState('');
  const [requestPassword, setRequestPassword] = useState('');
  const [requestStatus, setRequestStatus] = useState<string | null>(null);

  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('melvin_token'));
  const [isAdmin, setIsAdmin] = useState(false);

  const authHeaders = useMemo(() => ({ headers: { Authorization: token ? `Bearer ${token}` : '' } }), [token]);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newConversationTitle, setNewConversationTitle] = useState('New Conversation');
  const [question, setQuestion] = useState('');

  const [pendingRequests, setPendingRequests] = useState<AccountRequest[]>([]);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      const payload = decodeToken(token);
      setIsAdmin(payload?.admin ?? false);
      loadConversations();
      if (payload?.admin) {
        loadPendingRequests();
      }
    }
  }, [token]);

  const loadConversations = async () => {
    if (!token) return;
    try {
      const response = await api.get<Conversation[]>('/conversations', authHeaders);
      setConversations(response.data);
      if (response.data.length && !selectedConversation) {
        selectConversation(response.data[0]);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const selectConversation = async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    try {
      const response = await api.get(`/conversations/${conversation.id}`, authHeaders);
      setMessages(response.data.messages ?? []);
    } catch (error) {
      console.error(error);
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
      localStorage.setItem('melvin_token', receivedToken);
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
      const response = await api.post('/conversations', {
        title: newConversationTitle,
      }, authHeaders);
      setNewConversationTitle('New Conversation');
      loadConversations();
      selectConversation(response.data);
    } catch (error) {
      alert('Failed to create conversation');
    }
  };

  const handleSendQuestion = async () => {
    if (!selectedConversation || !question.trim()) return;
    const convoId = selectedConversation.id;
    const userMessage: Message = { sender: 'user', content: question, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    try {
      const response = await api.post(`/conversations/${convoId}/chat`, {
        question: userMessage.content,
      }, authHeaders);
      setMessages(prev => [...prev, response.data]);
    } catch (error) {
      alert('Failed to send message');
    }
  };

  const loadPendingRequests = async () => {
    if (!token) return;
    try {
      const response = await api.get<AccountRequest[]>('/auth/requests', authHeaders);
      setPendingRequests(response.data);
    } catch (error) {
      console.error('Failed to load pending requests');
    }
  };

  const handleApprove = async (requestId: number) => {
    try {
      await api.post(`/auth/requests/${requestId}/approve`, {}, authHeaders);
      setAdminStatus('Request approved');
      loadPendingRequests();
    } catch (error) {
      setAdminStatus('Failed to approve request');
    }
  };

  const handleDeny = async (requestId: number) => {
    try {
      await api.post(`/auth/requests/${requestId}/deny`, {}, authHeaders);
      setAdminStatus('Request denied');
      loadPendingRequests();
    } catch (error) {
      setAdminStatus('Failed to deny request');
    }
  };

  const handleLogout = () => {
    setToken(null);
    setIsAdmin(false);
    localStorage.removeItem('melvin_token');
    setConversations([]);
    setMessages([]);
    setSelectedConversation(null);
  };

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Melvin</h1>
          <p className="text-slate-400">Magic: The Gathering rules assistant</p>
        </div>
        {token && (
          <button className="bg-red-600 px-4 py-2 rounded" onClick={handleLogout}>
            Logout
          </button>
        )}
      </header>

      {!token && (
        <div className="grid md:grid-cols-2 gap-6">
          <section className="bg-slate-900 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Request an Account</h2>
            <p className="text-sm text-slate-400 mb-4">
              Submit your desired username and password. An administrator will review your request; try logging in later to check whether you&apos;ve been approved.
            </p>
            <label className="block mb-2 text-sm">Username</label>
            <input className="w-full p-2 rounded bg-slate-800" value={requestUsername} onChange={(e) => setRequestUsername(e.target.value)} />
            <label className="block mb-2 mt-4 text-sm">Password</label>
            <input type="password" className="w-full p-2 rounded bg-slate-800" value={requestPassword} onChange={(e) => setRequestPassword(e.target.value)} />
            <button className="mt-4 bg-blue-600 px-4 py-2 rounded" onClick={handleRequestAccount}>
              Submit Request
            </button>
            {requestStatus && <p className="text-sm text-green-400 mt-3">{requestStatus}</p>}
          </section>

          <section className="bg-slate-900 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Login</h2>
            <label className="block mb-2 text-sm">Username</label>
            <input className="w-full p-2 rounded bg-slate-800" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} />
            <label className="block mb-2 mt-4 text-sm">Password</label>
            <input type="password" className="w-full p-2 rounded bg-slate-800" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
            <button className="mt-4 bg-green-600 px-4 py-2 rounded" onClick={handleLogin}>
              Login
            </button>
          </section>
        </div>
      )}

      {token && (
        <div className="grid md:grid-cols-3 gap-6">
          <section className="bg-slate-900 p-4 rounded-lg shadow md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <input className="flex-1 p-2 rounded bg-slate-800" value={newConversationTitle} onChange={(e) => setNewConversationTitle(e.target.value)} />
              <button className="bg-blue-600 px-3 py-2 rounded" onClick={handleCreateConversation}>+</button>
            </div>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
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
            <div className="flex-1 overflow-y-auto space-y-3 mb-4">
              {messages.map((message, idx) => (
                <div key={idx} className={`p-3 rounded ${message.sender === 'user' ? 'bg-blue-900/40' : 'bg-slate-800'}`}>
                  <p className="text-sm text-slate-400 mb-1">{message.sender} — {new Date(message.created_at).toLocaleTimeString()}</p>
                  <p>{message.content}</p>
                </div>
              ))}
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

      {token && isAdmin && (
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

      <ScryfallSearch />
      <BoardBuilder />
    </div>
  );
}

export default App;
