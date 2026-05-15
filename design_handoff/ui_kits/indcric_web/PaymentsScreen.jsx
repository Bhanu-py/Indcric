/* global React, Card, Badge, Button, Eyebrow, Avatar, StatColumn, Icons */
const { Wallet, Check, Rupee, Send, Share, Copy, ChevRt } = Icons;

function PaymentsScreen({ matches, allPlayers, onBack }) {
  const [tab, setTab] = React.useState('match'); // 'match' | 'settle'
  const [selected, setSelected] = React.useState(matches[0]);
  const [paid, setPaid] = React.useState(new Set(selected.paid || []));

  // ── derive outstanding totals across all matches for the settlement view ──
  const balances = computeBalances(matches, allPlayers);

  const togglePaid = (username) => {
    const next = new Set(paid);
    next.has(username) ? next.delete(username) : next.add(username);
    setPaid(next);
  };

  // totals for header strip
  const totalOutstanding = balances.reduce((sum, b) => sum + Math.max(0, b.owes), 0);

  return (
    <div style={{maxWidth:1024, margin:'0 auto', padding:'28px 24px'}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none', marginBottom:14
      }}>← Back</a>

      <div style={{marginBottom:18}}>
        <h1 style={{fontSize:22, fontWeight:600, color:'var(--stone-900)', margin:0,
                    letterSpacing:'-0.02em'}}>Payments</h1>
        <p style={{fontSize:13, color:'var(--stone-500)', margin:'4px 0 0'}}>
          Track session payments and settle balances across the club
        </p>
      </div>

      {/* Snapshot strip */}
      <div style={{
        display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:14, marginBottom:18,
      }}>
        <Card>
          <div style={{padding:'12px 16px'}}>
            <StatColumn first label="● Outstanding" value={`€${totalOutstanding.toFixed(2)}`} dot="var(--amber-500)"/>
          </div>
        </Card>
        <Card>
          <div style={{padding:'12px 16px'}}>
            <StatColumn first label="● Matches · 30d" value={String(matches.length)} dot="var(--pitch-500)"/>
          </div>
        </Card>
        <Card>
          <div style={{padding:'12px 16px'}}>
            <StatColumn first label="● Settled" value={`${balances.filter(b => b.owes <= 0).length} / ${balances.length}`} dot="var(--emerald-600)"/>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div role="tablist" style={{
        display:'inline-flex', gap:4, marginBottom:16,
        background:'var(--stone-100)', padding:3, borderRadius:8,
      }}>
        <Tab active={tab==='match'} onClick={() => setTab('match')}>By match</Tab>
        <Tab active={tab==='settle'} onClick={() => setTab('settle')}>Who owes whom</Tab>
      </div>

      {tab === 'match' ? (
        <MatchView
          matches={matches} selected={selected} setSelected={(m) => { setSelected(m); setPaid(new Set(m.paid)); }}
          paid={paid} togglePaid={togglePaid} allPlayers={allPlayers}
        />
      ) : (
        <SettleView balances={balances}/>
      )}
    </div>
  );
}

function Tab({ active, children, onClick }) {
  return (
    <button onClick={onClick} role="tab" aria-selected={active} style={{
      padding:'5px 12px', borderRadius:6, border:'none', cursor:'pointer',
      fontSize:12, fontWeight:500, fontFamily:'inherit', lineHeight:1,
      background: active ? '#fff' : 'transparent',
      color: active ? 'var(--stone-900)' : 'var(--stone-500)',
      boxShadow: active ? 'var(--shadow-sm)' : 'none',
    }}>{children}</button>
  );
}

function MatchView({ matches, selected, setSelected, paid, togglePaid, allPlayers }) {
  return (
    <>
      <section style={{marginBottom:22}}>
        <Eyebrow>Select a match</Eyebrow>
        <div className="grid-3">
          {matches.map(m => {
            const isSel = m.id === selected.id;
            return (
              <a key={m.id} onClick={() => setSelected(m)} style={{
                display:'block', textDecoration:'none',
                background:'#fff', border:'1px solid var(--stone-100)', borderRadius:14,
                padding:14, cursor:'pointer',
                boxShadow: isSel ? '0 0 0 2px var(--pitch-500), var(--shadow-md)' : 'var(--shadow-sm)',
                transition:'box-shadow .15s'
              }}>
                <div style={{display:'flex', alignItems:'center', gap:12}}>
                  <div style={{
                    width:36, height:36, borderRadius:10, background:'var(--pitch-50)',
                    display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
                  }}>
                    <span style={{fontSize:13, fontWeight:600, color:'var(--pitch-800)', lineHeight:1}}>{m.dateDay}</span>
                    <span style={{fontFamily:'var(--font-mono)', fontSize:8, fontWeight:500,
                                  color:'var(--pitch-700)', letterSpacing:'0.06em'}}>{m.dateMonth}</span>
                  </div>
                  <div style={{minWidth:0, flex:1}}>
                    <p style={{fontSize:13, fontWeight:600, color:'var(--stone-800)', margin:0,
                               overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap',
                               letterSpacing:'-0.005em'}}>{m.name}</p>
                    <p style={{fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
                               margin:'2px 0 0'}}>{m.dateFull} · €{m.perPlayer}/p</p>
                  </div>
                  {isSel && <div style={{color:'var(--pitch-600)'}}><Check size={16}/></div>}
                </div>
              </a>
            );
          })}
        </div>
      </section>

      <section>
        <Eyebrow accent="var(--amber-500)">{selected.name} — payments</Eyebrow>
        <Card>
          <div style={{padding:'12px 18px', borderBottom:'1px solid var(--stone-100)',
                       display:'flex', alignItems:'center', justifyContent:'space-between'}}>
            <h3 style={{
              fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
              color:'var(--stone-500)', textTransform:'uppercase', letterSpacing:'0.08em',
              margin:0,
            }}>
              {paid.size} of {allPlayers.length} paid · €{((allPlayers.length - paid.size) * selected.perPlayer).toFixed(2)} outstanding
            </h3>
            <Button variant="primary" size="sm" icon={<Wallet size={12} sw={1.75}/>}>Save</Button>
          </div>
          <div style={{padding:12, display:'flex', flexDirection:'column', gap:6}}>
            {allPlayers.map(p => {
              const isPaid = paid.has(p.username);
              return (
                <label key={p.username} style={{
                  display:'flex', alignItems:'center', justifyContent:'space-between',
                  padding:'10px 14px', borderRadius:10, border:'1px solid var(--stone-100)',
                  cursor:'pointer', background: isPaid ? 'var(--pitch-50)' : '#fff',
                  transition:'all .15s'
                }}>
                  <div style={{display:'flex', alignItems:'center', gap:12}}>
                    <Avatar user={p} size={30}/>
                    <div>
                      <p style={{fontSize:13, fontWeight:500, color:'var(--stone-800)', margin:0}}>{p.username}</p>
                      <p style={{fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
                                 margin:'2px 0 0'}}>{p.role} · €{selected.perPlayer}</p>
                    </div>
                  </div>
                  <div style={{display:'flex', alignItems:'center', gap:10}}>
                    <Badge tone={isPaid ? 'green' : 'amber'}>{isPaid ? 'Paid' : 'Pending'}</Badge>
                    <input type="checkbox" checked={isPaid} onChange={() => togglePaid(p.username)}
                           style={{width:14, height:14, accentColor:'var(--pitch-600)', cursor:'pointer'}}/>
                  </div>
                </label>
              );
            })}
          </div>
        </Card>
      </section>
    </>
  );
}

function SettleView({ balances }) {
  // build a simple settlement plan: who pays whom what
  const plan = makeSettlementPlan(balances);

  return (
    <>
      <section style={{marginBottom:22}}>
        <Eyebrow accent="var(--amber-500)">Member balances</Eyebrow>
        <Card>
          <div style={{padding:12, display:'flex', flexDirection:'column', gap:6}}>
            {balances.map(b => {
              const owes = b.owes;
              const tone = owes > 0 ? 'amber' : owes < 0 ? 'green' : 'stone';
              const label = owes > 0 ? `Owes €${owes.toFixed(2)}`
                          : owes < 0 ? `Receives €${(-owes).toFixed(2)}`
                          : 'Settled';
              return (
                <div key={b.player.username} style={{
                  display:'flex', alignItems:'center', justifyContent:'space-between',
                  padding:'10px 14px', borderRadius:10, border:'1px solid var(--stone-100)',
                  background: '#fff',
                }}>
                  <div style={{display:'flex', alignItems:'center', gap:12}}>
                    <Avatar user={b.player} size={30}/>
                    <div>
                      <p style={{fontSize:13, fontWeight:500, color:'var(--stone-800)', margin:0}}>{b.player.username}</p>
                      <p style={{fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
                                 margin:'2px 0 0'}}>
                        Paid €{b.paid.toFixed(2)} of €{b.due.toFixed(2)} · {b.matches} matches
                      </p>
                    </div>
                  </div>
                  <Badge tone={tone}>{label}</Badge>
                </div>
              );
            })}
          </div>
        </Card>
      </section>

      <section>
        <Eyebrow>Suggested settlement</Eyebrow>
        <Card>
          <div style={{padding:'10px 18px', borderBottom:'1px solid var(--stone-100)',
                       display:'flex', alignItems:'center', justifyContent:'space-between'}}>
            <span style={{
              fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-500)',
              textTransform:'uppercase', letterSpacing:'0.08em',
            }}>{plan.length} transfer{plan.length !== 1 ? 's' : ''} to clear all balances</span>
            <Button variant="ghost" size="sm" icon={<Share size={13} sw={1.75}/>}>Share to WhatsApp</Button>
          </div>
          <div style={{padding:14, display:'flex', flexDirection:'column', gap:8}}>
            {plan.length === 0 && (
              <div style={{padding:'20px 0', textAlign:'center', fontSize:13, color:'var(--stone-400)'}}>
                All settled — nothing to pay.
              </div>
            )}
            {plan.map((t, i) => (
              <div key={i} style={{
                display:'grid', gridTemplateColumns:'1fr auto 1fr auto auto',
                alignItems:'center', columnGap:10,
                padding:'10px 14px', border:'1px solid var(--stone-100)', borderRadius:10,
              }}>
                <PersonCell player={t.from} role="from"/>
                <div style={{display:'flex', flexDirection:'column', alignItems:'center'}}>
                  <ChevRt size={14} sw={2} color="var(--stone-400)"/>
                </div>
                <PersonCell player={t.to} role="to"/>
                <span style={{
                  fontFamily:'var(--font-mono)', fontSize:13, fontWeight:600,
                  color:'var(--stone-900)', fontFeatureSettings:'"tnum" 1',
                }}>€{t.amount.toFixed(2)}</span>
                <Button variant="secondary" size="sm" icon={<Send size={11} sw={1.75}/>}>Ping</Button>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </>
  );
}

function PersonCell({ player, role }) {
  return (
    <div style={{display:'flex', alignItems:'center', gap:8, minWidth:0}}>
      <Avatar user={player} size={26}/>
      <div style={{minWidth:0}}>
        <div style={{fontSize:13, fontWeight:500, color:'var(--stone-800)',
                     overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{player.username}</div>
        <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                     textTransform:'uppercase', letterSpacing:'0.06em'}}>
          {role === 'from' ? 'PAYS' : 'RECEIVES'}
        </div>
      </div>
    </div>
  );
}

/* ────────── Settlement math ──────────
   For each player, sum up what they owe across matches minus what they've paid.
   Then greedily pair debtors with creditors. */
function computeBalances(matches, players) {
  return players.map(p => {
    let due = 0, paid = 0, matchCount = 0;
    matches.forEach(m => {
      due += m.perPlayer;
      matchCount += 1;
      if ((m.paid || []).includes(p.username)) paid += m.perPlayer;
    });
    return { player: p, due, paid, owes: due - paid, matches: matchCount };
  });
}

function makeSettlementPlan(balances) {
  // positive = owes, negative = should receive
  const debtors  = balances.filter(b => b.owes > 0.01).map(b => ({ ...b }))
                           .sort((a,b) => b.owes - a.owes);
  const credits  = balances.filter(b => b.owes < -0.01).map(b => ({ ...b, owes: -b.owes }))
                           .sort((a,b) => b.owes - a.owes);
  const plan = [];
  let i = 0, j = 0;
  while (i < debtors.length && j < credits.length) {
    const amount = Math.min(debtors[i].owes, credits[j].owes);
    plan.push({ from: debtors[i].player, to: credits[j].player, amount });
    debtors[i].owes -= amount;
    credits[j].owes -= amount;
    if (debtors[i].owes < 0.01) i++;
    if (credits[j].owes < 0.01) j++;
  }
  return plan;
}

window.PaymentsScreen = PaymentsScreen;
