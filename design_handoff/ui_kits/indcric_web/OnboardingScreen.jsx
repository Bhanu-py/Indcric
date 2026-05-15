/* global React, Card, Badge, Button, Input, RoleBadge, RatingBar, Avatar, Icons */
const { Roundel, Bat, Ball, AllRounder, Keeper, Check, ArrowRt } = Icons;

/* ────────── Onboarding — first-time member ──────────
   3 steps: 1) profile basics 2) role & skill 3) say hi
   Sits in a modal-like card centred on the page (no full-bleed hero — fast). */
function OnboardingScreen({ onDone, onSkip }) {
  const [step, setStep] = React.useState(0);
  const [name, setName] = React.useState('');
  const [username, setUsername] = React.useState('');
  const [role, setRole] = React.useState('batsman');
  const [batting, setBatting] = React.useState(3);
  const [bowling, setBowling] = React.useState(3);
  const [fielding, setFielding] = React.useState(3);
  const [whatsapp, setWhatsapp] = React.useState(true);

  const steps = ['Identity', 'Role & skill', 'Wrap up'];

  const next = () => step < 2 ? setStep(step + 1) : onDone({
    name, username, role, batting, bowling, fielding, whatsapp,
    email: `${username || 'me'}@indcric.club`,
    stats:{ matches:0, runs:0, wickets:0, catches:0, stumpings:0 },
  });
  const back = () => setStep(Math.max(0, step - 1));

  return (
    <div style={{
      minHeight:'100vh', background:'var(--stone-50)',
      display:'flex', alignItems:'center', justifyContent:'center',
      padding:'40px 24px',
    }}>
      <Card style={{width:'100%', maxWidth:520}}>
        <div style={{padding:'22px 24px 16px', borderBottom:'1px solid var(--stone-100)',
                     display:'flex', alignItems:'center', gap:12}}>
          <Roundel size={32}/>
          <div style={{flex:1}}>
            <div style={{fontSize:11, fontFamily:'var(--font-mono)', letterSpacing:'0.08em',
                         color:'var(--stone-400)', textTransform:'uppercase'}}>
              Step {step+1} of 3
            </div>
            <div style={{fontSize:15, fontWeight:600, color:'var(--stone-900)', marginTop:2,
                         letterSpacing:'-0.005em'}}>{steps[step]}</div>
          </div>
          {/* Progress dots */}
          <div style={{display:'flex', gap:4}}>
            {steps.map((_, i) => (
              <span key={i} style={{
                width: i === step ? 18 : 8, height:6, borderRadius:3,
                background: i <= step ? 'var(--pitch-600)' : 'var(--stone-200)',
                transition:'width .2s, background .2s',
              }}/>
            ))}
          </div>
        </div>

        <div style={{padding:'20px 24px'}}>
          {step === 0 && (
            <StepIdentity name={name} setName={setName} username={username} setUsername={setUsername}/>
          )}
          {step === 1 && (
            <StepRole role={role} setRole={setRole}
                      batting={batting} setBatting={setBatting}
                      bowling={bowling} setBowling={setBowling}
                      fielding={fielding} setFielding={setFielding}/>
          )}
          {step === 2 && (
            <StepWrap name={name} role={role} whatsapp={whatsapp} setWhatsapp={setWhatsapp}
                      batting={batting} bowling={bowling} fielding={fielding}/>
          )}
        </div>

        <div style={{padding:'14px 24px 18px', borderTop:'1px solid var(--stone-100)',
                     display:'flex', alignItems:'center', justifyContent:'space-between', gap:10}}>
          <Button variant="ghost" onClick={step === 0 ? onSkip : back}>
            {step === 0 ? 'Skip' : '← Back'}
          </Button>
          <Button variant="primary" onClick={next}
                  icon={step === 2 ? <Check size={13} sw={1.75}/> : null}>
            {step === 2 ? 'Enter the club' : 'Next'} {step < 2 && <ArrowRt size={13} sw={1.75}/>}
          </Button>
        </div>
      </Card>
    </div>
  );
}

function StepIdentity({ name, setName, username, setUsername }) {
  return (
    <div style={{display:'flex', flexDirection:'column', gap:14}}>
      <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>
        Welcome to IndCric — let's set up your member profile. Takes about 30 seconds.
      </p>
      <Input label="Full name" placeholder="Bhanu Tej" value={name}
             onChange={e => setName(e.target.value)}/>
      <Input label="Username" placeholder="bhanu" hint="Lowercase, used everywhere in the club."
             value={username} onChange={e => setUsername(e.target.value.toLowerCase())}/>
    </div>
  );
}

function StepRole({ role, setRole, batting, setBatting, bowling, setBowling, fielding, setFielding }) {
  const ROLES = [
    { id:'batsman',    label:'Batsman',    Glyph: Bat,        tone:{ bg:'var(--sky-100)',    bd:'#bae6fd', fg:'var(--sky-800)' } },
    { id:'bowler',     label:'Bowler',     Glyph: Ball,       tone:{ bg:'var(--red-50)',     bd:'var(--red-100)', fg:'var(--red-800)' } },
    { id:'allrounder', label:'Allrounder', Glyph: AllRounder, tone:{ bg:'var(--purple-100)', bd:'#e9d5ff', fg:'var(--purple-800)' } },
    { id:'keeper',     label:'Keeper',     Glyph: Keeper,     tone:{ bg:'var(--stone-100)',  bd:'var(--stone-200)', fg:'var(--stone-700)' } },
  ];
  return (
    <div style={{display:'flex', flexDirection:'column', gap:18}}>
      <div>
        <label style={{fontSize:13, fontWeight:500, color:'var(--stone-700)', display:'block', marginBottom:8}}>
          Pick your role
        </label>
        <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:8}}>
          {ROLES.map(r => {
            const selected = role === r.id;
            return (
              <button key={r.id} onClick={() => setRole(r.id)} style={{
                display:'flex', alignItems:'center', gap:10, padding:'10px 12px',
                background: selected ? r.tone.bg : '#fff',
                border:`1px solid ${selected ? r.tone.bd : 'var(--stone-200)'}`,
                color: selected ? r.tone.fg : 'var(--stone-700)',
                borderRadius:10, cursor:'pointer', fontFamily:'inherit', fontSize:13, fontWeight:500,
                textAlign:'left',
              }}>
                <r.Glyph size={16} sw={1.75}/> {r.label}
              </button>
            );
          })}
        </div>
      </div>
      <div>
        <label style={{fontSize:13, fontWeight:500, color:'var(--stone-700)', display:'block', marginBottom:8}}>
          Rate yourself
        </label>
        <div style={{display:'flex', flexDirection:'column', gap:12}}>
          <SkillRow label="Batting"  value={batting}  onChange={setBatting}/>
          <SkillRow label="Bowling"  value={bowling}  onChange={setBowling}/>
          <SkillRow label="Fielding" value={fielding} onChange={setFielding}/>
        </div>
        <p style={{fontSize:11, color:'var(--stone-400)', margin:'10px 0 0',
                   fontFamily:'var(--font-mono)', letterSpacing:'0.04em'}}>
          Teammates can refine your ratings later · rolling avg over time
        </p>
      </div>
    </div>
  );
}

function SkillRow({ label, value, onChange }) {
  return (
    <div style={{display:'grid', gridTemplateColumns:'1fr auto auto', alignItems:'center', columnGap:14}}>
      <span style={{fontSize:13, fontWeight:500, color:'var(--stone-700)'}}>{label}</span>
      <RatingBar value={value} editable onChange={onChange}/>
      <span style={{fontFamily:'var(--font-mono)', fontSize:11, color:'var(--stone-500)',
                    fontFeatureSettings:'"tnum" 1', minWidth:28, textAlign:'right'}}>
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function StepWrap({ name, role, whatsapp, setWhatsapp, batting, bowling, fielding }) {
  const avg = ((batting + bowling + fielding) / 3).toFixed(2);
  return (
    <div style={{display:'flex', flexDirection:'column', gap:14}}>
      <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>
        Looking good. Here's your profile snapshot:
      </p>
      <div style={{
        display:'flex', alignItems:'center', gap:12,
        padding:'12px 14px', background:'var(--stone-50)', borderRadius:10,
        border:'1px solid var(--stone-100)',
      }}>
        <Avatar user={{name: name || 'New Member'}} size={42}/>
        <div style={{flex:1, minWidth:0}}>
          <div style={{fontSize:14, fontWeight:600, color:'var(--stone-900)',
                       letterSpacing:'-0.005em'}}>{name || 'New Member'}</div>
          <div style={{
            fontFamily:'var(--font-mono)', fontSize:10, color:'var(--stone-500)',
            letterSpacing:'0.04em', marginTop:2,
          }}>
            Avg skill {avg} · joining 14 active members
          </div>
        </div>
        <RoleBadge role={role}/>
      </div>

      <label style={{
        display:'flex', alignItems:'flex-start', gap:10, padding:'12px 14px',
        border:'1px solid var(--stone-100)', borderRadius:10, cursor:'pointer',
      }}>
        <input type="checkbox" checked={whatsapp} onChange={e => setWhatsapp(e.target.checked)}
               style={{marginTop:2, accentColor:'var(--pitch-600)'}}/>
        <div>
          <div style={{fontSize:13, fontWeight:500, color:'var(--stone-800)'}}>Join the WhatsApp community</div>
          <div style={{fontSize:12, color:'var(--stone-500)', marginTop:2}}>
            Get session announcements, polls, and line-ups in your phone — same channel the club already uses.
          </div>
        </div>
      </label>
    </div>
  );
}

window.OnboardingScreen = OnboardingScreen;
