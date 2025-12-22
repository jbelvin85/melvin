import axios from 'axios';
import { useEffect, useState } from 'react';

const api = axios.create({ baseURL: '/api' });

type CardSlot = {
  id: string;
  card_name: string;
  controller: string;
  tapped?: boolean;
  type_line?: string;
};

export default function BoardBuilder() {
  const [name, setName] = useState('My Board');
  const [slots, setSlots] = useState<CardSlot[]>([]);
  const [owner, setOwner] = useState('tester');
  const [ownerMana, setOwnerMana] = useState<number>(3);
  const [savedStates, setSavedStates] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<Record<string, string[]>>({});
  const [results, setResults] = useState<Record<string, any>>({});

  useEffect(() => { loadStates(); }, []);

  const loadStates = async () => {
    try { const res = await api.get('/game_state'); setSavedStates(res.data); } catch (e) { console.error(e); }
  };

  const addSlot = () => {
    setSlots(prev => [...prev, { id: String(Date.now()), card_name: '', controller: owner, tapped: false }]);
  };

  const save = async () => {
    const payload = { name, owner, state: { players: [{name: owner, life:40, id:'p1', mana_available: ownerMana}], battlefield: slots, stack: [] } };
    try {
      await api.post('/game_state', payload);
      setSlots([]);
      loadStates();
    } catch (e) { console.error(e); }
  };

  const analyze = async (stateId: number) => {
    try {
      const res = await api.get(`/game_state/${stateId}`);
      const question = `Given this board state: ${JSON.stringify(res.data.state)} what will happen if players pass priority?`;
      const chatRes = await api.post('/conversations/1/chat', { question });
      alert(chatRes.data.content);
    } catch (e:any) { alert(e.response?.data?.detail ?? 'Failed to analyze'); }
  };

  const fetchAutocomplete = async (slotId: string, q: string) => {
    if (!q || q.length < 2) {
      setSuggestions(prev => ({ ...prev, [slotId]: [] }));
      return;
    }
    try {
      const res = await api.get('/scryfall/autocomplete', { params: { q } });
      setSuggestions(prev => ({ ...prev, [slotId]: res.data.data ?? [] }));
    } catch (e) {
      console.error(e);
      setSuggestions(prev => ({ ...prev, [slotId]: [] }));
    }
  };

  const handleSlotChange = (slotId: string, cardName: string) => {
    setSlots(prev => prev.map(s => s.id === slotId ? { ...s, card_name: cardName } : s));
    fetchAutocomplete(slotId, cardName);
    // debounce autovalidation
    if ((window as any)._validateTimers === undefined) (window as any)._validateTimers = {};
    const timers = (window as any)._validateTimers;
    if (timers[slotId]) clearTimeout(timers[slotId]);
    timers[slotId] = setTimeout(() => validateSlot(slotId), 700);
  };

  const selectSuggestion = (slotId: string, name: string) => {
    setSlots(prev => prev.map(s => s.id === slotId ? { ...s, card_name: name } : s));
    setSuggestions(prev => ({ ...prev, [slotId]: [] }));
    fetchCardPreview(slotId, name);
    // validate after selecting suggestion
    setTimeout(() => validateSlot(slotId), 200);
  };

  const fetchCardPreview = async (slotId: string, name: string) => {
    try {
      const res = await api.get(`/scryfall/card/${encodeURIComponent(name)}`);
      setSlots(prev => prev.map(s => s.id === slotId ? { ...s, type_line: res.data.type_line } : s));
      setResults(prev => ({ ...prev, [slotId]: { ...(prev[slotId] ?? {}), preview: res.data } }));
    } catch (e) {
      console.error(e);
    }
  };

  const validateSlot = async (slotId: string) => {
    const slot = slots.find(s => s.id === slotId);
    if (!slot) return;
    const statePayload = { players: [{ id: 'p1', name: owner, mana_available: ownerMana }], battlefield: slots, stack: [] };
    try {
      const castRes = await api.post('/rules/is_castable', {
        state: statePayload,
        player_id: 'p1',
        card_name: slot.card_name,
      });
      const valRes = await api.post('/rules/validate_targets', {
        state: statePayload,
        spell: { card_name: slot.card_name, targets: [] },
      });
      setResults(prev => ({ ...prev, [slotId]: { cast: castRes.data, validate: valRes.data } }));
    } catch (e) {
      console.error(e);
      setResults(prev => ({ ...prev, [slotId]: { error: 'validation_failed' } }));
    }
  };

  return (
    <section className="bg-slate-900 p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Board Builder</h2>
      <div className="mb-4 flex gap-2">
        <input className="p-2 rounded bg-slate-800" value={name} onChange={e => setName(e.target.value)} />
        <input className="p-2 rounded bg-slate-800" value={owner} onChange={e => setOwner(e.target.value)} />
        <input type="number" className="p-2 rounded bg-slate-800 w-24" value={ownerMana} onChange={e => setOwnerMana(Number(e.target.value))} />
        <button className="bg-blue-600 px-3 py-2 rounded" onClick={addSlot}>Add Slot</button>
        <button className="bg-green-600 px-3 py-2 rounded" onClick={save}>Save State</button>
      </div>

      <div className="space-y-2 mb-4">
        {slots.map((s, idx) => (
          <div key={s.id} className="bg-slate-800 p-3 rounded">
            <div className="flex gap-2 items-center">
              <input className="flex-1 p-2 rounded bg-slate-700" value={s.card_name} onChange={e => handleSlotChange(s.id, e.target.value)} placeholder="Card name" />
              <label className="flex items-center gap-2"><input type="checkbox" checked={s.tapped} onChange={e => setSlots(prev => prev.map(p => p.id===s.id ? {...p, tapped: e.target.checked} : p))} /> Tapped</label>
              <button className="bg-yellow-600 px-3 py-1 rounded" onClick={() => validateSlot(s.id)}>Validate</button>
            </div>
            {suggestions[s.id] && suggestions[s.id].length > 0 && (
              <div className="mt-2 grid grid-cols-3 gap-2">
                {suggestions[s.id].map((name) => (
                  <button key={name} className="text-left p-1 bg-slate-700 rounded" onClick={() => selectSuggestion(s.id, name)}>{name}</button>
                ))}
              </div>
            )}
            {results[s.id] && (
              <div className="mt-2 text-sm">
                {results[s.id].error && <p className="text-red-400">Validation failed</p>}
                {results[s.id].cast && <p className="text-green-300">Castable: {String(results[s.id].cast.castable)} — {results[s.id].cast.reason ?? ''}</p>}
                {results[s.id].validate && <p className="text-slate-300">Targets valid: {String(results[s.id].validate.valid)} — {results[s.id].validate.problems?.join(', ')}</p>}
                {results[s.id].preview && (
                  <div className="mt-2 flex gap-2 items-start">
                    {results[s.id].preview.image_uris?.normal && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={results[s.id].preview.image_uris.normal} alt={s.card_name} className="w-20 h-auto rounded" />
                    )}
                    <div>
                      <p className="font-semibold">{results[s.id].preview.name}</p>
                      <p className="text-sm text-slate-400">{results[s.id].preview.type_line}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div>
        <h3 className="font-semibold mb-2">Saved States</h3>
        <div className="space-y-2">
          {savedStates.map(s => (
            <div key={s.id} className="bg-slate-800 p-3 rounded flex justify-between items-center">
              <div>
                <p className="font-semibold">{s.name}</p>
                <p className="text-sm text-slate-400">Owner: {s.owner} — {new Date(s.updated_at).toLocaleString()}</p>
              </div>
              <div className="flex gap-2">
                <button className="bg-blue-600 px-3 py-1 rounded" onClick={() => analyze(s.id)}>Analyze</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
