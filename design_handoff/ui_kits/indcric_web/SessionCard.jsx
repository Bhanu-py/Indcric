/* global React, Card, Badge, VoteBar, Icons */
const { Calendar, Pin, Clock, Trash, ArrowRt, Lock } = Icons;

function SessionCard({ session, onClick, onDelete, isStaff, dimmed, locked, lockedHint }) {
  const [hover, setHover] = React.useState(false);
  const past = !!dimmed;
  const accent = past ? 'var(--stone-200)' : 'var(--pitch-600)';
  return (
    <Card accent={accent} hoverable style={{
      position:'relative', cursor:'pointer', opacity: past ? 0.92 : 1,
      transition:'opacity .15s'
    }}>
      <div style={{padding:18}}
           onMouseEnter={() => setHover(true)}
           onMouseLeave={() => setHover(false)}
           onClick={onClick}>

        {/* Date pill + delete */}
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:10}}>
          <div style={{
            display:'inline-flex', alignItems:'center', gap:6,
            background: past ? 'var(--stone-100)' : 'var(--pitch-50)',
            color: past ? 'var(--stone-600)' : 'var(--pitch-800)',
            borderRadius:8, padding:'4px 10px'
          }}>
            <Calendar size={12} sw={1.75}/>
            <span style={{fontSize:11, fontWeight:600, letterSpacing:'0.005em'}}>{session.dateLabel}</span>
          </div>
          {isStaff && hover && (
            <button onClick={e => { e.stopPropagation(); onDelete && onDelete(session); }}
              style={{padding:6, borderRadius:8, border:'none', background:'transparent',
                      color:'var(--stone-400)', cursor:'pointer', display:'flex'}}
              onMouseEnter={e => { e.currentTarget.style.background='var(--red-50)'; e.currentTarget.style.color='var(--red-500)'; }}
              onMouseLeave={e => { e.currentTarget.style.background='transparent'; e.currentTarget.style.color='var(--stone-400)'; }}>
              <Trash size={14}/>
            </button>
          )}
        </div>

        <h3 style={{
          fontSize:15, fontWeight:600, color: past ? 'var(--stone-700)' : 'var(--stone-900)',
          margin:'0 0 6px', letterSpacing:'-0.005em', transition:'color .15s'
        }}>{session.name}</h3>

        <div style={{display:'flex', flexDirection:'column', gap:3, fontSize:12,
                     color: past ? 'var(--stone-400)' : 'var(--stone-500)'}}>
          <span style={{display:'inline-flex', alignItems:'center', gap:5}}>
            <Pin size={12}/> {session.location}
          </span>
          {!past && (
            <span style={{display:'inline-flex', alignItems:'center', gap:5}}>
              <Clock size={12}/> {session.time} · {session.duration}h
            </span>
          )}
        </div>

        {/* Poll */}
        {!past && session.poll && (
          <div style={{marginTop:14, paddingTop:12, borderTop:'1px solid var(--stone-100)'}}>
            <div style={{display:'flex', alignItems:'center', justifyContent:'space-between',
                         fontSize:11, marginBottom:8}}>
              <span style={{
                fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                textTransform:'uppercase', letterSpacing:'0.08em',
              }}>Availability</span>
              <div style={{display:'flex', gap:6}}>
                <Badge tone="green">● {session.poll.yes} Yes</Badge>
                <Badge tone="red">{session.poll.no} No</Badge>
                {session.poll.closed && <Badge tone="stone">Closed</Badge>}
              </div>
            </div>
            <VoteBar yes={session.poll.yes} total={session.poll.yes + session.poll.no}/>
          </div>
        )}

        {/* Past result */}
        {past && session.winner && (
          <div style={{marginTop:12, paddingTop:10, borderTop:'1px solid var(--stone-100)',
                       display:'flex', alignItems:'center', justifyContent:'space-between'}}>
            <div style={{display:'flex', alignItems:'center', gap:6, fontSize:12, color:'var(--stone-500)'}}>
              <span style={{color:'var(--amber-600)', fontWeight:600}}>{session.winner}</span>
              <span>won</span>
            </div>
            <ArrowRt size={12} color="var(--stone-400)"/>
          </div>
        )}
      </div>

      {/* Locked overlay — sign-in gate for guests */}
      {locked && (
        <div style={{
          position:'absolute', inset:0,
          background:'rgba(255,255,255,0.55)', backdropFilter:'blur(2px)',
          WebkitBackdropFilter:'blur(2px)',
          display:'flex', alignItems:'center', justifyContent:'center',
        }}>
          <div style={{
            display:'inline-flex', alignItems:'center', gap:7,
            background:'rgba(255,255,255,0.96)', border:'1px solid var(--stone-200)',
            borderRadius:9999, padding:'5px 12px',
            fontSize:12, fontWeight:500, color:'var(--stone-700)',
            boxShadow:'var(--shadow-sm)',
          }}>
            <Lock size={12} sw={1.75}/>
            {lockedHint || 'Sign in to view'}
          </div>
        </div>
      )}
    </Card>
  );
}

window.SessionCard = SessionCard;
