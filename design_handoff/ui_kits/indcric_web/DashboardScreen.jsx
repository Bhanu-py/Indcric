/* global React, SessionCard, Button, Eyebrow, Card, Alert, StatColumn, Icons */
const { Plus, Calendar: CalIcon, Wallet, Users: UsersIcon, ArrowRt, ChevRt, Check, Lock } = Icons;

const fmtEur = n => '€' + (n == null ? '0.00' : Number(n).toFixed(2));

/* ────────── Dashboard ──────────
   Visibility matrix:
   • GUEST  (no user)    — upcoming cards + previous (locked overlay). No stats strip.
                           No "settle payments" shortcut. CTA to sign in.
   • MEMBER (logged in)  — upcoming + previous, both clickable. No stats strip.
                           No "settle payments" shortcut.
   • STAFF  (is_staff)   — everything: stats strip, all shortcuts, new-session CTA.
*/
function DashboardScreen({ user, sessions, onOpenSession, onDelete, onCreate, onNavigate, onSignIn }) {
  const upcoming = sessions.filter(s => !s.past);
  const past = sessions.filter(s => s.past);
  const next = upcoming[0];

  const isGuest = !user;
  const isStaff = !!user?.is_staff;

  return (
    <div style={{maxWidth:1280, margin:'0 auto', padding:'28px 24px'}}>

      {/* ── Welcome row ── */}
      <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between',
                   gap:16, marginBottom:24, flexWrap:'wrap'}}>
        <div>
          {isGuest ? (
            <>
              <h1 style={{fontSize:24, fontWeight:600, color:'var(--stone-900)', margin:0,
                          letterSpacing:'-0.02em'}}>
                Welcome to ICG
              </h1>
              <p style={{fontSize:13, color:'var(--stone-500)', marginTop:4, marginBottom:0}}>
                Sign in to vote on sessions, see line-ups, and track payments.
              </p>
            </>
          ) : (
            <>
              <h1 style={{fontSize:24, fontWeight:600, color:'var(--stone-900)', margin:0,
                          letterSpacing:'-0.02em'}}>
                Welcome back, {user.name.split(' ')[0]} <span style={{display:'inline-block'}}>👋</span>
              </h1>
              <p style={{fontSize:13, color:'var(--stone-500)', marginTop:4, marginBottom:0}}>
                Here's what's happening with IndCric
              </p>
            </>
          )}
        </div>
        <div style={{display:'flex', gap:8}}>
          {isGuest && (
            <Button variant="primary" onClick={onSignIn}>Sign in →</Button>
          )}
          {isStaff && (
            <Button variant="primary" icon={<Plus size={13} sw={1.75}/>} onClick={onCreate}>
              New Session
            </Button>
          )}
        </div>
      </div>

      {/* ── Member snapshot · ALL authenticated users (staff is also a member) ──
           Next up (with vote-status pill) · Your outstanding · Wallet balance.
           Mirrors templates/home.html — outstanding + wallet are PER USER and
           link to the matching profile tabs. */}
      {!isGuest && (
        <div className="snapshot-strip" style={{marginBottom:24}}>
          {next ? (
            <Card hoverable style={{cursor:'pointer'}} accent="var(--pitch-600)">
              <div onClick={() => onOpenSession(next)} style={{padding:'14px 18px'}}>
                <div style={{display:'flex', alignItems:'center', justifyContent:'space-between',
                             gap:8, marginBottom:6}}>
                  <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                               textTransform:'uppercase', letterSpacing:'0.08em'}}>Next up · {next.dateLabel}</div>
                  {next.poll && !next.poll.closed && (
                    <span style={{display:'inline-flex', alignItems:'center', gap:5, fontSize:9, fontWeight:700,
                                  color:'var(--emerald-700)', fontFamily:'var(--font-mono)',
                                  textTransform:'uppercase', letterSpacing:'0.06em'}}>
                      <span style={{width:6, height:6, borderRadius:'50%', background:'var(--emerald-500)'}}/>Live poll
                    </span>
                  )}
                </div>
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
                  fontSize:12, gap:8,
                }}>
                  <span style={{color:'var(--stone-600)'}}>
                    <b style={{color:'var(--emerald-700)'}}>{next.poll?.yes}</b> in · {next.poll?.no} out
                  </span>
                  <VotePill vote={next.userVote} open={next.poll && !next.poll.closed}/>
                </div>
              </div>
            </Card>
          ) : (
            <Card><div style={{padding:'14px 18px'}}>
              <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                           textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:8}}>Next up</div>
              <div style={{fontSize:13, color:'var(--stone-500)'}}>No upcoming sessions yet.</div>
            </div></Card>
          )}

          <SnapshotStat label="Your outstanding" value={fmtEur(user.outstanding)}
                        dot="var(--amber-500)" onClick={() => onNavigate('profile')}/>
          <SnapshotStat label="Wallet balance" value={fmtEur(user.wallet)}
                        dot="var(--sky-500)" onClick={() => onNavigate('profile')}/>
        </div>
      )}

      {/* ── Inline action shortcuts ── */}
      {!isGuest && (
        <div style={{display:'flex', gap:8, marginBottom:28, flexWrap:'wrap'}}>
          {next && (
            <Shortcut icon={<UsersIcon size={14}/>} label="Balance teams"
                      onClick={() => onOpenSession(next)}/>
          )}
          {isStaff && (
            <Shortcut icon={<Wallet size={14}/>} label="Settle payments" onClick={() => onNavigate('payments')}/>
          )}
          <Shortcut icon={<CalIcon size={14}/>} label="Past sessions"
                    onClick={() => window.scrollTo({top: document.body.scrollHeight, behavior:'smooth'})}/>
        </div>
      )}

      <section style={{marginBottom:34}}>
        <Eyebrow>Upcoming Sessions</Eyebrow>
        {upcoming.length ? (
          <div className="grid-3">
            {upcoming.map(s => (
              <SessionCard key={s.id} session={s}
                onClick={() => isGuest ? onSignIn() : onOpenSession(s)}
                onDelete={onDelete} isStaff={isStaff}
                locked={isGuest}
                lockedHint="Sign in to vote"/>
            ))}
          </div>
        ) : (
          <div style={{background:'#fff', border:'1px solid var(--stone-100)', borderRadius:16,
                       padding:'36px 24px', textAlign:'center'}}>
            <div style={{margin:'0 auto 12px', color:'var(--stone-300)'}}><CalIcon size={36} sw={1.5}/></div>
            <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>No upcoming sessions.</p>
            {isStaff && <div style={{marginTop:14}}><Button variant="primary" onClick={onCreate}>Create one</Button></div>}
          </div>
        )}
      </section>

      <section>
        <Eyebrow accent="var(--stone-300)">Previous Sessions</Eyebrow>
        <div className="grid-3">
          {past.map(s => (
            <SessionCard key={s.id} session={s} dimmed
              onClick={() => isGuest ? onSignIn() : onOpenSession(s)}
              isStaff={isStaff}
              locked={isGuest}
              lockedHint="Sign in to see line-ups"/>
          ))}
        </div>
      </section>
    </div>
  );
}

/* Per-user money card — left stat + chevron, links to the profile tab */
function SnapshotStat({ label, value, dot, onClick }) {
  return (
    <Card hoverable style={{cursor:'pointer'}}>
      <div onClick={onClick} style={{padding:'14px 16px', display:'flex',
                                     alignItems:'center', justifyContent:'space-between', gap:8}}>
        <StatColumn first label={label} value={value} dot={dot}/>
        <span style={{color:'var(--stone-300)', flexShrink:0, display:'inline-flex'}}><ChevRt size={16}/></span>
      </div>
    </Card>
  );
}

/* Vote-status pill on the Next-up card */
function VotePill({ vote, open }) {
  const base = {
    display:'inline-flex', alignItems:'center', gap:4, flexShrink:0,
    padding:'2px 8px', borderRadius:9999, fontSize:11, fontWeight:600, lineHeight:1.4,
  };
  if (vote === 'yes')
    return <span style={{...base, background:'var(--emerald-100)', color:'var(--emerald-800)'}}><Check size={12} sw={3}/>You're in</span>;
  if (vote === 'no')
    return <span style={{...base, background:'var(--stone-100)', color:'var(--stone-600)'}}>You're out</span>;
  if (open)
    return (
      <span style={{...base, background:'var(--pitch-100)', color:'var(--pitch-700)'}}>
        <span style={{width:6, height:6, borderRadius:'50%', background:'var(--pitch-500)',
                      animation:'pulse 2s ease-in-out infinite'}}/>Tap to vote
      </span>
    );
  return null;
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
