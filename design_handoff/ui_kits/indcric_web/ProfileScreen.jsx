/* global React, Card, Badge, Button, RatingBar, Avatar, RoleBadge, StatColumn, Icons */
const { Pencil, Mail } = Icons;

function ProfileScreen({ user, onBack }) {
  const [editing, setEditing] = React.useState(false);
  const [batting, setBatting] = React.useState(user.batting);
  const [bowling, setBowling] = React.useState(user.bowling);
  const [fielding, setFielding] = React.useState(user.fielding);

  return (
    <div style={{maxWidth:720, margin:'0 auto', padding:'28px 24px',
                 display:'flex', flexDirection:'column', gap:18}}>
      <a onClick={onBack} style={{
        display:'inline-flex', alignItems:'center', gap:6, fontSize:13, color:'var(--stone-500)',
        cursor:'pointer', width:'fit-content', textDecoration:'none'
      }}>← Back</a>

      {/* Identity card */}
      <Card>
        <div style={{height:64, background:'linear-gradient(90deg, var(--pitch-800), var(--pitch-600))'}}/>
        <div style={{padding:'0 22px 22px'}}>
          <div style={{display:'flex', alignItems:'flex-end', justifyContent:'space-between',
                       marginTop:-30, marginBottom:14}}>
            <Avatar user={user} size={60} ring/>
            <Button variant="secondary" size="sm"
                    icon={<Pencil size={12} sw={1.75}/>}
                    onClick={() => setEditing(v => !v)}>
              {editing ? 'Done' : 'Edit Profile'}
            </Button>
          </div>

          <div style={{display:'flex', alignItems:'center', gap:10, flexWrap:'wrap'}}>
            <div>
              <h1 style={{fontSize:18, fontWeight:600, color:'var(--stone-900)', margin:0,
                          letterSpacing:'-0.01em'}}>{user.name}</h1>
              <p style={{fontSize:12, color:'var(--stone-400)', fontFamily:'var(--font-mono)',
                         margin:'2px 0 0'}}>@{user.username}</p>
            </div>
            <RoleBadge role={user.role}/>
            {user.is_staff && <Badge tone="amber">Staff</Badge>}
          </div>
          <p style={{fontSize:12, color:'var(--stone-500)', margin:'10px 0 0',
                     display:'flex', alignItems:'center', gap:6}}>
            <Mail size={13} sw={1.75}/> {user.email}
          </p>
        </div>
      </Card>

      {/* Skill ratings */}
      <Card>
        <SectionHeader title="Skill Ratings"/>
        <div style={{padding:'4px 22px 18px', display:'flex', flexDirection:'column', gap:14}}>
          <RatingRow label="Batting" value={batting} editing={editing} onChange={setBatting}/>
          <RatingRow label="Bowling" value={bowling} editing={editing} onChange={setBowling}/>
          <RatingRow label="Fielding" value={fielding} editing={editing} onChange={setFielding}/>
        </div>
      </Card>

      {/* Career stats — typographic columns */}
      <Card>
        <SectionHeader title="Career Stats"/>
        <div style={{padding:'14px 22px 18px', display:'grid', gridTemplateColumns:'repeat(5, 1fr)'}}>
          <StatColumn first label="● Matches"  value={user.stats.matches}   dot="var(--pitch-500)"/>
          <StatColumn       label="● Runs"     value={user.stats.runs}      dot="var(--sky-500)"/>
          <StatColumn       label="● Wickets"  value={user.stats.wickets}   dot="var(--red-500)"/>
          <StatColumn       label="● Catches"  value={user.stats.catches}   dot="#a855f7"/>
          <StatColumn       label="● Stumps"   value={user.stats.stumpings} dot="var(--amber-500)"/>
        </div>
      </Card>
    </div>
  );
}

function SectionHeader({ title }) {
  return (
    <div style={{padding:'12px 22px', borderBottom:'1px solid var(--stone-100)'}}>
      <h2 style={{
        fontFamily:'var(--font-mono)', fontSize:10, fontWeight:500,
        textTransform:'uppercase', letterSpacing:'0.08em',
        color:'var(--stone-500)', margin:0,
      }}>{title}</h2>
    </div>
  );
}

function RatingRow({ label, value, editing, onChange }) {
  return (
    <div style={{
      display:'grid', gridTemplateColumns:'1fr auto auto',
      alignItems:'center', columnGap:14,
    }}>
      <span style={{fontSize:13, fontWeight:500, color:'var(--stone-700)'}}>{label}</span>
      <RatingBar value={value} editable={editing} onChange={onChange}/>
      {editing ? (
        <input type="number" min={0} max={5} step={0.5} value={value}
               onChange={e => onChange(Math.max(0, Math.min(5, parseFloat(e.target.value)||0)))}
               style={{width:54, padding:'3px 8px', textAlign:'right',
                       border:'1px solid var(--stone-200)', borderRadius:6,
                       fontFamily:'var(--font-mono)', fontSize:11}}/>
      ) : (
        <span style={{
          fontFamily:'var(--font-mono)', fontSize:12, color:'var(--stone-500)',
          minWidth:28, textAlign:'right',
          fontFeatureSettings:'"tnum" 1',
        }}>{value.toFixed(1)}</span>
      )}
    </div>
  );
}

window.ProfileScreen = ProfileScreen;
