/* global React, Card, Badge, Button, RoleBadge, RatingBar, Avatar, PlayerChip, Eyebrow, Icons */
const { Users: UsersIc, Share, Refresh, Plus, Close, ChevRt: ChevRtIc, Trophy } = Icons;

/* ────────── Team Balance / Draft ──────────
   Given a pool of available players, distribute them across two teams to
   minimise the gap in mean skill (batting + bowling + fielding) / 3. */
function TeamBalanceScreen({ session, allPlayers, onBack }) {
  // pool = everyone who said yes
  const initialPool = React.useMemo(() => (
    allPlayers.map(p => ({
      ...p,
      rating: ((p.batting || 3) + (p.bowling || 3) + (p.fielding || 3)) / 3,
    }))
  ), [allPlayers]);

  const [pool, setPool] = React.useState(initialPool.slice(10));
  const [teamA, setTeamA] = React.useState(initialPool.slice(0, 5));
  const [teamB, setTeamB] = React.useState(initialPool.slice(5, 10));
  const [autoBalanced, setAutoBalanced] = React.useState(false);

  const mean = (arr) => arr.length ? arr.reduce((s, p) => s + p.rating, 0) / arr.length : 0;
  const ratingA = mean(teamA), ratingB = mean(teamB);
  const gap = Math.abs(ratingA - ratingB);

  const rebalance = () => {
    const all = [...teamA, ...teamB, ...pool].sort((a, b) => b.rating - a.rating);
    const A = [], B = [];
    // snake draft
    all.forEach((p, i) => {
      const round = Math.floor(i / 2);
      const goesA = round % 2 === 0 ? (i % 2 === 0) : (i % 2 === 1);
      if (goesA && A.length < 6) A.push(p);
      else if (B.length < 6) B.push(p);
      else (A.length <= B.length ? A : B).push(p);
    });
    setTeamA(A.slice(0,6));
    setTeamB(B.slice(0,6));
    setPool(all.filter(p => !A.slice(0,6).includes(p) && !B.slice(0,6).includes(p)));
    setAutoBalanced(true);
  };

  const moveTo = (player, target) => {
    const remove = (arr, p) => arr.filter(x => x.username !== p.username);
    setTeamA(target === 'A' ? [...remove(teamA, player), player] : remove(teamA, player));
    setTeamB(target === 'B' ? [...remove(teamB, player), player] : remove(teamB, player));
    setPool(target === 'pool' ? [...remove(pool, player), player] : remove(pool, player));
    setAutoBalanced(false);
  };

  return (
    <div style={{maxWidth:1280, margin:'0 auto', padding:'28px 24px'}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none', marginBottom:14
      }}>← Back to dashboard</a>

      <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between',
                   gap:16, marginBottom:20, flexWrap:'wrap'}}>
        <div>
          <h1 style={{fontSize:22, fontWeight:600, color:'var(--stone-900)', margin:0,
                      letterSpacing:'-0.02em'}}>Team balance · Draft</h1>
          <p style={{fontSize:13, color:'var(--stone-500)', margin:'4px 0 0'}}>
            Drag-equivalent: click a player to send them to A, B or back to pool. Use auto-balance for a snake draft.
          </p>
        </div>
        <div style={{display:'flex', gap:8}}>
          <Button variant="secondary" icon={<Refresh size={13} sw={1.75}/>} onClick={rebalance}>Auto-balance</Button>
          <Button variant="primary" icon={<Share size={13} sw={1.75}/>}>Share line-ups</Button>
        </div>
      </div>

      {/* Balance meter */}
      <Card style={{marginBottom:16}}>
        <div style={{padding:'14px 18px',
                     display:'grid', gridTemplateColumns:'1fr auto 1fr', alignItems:'center', columnGap:18}}>
          <TeamHeader name="Team A" tone="pitch" rating={ratingA} count={teamA.length}/>
          <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap:6, minWidth:120}}>
            <div style={{
              fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
              textTransform:'uppercase', letterSpacing:'0.08em',
            }}>Skill gap</div>
            <div style={{
              fontSize:20, fontWeight:600, color: gap < 0.15 ? 'var(--emerald-700)' : 'var(--stone-900)',
              letterSpacing:'-0.01em', fontFeatureSettings:'"tnum" 1', lineHeight:1,
            }}>{gap.toFixed(2)}</div>
            <Badge tone={gap < 0.15 ? 'green' : gap < 0.5 ? 'amber' : 'red'}>
              {gap < 0.15 ? 'Balanced' : gap < 0.5 ? 'Close' : 'Uneven'}
            </Badge>
          </div>
          <TeamHeader name="Team B" tone="amber" rating={ratingB} count={teamB.length}/>
        </div>
      </Card>

      {/* Two columns + pool */}
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:14, marginBottom:18}}>
        <TeamSlot name="Team A" tone="pitch" players={teamA}
                  onMoveTo={(p, t) => moveTo(p, t)} otherTeam="B"/>
        <TeamSlot name="Team B" tone="amber" players={teamB}
                  onMoveTo={(p, t) => moveTo(p, t)} otherTeam="A"/>
      </div>

      <Eyebrow>Available pool · {pool.length}</Eyebrow>
      <Card>
        <div style={{padding:14, display:'flex', flexWrap:'wrap', gap:8}}>
          {pool.length === 0 && <div style={{fontSize:12, color:'var(--stone-400)', padding:'10px 4px'}}>Everyone assigned.</div>}
          {pool.map(p => (
            <PoolChip key={p.username} player={p}
                      onAddA={() => moveTo(p, 'A')} onAddB={() => moveTo(p, 'B')}/>
          ))}
        </div>
      </Card>
    </div>
  );
}

function TeamHeader({ name, tone, rating, count }) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  return (
    <div style={{display:'flex', alignItems:'center', gap:10}}>
      <div style={{width:8, height:8, borderRadius:'50%', background: accent}}/>
      <div>
        <div style={{fontSize:14, fontWeight:600, color:'var(--stone-900)',
                     letterSpacing:'-0.005em'}}>{name}</div>
        <div style={{
          fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-500)',
          letterSpacing:'0.04em',
        }}>
          {count} players · avg {rating.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

function TeamSlot({ name, tone, players, onMoveTo, otherTeam }) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  return (
    <Card>
      <div style={{padding:'12px 18px', borderBottom:'1px solid var(--stone-100)',
                   display:'flex', alignItems:'center', gap:10}}>
        <div style={{width:6, height:6, borderRadius:'50%', background: accent}}/>
        <h3 style={{fontSize:13, fontWeight:600, color:'var(--stone-800)', margin:0,
                    letterSpacing:'-0.005em'}}>{name}</h3>
        <span style={{
          marginLeft:'auto', fontFamily:'var(--font-mono)', fontSize:10,
          color:'var(--stone-400)', letterSpacing:'0.04em',
        }}>{players.length} · drop to remove</span>
      </div>
      <div style={{padding:14, display:'flex', flexDirection:'column', gap:6, minHeight:200}}>
        {players.length === 0 && (
          <div style={{textAlign:'center', fontSize:12, color:'var(--stone-400)', padding:'30px 0'}}>
            No players yet
          </div>
        )}
        {players.map(p => (
          <div key={p.username} style={{
            display:'flex', alignItems:'center', justifyContent:'space-between',
            padding:'8px 12px', border:'1px solid var(--stone-100)', borderRadius:10, background:'#fff',
          }}>
            <div style={{display:'flex', alignItems:'center', gap:10, minWidth:0}}>
              <Avatar user={p} size={26}/>
              <div style={{minWidth:0}}>
                <div style={{fontSize:13, fontWeight:500, color:'var(--stone-800)'}}>{p.username}</div>
                <div style={{
                  fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
                  letterSpacing:'0.04em',
                }}>{p.role} · {p.rating.toFixed(2)}</div>
              </div>
            </div>
            <div style={{display:'flex', alignItems:'center', gap:6}}>
              <RatingBar value={p.rating} compact/>
              <button onClick={() => onMoveTo(p, otherTeam)} title={`Swap to Team ${otherTeam}`} style={{
                width:22, height:22, borderRadius:6, border:'1px solid var(--stone-200)',
                background:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                cursor:'pointer', color:'var(--stone-500)',
              }}>
                <ChevRtIc size={12} sw={2}/>
              </button>
              <button onClick={() => onMoveTo(p, 'pool')} title="Back to pool" style={{
                width:22, height:22, borderRadius:6, border:'1px solid var(--stone-200)',
                background:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                cursor:'pointer', color:'var(--stone-400)',
              }}>
                <Close size={12} sw={2}/>
              </button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function PoolChip({ player, onAddA, onAddB }) {
  const roleToneMap = {
    batsman:    { bg:'var(--sky-100)',    bd:'#bae6fd',   fg:'var(--sky-800)' },
    bowler:     { bg:'var(--red-50)',     bd:'var(--red-100)', fg:'var(--red-800)' },
    allrounder: { bg:'var(--purple-100)', bd:'#e9d5ff',   fg:'var(--purple-800)' },
    keeper:     { bg:'#fff',              bd:'var(--stone-200)', fg:'var(--stone-800)' },
  };
  const t = roleToneMap[player.role] || roleToneMap.keeper;
  return (
    <div style={{
      display:'inline-flex', alignItems:'center', gap:8, padding:'3px 3px 3px 8px',
      background:t.bg, color:t.fg, border:`1px solid ${t.bd}`, borderRadius:8,
      fontSize:13, fontWeight:500, letterSpacing:'0.005em',
    }}>
      <span>{player.username}</span>
      <span style={{
        fontFamily:'var(--font-mono)', fontSize:10, opacity:0.7,
      }}>· {player.rating.toFixed(1)}</span>
      <span style={{display:'inline-flex', gap:2, marginLeft:4}}>
        <button onClick={onAddA} title="Send to Team A" style={btn('var(--pitch-700)')}>A</button>
        <button onClick={onAddB} title="Send to Team B" style={btn('var(--amber-600)')}>B</button>
      </span>
    </div>
  );
}
function btn(bg) { return {
  width:18, height:18, borderRadius:5, border:'none', background:bg, color:'#fff',
  fontSize:10, fontWeight:600, cursor:'pointer', fontFamily:'inherit', lineHeight:1,
}; }

window.TeamBalanceScreen = TeamBalanceScreen;
