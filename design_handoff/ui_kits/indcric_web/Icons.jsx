/* global React */
/* ────────────────────────────────────────────────────────────
   Inline SVG icons.
   24-px viewBox, 1.75 stroke, round caps + joins.
   Stroke colour inherits from `currentColor`.
   ──────────────────────────────────────────────────────────── */

const Icon = ({ d, size = 18, sw = 1.75, fill = 'none', ...p }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
       stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" {...p}>
    {Array.isArray(d) ? d.map((x, i) => <path key={i} d={x}/>) : <path d={d}/>}
  </svg>
);

/* ── Comet-ball mark · primary logo ──
   Image lives at assets/logo-mark.png. Mark has a white background, so on dark
   surfaces (the app header / sign-in hero) we wrap it in a soft white tile to
   keep the cricket-ball + flame both legible. */
const Roundel = ({ size = 32, light = false }) => (
  <span style={{
    display:'inline-flex', alignItems:'center', justifyContent:'center',
    width: size, height: size,
    background: light ? 'transparent' : '#ffffff',
    borderRadius: light ? 0 : Math.round(size * 0.22),
    padding: light ? 0 : Math.max(2, Math.round(size * 0.08)),
    boxShadow: light ? 'none' : '0 1px 2px rgb(0 0 0 / 0.08)',
  }}>
    <img src="../../assets/logo-mark.png" alt="ICG"
         width={size - (light ? 0 : Math.max(2, Math.round(size * 0.08))*2)}
         height={size - (light ? 0 : Math.max(2, Math.round(size * 0.08))*2)}
         style={{display:'block', objectFit:'contain'}}/>
  </span>
);

/* ── Cricket role glyphs ── */
const Bat = (p) => <Icon {...p} d={["M12 3v5","M10 5.5h4","M9 8.5h6v11a1.5 1.5 0 01-1.5 1.5h-3A1.5 1.5 0 019 19.5v-11z"]}/>;
const Ball = (p) => (
  <svg width={p.size||18} height={p.size||18} viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth={p.sw||1.75} strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="12" r="8.5"/>
    <path d="M5 14c3.5 2.5 10.5 2.5 14 0"/>
    <path d="M8 14.6v1.4M11 15.4v1.4M14 15.4v1.4M16.8 14.6v1.4"/>
  </svg>
);
const AllRounder = (p) => <Icon {...p} d={["M4 4l4 4","M7 7l9 9","M14 14l3 3","M9.5 17.5a3 3 0 11-6 0 3 3 0 016 0z"]}/>;
const Keeper = (p) => <Icon {...p} d={["M7 21V11a2 2 0 014 0v2","M11 13v-1a2 2 0 014 0v3","M15 15v-2a2 2 0 014 0v6a3 3 0 01-3 3H10a3 3 0 01-3-3"]}/>;
const Trophy = (p) => <Icon {...p} d={["M7 4h10v4a5 5 0 01-10 0V4z","M7 6H4v2a3 3 0 003 3","M17 6h3v2a3 3 0 01-3 3","M9 21h6","M12 13v8"]}/>;
const Stumps = (p) => <Icon {...p} d={["M6 7v14","M12 7v14","M18 7v14","M5 6h6","M13 6h6"]}/>;

/* ── UI navigation & general ── */
const Home    = (p) => <Icon {...p} d={["M3 10l9-7 9 7","M5 10v10a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V10"]}/>;
const Calendar= (p) => <Icon {...p} d={["M3 5h18v16H3z","M3 9h18","M8 3v4","M16 3v4"]}/>;
const Pin     = (p) => <Icon {...p} d={["M12 21s-7-6.5-7-12a7 7 0 0114 0c0 5.5-7 12-7 12z","M14.5 9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"]}/>;
const Clock   = (p) => <Icon {...p} d={["M21 12a9 9 0 11-18 0 9 9 0 0118 0z","M12 7v5l3 2"]}/>;
const Wallet  = (p) => <Icon {...p} d={["M3 8a2 2 0 012-2h12a2 2 0 012 2v1h1a1 1 0 011 1v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8z","M17 13.5a.5.5 0 110-1 .5.5 0 010 1z"]}/>;
const Users   = (p) => <Icon {...p} d={["M9 8.5a3.5 3.5 0 117 0 3.5 3.5 0 01-7 0z","M4 20a8 8 0 0116 0","M16 7a3 3 0 100 6","M18 20a6 6 0 014-5.7"]}/>;
const Cog     = (p) => <Icon {...p} d={["M12 9.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z","M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.6 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.6-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"]}/>;
const Plus    = (p) => <Icon {...p} d={["M12 5v14","M5 12h14"]}/>;
const Check   = (p) => <Icon {...p} d="M5 12l5 5 9-11"/>;
const Close   = (p) => <Icon {...p} d={["M6 6l12 12","M18 6L6 18"]}/>;
const ChevDown= (p) => <Icon {...p} sw={2} d="M5 9l7 7 7-7"/>;
const ChevRt  = (p) => <Icon {...p} sw={2} d="M9 5l7 7-7 7"/>;
const Pencil  = (p) => <Icon {...p} d={["M4 20h4l10-10-4-4L4 16v4z","M14 6l4 4"]}/>;
const Logout  = (p) => <Icon {...p} d={["M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3","M10 17l-5-5 5-5","M5 12h11"]}/>;
const ArrowRt = (p) => <Icon {...p} d={["M5 12h14","M13 5l7 7-7 7"]}/>;
const Mail    = (p) => <Icon {...p} d={["M3 6h18v12H3z","M3 7l9 7 9-7"]}/>;
const Lock    = (p) => <Icon {...p} d={["M5 11h14v10H5z","M8 11V7a4 4 0 018 0v4"]}/>;
const UserIc  = (p) => <Icon {...p} d={["M8 8a4 4 0 118 0 4 4 0 01-8 0z","M4 21a8 8 0 0116 0"]}/>;
const Trash   = (p) => <Icon {...p} d={["M4 7h16","M9 7V4h6v3","M6 7l1 13a2 2 0 002 2h6a2 2 0 002-2l1-13","M10 11v7","M14 11v7"]}/>;
const Bell    = (p) => <Icon {...p} d={["M15 17H4l1.5-2v-5a6.5 6.5 0 1113 0v5l1.5 2h-3","M10 20a2 2 0 004 0"]}/>;
const Send    = (p) => <Icon {...p} d="M3 11l18-8-7 18-3-7-8-3z"/>;
const Chat    = (p) => <Icon {...p} d="M4 4h13a3 3 0 013 3v7a3 3 0 01-3 3H10l-5 4v-4a3 3 0 01-1-2V7a3 3 0 011-3z"/>;
const Phone   = (p) => <Icon {...p} d="M5 4h3l2 5-2.5 1.5a11 11 0 006 6L15 14l5 2v3a2 2 0 01-2 2A15 15 0 013 6a2 2 0 012-2z"/>;
const Share   = (p) => <Icon {...p} d={["M6 10a2 2 0 11-4 0 2 2 0 014 0z","M20 6a2 2 0 11-4 0 2 2 0 014 0z","M20 18a2 2 0 11-4 0 2 2 0 014 0z","M5.8 9l8.4-4","M5.8 11l8.4 4"]}/>;
const Copy    = (p) => <Icon {...p} d={["M8 3h10a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V5a2 2 0 012-2z","M16 17v2a2 2 0 01-2 2H4a2 2 0 01-2-2V9a2 2 0 012-2h2"]}/>;
const Download= (p) => <Icon {...p} d={["M12 4v12","M7 11l5 5 5-5","M5 20h14"]}/>;
const Search  = (p) => <Icon {...p} d={["M16.5 16.5a6 6 0 10-8.49-8.49 6 6 0 008.49 8.49z","M21 21l-4.5-4.5"]}/>;
const Filter  = (p) => <Icon {...p} d="M4 5h16l-6 8v6l-4-2v-4z"/>;
const More    = (p) => <Icon {...p} d={["M5 12.5a.5.5 0 11.001-1.001A.5.5 0 015 12.5z","M12 12.5a.5.5 0 11.001-1.001A.5.5 0 0112 12.5z","M19 12.5a.5.5 0 11.001-1.001A.5.5 0 0119 12.5z"]} sw={2.5}/>;
const Info    = (p) => <Icon {...p} d={["M21 12a9 9 0 11-18 0 9 9 0 0118 0z","M12 8v5","M12 16h.01"]}/>;
const Warn    = (p) => <Icon {...p} d={["M12 3l10 18H2L12 3z","M12 10v4","M12 17h.01"]}/>;
const Refresh = (p) => <Icon {...p} d="M21 12a8 8 0 11-3-6.2L21 4v5h-5"/>;
const Rupee   = (p) => <Icon {...p} d={["M21 12a9 9 0 11-18 0 9 9 0 0118 0z","M9 8h6","M9 11h6","M9 11c2.5 0 4 1 4 3 0 1.5-1.5 2.5-3 2.5L15 16"]}/>;
const Star    = (p) => <Icon {...p} d="M12 3l2.6 5.4 5.9.8-4.3 4.2 1 5.9L12 16.5l-5.3 2.8 1-5.9L3.5 9.2l5.9-.8L12 3z"/>;
const Image   = (p) => <Icon {...p} d={["M3 5h18v14H3z","M9 11a2 2 0 100-4 2 2 0 000 4z","M21 17l-5-5-7 7"]}/>;
const Camera  = (p) => <Icon {...p} d={["M9 4l-1.5 2H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-2.5L15 4z","M15.5 13a3.5 3.5 0 11-7 0 3.5 3.5 0 017 0z"]}/>;

window.Icons = {
  Roundel,
  // sport
  Bat, Ball, AllRounder, Keeper, Trophy, Stumps,
  // ui
  Home, Calendar, Pin, Clock, Wallet, Users, Cog, Plus, Check, Close, ChevDown, ChevRt,
  Pencil, Logout, ArrowRt, Mail, Lock, User: UserIc, Trash, Bell, Send, Chat, Phone,
  Share, Copy, Download, Search, Filter, More, Info, Warn, Refresh, Rupee, Star,
  Image, Camera,
  // legacy alias
  CricketBall: Ball,
};
