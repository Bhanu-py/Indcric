/* global React, Card, Badge, Button, Eyebrow, Avatar, RoleBadge, Icons */
const { Bell, Wallet, Trophy, Check, Calendar, Users: U, Chat, Send } = Icons;

/* ────────── Notifications / activity feed ──────────
   Single, scrollable timeline. Tabs filter by category. */
function NotificationsScreen({ items, onBack }) {
  const [tab, setTab] = React.useState('all');
  const [readSet, setReadSet] = React.useState(() => new Set(items.filter(i => i.read).map(i => i.id)));

  const filtered = items.filter(i => tab === 'all' || i.kind === tab);
  const markAll = () => setReadSet(new Set(items.map(i => i.id)));

  return (
    <div style={{maxWidth:780, margin:'0 auto', padding:'28px 24px',
                 display:'flex', flexDirection:'column', gap:18}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none'
      }}>← Back</a>

      <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between',
                   gap:12, flexWrap:'wrap'}}>
        <div>
          <h1 style={{fontSize:22, fontWeight:600, color:'var(--stone-900)', margin:0,
                      letterSpacing:'-0.02em'}}>Activity</h1>
          <p style={{fontSize:13, color:'var(--stone-500)', margin:'4px 0 0'}}>
            Everything that happened at the club, newest first
          </p>
        </div>
        <Button variant="ghost" size="sm" icon={<Check size={13} sw={1.75}/>} onClick={markAll}>
          Mark all read
        </Button>
      </div>

      {/* Tabs */}
      <div role="tablist" style={{
        display:'inline-flex', gap:4, alignSelf:'flex-start',
        background:'var(--stone-100)', padding:3, borderRadius:8,
      }}>
        {[
          { id:'all',      label:'All' },
          { id:'session',  label:'Sessions' },
          { id:'payment',  label:'Payments' },
          { id:'match',    label:'Match' },
          { id:'mention',  label:'Mentions' },
        ].map(t => (
          <Tab key={t.id} active={tab===t.id} onClick={() => setTab(t.id)}>{t.label}</Tab>
        ))}
      </div>

      <Card>
        <div style={{padding:'4px 0'}}>
          {filtered.length === 0 && (
            <div style={{padding:'30px 18px', textAlign:'center', fontSize:13, color:'var(--stone-400)'}}>
              Nothing here.
            </div>
          )}
          {filtered.map((n, i) => (
            <Row key={n.id} item={n} read={readSet.has(n.id)}
                 last={i === filtered.length - 1}/>
          ))}
        </div>
      </Card>
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

function Row({ item, read, last }) {
  const cfg = ROW_CFG[item.kind] || ROW_CFG.session;
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'auto 1fr auto', columnGap:12, alignItems:'flex-start',
      padding:'14px 18px',
      borderBottom: last ? 'none' : '1px solid var(--stone-100)',
      background: read ? '#fff' : 'var(--pitch-50)',
    }}>
      <span style={{
        display:'inline-flex', alignItems:'center', justifyContent:'center',
        width:30, height:30, borderRadius:8,
        background: cfg.bg, color: cfg.fg, flexShrink:0, marginTop:2,
      }}>
        <cfg.Glyph size={15} sw={1.75}/>
      </span>
      <div style={{minWidth:0}}>
        <div style={{fontSize:13, color:'var(--stone-800)', lineHeight:1.45}}>
          {item.body}
        </div>
        <div style={{
          fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
          marginTop:4, letterSpacing:'0.04em',
        }}>
          {item.when}{item.context ? ` · ${item.context}` : ''}
        </div>
      </div>
      <div style={{display:'flex', alignItems:'center', gap:6, marginTop:4}}>
        {!read && <span style={{width:7, height:7, borderRadius:'50%', background:'var(--amber-500)'}}/>}
        {item.action && (
          <Button variant="ghost" size="sm">{item.action}</Button>
        )}
      </div>
    </div>
  );
}

const ROW_CFG = {
  session: { Glyph: Calendar, bg:'var(--pitch-50)',  fg:'var(--pitch-700)'  },
  payment: { Glyph: Wallet,   bg:'var(--amber-50)',  fg:'var(--amber-800)'  },
  match:   { Glyph: Trophy,   bg:'var(--amber-100)', fg:'var(--amber-800)'  },
  mention: { Glyph: Chat,     bg:'var(--sky-100)',   fg:'var(--sky-800)'    },
  rsvp:    { Glyph: Check,    bg:'var(--emerald-100)', fg:'var(--emerald-800)' },
  team:    { Glyph: U,        bg:'var(--purple-100)',fg:'var(--purple-800)' },
  ping:    { Glyph: Send,     bg:'var(--stone-100)', fg:'var(--stone-700)'  },
};

window.NotificationsScreen = NotificationsScreen;
