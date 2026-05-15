/* global React, Card, Badge, Button, Eyebrow, RatingBar, VoteBar, Avatar, PlayerChip, StatColumn, Icons */
const { Pin, Clock, Calendar: Cal, Check, Close, Share, Refresh, ChevRt: ChevRtIc } = Icons;

/* ────────── Session Detail (now includes Team Balance / Draft) ──────────
   Visibility:
   • Member  — sees teams read-only
   • Staff   — can auto-balance, move players between teams + pool, share line-ups
*/
function SessionDetailScreen({ session, players, currentUser, onBack }) {
  const [vote, setVote] = React.useState(session.userVote || null);
  const isStaff = !!currentUser?.is_staff;

  // ── Pool / teams (in-page draft) ──────────────────────────────────────
  // Each player gets a derived "rating" so the skill-gap meter has something to compute.
  const withRatings = React.useMemo(() => (
    players.map(p => ({
      ...p,
      rating: ((p.batting || 3) + (p.bowling || 3) + (p.fielding || 3)) / 3,
    }))
  ), [players]);

  const [teamA, setTeamA] = React.useState(() => withRatings.slice(0, 5));
  const [teamB, setTeamB] = React.useState(() => withRatings.slice(5, 10));
  const [pool,  setPool ] = React.useState(() => withRatings.slice(10));

  const mean   = (arr) => arr.length ? arr.reduce((s, p) => s + p.rating, 0) / arr.length : 0;
  const rA     = mean(teamA), rB = mean(teamB);
  const gap    = Math.abs(rA - rB);

  const yes = (session.poll?.yes || 0) + (vote === 'yes' && !session.userVote ? 1 : 0);
  const no  = (session.poll?.no  || 0) + (vote === 'no'  && !session.userVote ? 1 : 0);

  const moveTo = (player, target) => {
    if (!isStaff) return;
    const remove = (arr, p) => arr.filter(x => x.username !== p.username);
    setTeamA(target === 'A' ? [...remove(teamA, player), player] : remove(teamA, player));
    setTeamB(target === 'B' ? [...remove(teamB, player), player] : remove(teamB, player));
    setPool (target === 'pool' ? [...remove(pool , player), player] : remove(pool , player));
  };

  const autoBalance = () => {
    if (!isStaff) return;
    const all = [...teamA, ...teamB, ...pool].sort((a, b) => b.rating - a.rating);
    const A = [], B = [];
    // snake-draft: A B B A A B B A …
    all.forEach((p, i) => {
      const round = Math.floor(i / 2);
      const aTurn = round % 2 === 0 ? (i % 2 === 0) : (i % 2 === 1);
      if (aTurn && A.length < 6) A.push(p);
      else if (B.length < 6)     B.push(p);
      else (A.length <= B.length ? A : B).push(p);
    });
    setTeamA(A.slice(0, 6));
    setTeamB(B.slice(0, 6));
    setPool(all.filter(p => !A.slice(0,6).includes(p) && !B.slice(0,6).includes(p)));
  };

  return (
    <div style={{maxWidth:1024, margin:'0 auto', padding:'28px 24px',
                 display:'flex', flexDirection:'column', gap:18}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none'
      }}>← Back to dashboard</a>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <Card>
        <div style={{height:60, background:'linear-gradient(90deg, var(--pitch-800), var(--pitch-600))'}}/>
        <div style={{padding:'0 22px 22px', marginTop:-22}}>
          <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between', marginBottom:14}}>
            <div style={{
              width:54, height:54, borderRadius:14, background:'#fff',
              border:'1px solid var(--stone-100)',
              display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
              boxShadow:'var(--shadow-md)',
            }}>
              <span style={{fontSize:20, fontWeight:600, color:'var(--stone-900)',
                            lineHeight:1, letterSpacing:'-0.02em'}}>{session.dateDay}</span>
              <span style={{fontFamily:'var(--font-mono)', fontSize:9, fontWeight:500,
                            color:'var(--stone-500)', letterSpacing:'0.06em', marginTop:2}}>{session.dateMonth}</span>
            </div>
            <div style={{display:'flex', gap:8}}>
              <Badge tone={session.poll?.closed ? 'stone' : 'green'}>
                {session.poll?.closed ? 'Poll closed' : '● Poll open'}
              </Badge>
              <Button variant="ghost" size="sm" icon={<Share size={13} sw={1.75}/>}>Share</Button>
            </div>
          </div>
          <h1 style={{fontSize:20, fontWeight:600, color:'var(--stone-900)', margin:'0 0 6px',
                      letterSpacing:'-0.015em'}}>{session.name}</h1>
          <div style={{display:'flex', flexWrap:'wrap', gap:14, fontSize:12, color:'var(--stone-500)'}}>
            <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Pin size={13}/>{session.location}</span>
            <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Clock size={13}/>{session.time} · {session.duration}h</span>
            <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Cal size={13}/>{session.dateLabel}</span>
          </div>
        </div>
      </Card>

      {/* ── Cost split ──────────────────────────────────────────────── */}
      <Card>
        <SectionHeader title="Cost split"/>
        <div style={{padding:'14px 22px', display:'grid', gridTemplateColumns:'repeat(3, 1fr)'}}>
          <StatColumn first label="● Hall fee"   value="€72"  dot="var(--stone-400)"/>
          <StatColumn       label="● Players"    value={players.length} dot="var(--sky-500)"/>
          <StatColumn       label="● Per player" value={`€${(72/players.length).toFixed(2)}`} dot="var(--pitch-500)"/>
        </div>
      </Card>

      {/* ── Availability poll ───────────────────────────────────────── */}
      <Card>
        <div style={{padding:'12px 22px', borderBottom:'1px solid var(--stone-100)',
                     display:'flex', alignItems:'center', justifyContent:'space-between'}}>
          <h2 style={{
            fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
            textTransform:'uppercase', letterSpacing:'0.08em',
            color:'var(--stone-500)', margin:0,
          }}>Availability poll</h2>
          <div style={{display:'flex', gap:6}}>
            <Badge tone="green">● {yes} Yes</Badge>
            <Badge tone="red">{no} No</Badge>
          </div>
        </div>
        <div style={{padding:18}}>
          <VoteBar yes={yes} total={yes + no}/>
          <div style={{display:'flex', gap:10, marginTop:14}}>
            <Button variant={vote==='yes' ? 'success' : 'secondary'} onClick={() => setVote('yes')}
                    style={{flex:1, justifyContent:'center', padding:'9px 14px'}}
                    icon={<Check size={14} sw={1.75}/>}>
              I'm in
            </Button>
            <Button variant={vote==='no' ? 'danger' : 'secondary'} onClick={() => setVote('no')}
                    style={{flex:1, justifyContent:'center', padding:'9px 14px'}}
                    icon={<Close size={14} sw={1.75}/>}>
              Can't make it
            </Button>
          </div>
        </div>
      </Card>

      {/* ── Team balance / draft ────────────────────────────────────── */}
      <Card>
        <div style={{padding:'12px 22px', borderBottom:'1px solid var(--stone-100)',
                     display:'flex', alignItems:'center', justifyContent:'space-between',
                     flexWrap:'wrap', gap:10}}>
          <h2 style={{
            fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
            textTransform:'uppercase', letterSpacing:'0.08em',
            color:'var(--stone-500)', margin:0,
          }}>Team balance · {isStaff ? 'Draft' : 'Read-only'}</h2>
          {isStaff && (
            <div style={{display:'flex', gap:6}}>
              <Button variant="secondary" size="sm" icon={<Refresh size={12} sw={1.75}/>}
                      onClick={autoBalance}>Auto-balance</Button>
              <Button variant="primary" size="sm" icon={<Share size={12} sw={1.75}/>}>
                Share line-ups
              </Button>
            </div>
          )}
        </div>

        {/* Balance meter */}
        <div style={{padding:'14px 22px',
                     display:'grid', gridTemplateColumns:'1fr auto 1fr',
                     alignItems:'center', columnGap:18,
                     borderBottom:'1px solid var(--stone-100)'}}>
          <TeamMeter name="Team A" tone="pitch" rating={rA} count={teamA.length}/>
          <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap:5, minWidth:110}}>
            <div style={{
              fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
              textTransform:'uppercase', letterSpacing:'0.08em',
            }}>Skill gap</div>
            <div style={{
              fontSize:20, fontWeight:600,
              color: gap < 0.15 ? 'var(--emerald-700)' : 'var(--stone-900)',
              letterSpacing:'-0.01em', fontFeatureSettings:'"tnum" 1', lineHeight:1,
            }}>{gap.toFixed(2)}</div>
            <Badge tone={gap < 0.15 ? 'green' : gap < 0.5 ? 'amber' : 'red'}>
              {gap < 0.15 ? 'Balanced' : gap < 0.5 ? 'Close' : 'Uneven'}
            </Badge>
          </div>
          <TeamMeter name="Team B" tone="amber" rating={rB} count={teamB.length}/>
        </div>

        {/* Two-team slot grid */}
        <div style={{padding:'14px 18px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
          <TeamSlot name="Team A" tone="pitch" players={teamA} otherTeam="B"
                    editable={isStaff} onMoveTo={moveTo}/>
          <TeamSlot name="Team B" tone="amber" players={teamB} otherTeam="A"
                    editable={isStaff} onMoveTo={moveTo}/>
        </div>

        {/* Available pool */}
        {(isStaff || pool.length > 0) && (
          <div style={{padding:'4px 18px 18px'}}>
            <div style={{
              fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
              textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8,
            }}>Available pool · {pool.length}</div>
            <div style={{
              padding:'10px 12px', border:'1px dashed var(--stone-200)', borderRadius:10,
              background:'var(--stone-50)',
              display:'flex', flexWrap:'wrap', gap:6, minHeight:36,
            }}>
              {pool.length === 0 && (
                <div style={{fontSize:12, color:'var(--stone-400)', padding:'6px 4px'}}>
                  Everyone assigned.
                </div>
              )}
              {pool.map(p => (
                <PoolChip key={p.username} player={p} editable={isStaff}
                          onAddA={() => moveTo(p, 'A')} onAddB={() => moveTo(p, 'B')}/>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function SectionHeader({ title }) {
  return (
    <div style={{padding:'12px 22px', borderBottom:'1px solid var(--stone-100)'}}>
      <h2 style={{
        fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
        textTransform:'uppercase', letterSpacing:'0.08em',
        color:'var(--stone-500)', margin:0,
      }}>{title}</h2>
    </div>
  );
}

function TeamMeter({ name, tone, rating, count }) {
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
        }}>{count} players · avg {rating.toFixed(2)}</div>
      </div>
    </div>
  );
}

function TeamSlot({ name, tone, players, otherTeam, editable, onMoveTo }) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  const captain = players[0];
  return (
    <div style={{
      border:'1px solid var(--stone-100)', borderRadius:12,
      background:'#fff', overflow:'hidden',
    }}>
      <div style={{padding:'10px 14px', borderBottom:'1px solid var(--stone-100)',
                   display:'flex', alignItems:'center', gap:10}}>
        <div style={{width:6, height:6, borderRadius:'50%', background: accent}}/>
        <h3 style={{fontSize:13, fontWeight:600, color:'var(--stone-800)', margin:0,
                    letterSpacing:'-0.005em'}}>{name}</h3>
        {captain && (
          <span style={{
            fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
            marginLeft:'auto', letterSpacing:'0.04em',
          }}>C · @{captain.username}</span>
        )}
      </div>
      <div style={{padding:10, display:'flex', flexDirection:'column', gap:6, minHeight:180}}>
        {players.length === 0 && (
          <div style={{textAlign:'center', fontSize:12, color:'var(--stone-400)', padding:'30px 0'}}>
            No players yet
          </div>
        )}
        {players.map(p => (
          <div key={p.username} style={{
            display:'flex', alignItems:'center', justifyContent:'space-between',
            padding:'7px 10px', border:'1px solid var(--stone-100)', borderRadius:8, background:'#fff',
          }}>
            <div style={{display:'flex', alignItems:'center', gap:9, minWidth:0}}>
              <Avatar user={p} size={24}/>
              <div style={{minWidth:0}}>
                <div style={{fontSize:12, fontWeight:500, color:'var(--stone-800)'}}>{p.username}</div>
                <div style={{
                  fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                  letterSpacing:'0.04em',
                }}>{p.role} · {p.rating.toFixed(2)}</div>
              </div>
            </div>
            <div style={{display:'flex', alignItems:'center', gap:6}}>
              <RatingBar value={p.rating} compact/>
              {editable && (
                <>
                  <button onClick={() => onMoveTo(p, otherTeam)} title={`Swap to Team ${otherTeam}`} style={{
                    width:20, height:20, borderRadius:5, border:'1px solid var(--stone-200)',
                    background:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                    cursor:'pointer', color:'var(--stone-500)',
                  }}>
                    <ChevRtIc size={11} sw={2}/>
                  </button>
                  <button onClick={() => onMoveTo(p, 'pool')} title="Back to pool" style={{
                    width:20, height:20, borderRadius:5, border:'1px solid var(--stone-200)',
                    background:'#fff', display:'flex', alignItems:'center', justifyContent:'center',
                    cursor:'pointer', color:'var(--stone-400)',
                  }}>
                    <Close size={11} sw={2}/>
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PoolChip({ player, editable, onAddA, onAddB }) {
  const roleToneMap = {
    batsman:    { bg:'var(--sky-100)',    bd:'#bae6fd',         fg:'var(--sky-800)' },
    bowler:     { bg:'var(--red-50)',     bd:'var(--red-100)',  fg:'var(--red-800)' },
    allrounder: { bg:'var(--purple-100)', bd:'#e9d5ff',         fg:'var(--purple-800)' },
    keeper:     { bg:'#fff',              bd:'var(--stone-200)', fg:'var(--stone-800)' },
  };
  const t = roleToneMap[player.role] || roleToneMap.keeper;
  return (
    <div style={{
      display:'inline-flex', alignItems:'center', gap:8,
      padding: editable ? '3px 3px 3px 8px' : '3px 8px',
      background:t.bg, color:t.fg, border:`1px solid ${t.bd}`, borderRadius:8,
      fontSize:12, fontWeight:500, letterSpacing:'0.005em',
    }}>
      <span>{player.username}</span>
      <span style={{fontFamily:'var(--font-mono)', fontSize:10, opacity:0.7}}>
        · {player.rating.toFixed(1)}
      </span>
      {editable && (
        <span style={{display:'inline-flex', gap:2, marginLeft:4}}>
          <button onClick={onAddA} title="Send to Team A" style={poolBtn('var(--pitch-700)')}>A</button>
          <button onClick={onAddB} title="Send to Team B" style={poolBtn('var(--amber-600)')}>B</button>
        </span>
      )}
    </div>
  );
}
function poolBtn(bg) { return {
  width:18, height:18, borderRadius:5, border:'none', background:bg, color:'#fff',
  fontSize:10, fontWeight:600, cursor:'pointer', fontFamily:'inherit', lineHeight:1,
}; }

window.SessionDetailScreen = SessionDetailScreen;
