/* global React, Icons */

/* ────────── Button (slim) ──────────
   13-px label, 500 weight, 8-px radius, tighter padding.
   Matches preview/buttons.html exactly. */
function Button({ variant='primary', size='md', icon, children, style, ...p }) {
  const base = {
    display:'inline-flex', alignItems:'center', justifyContent:'center', gap:6,
    fontFamily:'inherit', fontWeight:500, letterSpacing:'0.005em',
    borderRadius:8, border:'1px solid transparent', cursor:'pointer',
    transition:'background .15s, transform .15s', userSelect:'none', whiteSpace:'nowrap',
    lineHeight:1,
  };
  const sizes = {
    sm: { padding:'5px 10px',  fontSize:12, borderRadius:7 },
    md: { padding:'7px 14px',  fontSize:13 },
    lg: { padding:'9px 18px',  fontSize:13, borderRadius:9 },
    xl: { padding:'11px 20px', fontSize:14, borderRadius:10 },
  };
  const variants = {
    primary:   { background:'var(--pitch-700)',   color:'#fff' },
    secondary: { background:'#fff',               color:'var(--stone-700)', borderColor:'var(--stone-300)' },
    amber:     { background:'var(--amber-500)',   color:'#fff' },
    danger:    { background:'var(--red-600)',     color:'#fff' },
    success:   { background:'var(--emerald-600)', color:'#fff' },
    ghost:     { background:'transparent',        color:'var(--stone-600)' },
  };
  const hover = {
    primary:'var(--pitch-800)', amber:'var(--amber-600)', danger:'var(--red-700)',
    success:'var(--emerald-700, #047857)', secondary:'var(--stone-50)', ghost:'var(--stone-100)'
  };
  return (
    <button {...p} style={{...base, ...sizes[size], ...variants[variant], ...(style||{})}}
      onMouseDown={e => e.currentTarget.style.transform = 'scale(0.96)'}
      onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
      onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)';
                           e.currentTarget.style.background = variants[variant].background; }}
      onMouseEnter={e => e.currentTarget.style.background = hover[variant]}
    >{icon}{children}</button>
  );
}

/* ────────── Card ────────── */
function Card({ children, accent, hoverable, style, ...p }) {
  const [hover, setHover] = React.useState(false);
  return (
    <div {...p} style={{
      background:'#fff', borderRadius:16, border:'1px solid var(--stone-100)',
      boxShadow: hoverable && hover ? 'var(--shadow-md)' : 'var(--shadow-sm)',
      overflow:'hidden', transition:'box-shadow .15s', ...style
    }} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
      {accent && <div style={{height:4, background: accent}}/>}
      {children}
    </div>
  );
}

/* ────────── Badge ────────── */
const BADGE_TINTS = {
  green:  { bg:'var(--emerald-100)', fg:'var(--emerald-800)' },
  pitch:  { bg:'var(--pitch-100)',   fg:'var(--pitch-800)' },
  red:    { bg:'var(--red-100)',     fg:'var(--red-700)' },
  amber:  { bg:'var(--amber-100)',   fg:'var(--amber-800)' },
  sky:    { bg:'var(--sky-100)',     fg:'var(--sky-800)' },
  purple: { bg:'var(--purple-100)',  fg:'var(--purple-800)' },
  stone:  { bg:'var(--stone-100)',   fg:'var(--stone-700)' },
};
function Badge({ tone='stone', children, style }) {
  const t = BADGE_TINTS[tone];
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:4,
      padding:'3px 10px', borderRadius:9999, fontSize:11, fontWeight:600,
      background: t.bg, color: t.fg, lineHeight:1.4, ...style
    }}>{children}</span>
  );
}

/* ────────── Role badge — symbol + label ──────────
   The on-brand way to communicate role. Glyph carries the color. */
const { Bat, Ball, AllRounder, Keeper } = (window.Icons || {});
function RoleBadge({ role='batsman', iconOnly=false, size }) {
  const map = {
    batsman:    { tone:'sky',    label:'Batsman',    Glyph: Bat },
    bowler:     { tone:'red',    label:'Bowler',     Glyph: Ball },
    allrounder: { tone:'purple', label:'Allrounder', Glyph: AllRounder },
    keeper:     { tone:'stone',  label:'Keeper',     Glyph: Keeper },
  };
  const { tone, label, Glyph } = map[role] || map.batsman;
  if (iconOnly) {
    return (
      <span style={{
        display:'inline-flex', alignItems:'center', justifyContent:'center',
        width: size||22, height: size||22, borderRadius:9999,
        background: BADGE_TINTS[tone].bg, color: BADGE_TINTS[tone].fg,
      }} title={label}>
        {Glyph && <Glyph size={(size||22) - 9} sw={1.75}/>}
      </span>
    );
  }
  return (
    <Badge tone={tone}>
      {Glyph && <Glyph size={12} sw={1.75}/>}
      {label}
    </Badge>
  );
}

/* ────────── Eyebrow (section heading) ────────── */
function Eyebrow({ children, accent='var(--pitch-600)' }) {
  return (
    <div style={{display:'flex', alignItems:'center', gap:8, marginBottom:14}}>
      <div style={{width:3, height:14, borderRadius:9999, background:accent}}/>
      <h2 style={{
        fontSize:11, fontWeight:700, color: 'var(--stone-500)',
        textTransform:'uppercase', letterSpacing:'0.08em', margin:0
      }}>{children}</h2>
    </div>
  );
}

/* ────────── Input ────────── */
function Input({ icon, label, error, hint, ...p }) {
  const [focus, setFocus] = React.useState(false);
  return (
    <div>
      {label && <label style={{display:'block', fontSize:13, fontWeight:500, color:'var(--stone-700)', marginBottom:6}}>{label}</label>}
      <div style={{position:'relative'}}>
        {icon && (
          <div style={{position:'absolute', left:12, top:'50%', transform:'translateY(-50%)',
                       color:'var(--stone-400)', pointerEvents:'none', display:'flex'}}>{icon}</div>
        )}
        <input {...p} onFocus={() => setFocus(true)} onBlur={() => setFocus(false)} style={{
          width:'100%', boxSizing:'border-box', padding: icon ? '9px 12px 9px 36px' : '9px 12px',
          fontSize:13, fontFamily:'inherit', color:'var(--stone-900)',
          background:'#fff', border: `1px solid ${error ? '#fda4af' : 'var(--stone-200)'}`,
          borderRadius:10, outline:'none',
          boxShadow: focus ? `0 0 0 2px ${error ? '#fda4af' : 'var(--pitch-500)'}` : 'none',
          borderColor: focus ? 'transparent' : (error ? '#fda4af' : 'var(--stone-200)'),
          transition:'box-shadow .15s'
        }}/>
      </div>
      {error && <div style={{fontSize:12, color:'var(--red-600)', marginTop:6}}>{error}</div>}
      {hint && !error && <div style={{fontSize:12, color:'var(--stone-500)', marginTop:6}}>{hint}</div>}
    </div>
  );
}

/* ────────── RatingBar — 5-segment dot row ──────────
   Filled in stone-800, empties stone-100, halves use a hard 50% gradient.
   Compact variant trims segment width. */
function RatingBar({ value=0, max=5, compact=false, editable=false, onChange }) {
  const segW = compact ? 10 : 16;
  const gap  = compact ? 3 : 4;
  // value 0..5 → for each segment i (0..max-1): full if value >= i+1, half if value >= i+0.5
  return (
    <span style={{display:'inline-flex', gap}}>
      {Array.from({length:max}).map((_, i) => {
        const v = value;
        const full = v >= i+1;
        const half = !full && v >= i+0.5;
        const bg = full
          ? 'var(--stone-800)'
          : half
            ? 'linear-gradient(to right, var(--stone-800) 50%, var(--stone-100) 50%)'
            : 'var(--stone-100)';
        return (
          <span key={i}
            onClick={editable ? () => onChange && onChange(i+1) : undefined}
            style={{
              width: segW, height:4, borderRadius:2, background: bg,
              cursor: editable ? 'pointer' : 'default',
            }}/>
        );
      })}
    </span>
  );
}

/* ────────── VoteBar — full-width track (poll yes/no) ────────── */
function VoteBar({ yes, total }) {
  const pct = total > 0 ? (yes/total)*100 : 0;
  return (
    <div style={{height:6, borderRadius:9999, background:'var(--stone-100)', overflow:'hidden'}}>
      <div style={{height:'100%', borderRadius:9999, background:'var(--emerald-500)',
                   width:`${pct}%`, transition:'width .5s'}}/>
    </div>
  );
}

/* ────────── Alert ────────── */
const ALERT_TONES = {
  info:    { bg:'var(--sky-50, #f0f9ff)',     fg:'var(--sky-800)',     bd:'#bae6fd', Glyph: window.Icons?.Info  },
  success: { bg:'var(--emerald-50, #ecfdf5)', fg:'var(--emerald-800)', bd:'#a7f3d0', Glyph: window.Icons?.Check },
  warn:    { bg:'var(--amber-50, #fffbeb)',   fg:'var(--amber-800)',   bd:'#fde68a', Glyph: window.Icons?.Warn  },
  error:   { bg:'var(--red-50, #fef2f2)',     fg:'var(--red-800)',     bd:'#fecaca', Glyph: window.Icons?.Warn  },
};
function Alert({ tone='info', title, children, action }) {
  const t = ALERT_TONES[tone] || ALERT_TONES.info;
  return (
    <div role="alert" style={{
      display:'flex', alignItems:'flex-start', gap:10,
      background:t.bg, color:t.fg, border:`1px solid ${t.bd}`,
      borderRadius:10, padding:'10px 12px', fontSize:13,
    }}>
      {t.Glyph && <div style={{display:'flex', paddingTop:1, color:t.fg}}><t.Glyph size={16} sw={1.75}/></div>}
      <div style={{flex:1, minWidth:0}}>
        {title && <div style={{fontWeight:600, marginBottom: children ? 2 : 0}}>{title}</div>}
        {children && <div style={{color:t.fg, opacity:0.9}}>{children}</div>}
      </div>
      {action}
    </div>
  );
}

/* ────────── Avatar (lifted from Header.jsx so other screens can reuse) ────────── */
function Avatar({ user, size=36, ring=false }) {
  const initials = (user.name || user.username || '?').split(' ').map(s => s[0]).join('').slice(0,2).toUpperCase();
  const colors = { B:'var(--pitch-700)', A:'var(--sky-500)', R:'var(--purple-800)', K:'var(--amber-600)', S:'var(--emerald-600)' };
  const bg = user.avatarColor || colors[initials[0]] || 'var(--pitch-700)';
  return (
    <span style={{
      width:size, height:size, borderRadius:'50%', background: bg,
      color:'#fff', fontWeight:600, fontSize: size*0.4,
      display:'inline-flex', alignItems:'center', justifyContent:'center',
      boxShadow: ring ? '0 0 0 2px var(--amber-400)' : 'none', flexShrink:0
    }}>{initials}</span>
  );
}

/* ────────── PlayerChip ──────────
   8 px radius, hairline border, neutral stone avatar, role glyph inline. */
function PlayerChip({ player, captain=false, tinted=true, onClick }) {
  const roleToneMap = {
    batsman:    { bg:'var(--sky-100)',    bd:'#bae6fd',   fg:'var(--sky-800)' },
    bowler:     { bg:'var(--red-50)',     bd:'var(--red-100)', fg:'var(--red-800)' },
    allrounder: { bg:'var(--purple-100)', bd:'#e9d5ff',   fg:'var(--purple-800)' },
    keeper:     { bg:'#fff',              bd:'var(--stone-200)', fg:'var(--stone-800)' },
  };
  const tone = tinted ? (roleToneMap[player.role] || { bg:'#fff', bd:'var(--stone-200)', fg:'var(--stone-800)' })
                      : { bg:'#fff', bd:'var(--stone-200)', fg:'var(--stone-800)' };
  const Glyph = { batsman: Icons.Bat, bowler: Icons.Ball, allrounder: Icons.AllRounder, keeper: Icons.Keeper }[player.role];
  return (
    <span onClick={onClick} style={{
      display:'inline-flex', alignItems:'center', gap:7,
      background: tone.bg, color: tone.fg, border:`1px solid ${tone.bd}`,
      borderRadius:8, padding:'3px 9px 3px 4px', fontSize:13, fontWeight:500,
      letterSpacing:'0.005em', lineHeight:1,
      cursor: onClick ? 'pointer' : 'default',
    }}>
      <Avatar user={{ username: player.username, avatarColor:'transparent' }} size={20}/>
      {player.username}
      {Glyph && <Glyph size={12} sw={1.75}/>}
      {captain && (
        <span title="Captain" style={{
          marginLeft:1, width:14, height:14,
          background:'var(--amber-100)', color:'var(--amber-800)',
          borderRadius:9999, fontSize:9, fontWeight:600,
          display:'inline-flex', alignItems:'center', justifyContent:'center',
        }}>C</span>
      )}
    </span>
  );
}

/* override avatar background in PlayerChip with neutral disc */
const PlayerChipAvatarStyle = `
  /* injected */
`;

/* ────────── StatColumn — typographic column from the DS preview ────────── */
function StatColumn({ label, value, dot, first=false }) {
  return (
    <div style={{
      padding: first ? '4px 12px 4px 0' : '4px 12px',
      borderLeft: first ? 'none' : '1px solid var(--stone-100)',
      display:'flex', flexDirection:'column', gap:6,
    }}>
      <span style={{
        display:'inline-flex', alignItems:'center', gap:5,
        fontFamily:'var(--font-mono)', fontSize:9, fontWeight:500,
        color:'var(--stone-500)', textTransform:'uppercase', letterSpacing:'0.08em',
      }}>
        {dot && <span style={{width:6, height:6, borderRadius:9999, background:dot}}/>}
        {label}
      </span>
      <span style={{
        fontSize:24, fontWeight:500, color:'var(--stone-900)',
        lineHeight:1, letterSpacing:'-0.015em',
        fontFeatureSettings:'"tnum" 1',
      }}>{value}</span>
    </div>
  );
}

/* ────────── StatTile — single-metric soft-tinted block ────────── */
function StatTile({ label, value, delta, tone='stone' }) {
  const map = {
    sky:     { bg:'var(--sky-100)',     fg:'var(--sky-800)' },
    red:     { bg:'var(--red-50)',      fg:'var(--red-800)' },
    emerald: { bg:'var(--emerald-100)', fg:'var(--emerald-800)' },
    amber:   { bg:'var(--amber-50)',    fg:'var(--amber-800)' },
    pitch:   { bg:'var(--pitch-50)',    fg:'var(--pitch-800)' },
    stone:   { bg:'var(--stone-50)',    fg:'var(--stone-600)' },
  };
  const t = map[tone] || map.stone;
  return (
    <div style={{
      display:'flex', flexDirection:'column', gap:6,
      padding:'12px 14px', background:t.bg, borderRadius:10, minWidth:96,
    }}>
      <span style={{
        fontFamily:'var(--font-mono)', fontSize:9,
        color:t.fg, textTransform:'uppercase', letterSpacing:'0.08em',
      }}>{label}</span>
      <div style={{display:'flex', alignItems:'baseline', gap:6}}>
        <span style={{
          fontSize:24, fontWeight:500, color:'var(--stone-900)',
          lineHeight:1, letterSpacing:'-0.015em',
          fontFeatureSettings:'"tnum" 1',
        }}>{value}</span>
        {delta && (
          <span style={{
            fontFamily:'var(--font-mono)', fontSize:11,
            color: delta.startsWith('-') || delta.startsWith('−')
              ? 'var(--red-700)' : 'var(--pitch-800)',
          }}>{delta}</span>
        )}
      </div>
    </div>
  );
}

Object.assign(window, {
  Button, Card, Badge, RoleBadge, Eyebrow, Input, RatingBar, VoteBar, Alert,
  Avatar, PlayerChip, StatColumn, StatTile,
});
