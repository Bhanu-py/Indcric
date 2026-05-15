/* global React, Icons, Avatar */
const { Home, Cog, ChevDown, User, Logout, UsersIcon = Icons.Users, Wallet, Calendar, Plus, Bell, Roundel } = Icons;

function Header({ user, route, onNavigate, onLogout, unread=0 }) {
  const [manageOpen, setManageOpen] = React.useState(false);
  const [userOpen, setUserOpen] = React.useState(false);

  return (
    <header style={{
      background: 'var(--pitch-900)', color: '#fff',
      boxShadow: 'var(--shadow-header)', position: 'sticky', top: 0, zIndex: 40
    }}>
      <div style={{maxWidth: 1280, margin: '0 auto', padding: '0 24px',
                   display:'flex', alignItems:'center', justifyContent:'space-between', height: 60}}>
        <a onClick={() => onNavigate('home')} style={{display:'flex', alignItems:'center', gap:10, cursor:'pointer', textDecoration:'none', color:'#fff'}}>
          <Roundel size={34}/>
        </a>

        <nav style={{display:'flex', alignItems:'center', gap:2}}>
          <NavLink active={route==='home'} onClick={() => onNavigate('home')} icon={<Home size={16}/>}>Dashboard</NavLink>
          <NavLink active={route==='balance'} onClick={() => onNavigate('balance')} icon={<Icons.Users size={16}/>}>Teams</NavLink>
          <NavLink active={route==='payments'} onClick={() => onNavigate('payments')} icon={<Wallet size={16}/>}>Payments</NavLink>

          {user.is_staff && (
            <div style={{position:'relative'}} onMouseLeave={() => setManageOpen(false)}>
              <NavLink onClick={() => setManageOpen(v => !v)} icon={<Cog size={16}/>}
                       active={manageOpen || ['create-session','users'].includes(route)}>
                Manage
                <span style={{transform: manageOpen?'rotate(180deg)':'none', transition:'transform .15s', display:'inline-flex'}}>
                  <ChevDown size={12}/>
                </span>
              </NavLink>
              {manageOpen && (
                <Dropdown align="right">
                  <DropdownItem icon={<Plus color="var(--pitch-600)" size={16}/>} onClick={() => { setManageOpen(false); onNavigate('create-session'); }}>New Session</DropdownItem>
                  <DropdownItem icon={<Calendar color="var(--pitch-600)" size={16}/>} onClick={() => { setManageOpen(false); onNavigate('home'); }}>Attendance</DropdownItem>
                  <DropdownItem icon={<Wallet color="var(--pitch-600)" size={16}/>} onClick={() => { setManageOpen(false); onNavigate('payments'); }}>Payments</DropdownItem>
                  <div style={{borderTop:'1px solid var(--stone-100)', margin:'4px 0'}}/>
                  <DropdownItem icon={<Icons.Users color="var(--pitch-600)" size={16}/>} onClick={() => { setManageOpen(false); onNavigate('users'); }}>Users</DropdownItem>
                </Dropdown>
              )}
            </div>
          )}

          <BellButton unread={unread} onClick={() => onNavigate('notifications')} active={route==='notifications'}/>

          <div style={{position:'relative'}} onMouseLeave={() => setUserOpen(false)}>
            <button onClick={() => setUserOpen(v => !v)} style={{
              display:'flex', alignItems:'center', gap:8, height:38, padding:'0 8px',
              borderRadius:8, background: userOpen ? 'rgba(255,255,255,0.10)' : 'transparent',
              border:'none', color:'#fff', cursor:'pointer'
            }}>
              <Avatar user={user} size={26} ring/>
              <span style={{fontSize:13, fontWeight:500, maxWidth:120,
                            overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{user.name}</span>
              <span style={{transform: userOpen?'rotate(180deg)':'none', transition:'transform .15s', display:'inline-flex'}}>
                <ChevDown size={12}/>
              </span>
            </button>
            {userOpen && (
              <Dropdown align="right">
                <div style={{padding:'10px 16px 10px', borderBottom:'1px solid var(--stone-100)', marginBottom:4}}>
                  <div style={{fontSize:12, fontWeight:600, color:'var(--stone-900)'}}>{user.name}</div>
                  <div style={{fontSize:11, color:'var(--stone-400)', fontFamily:'var(--font-mono)'}}>{user.email}</div>
                </div>
                <DropdownItem icon={<User color="var(--stone-400)" size={16}/>} onClick={() => { setUserOpen(false); onNavigate('profile'); }}>My Profile</DropdownItem>
                <DropdownItem icon={<Cog color="var(--stone-400)" size={16}/>} onClick={() => { setUserOpen(false); onNavigate('profile'); }}>Settings</DropdownItem>
                <div style={{borderTop:'1px solid var(--stone-100)', margin:'4px 0'}}/>
                <DropdownItem icon={<Logout color="var(--red-600)" size={16}/>} danger onClick={onLogout}>Log Out</DropdownItem>
              </Dropdown>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}

function BellButton({ unread, onClick, active }) {
  return (
    <button onClick={onClick} style={{
      position:'relative', display:'flex', alignItems:'center', justifyContent:'center',
      width:38, height:38, marginRight:4, borderRadius:8,
      background: active ? 'rgba(255,255,255,0.10)' : 'transparent',
      color:'#fff', border:'none', cursor:'pointer',
    }}
    onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}
    onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}>
      <Bell size={17} sw={1.75}/>
      {unread > 0 && (
        <span style={{
          position:'absolute', top:7, right:7,
          minWidth:14, height:14, padding:'0 4px', borderRadius:9999,
          background:'var(--amber-500)', color:'#fff',
          fontSize:9, fontWeight:700, fontFamily:'var(--font-mono)',
          display:'flex', alignItems:'center', justifyContent:'center',
          boxShadow:'0 0 0 2px var(--pitch-900)',
        }}>{unread}</span>
      )}
    </button>
  );
}

function NavLink({ active, onClick, icon, children }) {
  return (
    <button onClick={onClick} style={{
      display:'flex', alignItems:'center', gap:6, height:38, padding:'0 12px',
      background: active ? 'rgba(255,255,255,0.10)' : 'transparent',
      color:'#fff', border:'none', borderRadius:8, cursor:'pointer',
      fontSize:13, fontWeight:500, fontFamily:'inherit',
      transition:'background .15s', letterSpacing:'0.005em',
    }}
    onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}
    onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
    >
      {icon}{children}
    </button>
  );
}

function Dropdown({ children, align='right' }) {
  return (
    <div style={{
      position:'absolute', top: 48, [align]: 0, width: 208,
      background:'#fff', color:'var(--stone-800)',
      borderRadius:12, boxShadow:'var(--shadow-xl)',
      border:'1px solid var(--stone-100)', padding:'6px 0', zIndex:50
    }}>{children}</div>
  );
}

function DropdownItem({ icon, children, onClick, danger }) {
  return (
    <a onClick={onClick} style={{
      display:'flex', alignItems:'center', gap:10, padding:'8px 14px',
      fontSize:13, color: danger ? 'var(--red-600)' : 'var(--stone-700)',
      cursor:'pointer', textDecoration:'none'
    }}
    onMouseEnter={e => e.currentTarget.style.background = danger ? 'var(--red-50)' : 'var(--stone-50)'}
    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {icon}{children}
    </a>
  );
}

window.Header = Header;
