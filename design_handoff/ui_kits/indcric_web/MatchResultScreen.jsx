/* global React, Card, Badge, Button, Eyebrow, Avatar, PlayerChip, RoleBadge, StatColumn, Icons */
const { Trophy, Share, Star, Pin, Calendar: Cal, Clock, ChevRt, Bat, Ball, AllRounder, Keeper } = Icons;

/* ────────── Match Result + Scorecard ──────────
   Cricket scorecard adapted for a club casual match. Both innings,
   batting + bowling cards, fall-of-wickets, MOTM, highlights. */
function MatchResultScreen({ match, onBack }) {
  const [innings, setInnings] = React.useState(0); // 0 = first innings, 1 = second
  const cur = match.innings[innings];
  const other = match.innings[1 - innings];

  return (
    <div style={{maxWidth:1024, margin:'0 auto', padding:'28px 24px',
                 display:'flex', flexDirection:'column', gap:18}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none'
      }}>← Back</a>

      {/* ─── Result hero ─── */}
      <Card>
        <div style={{padding:'18px 22px',
                     display:'grid', gridTemplateColumns:'1fr auto 1fr',
                     alignItems:'center', columnGap:16}}>
          <TeamScore team={match.teamA} score={match.innings[0]} winner={match.winner === 'A'}/>
          <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap:6, minWidth:120}}>
            <div style={{
              fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
              textTransform:'uppercase', letterSpacing:'0.08em',
            }}>vs</div>
            <Badge tone="amber">
              <Trophy size={11} sw={1.75}/> {match.resultLine}
            </Badge>
          </div>
          <TeamScore team={match.teamB} score={match.innings[1]} winner={match.winner === 'B'} alignRight/>
        </div>
        <div style={{
          padding:'12px 22px', borderTop:'1px solid var(--stone-100)',
          display:'flex', flexWrap:'wrap', gap:14,
          fontSize:12, color:'var(--stone-500)',
        }}>
          <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Cal size={13}/>{match.dateLabel}</span>
          <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Pin size={13}/>{match.location}</span>
          <span style={{display:'inline-flex', alignItems:'center', gap:5}}><Clock size={13}/>{match.format}</span>
          <span style={{marginLeft:'auto', display:'inline-flex', gap:6}}>
            <Button variant="ghost" size="sm" icon={<Share size={13} sw={1.75}/>}>Share</Button>
          </span>
        </div>
      </Card>

      {/* ─── MOTM strip ─── */}
      <Card>
        <div style={{
          padding:'14px 18px',
          display:'grid', gridTemplateColumns:'auto 1fr auto auto', alignItems:'center', columnGap:14,
        }}>
          <div style={{
            display:'inline-flex', alignItems:'center', justifyContent:'center',
            width:36, height:36, borderRadius:10,
            background:'var(--amber-100)', color:'var(--amber-800)',
          }}>
            <Star size={18} sw={1.75}/>
          </div>
          <div>
            <div style={{
              fontFamily:'var(--font-mono)', fontSize:9, fontWeight:500,
              color:'var(--amber-800)', textTransform:'uppercase', letterSpacing:'0.08em',
            }}>Player of the Match</div>
            <div style={{fontSize:15, fontWeight:600, color:'var(--stone-900)', marginTop:2,
                         letterSpacing:'-0.005em'}}>
              {match.motm.name} <span style={{
                fontFamily:'var(--font-mono)', fontSize:11, fontWeight:400, color:'var(--stone-500)',
              }}>@{match.motm.username}</span>
            </div>
            <div style={{fontSize:12, color:'var(--stone-500)', marginTop:4}}>
              {match.motm.line}
            </div>
          </div>
          <RoleBadge role={match.motm.role}/>
          <Button variant="ghost" size="sm" icon={<ChevRt size={13} sw={1.75}/>}>Profile</Button>
        </div>
      </Card>

      {/* ─── Innings tabs ─── */}
      <div role="tablist" style={{
        display:'inline-flex', gap:4, alignSelf:'flex-start',
        background:'var(--stone-100)', padding:3, borderRadius:8,
      }}>
        {match.innings.map((inn, i) => (
          <Tab key={i} active={innings === i} onClick={() => setInnings(i)}>
            {inn.battingTeam} · {inn.runs}/{inn.wickets}
          </Tab>
        ))}
      </div>

      {/* ─── Batting card ─── */}
      <Card>
        <SectionHeader title={`${cur.battingTeam} batting · ${cur.runs}/${cur.wickets} (${cur.overs} overs)`}/>
        <div style={{padding:'4px 0'}}>
          <Row header>
            <span style={{flex:'1 1 0'}}>Batter</span>
            <Mono>R</Mono><Mono>B</Mono><Mono>4s</Mono><Mono>6s</Mono><Mono>SR</Mono>
          </Row>
          {cur.batting.map((b, i) => (
            <Row key={i} dim={!!b.out}>
              <div style={{flex:'1 1 0', display:'flex', flexDirection:'column', gap:2, minWidth:0}}>
                <div style={{display:'flex', alignItems:'center', gap:8}}>
                  <span style={{fontSize:13, fontWeight:500, color:'var(--stone-900)'}}>{b.name}</span>
                  {b.captain && <CapPill/>}
                  {!b.out && <span style={{
                    fontSize:10, color:'var(--emerald-700)', fontWeight:600,
                    fontFamily:'var(--font-mono)', letterSpacing:'0.04em',
                  }}>NOT OUT</span>}
                </div>
                <span style={{fontSize:11, color:'var(--stone-400)', fontFamily:'var(--font-mono)'}}>
                  {b.out || '—'}
                </span>
              </div>
              <Mono bold>{b.r}</Mono>
              <Mono>{b.balls}</Mono>
              <Mono>{b.fours}</Mono>
              <Mono>{b.sixes}</Mono>
              <Mono>{b.sr}</Mono>
            </Row>
          ))}
          <Row footer>
            <span style={{flex:'1 1 0', fontSize:12, color:'var(--stone-500)',
                          fontFamily:'var(--font-mono)', letterSpacing:'0.04em'}}>
              Extras · {cur.extras.total} ({cur.extras.desc})
            </span>
            <span style={{
              fontFamily:'var(--font-mono)', fontSize:13, fontWeight:600,
              color:'var(--stone-900)', fontFeatureSettings:'"tnum" 1',
            }}>Total {cur.runs}/{cur.wickets}</span>
          </Row>
        </div>
      </Card>

      {/* ─── Bowling card (other team) ─── */}
      <Card>
        <SectionHeader title={`${other.battingTeam} bowling`}/>
        <div style={{padding:'4px 0'}}>
          <Row header>
            <span style={{flex:'1 1 0'}}>Bowler</span>
            <Mono>O</Mono><Mono>M</Mono><Mono>R</Mono><Mono>W</Mono><Mono>Econ</Mono>
          </Row>
          {cur.bowling.map((b, i) => (
            <Row key={i}>
              <div style={{flex:'1 1 0', display:'flex', alignItems:'center', gap:8}}>
                <span style={{fontSize:13, fontWeight:500, color:'var(--stone-900)'}}>{b.name}</span>
                {b.w >= 3 && <Badge tone="purple">★ {b.w}-fer</Badge>}
              </div>
              <Mono>{b.o}</Mono>
              <Mono>{b.m}</Mono>
              <Mono>{b.r}</Mono>
              <Mono bold>{b.w}</Mono>
              <Mono>{b.econ}</Mono>
            </Row>
          ))}
        </div>
      </Card>

      {/* ─── Fall of wickets ─── */}
      {cur.fow && cur.fow.length > 0 && (
        <Card>
          <SectionHeader title="Fall of wickets"/>
          <div style={{padding:'12px 18px', display:'flex', flexWrap:'wrap', gap:8}}>
            {cur.fow.map((f, i) => (
              <div key={i} style={{
                display:'inline-flex', alignItems:'center', gap:6,
                padding:'5px 10px', borderRadius:9999,
                background:'var(--stone-50)', border:'1px solid var(--stone-100)',
                fontSize:12,
              }}>
                <span style={{
                  fontFamily:'var(--font-mono)', fontSize:11, fontWeight:600,
                  color:'var(--stone-900)', fontFeatureSettings:'"tnum" 1',
                }}>{f.score}</span>
                <span style={{color:'var(--stone-500)'}}>{f.batter}</span>
                <span style={{fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)'}}>
                  ov {f.over}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ─── Highlights ─── */}
      <Card>
        <SectionHeader title="Highlights"/>
        <div style={{padding:14, display:'flex', flexDirection:'column', gap:8}}>
          {match.highlights.map((h, i) => (
            <Highlight key={i} item={h}/>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ── parts ── */

function TeamScore({ team, score, winner, alignRight }) {
  return (
    <div style={{
      display:'flex', flexDirection:'column', gap:6,
      alignItems: alignRight ? 'flex-end' : 'flex-start',
    }}>
      <div style={{display:'flex', alignItems:'center', gap:8}}>
        <span style={{width:8, height:8, borderRadius:'50%', background: team.accent}}/>
        <span style={{fontSize:14, fontWeight:600, color:'var(--stone-900)',
                      letterSpacing:'-0.005em'}}>{team.name}</span>
        {winner && <Badge tone="amber">WON</Badge>}
      </div>
      <div style={{display:'flex', alignItems:'baseline', gap:6}}>
        <span style={{
          fontSize:34, fontWeight:600, color:'var(--stone-900)',
          letterSpacing:'-0.025em', lineHeight:1,
          fontFeatureSettings:'"tnum" 1',
        }}>{score.runs}<span style={{color:'var(--stone-400)'}}>/{score.wickets}</span></span>
        <span style={{
          fontFamily:'var(--font-mono)', fontSize:11, color:'var(--stone-500)',
          letterSpacing:'0.04em',
        }}>({score.overs} ov)</span>
      </div>
      <div style={{
        fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
        letterSpacing:'0.04em',
      }}>
        RR {score.rr}
      </div>
    </div>
  );
}

function SectionHeader({ title }) {
  return (
    <div style={{padding:'12px 18px', borderBottom:'1px solid var(--stone-100)'}}>
      <h2 style={{
        fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
        textTransform:'uppercase', letterSpacing:'0.08em',
        color:'var(--stone-500)', margin:0,
      }}>{title}</h2>
    </div>
  );
}

function Row({ header, footer, dim, children }) {
  return (
    <div style={{
      display:'flex', alignItems:'center', gap:8,
      padding: header ? '8px 18px 6px' : footer ? '10px 18px' : '10px 18px',
      borderBottom: header || footer ? '1px solid var(--stone-100)' : '1px solid var(--stone-50, #fafaf9)',
      background: footer ? 'var(--stone-50)' : 'transparent',
      color: dim ? 'var(--stone-600)' : 'var(--stone-800)',
      fontSize: header ? 10 : 13,
      fontFamily: header ? 'var(--font-mono)' : 'inherit',
      textTransform: header ? 'uppercase' : 'none',
      letterSpacing: header ? '0.08em' : '0.005em',
      fontWeight: header ? 500 : 400,
    }}>{children}</div>
  );
}

function Mono({ children, bold }) {
  return (
    <span style={{
      width: 40, textAlign:'right', flexShrink:0,
      fontFamily:'var(--font-mono)', fontSize: 12,
      fontWeight: bold ? 600 : 400,
      color: bold ? 'var(--stone-900)' : 'var(--stone-600)',
      fontFeatureSettings:'"tnum" 1',
    }}>{children}</span>
  );
}

function CapPill() {
  return (
    <span title="Captain" style={{
      width:14, height:14, borderRadius:9999,
      background:'var(--amber-100)', color:'var(--amber-800)',
      fontFamily:'var(--font-mono)', fontSize:9, fontWeight:600,
      display:'inline-flex', alignItems:'center', justifyContent:'center',
    }}>C</span>
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

const HIGHLIGHT_CFG = {
  six:     { bg:'var(--purple-100)',  fg:'var(--purple-800)', label:'SIX' },
  four:    { bg:'var(--sky-100)',     fg:'var(--sky-800)',    label:'4' },
  wicket:  { bg:'var(--red-50)',      fg:'var(--red-800)',    label:'W' },
  fifty:   { bg:'var(--amber-100)',   fg:'var(--amber-800)',  label:'50' },
  catch:   { bg:'var(--emerald-100)', fg:'var(--emerald-800)',label:'CATCH' },
  hat:     { bg:'var(--purple-100)',  fg:'var(--purple-800)', label:'HAT-TRICK' },
};
function Highlight({ item }) {
  const cfg = HIGHLIGHT_CFG[item.kind] || HIGHLIGHT_CFG.four;
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'auto auto 1fr auto', alignItems:'center',
      columnGap:12, padding:'8px 12px', border:'1px solid var(--stone-100)', borderRadius:10,
    }}>
      <span style={{
        display:'inline-flex', alignItems:'center', justifyContent:'center',
        minWidth:48, height:24, padding:'0 8px', borderRadius:6,
        background:cfg.bg, color:cfg.fg,
        fontFamily:'var(--font-mono)', fontSize:10, fontWeight:600,
        letterSpacing:'0.06em',
      }}>{cfg.label}</span>
      <span style={{
        fontFamily:'var(--font-mono)', fontSize:11, color:'var(--stone-400)',
        letterSpacing:'0.04em', width:50,
      }}>Ov {item.over}</span>
      <span style={{fontSize:13, color:'var(--stone-800)'}}>{item.body}</span>
      <span style={{
        fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-400)',
        letterSpacing:'0.04em',
      }}>{item.byTeam}</span>
    </div>
  );
}

window.MatchResultScreen = MatchResultScreen;
