/* global React, SessionCard, Button, Eyebrow, Card, Alert, StatColumn, Icons */
const { Plus, Calendar: CalIcon, Wallet, Users: UsersIcon, ArrowRt } = Icons;

function DashboardScreen({ user, sessions, onOpenSession, onDelete, onCreate, onNavigate }) {
  const upcoming = sessions.filter(s => !s.past);
  const past = sessions.filter(s => s.past);

  // Next session for the hero
  const next = upcoming[0];

  return (
    <div style={{maxWidth:1280, margin:'0 auto', padding:'28px 24px'}}>

      {/* ── Welcome row ── */}
      <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between',
                   gap:16, marginBottom:24, flexWrap:'wrap'}}>
        <div>
          <h1 style={{fontSize:24, fontWeight:600, color:'var(--stone-900)', margin:0,
                      letterSpacing:'-0.02em'}}>
            Welcome back, {user.name.split(' ')[0]} <span style={{display:'inline-block'}}>👋</span>
          </h1>
          <p style={{fontSize:13, color:'var(--stone-500)', marginTop:4, marginBottom:0}}>
            Here's what's happening with IndCric
          </p>
        </div>
        <div style={{display:'flex', gap:8}}>
          {user.is_staff && (
            <Button variant="primary" icon={<Plus size={13} sw={1.75}/>} onClick={onCreate}>
              New Session
            </Button>
          )}
        </div>
      </div>

      {/* ── Snapshot strip ── */}
      <div style={{
        display:'grid', gridTemplateColumns:'1.4fr 1fr 1fr 1fr', gap:14, marginBottom:24,
      }}>
        {/* Next session highlight */}
        {next ? (
          <Card hoverable style={{cursor:'pointer'}} accent="var(--pitch-600)">
            <div onClick={() => onOpenSession(next)} style={{padding:'14px 18px'}}>
              <div style={{
                fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8,
              }}>Next up · {next.dateLabel}</div>
              <div style={{fontSize:18, fontWeight:600, color:'var(--stone-900)',
                           letterSpacing:'-0.01em', lineHeight:1.2, marginBottom:6}}>
                {next.name}
              </div>
              <div style={{fontSize:12, color:'var(--stone-500)'}}>
                {next.location} · {next.time}
              </div>
              <div style={{
                marginTop:12, paddingTop:10, borderTop:'1px solid var(--stone-100)',
                display:'flex', alignItems:'center', justifyContent:'space-between',
                fontSize:12,
              }}>
                <span style={{color:'var(--stone-600)'}}>
                  <b style={{color:'var(--emerald-700)'}}>{next.poll?.yes}</b> in · {next.poll?.no} out
                </span>
                <span style={{color:'var(--pitch-700)', fontWeight:500, display:'inline-flex',
                              alignItems:'center', gap:4}}>
                  Open <ArrowRt size={12}/>
                </span>
              </div>
            </div>
          </Card>
        ) : <div/>}

        <Card>
          <div style={{padding:'14px 16px 12px'}}>
            <StatColumn first label="● Sessions · 30d" value="6" dot="var(--pitch-500)"/>
          </div>
        </Card>
        <Card>
          <div style={{padding:'14px 16px 12px'}}>
            <StatColumn first label="● Outstanding" value="€48" dot="var(--amber-500)"/>
          </div>
        </Card>
        <Card>
          <div style={{padding:'14px 16px 12px'}}>
            <StatColumn first label="● Active members" value="14" dot="var(--sky-500)"/>
          </div>
        </Card>
      </div>

      {/* ── Inline action shortcuts ── */}
      <div style={{display:'flex', gap:8, marginBottom:28, flexWrap:'wrap'}}>
        <Shortcut icon={<UsersIcon size={14}/>} label="Balance teams" onClick={() => onNavigate('balance')}/>
        <Shortcut icon={<Wallet size={14}/>}    label="Settle payments" onClick={() => onNavigate('payments')}/>
        <Shortcut icon={<CalIcon size={14}/>}   label="Past sessions" onClick={() => window.scrollTo({top: document.body.scrollHeight, behavior:'smooth'})}/>
      </div>

      <section style={{marginBottom:34}}>
        <Eyebrow>Upcoming Sessions</Eyebrow>
        {upcoming.length ? (
          <div className="grid-3">
            {upcoming.map(s => (
              <SessionCard key={s.id} session={s} onClick={() => onOpenSession(s)} onDelete={onDelete} isStaff={user.is_staff}/>
            ))}
          </div>
        ) : (
          <div style={{background:'#fff', border:'1px solid var(--stone-100)', borderRadius:16,
                       padding:'36px 24px', textAlign:'center'}}>
            <div style={{margin:'0 auto 12px', color:'var(--stone-300)'}}><CalIcon size={36} sw={1.5}/></div>
            <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>No upcoming sessions.</p>
            {user.is_staff && <div style={{marginTop:14}}><Button variant="primary" onClick={onCreate}>Create one</Button></div>}
          </div>
        )}
      </section>

      <section>
        <Eyebrow accent="var(--stone-300)">Previous Sessions</Eyebrow>
        <div className="grid-3">
          {past.map(s => (
            <SessionCard key={s.id} session={s} dimmed onClick={() => onOpenSession(s)} isStaff={user.is_staff}/>
          ))}
        </div>
      </section>
    </div>
  );
}

function Shortcut({ icon, label, onClick }) {
  return (
    <button onClick={onClick} style={{
      display:'inline-flex', alignItems:'center', gap:6,
      background:'#fff', border:'1px solid var(--stone-200)', borderRadius:8,
      padding:'6px 12px', fontSize:13, fontWeight:500, color:'var(--stone-700)',
      cursor:'pointer', fontFamily:'inherit', lineHeight:1,
    }}
    onMouseEnter={e => e.currentTarget.style.background='var(--stone-50)'}
    onMouseLeave={e => e.currentTarget.style.background='#fff'}
    >
      {icon}{label}
    </button>
  );
}

window.DashboardScreen = DashboardScreen;
