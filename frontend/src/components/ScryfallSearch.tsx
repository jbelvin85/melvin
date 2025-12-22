import axios from 'axios';
import { useState } from 'react';

const api = axios.create({ baseURL: '/api' });

export default function ScryfallSearch() {
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const doSearch = async () => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await api.get('/scryfall/search', { params: { q } });
      setResults(res.data.data ?? []);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-slate-900 p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Scryfall Search</h2>
      <div className="flex gap-2 mb-4">
        <input className="flex-1 p-2 rounded bg-slate-800" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search cards (eg: sol ring)" />
        <button className="bg-blue-600 px-4 py-2 rounded" onClick={doSearch} disabled={loading}>{loading ? 'Searching...' : 'Search'}</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map((card:any) => (
          <div key={card.id} className="bg-slate-800 p-3 rounded flex gap-3 items-start">
            {card.image_uris?.normal && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={card.image_uris.normal} alt={card.name} className="w-20 h-auto rounded" />
            )}
            <div>
              <p className="font-semibold">{card.name} <span className="text-sm text-slate-400">{card.mana_cost ?? ''}</span></p>
              <p className="text-sm text-slate-400">{card.type_line}</p>
              <p className="text-sm mt-2">{card.oracle_text?.slice(0,200)}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
