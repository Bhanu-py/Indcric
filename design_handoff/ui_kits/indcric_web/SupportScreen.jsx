/* global React, Icons, Card, Badge, Button, Avatar, Eyebrow, Alert, Input */

/* ────────── Support page ──────────
   Faithful recreation of /support/ (apps/donations).
   Layout, top→bottom:
     header (eyebrow + h1 + lede)
     "What your donations fund" tile grid (from General Donations)
     [staff] action bar (+ Target fundraiser)
     active campaign cards (collapsible) — General Donations is the catch-all
     previous fundraisers (collapsed, log-form hidden)

   Each campaign card body: progress bar (goal only) · supporters wall
   (collapsible) · how-to-donate bank block · log-donation form (auth only). */

const { Heart, Server, Database, Trophy, Ball, ChevRt, ChevDown, ArrowRt, Copy, Check, Plus } = Icons;

/* tinted "what your donation funds" tile */
const FUND_TINTS = {
  pitch:   { bg:'var(--pitch-50)',    fg:'var(--pitch-700)' },
  sky:     { bg:'var(--sky-100)',     fg:'var(--sky-800)' },
  amber:   { bg:'var(--amber-50)',    fg:'var(--amber-800)' },
  emerald: { bg:'var(--emerald-100)', fg:'var(--emerald-800)' },
  red:     { bg:'var(--red-50)',      fg:'var(--red-800)' },
  stone:   { bg:'var(--stone-50)',    fg:'var(--stone-600)' },
};
const FUND_ICON = { server: Server, db: Database, cup: Trophy, ball: Ball, heart: Heart };

function FundItem({ tint='stone', title, body, icon='heart' }) {
  const t = FUND_TINTS[tint] || FUND_TINTS.stone;
  const Glyph = FUND_ICON[icon] || Heart;
  return (
    <div style={{
      display:'flex', alignItems:'flex-start', gap:12,
      background:t.bg, borderRadius:12, padding:'14px 16px',
    }}>
      <span style={{display:'flex', color:t.fg, flexShrink:0, paddingTop:1}}>
        <Glyph size={20} sw={1.75}/>
      </span>
      <div style={{minWidth:0}}>
        <div style={{fontSize:14, fontWeight:600, color:'var(--stone-800)', letterSpacing:'-0.005em'}}>{title}</div>
        <div style={{fontSize:12, color:'var(--stone-500)', lineHeight:1.4, marginTop:2}}>{body}</div>
      </div>
    </div>
  );
}

/* a single bank-detail row with a copy button */
function CopyRow({ label, value, mono=false }) {
  const [copied, setCopied] = React.useState(false);
  const copy = () => {
    try { navigator.clipboard.writeText(value); } catch (e) {}
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div style={{
      display:'flex', alignItems:'center', justifyContent:'space-between', gap:12,
      background:'var(--stone-50)', borderRadius:10, padding:'10px 14px',
    }}>
      <div style={{minWidth:0}}>
        <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-500)',
                     textTransform:'uppercase', letterSpacing:'0.08em'}}>{label}</div>
        <div style={{fontSize:14, fontWeight:600, color:'var(--stone-800)',
                     fontFamily: mono ? 'var(--font-mono)' : 'inherit',
                     overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', marginTop:2}}>{value}</div>
      </div>
      <Button variant="secondary" size="sm" style={{flexShrink:0, minWidth:62}} onClick={copy}>
        {copied ? <><Check size={13}/>Copied</> : 'Copy'}
      </Button>
    </div>
  );
}

/* How-to-donate block (club bank account) */
function HowToDonate({ bank }) {
  return (
    <div style={{border:'1px solid var(--stone-200)', borderRadius:10, padding:16,
                 display:'flex', flexDirection:'column', gap:12}}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
        <h3 style={{fontSize:14, fontWeight:700, color:'var(--stone-800)', margin:0}}>How to donate</h3>
        <Badge tone="pitch">SEPA transfer</Badge>
      </div>
      <p style={{fontSize:14, color:'var(--stone-600)', margin:0, lineHeight:1.5}}>
        Every donation goes to the club's bank account below. Send any amount by bank
        transfer and it will automatically be added to the tally.
      </p>
      <div style={{display:'flex', flexDirection:'column', gap:8}}>
        <CopyRow label="Account holder" value={bank.holder}/>
        <CopyRow label="IBAN" value={bank.iban} mono/>
        <CopyRow label="Reference" value={bank.reference}/>
      </div>
      <Button variant="primary" size="md" style={{width:'100%'}}>
        <ArrowRt size={16}/> Or donate online
      </Button>
    </div>
  );
}

/* Overlapping faces — for collapsed campaign headers + the featured summary.
   Newest-first; we reverse the z-order so the latest face sits on top. */
function AvatarStack({ donations, max = 5, size = 24 }) {
  const shown = donations.slice(0, max);
  const extra = donations.length - shown.length;
  return (
    <span style={{display:'inline-flex', alignItems:'center'}}>
      {shown.map((d, i) => (
        <span key={i} style={{
          marginLeft: i === 0 ? 0 : -size * 0.32, borderRadius:'50%',
          boxShadow:'0 0 0 2px #fff', display:'inline-flex',
          zIndex: shown.length - i, position:'relative',
        }}>
          <Avatar user={{ name: d.name }} size={size}/>
        </span>
      ))}
      {extra > 0 && (
        <span style={{
          marginLeft:-size * 0.32, width:size, height:size, borderRadius:'50%',
          background:'var(--stone-100)', color:'var(--stone-600)', boxShadow:'0 0 0 2px #fff',
          display:'inline-flex', alignItems:'center', justifyContent:'center',
          fontSize:Math.round(size * 0.34), fontWeight:700, position:'relative',
        }}>+{extra}</span>
      )}
    </span>
  );
}

const LATEST_TAG = {
  fontSize:9, fontWeight:700, textTransform:'uppercase', letterSpacing:'0.06em',
  color:'var(--amber-800)', background:'var(--amber-100)', padding:'1px 6px', borderRadius:9999,
};
const AUTO_TAG = {
  fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em',
  background:'var(--stone-100)', color:'var(--stone-500)', padding:'1px 6px', borderRadius:4,
};

/* ── Style 1 · Wall — celebratory horizontal rail of faces (default) ── */
function SupporterGrid({ donations }) {
  return (
    <div className="supporter-rail" style={{
      display:'flex', gap:10, overflowX:'auto', paddingBottom:4,
      scrollSnapType:'x proximity', WebkitOverflowScrolling:'touch',
    }}>
      {donations.map((d, i) => {
        const latest = i === 0;
        return (
          <div key={i} style={{
            flex:'0 0 132px', scrollSnapAlign:'start',
            display:'flex', flexDirection:'column', alignItems:'center', gap:6, textAlign:'center',
            padding:'14px 10px', borderRadius:14,
            background: latest ? 'var(--amber-50)' : 'var(--stone-50)',
            border:`1px solid ${latest ? 'var(--amber-100)' : 'transparent'}`,
          }}>
            <span style={{display:'inline-flex', borderRadius:'50%',
                          boxShadow: latest ? '0 0 0 2px var(--amber-400)' : 'none'}}>
              <Avatar user={{ name: d.name }} size={42}/>
            </span>
            <div style={{width:'100%', minWidth:0}}>
              <div style={{fontSize:13, fontWeight:600, color:'var(--stone-800)',
                           overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{d.name}</div>
              <div style={{fontSize:11, color:'var(--stone-400)', marginTop:1}}>{d.date}</div>
            </div>
            <div style={{fontSize:14, fontWeight:700, color:'var(--emerald-700, #047857)',
                         fontFeatureSettings:'"tnum" 1'}}>€{d.amount.toFixed(2)}</div>
            {latest ? <span style={LATEST_TAG}>Latest</span>
              : d.source === 'bank' ? <span title="Auto-imported from the linked bank account"
                  style={{fontSize:9, textTransform:'uppercase', letterSpacing:'0.05em', color:'var(--stone-400)'}}>auto</span>
              : null}
          </div>
        );
      })}
    </div>
  );
}

/* ── Style 2 · Honor list — rows, latest gently lifted ── */
function SupporterList({ donations }) {
  return (
    <ul style={{listStyle:'none', margin:0, padding:0}}>
      {donations.map((d, i) => {
        const latest = i === 0;
        return (
          <li key={i} style={{
            display:'flex', alignItems:'center', gap:12, padding:'10px 12px', borderRadius:12,
            background: latest ? 'var(--amber-50)' : 'transparent',
            borderTop: (!latest && i > 0) ? '1px solid var(--stone-100)' : 'none',
          }}>
            <span style={{display:'inline-flex', borderRadius:'50%',
                          boxShadow: latest ? '0 0 0 2px var(--amber-400)' : 'none'}}>
              <Avatar user={{ name: d.name }} size={34}/>
            </span>
            <div style={{minWidth:0, flex:1}}>
              <div style={{display:'flex', alignItems:'center', gap:6, minWidth:0}}>
                <span style={{fontSize:14, fontWeight:600, color:'var(--stone-800)',
                              overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{d.name}</span>
                {latest && <span style={LATEST_TAG}>Latest</span>}
                {!latest && d.source === 'bank' && (
                  <span title="Auto-imported from the linked bank account" style={AUTO_TAG}>auto</span>
                )}
              </div>
              {d.note && <div style={{fontSize:12, color:'var(--stone-400)',
                                      overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{d.note}</div>}
            </div>
            <div style={{textAlign:'right', flexShrink:0}}>
              <div style={{fontSize:14, fontWeight:700, color:'var(--stone-900)',
                           fontFeatureSettings:'"tnum" 1'}}>€{d.amount.toFixed(2)}</div>
              <div style={{fontSize:11, color:'var(--stone-400)'}}>{d.date}</div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

/* ── Style 3 · Featured — latest backer spotlit with their note as a quote ── */
function SupporterFeatured({ donations }) {
  const [top, ...rest] = donations;
  return (
    <div>
      <div style={{display:'flex', gap:14, alignItems:'flex-start', padding:16, borderRadius:14,
                   background:'var(--amber-50)', border:'1px solid var(--amber-100)'}}>
        <span style={{display:'inline-flex', borderRadius:'50%', flexShrink:0,
                      boxShadow:'0 0 0 3px var(--amber-400)'}}>
          <Avatar user={{ name: top.name }} size={52}/>
        </span>
        <div style={{minWidth:0, flex:1}}>
          <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--amber-800)',
                       textTransform:'uppercase', letterSpacing:'0.08em'}}>Latest supporter</div>
          <div style={{display:'flex', alignItems:'baseline', gap:8, flexWrap:'wrap', marginTop:3}}>
            <span style={{fontSize:16, fontWeight:700, color:'var(--stone-900)'}}>{top.name}</span>
            <span style={{fontSize:15, fontWeight:700, color:'var(--emerald-700, #047857)',
                          fontFeatureSettings:'"tnum" 1'}}>€{top.amount.toFixed(2)}</span>
          </div>
          {top.note
            ? <p style={{fontSize:13, color:'var(--stone-600)', fontStyle:'italic', margin:'6px 0 0', lineHeight:1.5}}>“{top.note}”</p>
            : <p style={{fontSize:13, color:'var(--stone-500)', margin:'6px 0 0'}}>Thanks for backing the club, {top.name.split(' ')[0]}.</p>}
        </div>
      </div>
      {rest.length > 0 && (
        <div style={{display:'flex', alignItems:'center', gap:10, marginTop:14, flexWrap:'wrap'}}>
          <AvatarStack donations={rest} max={7} size={30}/>
          <span style={{fontSize:13, color:'var(--stone-500)'}}>
            joined by {rest.length} other{rest.length === 1 ? '' : 's'}
          </span>
        </div>
      )}
    </div>
  );
}

/* Always-visible supporter shoutout — warm thank-you line + chosen layout */
function Supporters({ donations, count, justLogged, style = 'wall' }) {
  return (
    <div style={{borderTop:'1px solid var(--stone-100)', paddingTop:16}}>
      <div style={{display:'flex', alignItems:'center', gap:8, marginBottom: donations.length ? 4 : 0}}>
        <span style={{display:'inline-flex', color:'var(--amber-500)'}}><Heart size={15}/></span>
        <span style={{fontSize:14, fontWeight:700, color:'var(--stone-800)'}}>Supporters</span>
        <Badge tone="green">{count}</Badge>
      </div>
      {donations.length > 0 && (
        <p style={{fontSize:13, color:'var(--stone-500)', margin:'0 0 14px', lineHeight:1.5}}>
          Thank you to the {count} {count === 1 ? 'player' : 'players and friends'} backing this —
          every euro keeps the club on the pitch.
        </p>
      )}
      {justLogged && (
        <div style={{marginBottom:14}}>
          <Alert tone="success">Logged €{justLogged.amount.toFixed(2)} from {justLogged.name}. 🙏</Alert>
        </div>
      )}
      {!donations.length ? (
        <p style={{fontSize:14, color:'var(--stone-400)', textAlign:'center', padding:'12px 0', margin:0}}>
          Be the first to support this. 🏏
        </p>
      ) : style === 'list' ? <SupporterList donations={donations}/>
        : style === 'featured' ? <SupporterFeatured donations={donations}/>
        : <SupporterGrid donations={donations}/>}
    </div>
  );
}

/* Log-donation form (staff log for anyone; members log their own) */
function LogDonation({ user, onLog }) {
  const [open, setOpen] = React.useState(false);
  const [amount, setAmount] = React.useState('');
  const [name, setName] = React.useState('');
  const [note, setNote] = React.useState('');
  const [anon, setAnon] = React.useState(false);
  const isStaff = user.is_staff;

  const submit = (e) => {
    e.preventDefault();
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return;
    const display = anon ? 'Anonymous' : (isStaff ? (name || 'Club donor') : user.name);
    onLog({ name: display, amount: amt, note, date: 'today', source: 'manual' });
    setAmount(''); setName(''); setNote(''); setAnon(false);
  };

  return (
    <div style={{borderTop:'1px solid var(--stone-100)', paddingTop:16}}>
      <button onClick={() => setOpen(o => !o)} style={{
        width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between',
        background:'transparent', border:'none', cursor:'pointer', padding:0, textAlign:'left',
      }}>
        <span style={{display:'flex', alignItems:'center', gap:8}}>
          <span style={{fontSize:14, fontWeight:700, color:'var(--stone-800)'}}>
            {isStaff ? 'Log a donation' : 'Add your donation'}
          </span>
          <Badge tone={isStaff ? 'stone' : 'green'}>{isStaff ? 'Staff' : 'You'}</Badge>
        </span>
        <span style={{display:'inline-flex', color:'var(--stone-400)',
                      transform: open ? 'rotate(180deg)' : 'none', transition:'transform .15s'}}>
          <ChevDown size={16}/>
        </span>
      </button>
      {open && (
        <form onSubmit={submit} style={{display:'flex', flexDirection:'column', gap:12, marginTop:12}}>
          {isStaff && (
            <Input label="…or external donor name" placeholder="e.g. Local sponsor"
                   value={name} onChange={e => setName(e.target.value)}/>
          )}
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
            <Input label="Amount (€)" placeholder="25.00" inputMode="decimal"
                   value={amount} onChange={e => setAmount(e.target.value)}/>
            <Input label="Date" placeholder="2026-06-15"/>
          </div>
          <Input label="Note" placeholder="Optional"
                 value={note} onChange={e => setNote(e.target.value)}/>
          <label style={{display:'flex', alignItems:'center', gap:10, cursor:'pointer', padding:'2px 0'}}>
            <input type="checkbox" checked={anon} onChange={e => setAnon(e.target.checked)}
                   style={{width:16, height:16, accentColor:'var(--pitch-700)'}}/>
            <span style={{fontSize:14, color:'var(--stone-700)'}}>Show as “Anonymous” on the wall</span>
          </label>
          {!isStaff && (
            <p style={{fontSize:12, color:'var(--stone-400)', margin:0}}>
              Recorded under {user.name} — tick anonymous to hide your name on the wall.
            </p>
          )}
          <Button variant="primary" size="md" style={{width:'100%'}} type="submit">
            {isStaff ? 'Log donation' : 'Add my donation'}
          </Button>
        </form>
      )}
    </div>
  );
}

/* One fundraiser as a collapsible card */
function CampaignCard({ campaign, bank, user, closed=false, onLog, supporterStyle='wall' }) {
  const [open, setOpen] = React.useState(!closed);
  const [justLogged, setJustLogged] = React.useState(null);
  const accent = closed ? 'var(--stone-200)' : 'var(--pitch-600)';

  const handleLog = (d) => {
    setJustLogged(d);
    setOpen(true);
    onLog && onLog(campaign.id, d);
  };

  return (
    <Card accent={accent} style={{marginBottom:16}}>
      <button onClick={() => setOpen(o => !o)} style={{
        width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between', gap:12,
        background:'transparent', border:'none', cursor:'pointer', padding:'14px 18px', textAlign:'left',
      }}>
        <div style={{display:'flex', alignItems:'center', gap:10, minWidth:0}}>
          <span style={{display:'inline-flex', color:'var(--stone-400)', flexShrink:0,
                        transform: open ? 'rotate(90deg)' : 'none', transition:'transform .15s'}}>
            <ChevRt size={16}/>
          </span>
          <div style={{display:'flex', flexDirection:'column', gap:7, minWidth:0}}>
            <div style={{display:'flex', alignItems:'center', gap:8, minWidth:0}}>
              <span style={{fontSize:14, fontWeight:700, minWidth:0,
                            color: closed ? 'var(--stone-500)' : 'var(--stone-800)',
                            overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{campaign.title}</span>
              <Badge tone={closed ? 'stone' : 'green'} style={{flexShrink:0}}>
                <span style={{width:6, height:6, borderRadius:'50%',
                              background: closed ? 'var(--stone-400)' : 'var(--emerald-500)'}}/>
                {closed ? 'Closed' : 'Active'}
              </Badge>
            </div>
            {campaign.donations && campaign.donations.length > 0 && (
              <AvatarStack donations={campaign.donations} max={5} size={22}/>
            )}
          </div>
        </div>
        <div style={{textAlign:'right', flexShrink:0}}>
          <div style={{fontSize:14, fontWeight:700, fontFeatureSettings:'"tnum" 1',
                       color: closed ? 'var(--stone-600)' : 'var(--stone-900)'}}>
            €{campaign.raised.toFixed(2)}
            {campaign.goal && <span style={{color:'var(--stone-400)', fontWeight:400}}> / €{campaign.goal.toFixed(2)}</span>}
          </div>
          <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-400)',
                       textTransform:'uppercase', letterSpacing:'0.08em', marginTop:2}}>
            {campaign.supporterCount} supporter{campaign.supporterCount === 1 ? '' : 's'}
          </div>
        </div>
      </button>

      {open && (
        <div style={{padding:'4px 18px 18px', display:'flex', flexDirection:'column', gap:20,
                     borderTop:'1px solid var(--stone-100)'}}>
          {/* progress bar (goal campaigns only) */}
          {campaign.goal && (
            <div style={{paddingTop:16}}>
              <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between', gap:12, marginBottom:8}}>
                <div>
                  <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-500)',
                               textTransform:'uppercase', letterSpacing:'0.08em'}}>Raised so far</div>
                  <div style={{fontSize:30, fontWeight:700, color:'var(--stone-900)', lineHeight:1,
                               fontFeatureSettings:'"tnum" 1', marginTop:4}}>€{campaign.raised.toFixed(2)}</div>
                </div>
                <div style={{textAlign:'right'}}>
                  <div style={{fontFamily:'var(--font-mono)', fontSize:9, color:'var(--stone-500)',
                               textTransform:'uppercase', letterSpacing:'0.08em'}}>Goal</div>
                  <div style={{fontSize:14, fontWeight:600, color:'var(--stone-500)',
                               fontFeatureSettings:'"tnum" 1', marginTop:4}}>€{campaign.goal.toFixed(2)}</div>
                </div>
              </div>
              <div style={{height:10, borderRadius:9999, background:'var(--stone-100)', overflow:'hidden'}}>
                <div style={{height:'100%', borderRadius:9999, background:'var(--emerald-500)',
                             width:`${campaign.progressPct}%`, transition:'width .5s'}}/>
              </div>
              <div style={{display:'flex', alignItems:'center', justifyContent:'space-between',
                           marginTop:8, fontSize:12, color:'var(--stone-500)'}}>
                <span>{campaign.supporterCount} supporter{campaign.supporterCount === 1 ? '' : 's'}</span>
                <span style={{fontWeight:600, color:'var(--emerald-700, #047857)'}}>{campaign.progressPct}%</span>
              </div>
            </div>
          )}

          {/* specific-drive blurb + fund items (general drive shows these at the top of page instead) */}
          {!campaign.isDefault && campaign.blurb && (
            <p style={{fontSize:14, color:'var(--stone-600)', lineHeight:1.5, margin: campaign.goal ? 0 : '12px 0 0'}}>
              {campaign.blurb}
            </p>
          )}
          {!campaign.isDefault && campaign.fundItems && (
            <div style={{display:'grid', gridTemplateColumns:'repeat(2, minmax(0,1fr))', gap:12}}>
              {campaign.fundItems.map((f, i) => <FundItem key={i} {...f}/>)}
            </div>
          )}

          <Supporters donations={campaign.donations} count={campaign.supporterCount}
                      justLogged={justLogged} style={supporterStyle}/>
          <HowToDonate bank={bank}/>
          {!closed && user && <LogDonation user={user} onLog={handleLog}/>}
        </div>
      )}
    </Card>
  );
}

function SupportScreen({ user, general, activeCampaigns = [], closedCampaigns = [], bank, onLog, supporterStyle = 'wall' }) {
  return (
    <div style={{maxWidth:768, margin:'0 auto', padding:'28px 24px 64px'}}>
      {/* header */}
      <header style={{marginBottom:12}}>
        <Eyebrow accent="var(--amber-500)">Support the club</Eyebrow>
        <h1 style={{fontSize:24, fontWeight:700, color:'var(--stone-900)', margin:'0',
                    letterSpacing:'-0.02em', lineHeight:1.2}}>Back Indian Cricket Ghent</h1>
        <p style={{fontSize:14, color:'var(--stone-600)', margin:'8px 0 0', lineHeight:1.6, maxWidth:560}}>
          ICG runs on the goodwill of its players — every euro keeps the nets up,
          the balls fresh, and the hall booked through the winter block.
        </p>
      </header>

      {/* what your donations fund */}
      {general && general.fundItems && (
        <section style={{margin:'24px 0 32px'}}>
          <div style={{display:'grid', gridTemplateColumns:'repeat(2, minmax(0,1fr))', gap:12}}>
            {general.fundItems.map((f, i) => <FundItem key={i} {...f}/>)}
          </div>
        </section>
      )}

      {/* staff action bar */}
      {user && user.is_staff && (
        <div style={{display:'flex', justifyContent:'flex-end', marginBottom:12}}>
          <Button variant="secondary" size="sm"><Plus size={14}/>Target fundraiser</Button>
        </div>
      )}

      {/* active campaigns — specific drives first, General Donations (catch-all) last */}
      {activeCampaigns.map(c => (
        <CampaignCard key={c.id} campaign={c} bank={bank} user={user} onLog={onLog} supporterStyle={supporterStyle}/>
      ))}
      {general && (
        <CampaignCard campaign={general} bank={bank} user={user} onLog={onLog} supporterStyle={supporterStyle}/>
      )}

      {/* previous fundraisers */}
      {closedCampaigns.length > 0 && (
        <section style={{marginTop:32}}>
          <Eyebrow>Previous fundraisers</Eyebrow>
          {closedCampaigns.map(c => (
            <CampaignCard key={c.id} campaign={c} bank={bank} user={user} closed supporterStyle={supporterStyle}/>
          ))}
        </section>
      )}
    </div>
  );
}

window.SupportScreen = SupportScreen;
