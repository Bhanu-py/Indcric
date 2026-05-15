/* global React, Card, Badge, Button, Eyebrow, RatingBar, VoteBar, Avatar, PlayerChip, StatColumn, Icons */
const { Pin, Clock, Calendar: Cal, Check, Close, Share, Copy } = Icons;

function SessionDetailScreen({ session, players, currentUser, onBack }) {
  const [vote, setVote] = React.useState(session.userVote || null);
  const [teamA] = React.useState(session.teamA || []);
  const [teamB] = React.useState(session.teamB || []);
  const yes = (session.poll?.yes || 0) + (vote === 'yes' && !session.userVote ? 1 : 0);
  const no  = (session.poll?.no  || 0) + (vote === 'no'  && !session.userVote ? 1 : 0);

  return (
    <div style={{maxWidth:1024, margin:'0 auto', padding:'28px 24px',
                 display:'flex', flexDirection:'column', gap:18}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none'
      }}>← Back to dashboard</a>

      {/* Hero card */}
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

      {/* Cost split */}
      <Card>
        <SectionHeader title="Cost split"/>
        <div style={{padding:'14px 22px', display:'grid', gridTemplateColumns:'repeat(3, 1fr)'}}>
          <StatColumn first label="● Hall fee"   value="€72"  dot="var(--stone-400)"/>
          <StatColumn       label="● Players"    value={players.length} dot="var(--sky-500)"/>
          <StatColumn       label="● Per player" value={`€${(72/players.length).toFixed(2)}`} dot="var(--pitch-500)"/>
        </div>
      </Card>

      {/* Availability poll */}
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

      {/* Teams */}
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:18}}>
        <TeamCard name="Team A" tone="pitch" captain={teamA[0]} players={teamA}/>
        <TeamCard name="Team B" tone="amber" captain={teamB[0]} players={teamB}/>
      </div>

      {/* Going list */}
      <Card>
        <SectionHeader title={`Going · ${players.length}`}/>
        <div style={{padding:18, display:'flex', flexWrap:'wrap', gap:8}}>
          {players.map(p => <PlayerChip key={p.username} player={p}/>)}
        </div>
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

function TeamCard({ name, tone, captain, players }) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  return (
    <Card>
      <div style={{padding:'12px 18px', borderBottom:'1px solid var(--stone-100)',
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
      <div style={{padding:16, display:'flex', flexDirection:'column', gap:6, minHeight:120}}>
        {players.length
          ? players.map(p => <PlayerChip key={p.username} player={p} captain={p === captain}/>)
          : <div style={{textAlign:'center', fontSize:12, color:'var(--stone-400)', padding:'20px 0'}}>Not assigned yet</div>}
      </div>
    </Card>
  );
}

window.SessionDetailScreen = SessionDetailScreen;
