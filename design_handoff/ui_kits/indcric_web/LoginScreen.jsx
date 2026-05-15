/* global React, Button, Input, Icons */
const { Roundel, Mail, Lock, ArrowRt, Check } = Icons;

function LoginScreen({ onLogin }) {
  const [username, setUsername] = React.useState('bhanu');
  const [password, setPassword] = React.useState('••••••••');
  const [error, setError] = React.useState('');

  const submit = (e) => {
    e.preventDefault();
    if (!username) { setError('Please enter your username'); return; }
    onLogin({ name:'Bhanu Tej', username, email:'bhanu@indcric.club', is_staff: true });
  };

  return (
    <div style={{display:'flex', minHeight:'100vh', background:'#fff'}}>

      {/* ── Left — dark cricket hero ── */}
      <div style={{
        display:'flex', flexDirection:'column', width:'46%', maxWidth:560,
        background:'var(--pitch-950)', position:'relative', overflow:'hidden'
      }} className="login-hero">
        <CricketGroundSVG/>

        <div style={{position:'relative', zIndex:1, padding:'40px 48px',
                     display:'flex', flexDirection:'column', height:'100%'}}>
          <a style={{display:'flex', alignItems:'center', gap:10, width:'fit-content'}}>
            <Roundel size={36}/>
            <span style={{fontWeight:600, fontSize:14, color:'#fff', letterSpacing:'-0.005em'}}>ICG</span>
          </a>

          <div style={{flex:1, display:'flex', flexDirection:'column', justifyContent:'center', padding:'32px 0'}}>
            <div style={{
              display:'inline-flex', alignItems:'center', gap:8,
              background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.08)',
              borderRadius:9999, padding:'5px 12px', marginBottom:28, width:'fit-content'
            }}>
              <span style={{width:6, height:6, borderRadius:'50%', background:'var(--emerald-400, #34d399)',
                            display:'inline-block', animation:'pulse 2s infinite'}}/>
              <span style={{fontSize:11, fontWeight:500, color:'rgba(255,255,255,0.7)',
                            fontFamily:'var(--font-mono)', letterSpacing:'0.04em'}}>
                CRICKET CLUB MANAGER
              </span>
            </div>

            <h2 style={{fontSize:44, fontWeight:700, color:'#fff', lineHeight:1.05,
                        letterSpacing:'-0.025em', margin:'0 0 18px'}}>
              Your pitch.<br/>Your play.
              <span style={{display:'block', color:'var(--pitch-400)'}}>All in one place.</span>
            </h2>

            <p style={{fontSize:14, color:'var(--pitch-300, #86efac)', lineHeight:1.55, marginBottom:32, maxWidth:300}}>
              Manage sessions, split costs, balance teams by skill, and track every match — built for the way your club really runs.
            </p>

            <ul style={{listStyle:'none', padding:0, margin:0, display:'flex', flexDirection:'column', gap:12}}>
              {[
                'Smart team balancing by skill ratings',
                'Session payments & settlement',
                'Attendance polls & match history',
                'WhatsApp-shareable session cards'
              ].map((t,i) => (
                <li key={i} style={{display:'flex', alignItems:'center', gap:11}}>
                  <div style={{width:18, height:18, borderRadius:'50%', background:'var(--pitch-700)',
                               display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, color:'#fff'}}>
                    <Check size={11} sw={2.2}/>
                  </div>
                  <span style={{fontSize:13, color:'var(--pitch-200, #bbf7d0)', fontWeight:500}}>{t}</span>
                </li>
              ))}
            </ul>
          </div>

          <p style={{fontSize:11, color:'var(--pitch-700)', fontFamily:'var(--font-mono)',
                     letterSpacing:'0.04em', margin:0}}>
            © 2026 ICG · BUILT FOR THE CLUB
          </p>
        </div>
      </div>

      {/* ── Right — form ── */}
      <div style={{flex:1, display:'flex', alignItems:'center', justifyContent:'center', padding:40}}>
        <div style={{width:'100%', maxWidth:340}}>
          <div style={{marginBottom:28}}>
            <h1 style={{fontSize:22, fontWeight:700, color:'var(--stone-900)', margin:'0 0 6px',
                        letterSpacing:'-0.015em'}}>Welcome back</h1>
            <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>
              Sign in to continue to your club dashboard
            </p>
          </div>

          {error && (
            <div style={{marginBottom:16, padding:'10px 12px', background:'var(--red-50)',
                         border:'1px solid #fecaca', borderRadius:10,
                         fontSize:13, color:'var(--red-700)'}}>{error}</div>
          )}

          <form onSubmit={submit} style={{display:'flex', flexDirection:'column', gap:16}}>
            <Input label="Username or Email" icon={<Mail size={15} sw={1.75}/>}
                   value={username} onChange={e => setUsername(e.target.value)}
                   placeholder="your_username" autoComplete="username"/>
            <div>
              <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:6}}>
                <label style={{fontSize:13, fontWeight:500, color:'var(--stone-700)'}}>Password</label>
                <a style={{fontSize:12, fontWeight:500, color:'var(--pitch-700)', cursor:'pointer'}}>Forgot password?</a>
              </div>
              <Input icon={<Lock size={15} sw={1.75}/>} type="password" value={password}
                     onChange={e => setPassword(e.target.value)} placeholder="••••••••"/>
            </div>

            <label style={{display:'flex', alignItems:'center', gap:8, fontSize:13, color:'var(--stone-600)', cursor:'pointer'}}>
              <input type="checkbox" defaultChecked style={{width:14, height:14, accentColor:'var(--pitch-600)'}}/>
              Remember me for 30 days
            </label>

            <Button variant="primary" size="lg" type="submit"
                    style={{width:'100%', justifyContent:'center', marginTop:4}}>
              Sign In <ArrowRt size={14} sw={1.75}/>
            </Button>
          </form>

          <div style={{marginTop:28, paddingTop:20, borderTop:'1px solid var(--stone-100)', textAlign:'center'}}>
            <p style={{fontSize:13, color:'var(--stone-500)', margin:0}}>
              New to IndCric?
              <a style={{marginLeft:6, fontWeight:500, color:'var(--pitch-700)', cursor:'pointer'}}>
                Create an account →
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function CricketGroundSVG() {
  return (
    <svg style={{position:'absolute', inset:0, width:'100%', height:'100%', pointerEvents:'none'}}
         viewBox="0 0 480 680" fill="none" preserveAspectRatio="xMidYMid slice">
      <ellipse cx="240" cy="380" rx="240" ry="310" stroke="white" strokeWidth="1" opacity="0.05"/>
      <ellipse cx="240" cy="380" rx="148" ry="186" stroke="white" strokeWidth="1" opacity="0.05"/>
      <rect x="222" y="240" width="36" height="280" stroke="white" strokeWidth="1.5" opacity="0.08" rx="2"/>
      <line x1="210" y1="268" x2="270" y2="268" stroke="white" strokeWidth="1" opacity="0.12"/>
      <line x1="210" y1="492" x2="270" y2="492" stroke="white" strokeWidth="1" opacity="0.12"/>
      {[231,240,249].flatMap(x => [
        <line key={x+'a'} x1={x} y1="254" x2={x} y2="268" stroke="white" strokeWidth="1.5" opacity="0.18"/>,
        <line key={x+'b'} x1={x} y1="492" x2={x} y2="506" stroke="white" strokeWidth="1.5" opacity="0.18"/>,
      ])}
      <circle cx="420" cy="80" r="160" stroke="white" strokeWidth="1" opacity="0.03"/>
      <circle cx="420" cy="80" r="100" stroke="white" strokeWidth="1" opacity="0.03"/>
    </svg>
  );
}

window.LoginScreen = LoginScreen;
