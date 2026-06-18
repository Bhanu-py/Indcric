/* @ds-bundle: {"format":3,"namespace":"BhanuSDesignSystem_019e2a","components":[],"sourceHashes":{"ui_kits/indcric_web/DashboardScreen.jsx":"d3080a9ca765","ui_kits/indcric_web/Header.jsx":"5c4c71495123","ui_kits/indcric_web/Icons.jsx":"53bb525f5a0b","ui_kits/indcric_web/LoginScreen.jsx":"60622854bb40","ui_kits/indcric_web/MatchResultScreen.jsx":"cafad1fc70ce","ui_kits/indcric_web/NotificationsScreen.jsx":"91a3adebe0a6","ui_kits/indcric_web/OnboardingScreen.jsx":"361309f54d44","ui_kits/indcric_web/PaymentsScreen.jsx":"adea9e07e665","ui_kits/indcric_web/Primitives.jsx":"2f0829bcd0b0","ui_kits/indcric_web/ProfileScreen.jsx":"94184680708a","ui_kits/indcric_web/SessionCard.jsx":"3e6b982d84ab","ui_kits/indcric_web/SessionDetailScreen.jsx":"443feffb5af3","ui_kits/indcric_web/SupportScreen.jsx":"5263ae888a46","ui_kits/indcric_web/tweaks-panel.jsx":"22c052960f83"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.BhanuSDesignSystem_019e2a = window.BhanuSDesignSystem_019e2a || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/indcric_web/DashboardScreen.jsx
try { (() => {
/* global React, SessionCard, Button, Eyebrow, Card, Alert, StatColumn, Icons */
const {
  Plus,
  Calendar: CalIcon,
  Wallet,
  Users: UsersIcon,
  ArrowRt,
  ChevRt,
  Check,
  Lock
} = Icons;
const fmtEur = n => '€' + (n == null ? '0.00' : Number(n).toFixed(2));

/* ────────── Dashboard ──────────
   Visibility matrix:
   • GUEST  (no user)    — upcoming cards + previous (locked overlay). No stats strip.
                           No "settle payments" shortcut. CTA to sign in.
   • MEMBER (logged in)  — upcoming + previous, both clickable. No stats strip.
                           No "settle payments" shortcut.
   • STAFF  (is_staff)   — everything: stats strip, all shortcuts, new-session CTA.
*/
function DashboardScreen({
  user,
  sessions,
  onOpenSession,
  onDelete,
  onCreate,
  onNavigate,
  onSignIn
}) {
  const upcoming = sessions.filter(s => !s.past);
  const past = sessions.filter(s => s.past);
  const next = upcoming[0];
  const isGuest = !user;
  const isStaff = !!user?.is_staff;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1280,
      margin: '0 auto',
      padding: '28px 24px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      gap: 16,
      marginBottom: 24,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("div", null, isGuest ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 24,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: 0,
      letterSpacing: '-0.02em'
    }
  }, "Welcome to ICG"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      marginTop: 4,
      marginBottom: 0
    }
  }, "Sign in to vote on sessions, see line-ups, and track payments.")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 24,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: 0,
      letterSpacing: '-0.02em'
    }
  }, "Welcome back, ", user.name.split(' ')[0], " ", /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-block'
    }
  }, "\uD83D\uDC4B")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      marginTop: 4,
      marginBottom: 0
    }
  }, "Here's what's happening with IndCric"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8
    }
  }, isGuest && /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: onSignIn
  }, "Sign in \u2192"), isStaff && /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    icon: /*#__PURE__*/React.createElement(Plus, {
      size: 13,
      sw: 1.75
    }),
    onClick: onCreate
  }, "New Session"))), !isGuest && /*#__PURE__*/React.createElement("div", {
    className: "snapshot-strip",
    style: {
      marginBottom: 24
    }
  }, next ? /*#__PURE__*/React.createElement(Card, {
    hoverable: true,
    style: {
      cursor: 'pointer'
    },
    accent: "var(--pitch-600)"
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => onOpenSession(next),
    style: {
      padding: '14px 18px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Next up \xB7 ", next.dateLabel), next.poll && !next.poll.closed && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      fontSize: 9,
      fontWeight: 700,
      color: 'var(--emerald-700)',
      fontFamily: 'var(--font-mono)',
      textTransform: 'uppercase',
      letterSpacing: '0.06em'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'var(--emerald-500)'
    }
  }), "Live poll")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 600,
      color: 'var(--stone-900)',
      letterSpacing: '-0.01em',
      lineHeight: 1.2,
      marginBottom: 6
    }
  }, next.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)'
    }
  }, next.location, " \xB7 ", next.time), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 12,
      paddingTop: 10,
      borderTop: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: 12,
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--stone-600)'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--emerald-700)'
    }
  }, next.poll?.yes), " in \xB7 ", next.poll?.no, " out"), /*#__PURE__*/React.createElement(VotePill, {
    vote: next.userVote,
    open: next.poll && !next.poll.closed
  })))) : /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 18px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginBottom: 8
    }
  }, "Next up"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)'
    }
  }, "No upcoming sessions yet."))), /*#__PURE__*/React.createElement(SnapshotStat, {
    label: "Your outstanding",
    value: fmtEur(user.outstanding),
    dot: "var(--amber-500)",
    onClick: () => onNavigate('profile')
  }), /*#__PURE__*/React.createElement(SnapshotStat, {
    label: "Wallet balance",
    value: fmtEur(user.wallet),
    dot: "var(--sky-500)",
    onClick: () => onNavigate('profile')
  })), !isGuest && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginBottom: 28,
      flexWrap: 'wrap'
    }
  }, next && /*#__PURE__*/React.createElement(Shortcut, {
    icon: /*#__PURE__*/React.createElement(UsersIcon, {
      size: 14
    }),
    label: "Balance teams",
    onClick: () => onOpenSession(next)
  }), isStaff && /*#__PURE__*/React.createElement(Shortcut, {
    icon: /*#__PURE__*/React.createElement(Wallet, {
      size: 14
    }),
    label: "Settle payments",
    onClick: () => onNavigate('payments')
  }), /*#__PURE__*/React.createElement(Shortcut, {
    icon: /*#__PURE__*/React.createElement(CalIcon, {
      size: 14
    }),
    label: "Past sessions",
    onClick: () => window.scrollTo({
      top: document.body.scrollHeight,
      behavior: 'smooth'
    })
  })), /*#__PURE__*/React.createElement("section", {
    style: {
      marginBottom: 34
    }
  }, /*#__PURE__*/React.createElement(Eyebrow, null, "Upcoming Sessions"), upcoming.length ? /*#__PURE__*/React.createElement("div", {
    className: "grid-3"
  }, upcoming.map(s => /*#__PURE__*/React.createElement(SessionCard, {
    key: s.id,
    session: s,
    onClick: () => isGuest ? onSignIn() : onOpenSession(s),
    onDelete: onDelete,
    isStaff: isStaff,
    locked: isGuest,
    lockedHint: "Sign in to vote"
  }))) : /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#fff',
      border: '1px solid var(--stone-100)',
      borderRadius: 16,
      padding: '36px 24px',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '0 auto 12px',
      color: 'var(--stone-300)'
    }
  }, /*#__PURE__*/React.createElement(CalIcon, {
    size: 36,
    sw: 1.5
  })), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "No upcoming sessions."), isStaff && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: onCreate
  }, "Create one")))), /*#__PURE__*/React.createElement("section", null, /*#__PURE__*/React.createElement(Eyebrow, {
    accent: "var(--stone-300)"
  }, "Previous Sessions"), /*#__PURE__*/React.createElement("div", {
    className: "grid-3"
  }, past.map(s => /*#__PURE__*/React.createElement(SessionCard, {
    key: s.id,
    session: s,
    dimmed: true,
    onClick: () => isGuest ? onSignIn() : onOpenSession(s),
    isStaff: isStaff,
    locked: isGuest,
    lockedHint: "Sign in to see line-ups"
  })))));
}

/* Per-user money card — left stat + chevron, links to the profile tab */
function SnapshotStat({
  label,
  value,
  dot,
  onClick
}) {
  return /*#__PURE__*/React.createElement(Card, {
    hoverable: true,
    style: {
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    style: {
      padding: '14px 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: label,
    value: value,
    dot: dot
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--stone-300)',
      flexShrink: 0,
      display: 'inline-flex'
    }
  }, /*#__PURE__*/React.createElement(ChevRt, {
    size: 16
  }))));
}

/* Vote-status pill on the Next-up card */
function VotePill({
  vote,
  open
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    flexShrink: 0,
    padding: '2px 8px',
    borderRadius: 9999,
    fontSize: 11,
    fontWeight: 600,
    lineHeight: 1.4
  };
  if (vote === 'yes') return /*#__PURE__*/React.createElement("span", {
    style: {
      ...base,
      background: 'var(--emerald-100)',
      color: 'var(--emerald-800)'
    }
  }, /*#__PURE__*/React.createElement(Check, {
    size: 12,
    sw: 3
  }), "You're in");
  if (vote === 'no') return /*#__PURE__*/React.createElement("span", {
    style: {
      ...base,
      background: 'var(--stone-100)',
      color: 'var(--stone-600)'
    }
  }, "You're out");
  if (open) return /*#__PURE__*/React.createElement("span", {
    style: {
      ...base,
      background: 'var(--pitch-100)',
      color: 'var(--pitch-700)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'var(--pitch-500)',
      animation: 'pulse 2s ease-in-out infinite'
    }
  }), "Tap to vote");
  return null;
}
function Shortcut({
  icon,
  label,
  onClick
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      background: '#fff',
      border: '1px solid var(--stone-200)',
      borderRadius: 8,
      padding: '6px 12px',
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)',
      cursor: 'pointer',
      fontFamily: 'inherit',
      lineHeight: 1
    },
    onMouseEnter: e => e.currentTarget.style.background = 'var(--stone-50)',
    onMouseLeave: e => e.currentTarget.style.background = '#fff'
  }, icon, label);
}
window.DashboardScreen = DashboardScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/DashboardScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/Header.jsx
try { (() => {
/* global React, Icons, Avatar */
const {
  Home,
  Cog,
  ChevDown,
  User,
  Logout,
  UsersIcon = Icons.Users,
  Wallet,
  Calendar,
  Plus,
  Bell,
  Roundel,
  Heart
} = Icons;
function Header({
  user,
  route,
  onNavigate,
  onLogout,
  unread = 0
}) {
  const [manageOpen, setManageOpen] = React.useState(false);
  const [userOpen, setUserOpen] = React.useState(false);
  const manageRef = React.useRef(null);
  const userRef = React.useRef(null);

  // Close dropdowns on outside-click or Escape. Hover-leave was closing the
  // menu the instant the cursor crossed the small gap between trigger and
  // panel — that's why "Log Out" was unreachable.
  React.useEffect(() => {
    if (!manageOpen && !userOpen) return;
    const onDocDown = e => {
      if (manageOpen && manageRef.current && !manageRef.current.contains(e.target)) setManageOpen(false);
      if (userOpen && userRef.current && !userRef.current.contains(e.target)) setUserOpen(false);
    };
    const onKey = e => {
      if (e.key === 'Escape') {
        setManageOpen(false);
        setUserOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [manageOpen, userOpen]);
  return /*#__PURE__*/React.createElement("header", {
    style: {
      background: 'var(--pitch-700)',
      color: '#fff',
      boxShadow: 'var(--shadow-header)',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1280,
      margin: '0 auto',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: 60
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: () => onNavigate('home'),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      cursor: 'pointer',
      textDecoration: 'none',
      color: '#fff'
    }
  }, /*#__PURE__*/React.createElement(Roundel, {
    size: 44
  })), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 2
    }
  }, /*#__PURE__*/React.createElement(NavLink, {
    active: route === 'home',
    onClick: () => onNavigate('home'),
    icon: /*#__PURE__*/React.createElement(Home, {
      size: 16
    })
  }, "Dashboard"), /*#__PURE__*/React.createElement(NavLink, {
    active: route === 'support',
    onClick: () => onNavigate('support'),
    icon: /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        color: 'var(--amber-400)'
      }
    }, /*#__PURE__*/React.createElement(Heart, {
      size: 16
    }))
  }, "Support"), user.is_staff && /*#__PURE__*/React.createElement("div", {
    ref: manageRef,
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement(NavLink, {
    onClick: () => {
      setManageOpen(v => !v);
      setUserOpen(false);
    },
    icon: /*#__PURE__*/React.createElement(Cog, {
      size: 16
    }),
    active: manageOpen || ['create-session', 'users', 'payments'].includes(route)
  }, "Manage", /*#__PURE__*/React.createElement("span", {
    style: {
      transform: manageOpen ? 'rotate(180deg)' : 'none',
      transition: 'transform .15s',
      display: 'inline-flex'
    }
  }, /*#__PURE__*/React.createElement(ChevDown, {
    size: 12
  }))), manageOpen && /*#__PURE__*/React.createElement(Dropdown, {
    align: "right"
  }, /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Plus, {
      color: "var(--pitch-600)",
      size: 16
    }),
    onClick: () => {
      setManageOpen(false);
      onNavigate('create-session');
    }
  }, "New Session"), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Calendar, {
      color: "var(--pitch-600)",
      size: 16
    }),
    onClick: () => {
      setManageOpen(false);
      onNavigate('home');
    }
  }, "Attendance"), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Wallet, {
      color: "var(--pitch-600)",
      size: 16
    }),
    onClick: () => {
      setManageOpen(false);
      onNavigate('payments');
    }
  }, "Payments"), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--stone-100)',
      margin: '4px 0'
    }
  }), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Icons.Users, {
      color: "var(--pitch-600)",
      size: 16
    }),
    onClick: () => {
      setManageOpen(false);
      onNavigate('users');
    }
  }, "Users"))), /*#__PURE__*/React.createElement(BellButton, {
    unread: unread,
    onClick: () => onNavigate('notifications'),
    active: route === 'notifications'
  }), /*#__PURE__*/React.createElement("div", {
    ref: userRef,
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      setUserOpen(v => !v);
      setManageOpen(false);
    },
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      height: 38,
      padding: '0 8px',
      borderRadius: 8,
      background: userOpen ? 'rgba(255,255,255,0.10)' : 'transparent',
      border: 'none',
      color: '#fff',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: user,
    size: 26,
    ring: true
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      maxWidth: 120,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, user.name), /*#__PURE__*/React.createElement("span", {
    style: {
      transform: userOpen ? 'rotate(180deg)' : 'none',
      transition: 'transform .15s',
      display: 'inline-flex'
    }
  }, /*#__PURE__*/React.createElement(ChevDown, {
    size: 12
  }))), userOpen && /*#__PURE__*/React.createElement(Dropdown, {
    align: "right"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 16px 10px',
      borderBottom: '1px solid var(--stone-100)',
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--stone-900)'
    }
  }, user.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--stone-400)',
      fontFamily: 'var(--font-mono)'
    }
  }, user.email)), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(User, {
      color: "var(--stone-400)",
      size: 16
    }),
    onClick: () => {
      setUserOpen(false);
      onNavigate('profile');
    }
  }, "My Profile"), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Cog, {
      color: "var(--stone-400)",
      size: 16
    }),
    onClick: () => {
      setUserOpen(false);
      onNavigate('profile');
    }
  }, "Settings"), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--stone-100)',
      margin: '4px 0'
    }
  }), /*#__PURE__*/React.createElement(DropdownItem, {
    icon: /*#__PURE__*/React.createElement(Logout, {
      color: "var(--red-600)",
      size: 16
    }),
    danger: true,
    onClick: () => {
      setUserOpen(false);
      onLogout && onLogout();
    }
  }, "Log Out"))))));
}
function BellButton({
  unread,
  onClick,
  active
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 38,
      height: 38,
      marginRight: 4,
      borderRadius: 8,
      background: active ? 'rgba(255,255,255,0.10)' : 'transparent',
      color: '#fff',
      border: 'none',
      cursor: 'pointer'
    },
    onMouseEnter: e => {
      if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
    },
    onMouseLeave: e => {
      if (!active) e.currentTarget.style.background = 'transparent';
    }
  }, /*#__PURE__*/React.createElement(Bell, {
    size: 17,
    sw: 1.75
  }), unread > 0 && /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 7,
      right: 7,
      minWidth: 14,
      height: 14,
      padding: '0 4px',
      borderRadius: 9999,
      background: 'var(--amber-500)',
      color: '#fff',
      fontSize: 9,
      fontWeight: 700,
      fontFamily: 'var(--font-mono)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 0 0 2px var(--pitch-900)'
    }
  }, unread));
}
function NavLink({
  active,
  onClick,
  icon,
  children
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      height: 38,
      padding: '0 12px',
      background: active ? 'rgba(255,255,255,0.10)' : 'transparent',
      color: '#fff',
      border: 'none',
      borderRadius: 8,
      cursor: 'pointer',
      fontSize: 13,
      fontWeight: 500,
      fontFamily: 'inherit',
      transition: 'background .15s',
      letterSpacing: '0.005em'
    },
    onMouseEnter: e => {
      if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
    },
    onMouseLeave: e => {
      if (!active) e.currentTarget.style.background = 'transparent';
    }
  }, icon, children);
}
function Dropdown({
  children,
  align = 'right'
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 48,
      [align]: 0,
      width: 208,
      background: '#fff',
      color: 'var(--stone-800)',
      borderRadius: 12,
      boxShadow: 'var(--shadow-xl)',
      border: '1px solid var(--stone-100)',
      padding: '6px 0',
      zIndex: 50
    }
  }, children);
}
function DropdownItem({
  icon,
  children,
  onClick,
  danger
}) {
  return /*#__PURE__*/React.createElement("a", {
    onClick: onClick,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '8px 14px',
      fontSize: 13,
      color: danger ? 'var(--red-600)' : 'var(--stone-700)',
      cursor: 'pointer',
      textDecoration: 'none'
    },
    onMouseEnter: e => e.currentTarget.style.background = danger ? 'var(--red-50)' : 'var(--stone-50)',
    onMouseLeave: e => e.currentTarget.style.background = 'transparent'
  }, icon, children);
}
window.Header = Header;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/Header.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/Icons.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* global React */
/* ────────────────────────────────────────────────────────────
   Inline SVG icons.
   24-px viewBox, 1.75 stroke, round caps + joins.
   Stroke colour inherits from `currentColor`.
   ──────────────────────────────────────────────────────────── */

const Icon = ({
  d,
  size = 18,
  sw = 1.75,
  fill = 'none',
  ...p
}) => /*#__PURE__*/React.createElement("svg", _extends({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: fill,
  stroke: "currentColor",
  strokeWidth: sw,
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, p), Array.isArray(d) ? d.map((x, i) => /*#__PURE__*/React.createElement("path", {
  key: i,
  d: x
})) : /*#__PURE__*/React.createElement("path", {
  d: d
}));

/* ── ICG shield crest · primary logo ──
   The club crest — crown, Ghent belfry, cricket bat, "ICG" + "INDIAN CRICKET
   GHENT CLUB" banner — in heritage navy + brushed silver. It's self-contained
   and reads on light surfaces and on the dark app header alike, so we render it
   directly on a transparent background (no white tile). `size` sets the rendered
   HEIGHT; width follows the crest's ~0.79 aspect ratio.
   Trimmed art: assets/logo-crest.png · full/padded: assets/logo-crest-full.png */
const Roundel = ({
  size = 32
}) => /*#__PURE__*/React.createElement("img", {
  src: "../../assets/logo-crest.png",
  alt: "Indian Cricket Ghent",
  height: size,
  style: {
    display: 'block',
    height: size,
    width: 'auto',
    objectFit: 'contain'
  }
});

/* ── Cricket role glyphs ── */
const Bat = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 3v5", "M10 5.5h4", "M9 8.5h6v11a1.5 1.5 0 01-1.5 1.5h-3A1.5 1.5 0 019 19.5v-11z"]
}));
const Ball = p => /*#__PURE__*/React.createElement("svg", _extends({
  width: p.size || 18,
  height: p.size || 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: p.sw || 1.75,
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, p), /*#__PURE__*/React.createElement("circle", {
  cx: "12",
  cy: "12",
  r: "8.5"
}), /*#__PURE__*/React.createElement("path", {
  d: "M5 14c3.5 2.5 10.5 2.5 14 0"
}), /*#__PURE__*/React.createElement("path", {
  d: "M8 14.6v1.4M11 15.4v1.4M14 15.4v1.4M16.8 14.6v1.4"
}));
const AllRounder = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M4 4l4 4", "M7 7l9 9", "M14 14l3 3", "M9.5 17.5a3 3 0 11-6 0 3 3 0 016 0z"]
}));
const Keeper = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M7 21V11a2 2 0 014 0v2", "M11 13v-1a2 2 0 014 0v3", "M15 15v-2a2 2 0 014 0v6a3 3 0 01-3 3H10a3 3 0 01-3-3"]
}));
const Trophy = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M7 4h10v4a5 5 0 01-10 0V4z", "M7 6H4v2a3 3 0 003 3", "M17 6h3v2a3 3 0 01-3 3", "M9 21h6", "M12 13v8"]
}));
const Stumps = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M6 7v14", "M12 7v14", "M18 7v14", "M5 6h6", "M13 6h6"]
}));

/* ── UI navigation & general ── */
const Home = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 10l9-7 9 7", "M5 10v10a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V10"]
}));
const Calendar = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 5h18v16H3z", "M3 9h18", "M8 3v4", "M16 3v4"]
}));
const Pin = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 21s-7-6.5-7-12a7 7 0 0114 0c0 5.5-7 12-7 12z", "M14.5 9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"]
}));
const Clock = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M21 12a9 9 0 11-18 0 9 9 0 0118 0z", "M12 7v5l3 2"]
}));
const Wallet = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 8a2 2 0 012-2h12a2 2 0 012 2v1h1a1 1 0 011 1v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8z", "M17 13.5a.5.5 0 110-1 .5.5 0 010 1z"]
}));
const Users = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M9 8.5a3.5 3.5 0 117 0 3.5 3.5 0 01-7 0z", "M4 20a8 8 0 0116 0", "M16 7a3 3 0 100 6", "M18 20a6 6 0 014-5.7"]
}));
const Cog = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 9.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z", "M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.6 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.6-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"]
}));
const Plus = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 5v14", "M5 12h14"]
}));
const Check = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M5 12l5 5 9-11"
}));
const Close = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M6 6l12 12", "M18 6L6 18"]
}));
const ChevDown = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  sw: 2,
  d: "M5 9l7 7 7-7"
}));
const ChevRt = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  sw: 2,
  d: "M9 5l7 7-7 7"
}));
const Pencil = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M4 20h4l10-10-4-4L4 16v4z", "M14 6l4 4"]
}));
const Logout = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3", "M10 17l-5-5 5-5", "M5 12h11"]
}));
const ArrowRt = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M5 12h14", "M13 5l7 7-7 7"]
}));
const Mail = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 6h18v12H3z", "M3 7l9 7 9-7"]
}));
const Lock = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M5 11h14v10H5z", "M8 11V7a4 4 0 018 0v4"]
}));
const UserIc = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M8 8a4 4 0 118 0 4 4 0 01-8 0z", "M4 21a8 8 0 0116 0"]
}));
const Trash = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M4 7h16", "M9 7V4h6v3", "M6 7l1 13a2 2 0 002 2h6a2 2 0 002-2l1-13", "M10 11v7", "M14 11v7"]
}));
const Bell = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M15 17H4l1.5-2v-5a6.5 6.5 0 1113 0v5l1.5 2h-3", "M10 20a2 2 0 004 0"]
}));
const Send = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M3 11l18-8-7 18-3-7-8-3z"
}));
const Chat = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M4 4h13a3 3 0 013 3v7a3 3 0 01-3 3H10l-5 4v-4a3 3 0 01-1-2V7a3 3 0 011-3z"
}));
const Phone = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M5 4h3l2 5-2.5 1.5a11 11 0 006 6L15 14l5 2v3a2 2 0 01-2 2A15 15 0 013 6a2 2 0 012-2z"
}));
const Share = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M6 10a2 2 0 11-4 0 2 2 0 014 0z", "M20 6a2 2 0 11-4 0 2 2 0 014 0z", "M20 18a2 2 0 11-4 0 2 2 0 014 0z", "M5.8 9l8.4-4", "M5.8 11l8.4 4"]
}));
const Copy = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M8 3h10a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V5a2 2 0 012-2z", "M16 17v2a2 2 0 01-2 2H4a2 2 0 01-2-2V9a2 2 0 012-2h2"]
}));
const Download = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 4v12", "M7 11l5 5 5-5", "M5 20h14"]
}));
const Search = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M16.5 16.5a6 6 0 10-8.49-8.49 6 6 0 008.49 8.49z", "M21 21l-4.5-4.5"]
}));
const Filter = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M4 5h16l-6 8v6l-4-2v-4z"
}));
const More = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M5 12.5a.5.5 0 11.001-1.001A.5.5 0 015 12.5z", "M12 12.5a.5.5 0 11.001-1.001A.5.5 0 0112 12.5z", "M19 12.5a.5.5 0 11.001-1.001A.5.5 0 0119 12.5z"],
  sw: 2.5
}));
const Info = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M21 12a9 9 0 11-18 0 9 9 0 0118 0z", "M12 8v5", "M12 16h.01"]
}));
const Warn = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 3l10 18H2L12 3z", "M12 10v4", "M12 17h.01"]
}));
const Refresh = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M21 12a8 8 0 11-3-6.2L21 4v5h-5"
}));
const Rupee = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M21 12a9 9 0 11-18 0 9 9 0 0118 0z", "M9 8h6", "M9 11h6", "M9 11c2.5 0 4 1 4 3 0 1.5-1.5 2.5-3 2.5L15 16"]
}));
const Star = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M12 3l2.6 5.4 5.9.8-4.3 4.2 1 5.9L12 16.5l-5.3 2.8 1-5.9L3.5 9.2l5.9-.8L12 3z"
}));
const Image = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 5h18v14H3z", "M9 11a2 2 0 100-4 2 2 0 000 4z", "M21 17l-5-5-7 7"]
}));
const Heart = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: "M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
}));
const Server = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M3 4h18v6H3z", "M3 14h18v6H3z", "M7 7h.01", "M7 17h.01"]
}));
const Database = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M12 8c4.418 0 8-1.343 8-3s-3.582-3-8-3-8 1.343-8 3 3.582 3 8 3z", "M4 5v6c0 1.657 3.582 3 8 3s8-1.343 8-3V5", "M4 11v6c0 1.657 3.582 3 8 3s8-1.343 8-3v-6"]
}));
const Camera = p => /*#__PURE__*/React.createElement(Icon, _extends({}, p, {
  d: ["M9 4l-1.5 2H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-2.5L15 4z", "M15.5 13a3.5 3.5 0 11-7 0 3.5 3.5 0 017 0z"]
}));
window.Icons = {
  Roundel,
  // sport
  Bat,
  Ball,
  AllRounder,
  Keeper,
  Trophy,
  Stumps,
  // ui
  Home,
  Calendar,
  Pin,
  Clock,
  Wallet,
  Users,
  Cog,
  Plus,
  Check,
  Close,
  ChevDown,
  ChevRt,
  Pencil,
  Logout,
  ArrowRt,
  Mail,
  Lock,
  User: UserIc,
  Trash,
  Bell,
  Send,
  Chat,
  Phone,
  Share,
  Copy,
  Download,
  Search,
  Filter,
  More,
  Info,
  Warn,
  Refresh,
  Rupee,
  Star,
  Image,
  Camera,
  Heart,
  Server,
  Database,
  // legacy alias
  CricketBall: Ball
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/Icons.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/LoginScreen.jsx
try { (() => {
/* global React, Button, Input, Icons */
const {
  Roundel,
  Mail,
  Lock,
  ArrowRt,
  Check
} = Icons;
function LoginScreen({
  onLogin,
  onSignUp
}) {
  const [username, setUsername] = React.useState('bhanu');
  const [password, setPassword] = React.useState('••••••••');
  const [error, setError] = React.useState('');
  const submit = e => {
    e.preventDefault();
    if (!username) {
      setError('Please enter your username');
      return;
    }
    onLogin({
      name: 'Bhanu Tej',
      username,
      email: 'bhanu@indcric.club',
      is_staff: true
    });
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      minHeight: '100vh',
      background: '#fff'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      width: '46%',
      maxWidth: 560,
      background: 'var(--pitch-950)',
      position: 'relative',
      overflow: 'hidden'
    },
    className: "login-hero"
  }, /*#__PURE__*/React.createElement(CricketGroundSVG, null), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      padding: '40px 48px',
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }
  }, /*#__PURE__*/React.createElement("a", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      width: 'fit-content'
    }
  }, /*#__PURE__*/React.createElement(Roundel, {
    size: 60
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      fontSize: 14,
      color: '#fff',
      letterSpacing: '-0.005em'
    }
  }, "ICG")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: '32px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      background: 'rgba(255,255,255,0.06)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 9999,
      padding: '5px 12px',
      marginBottom: 28,
      width: 'fit-content'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'var(--emerald-400, #34d399)',
      display: 'inline-block',
      animation: 'pulse 2s infinite'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 500,
      color: 'rgba(255,255,255,0.7)',
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.04em'
    }
  }, "CRICKET CLUB MANAGER")), /*#__PURE__*/React.createElement("h2", {
    style: {
      fontSize: 44,
      fontWeight: 700,
      color: '#fff',
      lineHeight: 1.05,
      letterSpacing: '-0.025em',
      margin: '0 0 18px'
    }
  }, "Your pitch.", /*#__PURE__*/React.createElement("br", null), "Your play.", /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      color: 'var(--pitch-400)'
    }
  }, "All in one place.")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      color: 'var(--pitch-300, #86efac)',
      lineHeight: 1.55,
      marginBottom: 32,
      maxWidth: 300
    }
  }, "Manage sessions, split costs, balance teams by skill, and track every match \u2014 built for the way your club really runs."), /*#__PURE__*/React.createElement("ul", {
    style: {
      listStyle: 'none',
      padding: 0,
      margin: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, ['Smart team balancing by skill ratings', 'Session payments & settlement', 'Attendance polls & match history', 'WhatsApp-shareable session cards'].map((t, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 11
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 18,
      height: 18,
      borderRadius: '50%',
      background: 'var(--pitch-700)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      color: '#fff'
    }
  }, /*#__PURE__*/React.createElement(Check, {
    size: 11,
    sw: 2.2
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: 'var(--pitch-200, #bbf7d0)',
      fontWeight: 500
    }
  }, t))))), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 11,
      color: 'var(--pitch-700)',
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.04em',
      margin: 0
    }
  }, "\xA9 2026 ICG \xB7 BUILT FOR THE CLUB"))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 40
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: '100%',
      maxWidth: 340
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      color: 'var(--stone-900)',
      margin: '0 0 6px',
      letterSpacing: '-0.015em'
    }
  }, "Welcome back"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "Sign in to continue to your club dashboard")), error && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 16,
      padding: '10px 12px',
      background: 'var(--red-50)',
      border: '1px solid #fecaca',
      borderRadius: 10,
      fontSize: 13,
      color: 'var(--red-700)'
    }
  }, error), /*#__PURE__*/React.createElement("form", {
    onSubmit: submit,
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(Input, {
    label: "Username or Email",
    icon: /*#__PURE__*/React.createElement(Mail, {
      size: 15,
      sw: 1.75
    }),
    value: username,
    onChange: e => setUsername(e.target.value),
    placeholder: "your_username",
    autoComplete: "username"
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)'
    }
  }, "Password"), /*#__PURE__*/React.createElement("a", {
    style: {
      fontSize: 12,
      fontWeight: 500,
      color: 'var(--pitch-700)',
      cursor: 'pointer'
    }
  }, "Forgot password?")), /*#__PURE__*/React.createElement(Input, {
    icon: /*#__PURE__*/React.createElement(Lock, {
      size: 15,
      sw: 1.75
    }),
    type: "password",
    value: password,
    onChange: e => setPassword(e.target.value),
    placeholder: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
  })), /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 13,
      color: 'var(--stone-600)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    defaultChecked: true,
    style: {
      width: 14,
      height: 14,
      accentColor: 'var(--pitch-600)'
    }
  }), "Remember me for 30 days"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "lg",
    type: "submit",
    style: {
      width: '100%',
      justifyContent: 'center',
      marginTop: 4
    }
  }, "Sign In ", /*#__PURE__*/React.createElement(ArrowRt, {
    size: 14,
    sw: 1.75
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 28,
      paddingTop: 20,
      borderTop: '1px solid var(--stone-100)',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "New to IndCric?", /*#__PURE__*/React.createElement("a", {
    onClick: onSignUp,
    style: {
      marginLeft: 6,
      fontWeight: 500,
      color: 'var(--pitch-700)',
      cursor: 'pointer'
    }
  }, "Create an account \u2192"))))));
}
function CricketGroundSVG() {
  return /*#__PURE__*/React.createElement("svg", {
    style: {
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none'
    },
    viewBox: "0 0 480 680",
    fill: "none",
    preserveAspectRatio: "xMidYMid slice"
  }, /*#__PURE__*/React.createElement("ellipse", {
    cx: "240",
    cy: "380",
    rx: "240",
    ry: "310",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.05"
  }), /*#__PURE__*/React.createElement("ellipse", {
    cx: "240",
    cy: "380",
    rx: "148",
    ry: "186",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.05"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "222",
    y: "240",
    width: "36",
    height: "280",
    stroke: "white",
    strokeWidth: "1.5",
    opacity: "0.08",
    rx: "2"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "210",
    y1: "268",
    x2: "270",
    y2: "268",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "210",
    y1: "492",
    x2: "270",
    y2: "492",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.12"
  }), [231, 240, 249].flatMap(x => [/*#__PURE__*/React.createElement("line", {
    key: x + 'a',
    x1: x,
    y1: "254",
    x2: x,
    y2: "268",
    stroke: "white",
    strokeWidth: "1.5",
    opacity: "0.18"
  }), /*#__PURE__*/React.createElement("line", {
    key: x + 'b',
    x1: x,
    y1: "492",
    x2: x,
    y2: "506",
    stroke: "white",
    strokeWidth: "1.5",
    opacity: "0.18"
  })]), /*#__PURE__*/React.createElement("circle", {
    cx: "420",
    cy: "80",
    r: "160",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.03"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "420",
    cy: "80",
    r: "100",
    stroke: "white",
    strokeWidth: "1",
    opacity: "0.03"
  }));
}
window.LoginScreen = LoginScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/LoginScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/MatchResultScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, Eyebrow, Avatar, PlayerChip, RoleBadge, StatColumn, Icons */
const {
  Trophy,
  Share,
  Star,
  Pin,
  Calendar: Cal,
  Clock,
  ChevRt,
  Bat,
  Ball,
  AllRounder,
  Keeper
} = Icons;

/* ────────── Match Result + Scorecard ──────────
   Cricket scorecard adapted for a club casual match. Both innings,
   batting + bowling cards, fall-of-wickets, MOTM, highlights. */
function MatchResultScreen({
  match,
  onBack
}) {
  const [innings, setInnings] = React.useState(0); // 0 = first innings, 1 = second
  const cur = match.innings[innings];
  const other = match.innings[1 - innings];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1024,
      margin: '0 auto',
      padding: '28px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: onBack,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: 'var(--stone-500)',
      cursor: 'pointer',
      width: 'fit-content',
      textDecoration: 'none'
    }
  }, "\u2190 Back"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '18px 22px',
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr',
      alignItems: 'center',
      columnGap: 16
    }
  }, /*#__PURE__*/React.createElement(TeamScore, {
    team: match.teamA,
    score: match.innings[0],
    winner: match.winner === 'A'
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 6,
      minWidth: 120
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "vs"), /*#__PURE__*/React.createElement(Badge, {
    tone: "amber"
  }, /*#__PURE__*/React.createElement(Trophy, {
    size: 11,
    sw: 1.75
  }), " ", match.resultLine)), /*#__PURE__*/React.createElement(TeamScore, {
    team: match.teamB,
    score: match.innings[1],
    winner: match.winner === 'B',
    alignRight: true
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 22px',
      borderTop: '1px solid var(--stone-100)',
      display: 'flex',
      flexWrap: 'wrap',
      gap: 14,
      fontSize: 12,
      color: 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Cal, {
    size: 13
  }), match.dateLabel), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Pin, {
    size: 13
  }), match.location), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Clock, {
    size: 13
  }), match.format), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      display: 'inline-flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Share, {
      size: 13,
      sw: 1.75
    })
  }, "Share")))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 18px',
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto auto',
      alignItems: 'center',
      columnGap: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 36,
      height: 36,
      borderRadius: 10,
      background: 'var(--amber-100)',
      color: 'var(--amber-800)'
    }
  }, /*#__PURE__*/React.createElement(Star, {
    size: 18,
    sw: 1.75
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      fontWeight: 500,
      color: 'var(--amber-800)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Player of the Match"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 15,
      fontWeight: 600,
      color: 'var(--stone-900)',
      marginTop: 2,
      letterSpacing: '-0.005em'
    }
  }, match.motm.name, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      fontWeight: 400,
      color: 'var(--stone-500)'
    }
  }, "@", match.motm.username)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)',
      marginTop: 4
    }
  }, match.motm.line)), /*#__PURE__*/React.createElement(RoleBadge, {
    role: match.motm.role
  }), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(ChevRt, {
      size: 13,
      sw: 1.75
    })
  }, "Profile"))), /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'inline-flex',
      gap: 4,
      alignSelf: 'flex-start',
      background: 'var(--stone-100)',
      padding: 3,
      borderRadius: 8
    }
  }, match.innings.map((inn, i) => /*#__PURE__*/React.createElement(Tab, {
    key: i,
    active: innings === i,
    onClick: () => setInnings(i)
  }, inn.battingTeam, " \xB7 ", inn.runs, "/", inn.wickets))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: `${cur.battingTeam} batting · ${cur.runs}/${cur.wickets} (${cur.overs} overs)`
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 0'
    }
  }, /*#__PURE__*/React.createElement(Row, {
    header: true
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: '1 1 0'
    }
  }, "Batter"), /*#__PURE__*/React.createElement(Mono, null, "R"), /*#__PURE__*/React.createElement(Mono, null, "B"), /*#__PURE__*/React.createElement(Mono, null, "4s"), /*#__PURE__*/React.createElement(Mono, null, "6s"), /*#__PURE__*/React.createElement(Mono, null, "SR")), cur.batting.map((b, i) => /*#__PURE__*/React.createElement(Row, {
    key: i,
    dim: !!b.out
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: '1 1 0',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-900)'
    }
  }, b.name), b.captain && /*#__PURE__*/React.createElement(CapPill, null), !b.out && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--emerald-700)',
      fontWeight: 600,
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.04em'
    }
  }, "NOT OUT")), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--stone-400)',
      fontFamily: 'var(--font-mono)'
    }
  }, b.out || '—')), /*#__PURE__*/React.createElement(Mono, {
    bold: true
  }, b.r), /*#__PURE__*/React.createElement(Mono, null, b.balls), /*#__PURE__*/React.createElement(Mono, null, b.fours), /*#__PURE__*/React.createElement(Mono, null, b.sixes), /*#__PURE__*/React.createElement(Mono, null, b.sr))), /*#__PURE__*/React.createElement(Row, {
    footer: true
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: '1 1 0',
      fontSize: 12,
      color: 'var(--stone-500)',
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.04em'
    }
  }, "Extras \xB7 ", cur.extras.total, " (", cur.extras.desc, ")"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      fontWeight: 600,
      color: 'var(--stone-900)',
      fontFeatureSettings: '"tnum" 1'
    }
  }, "Total ", cur.runs, "/", cur.wickets)))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: `${other.battingTeam} bowling`
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 0'
    }
  }, /*#__PURE__*/React.createElement(Row, {
    header: true
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: '1 1 0'
    }
  }, "Bowler"), /*#__PURE__*/React.createElement(Mono, null, "O"), /*#__PURE__*/React.createElement(Mono, null, "M"), /*#__PURE__*/React.createElement(Mono, null, "R"), /*#__PURE__*/React.createElement(Mono, null, "W"), /*#__PURE__*/React.createElement(Mono, null, "Econ")), cur.bowling.map((b, i) => /*#__PURE__*/React.createElement(Row, {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: '1 1 0',
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-900)'
    }
  }, b.name), b.w >= 3 && /*#__PURE__*/React.createElement(Badge, {
    tone: "purple"
  }, "\u2605 ", b.w, "-fer")), /*#__PURE__*/React.createElement(Mono, null, b.o), /*#__PURE__*/React.createElement(Mono, null, b.m), /*#__PURE__*/React.createElement(Mono, null, b.r), /*#__PURE__*/React.createElement(Mono, {
    bold: true
  }, b.w), /*#__PURE__*/React.createElement(Mono, null, b.econ))))), cur.fow && cur.fow.length > 0 && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: "Fall of wickets"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 18px',
      display: 'flex',
      flexWrap: 'wrap',
      gap: 8
    }
  }, cur.fow.map((f, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '5px 10px',
      borderRadius: 9999,
      background: 'var(--stone-50)',
      border: '1px solid var(--stone-100)',
      fontSize: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--stone-900)',
      fontFeatureSettings: '"tnum" 1'
    }
  }, f.score), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--stone-500)'
    }
  }, f.batter), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-400)'
    }
  }, "ov ", f.over))))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: "Highlights"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 14,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, match.highlights.map((h, i) => /*#__PURE__*/React.createElement(Highlight, {
    key: i,
    item: h
  })))));
}

/* ── parts ── */

function TeamScore({
  team,
  score,
  winner,
  alignRight
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      alignItems: alignRight ? 'flex-end' : 'flex-start'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: team.accent
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-900)',
      letterSpacing: '-0.005em'
    }
  }, team.name), winner && /*#__PURE__*/React.createElement(Badge, {
    tone: "amber"
  }, "WON")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 34,
      fontWeight: 600,
      color: 'var(--stone-900)',
      letterSpacing: '-0.025em',
      lineHeight: 1,
      fontFeatureSettings: '"tnum" 1'
    }
  }, score.runs, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--stone-400)'
    }
  }, "/", score.wickets)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      color: 'var(--stone-500)',
      letterSpacing: '0.04em'
    }
  }, "(", score.overs, " ov)")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-400)',
      letterSpacing: '0.04em'
    }
  }, "RR ", score.rr));
}
function SectionHeader({
  title
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 18px',
      borderBottom: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: 'var(--stone-500)',
      margin: 0
    }
  }, title));
}
function Row({
  header,
  footer,
  dim,
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: header ? '8px 18px 6px' : footer ? '10px 18px' : '10px 18px',
      borderBottom: header || footer ? '1px solid var(--stone-100)' : '1px solid var(--stone-50, #fafaf9)',
      background: footer ? 'var(--stone-50)' : 'transparent',
      color: dim ? 'var(--stone-600)' : 'var(--stone-800)',
      fontSize: header ? 10 : 13,
      fontFamily: header ? 'var(--font-mono)' : 'inherit',
      textTransform: header ? 'uppercase' : 'none',
      letterSpacing: header ? '0.08em' : '0.005em',
      fontWeight: header ? 500 : 400
    }
  }, children);
}
function Mono({
  children,
  bold
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      width: 40,
      textAlign: 'right',
      flexShrink: 0,
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      fontWeight: bold ? 600 : 400,
      color: bold ? 'var(--stone-900)' : 'var(--stone-600)',
      fontFeatureSettings: '"tnum" 1'
    }
  }, children);
}
function CapPill() {
  return /*#__PURE__*/React.createElement("span", {
    title: "Captain",
    style: {
      width: 14,
      height: 14,
      borderRadius: 9999,
      background: 'var(--amber-100)',
      color: 'var(--amber-800)',
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      fontWeight: 600,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, "C");
}
function Tab({
  active,
  children,
  onClick
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    role: "tab",
    "aria-selected": active,
    style: {
      padding: '5px 12px',
      borderRadius: 6,
      border: 'none',
      cursor: 'pointer',
      fontSize: 12,
      fontWeight: 500,
      fontFamily: 'inherit',
      lineHeight: 1,
      background: active ? '#fff' : 'transparent',
      color: active ? 'var(--stone-900)' : 'var(--stone-500)',
      boxShadow: active ? 'var(--shadow-sm)' : 'none'
    }
  }, children);
}
const HIGHLIGHT_CFG = {
  six: {
    bg: 'var(--purple-100)',
    fg: 'var(--purple-800)',
    label: 'SIX'
  },
  four: {
    bg: 'var(--sky-100)',
    fg: 'var(--sky-800)',
    label: '4'
  },
  wicket: {
    bg: 'var(--red-50)',
    fg: 'var(--red-800)',
    label: 'W'
  },
  fifty: {
    bg: 'var(--amber-100)',
    fg: 'var(--amber-800)',
    label: '50'
  },
  catch: {
    bg: 'var(--emerald-100)',
    fg: 'var(--emerald-800)',
    label: 'CATCH'
  },
  hat: {
    bg: 'var(--purple-100)',
    fg: 'var(--purple-800)',
    label: 'HAT-TRICK'
  }
};
function Highlight({
  item
}) {
  const cfg = HIGHLIGHT_CFG[item.kind] || HIGHLIGHT_CFG.four;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'auto auto 1fr auto',
      alignItems: 'center',
      columnGap: 12,
      padding: '8px 12px',
      border: '1px solid var(--stone-100)',
      borderRadius: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      minWidth: 48,
      height: 24,
      padding: '0 8px',
      borderRadius: 6,
      background: cfg.bg,
      color: cfg.fg,
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 600,
      letterSpacing: '0.06em'
    }
  }, cfg.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      color: 'var(--stone-400)',
      letterSpacing: '0.04em',
      width: 50
    }
  }, "Ov ", item.over), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: 'var(--stone-800)'
    }
  }, item.body), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-400)',
      letterSpacing: '0.04em'
    }
  }, item.byTeam));
}
window.MatchResultScreen = MatchResultScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/MatchResultScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/NotificationsScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, Eyebrow, Avatar, RoleBadge, Icons */
const {
  Bell,
  Wallet,
  Trophy,
  Check,
  Calendar,
  Users: U,
  Chat,
  Send
} = Icons;

/* ────────── Notifications / activity feed ──────────
   Single, scrollable timeline. Tabs filter by category. */
function NotificationsScreen({
  items,
  onBack
}) {
  const [tab, setTab] = React.useState('all');
  const [readSet, setReadSet] = React.useState(() => new Set(items.filter(i => i.read).map(i => i.id)));
  const filtered = items.filter(i => tab === 'all' || i.kind === tab);
  const markAll = () => setReadSet(new Set(items.map(i => i.id)));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 780,
      margin: '0 auto',
      padding: '28px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: onBack,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: 'var(--stone-500)',
      cursor: 'pointer',
      width: 'fit-content',
      textDecoration: 'none'
    }
  }, "\u2190 Back"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      gap: 12,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 22,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: 0,
      letterSpacing: '-0.02em'
    }
  }, "Activity"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: '4px 0 0'
    }
  }, "Everything that happened at the club, newest first")), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Check, {
      size: 13,
      sw: 1.75
    }),
    onClick: markAll
  }, "Mark all read")), /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'inline-flex',
      gap: 4,
      alignSelf: 'flex-start',
      background: 'var(--stone-100)',
      padding: 3,
      borderRadius: 8
    }
  }, [{
    id: 'all',
    label: 'All'
  }, {
    id: 'session',
    label: 'Sessions'
  }, {
    id: 'payment',
    label: 'Payments'
  }, {
    id: 'match',
    label: 'Match'
  }, {
    id: 'mention',
    label: 'Mentions'
  }].map(t => /*#__PURE__*/React.createElement(Tab, {
    key: t.id,
    active: tab === t.id,
    onClick: () => setTab(t.id)
  }, t.label))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 0'
    }
  }, filtered.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '30px 18px',
      textAlign: 'center',
      fontSize: 13,
      color: 'var(--stone-400)'
    }
  }, "Nothing here."), filtered.map((n, i) => /*#__PURE__*/React.createElement(Row, {
    key: n.id,
    item: n,
    read: readSet.has(n.id),
    last: i === filtered.length - 1
  })))));
}
function Tab({
  active,
  children,
  onClick
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    role: "tab",
    "aria-selected": active,
    style: {
      padding: '5px 12px',
      borderRadius: 6,
      border: 'none',
      cursor: 'pointer',
      fontSize: 12,
      fontWeight: 500,
      fontFamily: 'inherit',
      lineHeight: 1,
      background: active ? '#fff' : 'transparent',
      color: active ? 'var(--stone-900)' : 'var(--stone-500)',
      boxShadow: active ? 'var(--shadow-sm)' : 'none'
    }
  }, children);
}
function Row({
  item,
  read,
  last
}) {
  const cfg = ROW_CFG[item.kind] || ROW_CFG.session;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto',
      columnGap: 12,
      alignItems: 'flex-start',
      padding: '14px 18px',
      borderBottom: last ? 'none' : '1px solid var(--stone-100)',
      background: read ? '#fff' : 'var(--pitch-50)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 30,
      height: 30,
      borderRadius: 8,
      background: cfg.bg,
      color: cfg.fg,
      flexShrink: 0,
      marginTop: 2
    }
  }, /*#__PURE__*/React.createElement(cfg.Glyph, {
    size: 15,
    sw: 1.75
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--stone-800)',
      lineHeight: 1.45
    }
  }, item.body), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-400)',
      marginTop: 4,
      letterSpacing: '0.04em'
    }
  }, item.when, item.context ? ` · ${item.context}` : '')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      marginTop: 4
    }
  }, !read && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: '50%',
      background: 'var(--amber-500)'
    }
  }), item.action && /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm"
  }, item.action)));
}
const ROW_CFG = {
  session: {
    Glyph: Calendar,
    bg: 'var(--pitch-50)',
    fg: 'var(--pitch-700)'
  },
  payment: {
    Glyph: Wallet,
    bg: 'var(--amber-50)',
    fg: 'var(--amber-800)'
  },
  match: {
    Glyph: Trophy,
    bg: 'var(--amber-100)',
    fg: 'var(--amber-800)'
  },
  mention: {
    Glyph: Chat,
    bg: 'var(--sky-100)',
    fg: 'var(--sky-800)'
  },
  rsvp: {
    Glyph: Check,
    bg: 'var(--emerald-100)',
    fg: 'var(--emerald-800)'
  },
  team: {
    Glyph: U,
    bg: 'var(--purple-100)',
    fg: 'var(--purple-800)'
  },
  ping: {
    Glyph: Send,
    bg: 'var(--stone-100)',
    fg: 'var(--stone-700)'
  }
};
window.NotificationsScreen = NotificationsScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/NotificationsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/OnboardingScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, Input, RoleBadge, RatingBar, Avatar, Icons */
const {
  Roundel,
  Bat,
  Ball,
  AllRounder,
  Keeper,
  Check,
  ArrowRt
} = Icons;

/* ────────── Onboarding — first-time member ──────────
   3 steps: 1) profile basics 2) role & skill 3) say hi
   Sits in a modal-like card centred on the page (no full-bleed hero — fast). */
function OnboardingScreen({
  onDone,
  onSkip
}) {
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
    name,
    username,
    role,
    batting,
    bowling,
    fielding,
    whatsapp,
    email: `${username || 'me'}@indcric.club`,
    stats: {
      matches: 0,
      runs: 0,
      wickets: 0,
      catches: 0,
      stumpings: 0
    }
  });
  const back = () => setStep(Math.max(0, step - 1));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: '100vh',
      background: 'var(--stone-50)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 24px'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    style: {
      width: '100%',
      maxWidth: 520
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '22px 24px 16px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Roundel, {
    size: 32
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.08em',
      color: 'var(--stone-400)',
      textTransform: 'uppercase'
    }
  }, "Step ", step + 1, " of 3"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 15,
      fontWeight: 600,
      color: 'var(--stone-900)',
      marginTop: 2,
      letterSpacing: '-0.005em'
    }
  }, steps[step])), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 4
    }
  }, steps.map((_, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      width: i === step ? 18 : 8,
      height: 6,
      borderRadius: 3,
      background: i <= step ? 'var(--pitch-600)' : 'var(--stone-200)',
      transition: 'width .2s, background .2s'
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '20px 24px'
    }
  }, step === 0 && /*#__PURE__*/React.createElement(StepIdentity, {
    name: name,
    setName: setName,
    username: username,
    setUsername: setUsername
  }), step === 1 && /*#__PURE__*/React.createElement(StepRole, {
    role: role,
    setRole: setRole,
    batting: batting,
    setBatting: setBatting,
    bowling: bowling,
    setBowling: setBowling,
    fielding: fielding,
    setFielding: setFielding
  }), step === 2 && /*#__PURE__*/React.createElement(StepWrap, {
    name: name,
    role: role,
    whatsapp: whatsapp,
    setWhatsapp: setWhatsapp,
    batting: batting,
    bowling: bowling,
    fielding: fielding
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 24px 18px',
      borderTop: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    onClick: step === 0 ? onSkip : back
  }, step === 0 ? 'Skip' : '← Back'), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: next,
    icon: step === 2 ? /*#__PURE__*/React.createElement(Check, {
      size: 13,
      sw: 1.75
    }) : null
  }, step === 2 ? 'Enter the club' : 'Next', " ", step < 2 && /*#__PURE__*/React.createElement(ArrowRt, {
    size: 13,
    sw: 1.75
  })))));
}
function StepIdentity({
  name,
  setName,
  username,
  setUsername
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "Welcome to IndCric \u2014 let's set up your member profile. Takes about 30 seconds."), /*#__PURE__*/React.createElement(Input, {
    label: "Full name",
    placeholder: "Bhanu Tej",
    value: name,
    onChange: e => setName(e.target.value)
  }), /*#__PURE__*/React.createElement(Input, {
    label: "Username",
    placeholder: "bhanu",
    hint: "Lowercase, used everywhere in the club.",
    value: username,
    onChange: e => setUsername(e.target.value.toLowerCase())
  }));
}
function StepRole({
  role,
  setRole,
  batting,
  setBatting,
  bowling,
  setBowling,
  fielding,
  setFielding
}) {
  const ROLES = [{
    id: 'batsman',
    label: 'Batsman',
    Glyph: Bat,
    tone: {
      bg: 'var(--sky-100)',
      bd: '#bae6fd',
      fg: 'var(--sky-800)'
    }
  }, {
    id: 'bowler',
    label: 'Bowler',
    Glyph: Ball,
    tone: {
      bg: 'var(--red-50)',
      bd: 'var(--red-100)',
      fg: 'var(--red-800)'
    }
  }, {
    id: 'allrounder',
    label: 'Allrounder',
    Glyph: AllRounder,
    tone: {
      bg: 'var(--purple-100)',
      bd: '#e9d5ff',
      fg: 'var(--purple-800)'
    }
  }, {
    id: 'keeper',
    label: 'Keeper',
    Glyph: Keeper,
    tone: {
      bg: 'var(--stone-100)',
      bd: 'var(--stone-200)',
      fg: 'var(--stone-700)'
    }
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)',
      display: 'block',
      marginBottom: 8
    }
  }, "Pick your role"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: 8
    }
  }, ROLES.map(r => {
    const selected = role === r.id;
    return /*#__PURE__*/React.createElement("button", {
      key: r.id,
      onClick: () => setRole(r.id),
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 12px',
        background: selected ? r.tone.bg : '#fff',
        border: `1px solid ${selected ? r.tone.bd : 'var(--stone-200)'}`,
        color: selected ? r.tone.fg : 'var(--stone-700)',
        borderRadius: 10,
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: 13,
        fontWeight: 500,
        textAlign: 'left'
      }
    }, /*#__PURE__*/React.createElement(r.Glyph, {
      size: 16,
      sw: 1.75
    }), " ", r.label);
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)',
      display: 'block',
      marginBottom: 8
    }
  }, "Rate yourself"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(SkillRow, {
    label: "Batting",
    value: batting,
    onChange: setBatting
  }), /*#__PURE__*/React.createElement(SkillRow, {
    label: "Bowling",
    value: bowling,
    onChange: setBowling
  }), /*#__PURE__*/React.createElement(SkillRow, {
    label: "Fielding",
    value: fielding,
    onChange: setFielding
  })), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 11,
      color: 'var(--stone-400)',
      margin: '10px 0 0',
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.04em'
    }
  }, "Teammates can refine your ratings later \xB7 rolling avg over time")));
}
function SkillRow({
  label,
  value,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr auto auto',
      alignItems: 'center',
      columnGap: 14
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)'
    }
  }, label), /*#__PURE__*/React.createElement(RatingBar, {
    value: value,
    editable: true,
    onChange: onChange
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      color: 'var(--stone-500)',
      fontFeatureSettings: '"tnum" 1',
      minWidth: 28,
      textAlign: 'right'
    }
  }, value.toFixed(1)));
}
function StepWrap({
  name,
  role,
  whatsapp,
  setWhatsapp,
  batting,
  bowling,
  fielding
}) {
  const avg = ((batting + bowling + fielding) / 3).toFixed(2);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "Looking good. Here's your profile snapshot:"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '12px 14px',
      background: 'var(--stone-50)',
      borderRadius: 10,
      border: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: {
      name: name || 'New Member'
    },
    size: 42
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-900)',
      letterSpacing: '-0.005em'
    }
  }, name || 'New Member'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-500)',
      letterSpacing: '0.04em',
      marginTop: 2
    }
  }, "Avg skill ", avg, " \xB7 joining 14 active members")), /*#__PURE__*/React.createElement(RoleBadge, {
    role: role
  })), /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 10,
      padding: '12px 14px',
      border: '1px solid var(--stone-100)',
      borderRadius: 10,
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: whatsapp,
    onChange: e => setWhatsapp(e.target.checked),
    style: {
      marginTop: 2,
      accentColor: 'var(--pitch-600)'
    }
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-800)'
    }
  }, "Join the WhatsApp community"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)',
      marginTop: 2
    }
  }, "Get session announcements, polls, and line-ups in your phone \u2014 same channel the club already uses."))));
}
window.OnboardingScreen = OnboardingScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/OnboardingScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/PaymentsScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, Eyebrow, Avatar, StatColumn, Icons */
const {
  Wallet,
  Check,
  Rupee,
  Send,
  Share,
  Copy,
  ChevRt
} = Icons;
function PaymentsScreen({
  matches,
  allPlayers,
  onBack
}) {
  const [tab, setTab] = React.useState('match'); // 'match' | 'settle'
  const [selected, setSelected] = React.useState(matches[0]);
  const [paid, setPaid] = React.useState(new Set(selected.paid || []));

  // ── derive outstanding totals across all matches for the settlement view ──
  const balances = computeBalances(matches, allPlayers);
  const togglePaid = username => {
    const next = new Set(paid);
    next.has(username) ? next.delete(username) : next.add(username);
    setPaid(next);
  };

  // totals for header strip
  const totalOutstanding = balances.reduce((sum, b) => sum + Math.max(0, b.owes), 0);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1024,
      margin: '0 auto',
      padding: '28px 24px'
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: onBack,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: 'var(--stone-500)',
      cursor: 'pointer',
      width: 'fit-content',
      textDecoration: 'none',
      marginBottom: 14
    }
  }, "\u2190 Back"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 22,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: 0,
      letterSpacing: '-0.02em'
    }
  }, "Payments"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: '4px 0 0'
    }
  }, "Track session payments and settle balances across the club")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 14,
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 16px'
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: "\u25CF Outstanding",
    value: `€${totalOutstanding.toFixed(2)}`,
    dot: "var(--amber-500)"
  }))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 16px'
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: "\u25CF Matches \xB7 30d",
    value: String(matches.length),
    dot: "var(--pitch-500)"
  }))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 16px'
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: "\u25CF Settled",
    value: `${balances.filter(b => b.owes <= 0).length} / ${balances.length}`,
    dot: "var(--emerald-600)"
  })))), /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'inline-flex',
      gap: 4,
      marginBottom: 16,
      background: 'var(--stone-100)',
      padding: 3,
      borderRadius: 8
    }
  }, /*#__PURE__*/React.createElement(Tab, {
    active: tab === 'match',
    onClick: () => setTab('match')
  }, "By match"), /*#__PURE__*/React.createElement(Tab, {
    active: tab === 'settle',
    onClick: () => setTab('settle')
  }, "Who owes whom")), tab === 'match' ? /*#__PURE__*/React.createElement(MatchView, {
    matches: matches,
    selected: selected,
    setSelected: m => {
      setSelected(m);
      setPaid(new Set(m.paid));
    },
    paid: paid,
    togglePaid: togglePaid,
    allPlayers: allPlayers
  }) : /*#__PURE__*/React.createElement(SettleView, {
    balances: balances
  }));
}
function Tab({
  active,
  children,
  onClick
}) {
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    role: "tab",
    "aria-selected": active,
    style: {
      padding: '5px 12px',
      borderRadius: 6,
      border: 'none',
      cursor: 'pointer',
      fontSize: 12,
      fontWeight: 500,
      fontFamily: 'inherit',
      lineHeight: 1,
      background: active ? '#fff' : 'transparent',
      color: active ? 'var(--stone-900)' : 'var(--stone-500)',
      boxShadow: active ? 'var(--shadow-sm)' : 'none'
    }
  }, children);
}
function MatchView({
  matches,
  selected,
  setSelected,
  paid,
  togglePaid,
  allPlayers
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("section", {
    style: {
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement(Eyebrow, null, "Select a match"), /*#__PURE__*/React.createElement("div", {
    className: "grid-3"
  }, matches.map(m => {
    const isSel = m.id === selected.id;
    return /*#__PURE__*/React.createElement("a", {
      key: m.id,
      onClick: () => setSelected(m),
      style: {
        display: 'block',
        textDecoration: 'none',
        background: '#fff',
        border: '1px solid var(--stone-100)',
        borderRadius: 14,
        padding: 14,
        cursor: 'pointer',
        boxShadow: isSel ? '0 0 0 2px var(--pitch-500), var(--shadow-md)' : 'var(--shadow-sm)',
        transition: 'box-shadow .15s'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 36,
        height: 36,
        borderRadius: 10,
        background: 'var(--pitch-50)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--pitch-800)',
        lineHeight: 1
      }
    }, m.dateDay), /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 8,
        fontWeight: 500,
        color: 'var(--pitch-700)',
        letterSpacing: '0.06em'
      }
    }, m.dateMonth)), /*#__PURE__*/React.createElement("div", {
      style: {
        minWidth: 0,
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("p", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--stone-800)',
        margin: 0,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        letterSpacing: '-0.005em'
      }
    }, m.name), /*#__PURE__*/React.createElement("p", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--stone-400)',
        margin: '2px 0 0'
      }
    }, m.dateFull, " \xB7 \u20AC", m.perPlayer, "/p")), isSel && /*#__PURE__*/React.createElement("div", {
      style: {
        color: 'var(--pitch-600)'
      }
    }, /*#__PURE__*/React.createElement(Check, {
      size: 16
    }))));
  }))), /*#__PURE__*/React.createElement("section", null, /*#__PURE__*/React.createElement(Eyebrow, {
    accent: "var(--amber-500)"
  }, selected.name, " \u2014 payments"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 18px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      margin: 0
    }
  }, paid.size, " of ", allPlayers.length, " paid \xB7 \u20AC", ((allPlayers.length - paid.size) * selected.perPlayer).toFixed(2), " outstanding"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Wallet, {
      size: 12,
      sw: 1.75
    })
  }, "Save")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 12,
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, allPlayers.map(p => {
    const isPaid = paid.has(p.username);
    return /*#__PURE__*/React.createElement("label", {
      key: p.username,
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderRadius: 10,
        border: '1px solid var(--stone-100)',
        cursor: 'pointer',
        background: isPaid ? 'var(--pitch-50)' : '#fff',
        transition: 'all .15s'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement(Avatar, {
      user: p,
      size: 30
    }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
      style: {
        fontSize: 13,
        fontWeight: 500,
        color: 'var(--stone-800)',
        margin: 0
      }
    }, p.username), /*#__PURE__*/React.createElement("p", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--stone-400)',
        margin: '2px 0 0'
      }
    }, p.role, " \xB7 \u20AC", selected.perPlayer))), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10
      }
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: isPaid ? 'green' : 'amber'
    }, isPaid ? 'Paid' : 'Pending'), /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      checked: isPaid,
      onChange: () => togglePaid(p.username),
      style: {
        width: 14,
        height: 14,
        accentColor: 'var(--pitch-600)',
        cursor: 'pointer'
      }
    })));
  })))));
}
function SettleView({
  balances
}) {
  // build a simple settlement plan: who pays whom what
  const plan = makeSettlementPlan(balances);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("section", {
    style: {
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement(Eyebrow, {
    accent: "var(--amber-500)"
  }, "Member balances"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 12,
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, balances.map(b => {
    const owes = b.owes;
    const tone = owes > 0 ? 'amber' : owes < 0 ? 'green' : 'stone';
    const label = owes > 0 ? `Owes €${owes.toFixed(2)}` : owes < 0 ? `Receives €${(-owes).toFixed(2)}` : 'Settled';
    return /*#__PURE__*/React.createElement("div", {
      key: b.player.username,
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderRadius: 10,
        border: '1px solid var(--stone-100)',
        background: '#fff'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement(Avatar, {
      user: b.player,
      size: 30
    }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
      style: {
        fontSize: 13,
        fontWeight: 500,
        color: 'var(--stone-800)',
        margin: 0
      }
    }, b.player.username), /*#__PURE__*/React.createElement("p", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--stone-400)',
        margin: '2px 0 0'
      }
    }, "Paid \u20AC", b.paid.toFixed(2), " of \u20AC", b.due.toFixed(2), " \xB7 ", b.matches, " matches"))), /*#__PURE__*/React.createElement(Badge, {
      tone: tone
    }, label));
  })))), /*#__PURE__*/React.createElement("section", null, /*#__PURE__*/React.createElement(Eyebrow, null, "Suggested settlement"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 18px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, plan.length, " transfer", plan.length !== 1 ? 's' : '', " to clear all balances"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Share, {
      size: 13,
      sw: 1.75
    })
  }, "Share to WhatsApp")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 14,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, plan.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '20px 0',
      textAlign: 'center',
      fontSize: 13,
      color: 'var(--stone-400)'
    }
  }, "All settled \u2014 nothing to pay."), plan.map((t, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr auto auto',
      alignItems: 'center',
      columnGap: 10,
      padding: '10px 14px',
      border: '1px solid var(--stone-100)',
      borderRadius: 10
    }
  }, /*#__PURE__*/React.createElement(PersonCell, {
    player: t.from,
    role: "from"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement(ChevRt, {
    size: 14,
    sw: 2,
    color: "var(--stone-400)"
  })), /*#__PURE__*/React.createElement(PersonCell, {
    player: t.to,
    role: "to"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      fontWeight: 600,
      color: 'var(--stone-900)',
      fontFeatureSettings: '"tnum" 1'
    }
  }, "\u20AC", t.amount.toFixed(2)), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Send, {
      size: 11,
      sw: 1.75
    })
  }, "Ping")))))));
}
function PersonCell({
  player,
  role
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: player,
    size: 26
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-800)',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, player.username), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.06em'
    }
  }, role === 'from' ? 'PAYS' : 'RECEIVES')));
}

/* ────────── Settlement math ──────────
   For each player, sum up what they owe across matches minus what they've paid.
   Then greedily pair debtors with creditors. */
function computeBalances(matches, players) {
  return players.map(p => {
    let due = 0,
      paid = 0,
      matchCount = 0;
    matches.forEach(m => {
      due += m.perPlayer;
      matchCount += 1;
      if ((m.paid || []).includes(p.username)) paid += m.perPlayer;
    });
    return {
      player: p,
      due,
      paid,
      owes: due - paid,
      matches: matchCount
    };
  });
}
function makeSettlementPlan(balances) {
  // positive = owes, negative = should receive
  const debtors = balances.filter(b => b.owes > 0.01).map(b => ({
    ...b
  })).sort((a, b) => b.owes - a.owes);
  const credits = balances.filter(b => b.owes < -0.01).map(b => ({
    ...b,
    owes: -b.owes
  })).sort((a, b) => b.owes - a.owes);
  const plan = [];
  let i = 0,
    j = 0;
  while (i < debtors.length && j < credits.length) {
    const amount = Math.min(debtors[i].owes, credits[j].owes);
    plan.push({
      from: debtors[i].player,
      to: credits[j].player,
      amount
    });
    debtors[i].owes -= amount;
    credits[j].owes -= amount;
    if (debtors[i].owes < 0.01) i++;
    if (credits[j].owes < 0.01) j++;
  }
  return plan;
}
window.PaymentsScreen = PaymentsScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/PaymentsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/Primitives.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* global React, Icons */

/* ────────── Button (slim) ──────────
   13-px label, 500 weight, 8-px radius, tighter padding.
   Matches preview/buttons.html exactly. */
function Button({
  variant = 'primary',
  size = 'md',
  icon,
  children,
  style,
  ...p
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    fontFamily: 'inherit',
    fontWeight: 500,
    letterSpacing: '0.005em',
    borderRadius: 8,
    border: '1px solid transparent',
    cursor: 'pointer',
    transition: 'background .15s, transform .15s',
    userSelect: 'none',
    whiteSpace: 'nowrap',
    lineHeight: 1
  };
  const sizes = {
    sm: {
      padding: '5px 10px',
      fontSize: 12,
      borderRadius: 7
    },
    md: {
      padding: '7px 14px',
      fontSize: 13
    },
    lg: {
      padding: '9px 18px',
      fontSize: 13,
      borderRadius: 9
    },
    xl: {
      padding: '11px 20px',
      fontSize: 14,
      borderRadius: 10
    }
  };
  const variants = {
    primary: {
      background: 'var(--pitch-700)',
      color: '#fff'
    },
    secondary: {
      background: '#fff',
      color: 'var(--stone-700)',
      borderColor: 'var(--stone-300)'
    },
    amber: {
      background: 'var(--amber-500)',
      color: '#fff'
    },
    danger: {
      background: 'var(--red-600)',
      color: '#fff'
    },
    success: {
      background: 'var(--emerald-600)',
      color: '#fff'
    },
    ghost: {
      background: 'transparent',
      color: 'var(--stone-600)'
    }
  };
  const hover = {
    primary: 'var(--pitch-800)',
    amber: 'var(--amber-600)',
    danger: 'var(--red-700)',
    success: 'var(--emerald-700, #047857)',
    secondary: 'var(--stone-50)',
    ghost: 'var(--stone-100)'
  };
  return /*#__PURE__*/React.createElement("button", _extends({}, p, {
    style: {
      ...base,
      ...sizes[size],
      ...variants[variant],
      ...(style || {})
    },
    onMouseDown: e => e.currentTarget.style.transform = 'scale(0.96)',
    onMouseUp: e => e.currentTarget.style.transform = 'scale(1)',
    onMouseLeave: e => {
      e.currentTarget.style.transform = 'scale(1)';
      e.currentTarget.style.background = variants[variant].background;
    },
    onMouseEnter: e => e.currentTarget.style.background = hover[variant]
  }), icon, children);
}

/* ────────── Card ────────── */
function Card({
  children,
  accent,
  hoverable,
  style,
  ...p
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", _extends({}, p, {
    style: {
      background: '#fff',
      borderRadius: 16,
      border: '1px solid var(--stone-100)',
      boxShadow: hoverable && hover ? 'var(--shadow-md)' : 'var(--shadow-sm)',
      overflow: 'hidden',
      transition: 'box-shadow .15s',
      ...style
    },
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }), accent && /*#__PURE__*/React.createElement("div", {
    style: {
      height: 4,
      background: accent
    }
  }), children);
}

/* ────────── Badge ────────── */
const BADGE_TINTS = {
  green: {
    bg: 'var(--emerald-100)',
    fg: 'var(--emerald-800)'
  },
  pitch: {
    bg: 'var(--pitch-100)',
    fg: 'var(--pitch-800)'
  },
  red: {
    bg: 'var(--red-100)',
    fg: 'var(--red-700)'
  },
  amber: {
    bg: 'var(--amber-100)',
    fg: 'var(--amber-800)'
  },
  sky: {
    bg: 'var(--sky-100)',
    fg: 'var(--sky-800)'
  },
  purple: {
    bg: 'var(--purple-100)',
    fg: 'var(--purple-800)'
  },
  stone: {
    bg: 'var(--stone-100)',
    fg: 'var(--stone-700)'
  }
};
function Badge({
  tone = 'stone',
  children,
  style
}) {
  const t = BADGE_TINTS[tone];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      padding: '3px 10px',
      borderRadius: 9999,
      fontSize: 11,
      fontWeight: 600,
      background: t.bg,
      color: t.fg,
      lineHeight: 1.4,
      ...style
    }
  }, children);
}

/* ────────── Role badge — symbol + label ──────────
   The on-brand way to communicate role. Glyph carries the color. */
const {
  Bat,
  Ball,
  AllRounder,
  Keeper
} = window.Icons || {};
function RoleBadge({
  role = 'batsman',
  iconOnly = false,
  size
}) {
  const map = {
    batsman: {
      tone: 'sky',
      label: 'Batsman',
      Glyph: Bat
    },
    bowler: {
      tone: 'red',
      label: 'Bowler',
      Glyph: Ball
    },
    allrounder: {
      tone: 'purple',
      label: 'Allrounder',
      Glyph: AllRounder
    },
    keeper: {
      tone: 'stone',
      label: 'Keeper',
      Glyph: Keeper
    }
  };
  const {
    tone,
    label,
    Glyph
  } = map[role] || map.batsman;
  if (iconOnly) {
    return /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: size || 22,
        height: size || 22,
        borderRadius: 9999,
        background: BADGE_TINTS[tone].bg,
        color: BADGE_TINTS[tone].fg
      },
      title: label
    }, Glyph && /*#__PURE__*/React.createElement(Glyph, {
      size: (size || 22) - 9,
      sw: 1.75
    }));
  }
  return /*#__PURE__*/React.createElement(Badge, {
    tone: tone
  }, Glyph && /*#__PURE__*/React.createElement(Glyph, {
    size: 12,
    sw: 1.75
  }), label);
}

/* ────────── Eyebrow (section heading) ────────── */
function Eyebrow({
  children,
  accent = 'var(--pitch-600)'
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 3,
      height: 14,
      borderRadius: 9999,
      background: accent
    }
  }), /*#__PURE__*/React.createElement("h2", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      margin: 0
    }
  }, children));
}

/* ────────── Input ────────── */
function Input({
  icon,
  label,
  error,
  hint,
  ...p
}) {
  const [focus, setFocus] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", null, label && /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)',
      marginBottom: 6
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative'
    }
  }, icon && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 12,
      top: '50%',
      transform: 'translateY(-50%)',
      color: 'var(--stone-400)',
      pointerEvents: 'none',
      display: 'flex'
    }
  }, icon), /*#__PURE__*/React.createElement("input", _extends({}, p, {
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: '100%',
      boxSizing: 'border-box',
      padding: icon ? '9px 12px 9px 36px' : '9px 12px',
      fontSize: 13,
      fontFamily: 'inherit',
      color: 'var(--stone-900)',
      background: '#fff',
      border: `1px solid ${error ? '#fda4af' : 'var(--stone-200)'}`,
      borderRadius: 10,
      outline: 'none',
      boxShadow: focus ? `0 0 0 2px ${error ? '#fda4af' : 'var(--pitch-500)'}` : 'none',
      borderColor: focus ? 'transparent' : error ? '#fda4af' : 'var(--stone-200)',
      transition: 'box-shadow .15s'
    }
  }))), error && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--red-600)',
      marginTop: 6
    }
  }, error), hint && !error && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)',
      marginTop: 6
    }
  }, hint));
}

/* ────────── RatingBar — 5-segment dot row ──────────
   Filled in stone-800, empties stone-100, halves use a hard 50% gradient.
   Compact variant trims segment width. */
function RatingBar({
  value = 0,
  max = 5,
  compact = false,
  editable = false,
  onChange
}) {
  const segW = compact ? 10 : 16;
  const gap = compact ? 3 : 4;
  // value 0..5 → for each segment i (0..max-1): full if value >= i+1, half if value >= i+0.5
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      gap
    }
  }, Array.from({
    length: max
  }).map((_, i) => {
    const v = value;
    const full = v >= i + 1;
    const half = !full && v >= i + 0.5;
    const bg = full ? 'var(--stone-800)' : half ? 'linear-gradient(to right, var(--stone-800) 50%, var(--stone-100) 50%)' : 'var(--stone-100)';
    return /*#__PURE__*/React.createElement("span", {
      key: i,
      onClick: editable ? () => onChange && onChange(i + 1) : undefined,
      style: {
        width: segW,
        height: 4,
        borderRadius: 2,
        background: bg,
        cursor: editable ? 'pointer' : 'default'
      }
    });
  }));
}

/* ────────── VoteBar — full-width track (poll yes/no) ────────── */
function VoteBar({
  yes,
  total
}) {
  const pct = total > 0 ? yes / total * 100 : 0;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: 6,
      borderRadius: 9999,
      background: 'var(--stone-100)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      borderRadius: 9999,
      background: 'var(--emerald-500)',
      width: `${pct}%`,
      transition: 'width .5s'
    }
  }));
}

/* ────────── Alert ────────── */
const ALERT_TONES = {
  info: {
    bg: 'var(--sky-50, #f0f9ff)',
    fg: 'var(--sky-800)',
    bd: '#bae6fd',
    Glyph: window.Icons?.Info
  },
  success: {
    bg: 'var(--emerald-50, #ecfdf5)',
    fg: 'var(--emerald-800)',
    bd: '#a7f3d0',
    Glyph: window.Icons?.Check
  },
  warn: {
    bg: 'var(--amber-50, #fffbeb)',
    fg: 'var(--amber-800)',
    bd: '#fde68a',
    Glyph: window.Icons?.Warn
  },
  error: {
    bg: 'var(--red-50, #fef2f2)',
    fg: 'var(--red-800)',
    bd: '#fecaca',
    Glyph: window.Icons?.Warn
  }
};
function Alert({
  tone = 'info',
  title,
  children,
  action
}) {
  const t = ALERT_TONES[tone] || ALERT_TONES.info;
  return /*#__PURE__*/React.createElement("div", {
    role: "alert",
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 10,
      background: t.bg,
      color: t.fg,
      border: `1px solid ${t.bd}`,
      borderRadius: 10,
      padding: '10px 12px',
      fontSize: 13
    }
  }, t.Glyph && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      paddingTop: 1,
      color: t.fg
    }
  }, /*#__PURE__*/React.createElement(t.Glyph, {
    size: 16,
    sw: 1.75
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 600,
      marginBottom: children ? 2 : 0
    }
  }, title), children && /*#__PURE__*/React.createElement("div", {
    style: {
      color: t.fg,
      opacity: 0.9
    }
  }, children)), action);
}

/* ────────── Avatar (lifted from Header.jsx so other screens can reuse) ────────── */
function Avatar({
  user,
  size = 36,
  ring = false
}) {
  const initials = (user.name || user.username || '?').split(' ').map(s => s[0]).join('').slice(0, 2).toUpperCase();
  const colors = {
    B: 'var(--pitch-700)',
    A: 'var(--sky-500)',
    R: 'var(--purple-800)',
    K: 'var(--amber-600)',
    S: 'var(--emerald-600)'
  };
  const bg = user.avatarColor || colors[initials[0]] || 'var(--pitch-700)';
  return /*#__PURE__*/React.createElement("span", {
    style: {
      width: size,
      height: size,
      borderRadius: '50%',
      background: bg,
      color: '#fff',
      fontWeight: 600,
      fontSize: size * 0.4,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: ring ? '0 0 0 2px var(--amber-400)' : 'none',
      flexShrink: 0
    }
  }, initials);
}

/* ────────── PlayerChip ──────────
   8 px radius, hairline border, neutral stone avatar, role glyph inline. */
function PlayerChip({
  player,
  captain = false,
  tinted = true,
  onClick
}) {
  const roleToneMap = {
    batsman: {
      bg: 'var(--sky-100)',
      bd: '#bae6fd',
      fg: 'var(--sky-800)'
    },
    bowler: {
      bg: 'var(--red-50)',
      bd: 'var(--red-100)',
      fg: 'var(--red-800)'
    },
    allrounder: {
      bg: 'var(--purple-100)',
      bd: '#e9d5ff',
      fg: 'var(--purple-800)'
    },
    keeper: {
      bg: '#fff',
      bd: 'var(--stone-200)',
      fg: 'var(--stone-800)'
    }
  };
  const tone = tinted ? roleToneMap[player.role] || {
    bg: '#fff',
    bd: 'var(--stone-200)',
    fg: 'var(--stone-800)'
  } : {
    bg: '#fff',
    bd: 'var(--stone-200)',
    fg: 'var(--stone-800)'
  };
  const Glyph = {
    batsman: Icons.Bat,
    bowler: Icons.Ball,
    allrounder: Icons.AllRounder,
    keeper: Icons.Keeper
  }[player.role];
  return /*#__PURE__*/React.createElement("span", {
    onClick: onClick,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      background: tone.bg,
      color: tone.fg,
      border: `1px solid ${tone.bd}`,
      borderRadius: 8,
      padding: '3px 9px 3px 4px',
      fontSize: 13,
      fontWeight: 500,
      letterSpacing: '0.005em',
      lineHeight: 1,
      cursor: onClick ? 'pointer' : 'default'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: {
      username: player.username,
      avatarColor: 'transparent'
    },
    size: 20
  }), player.username, Glyph && /*#__PURE__*/React.createElement(Glyph, {
    size: 12,
    sw: 1.75
  }), captain && /*#__PURE__*/React.createElement("span", {
    title: "Captain",
    style: {
      marginLeft: 1,
      width: 14,
      height: 14,
      background: 'var(--amber-100)',
      color: 'var(--amber-800)',
      borderRadius: 9999,
      fontSize: 9,
      fontWeight: 600,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, "C"));
}

/* override avatar background in PlayerChip with neutral disc */
const PlayerChipAvatarStyle = `
  /* injected */
`;

/* ────────── StatColumn — typographic column from the DS preview ────────── */
function StatColumn({
  label,
  value,
  dot,
  first = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: first ? '4px 12px 4px 0' : '4px 12px',
      borderLeft: first ? 'none' : '1px solid var(--stone-100)',
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      fontWeight: 500,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, dot && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: 9999,
      background: dot
    }
  }), label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 24,
      fontWeight: 500,
      color: 'var(--stone-900)',
      lineHeight: 1,
      letterSpacing: '-0.015em',
      fontFeatureSettings: '"tnum" 1'
    }
  }, value));
}

/* ────────── StatTile — single-metric soft-tinted block ────────── */
function StatTile({
  label,
  value,
  delta,
  tone = 'stone'
}) {
  const map = {
    sky: {
      bg: 'var(--sky-100)',
      fg: 'var(--sky-800)'
    },
    red: {
      bg: 'var(--red-50)',
      fg: 'var(--red-800)'
    },
    emerald: {
      bg: 'var(--emerald-100)',
      fg: 'var(--emerald-800)'
    },
    amber: {
      bg: 'var(--amber-50)',
      fg: 'var(--amber-800)'
    },
    pitch: {
      bg: 'var(--pitch-50)',
      fg: 'var(--pitch-800)'
    },
    stone: {
      bg: 'var(--stone-50)',
      fg: 'var(--stone-600)'
    }
  };
  const t = map[tone] || map.stone;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      padding: '12px 14px',
      background: t.bg,
      borderRadius: 10,
      minWidth: 96
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: t.fg,
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 24,
      fontWeight: 500,
      color: 'var(--stone-900)',
      lineHeight: 1,
      letterSpacing: '-0.015em',
      fontFeatureSettings: '"tnum" 1'
    }
  }, value), delta && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      color: delta.startsWith('-') || delta.startsWith('−') ? 'var(--red-700)' : 'var(--pitch-800)'
    }
  }, delta)));
}
Object.assign(window, {
  Button,
  Card,
  Badge,
  RoleBadge,
  Eyebrow,
  Input,
  RatingBar,
  VoteBar,
  Alert,
  Avatar,
  PlayerChip,
  StatColumn,
  StatTile
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/Primitives.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/ProfileScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, RatingBar, Avatar, RoleBadge, StatColumn, Icons */
const {
  Pencil,
  Mail
} = Icons;
function ProfileScreen({
  user,
  onBack
}) {
  const [editing, setEditing] = React.useState(false);
  const [batting, setBatting] = React.useState(user.batting);
  const [bowling, setBowling] = React.useState(user.bowling);
  const [fielding, setFielding] = React.useState(user.fielding);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 720,
      margin: '0 auto',
      padding: '28px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: onBack,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: 'var(--stone-500)',
      cursor: 'pointer',
      width: 'fit-content',
      textDecoration: 'none'
    }
  }, "\u2190 Back"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 64,
      background: 'linear-gradient(90deg, var(--pitch-800), var(--pitch-600))'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 22px 22px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      marginTop: -30,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: user,
    size: 60,
    ring: true
  }), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Pencil, {
      size: 12,
      sw: 1.75
    }),
    onClick: () => setEditing(v => !v)
  }, editing ? 'Done' : 'Edit Profile')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 18,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: 0,
      letterSpacing: '-0.01em'
    }
  }, user.name), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12,
      color: 'var(--stone-400)',
      fontFamily: 'var(--font-mono)',
      margin: '2px 0 0'
    }
  }, "@", user.username)), /*#__PURE__*/React.createElement(RoleBadge, {
    role: user.role
  }), user.is_staff && /*#__PURE__*/React.createElement(Badge, {
    tone: "amber"
  }, "Staff")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)',
      margin: '10px 0 0',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Mail, {
    size: 13,
    sw: 1.75
  }), " ", user.email))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: "Skill Ratings"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 22px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement(RatingRow, {
    label: "Batting",
    value: batting,
    editing: editing,
    onChange: setBatting
  }), /*#__PURE__*/React.createElement(RatingRow, {
    label: "Bowling",
    value: bowling,
    editing: editing,
    onChange: setBowling
  }), /*#__PURE__*/React.createElement(RatingRow, {
    label: "Fielding",
    value: fielding,
    editing: editing,
    onChange: setFielding
  }))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: "Career Stats"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 22px 18px',
      display: 'grid',
      gridTemplateColumns: 'repeat(5, 1fr)'
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: "\u25CF Matches",
    value: user.stats.matches,
    dot: "var(--pitch-500)"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Runs",
    value: user.stats.runs,
    dot: "var(--sky-500)"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Wickets",
    value: user.stats.wickets,
    dot: "var(--red-500)"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Catches",
    value: user.stats.catches,
    dot: "#a855f7"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Stumps",
    value: user.stats.stumpings,
    dot: "var(--amber-500)"
  }))));
}
function SectionHeader({
  title
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 22px',
      borderBottom: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: 'var(--stone-500)',
      margin: 0
    }
  }, title));
}
function RatingRow({
  label,
  value,
  editing,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr auto auto',
      alignItems: 'center',
      columnGap: 14
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--stone-700)'
    }
  }, label), /*#__PURE__*/React.createElement(RatingBar, {
    value: value,
    editable: editing,
    onChange: onChange
  }), editing ? /*#__PURE__*/React.createElement("input", {
    type: "number",
    min: 0,
    max: 5,
    step: 0.5,
    value: value,
    onChange: e => onChange(Math.max(0, Math.min(5, parseFloat(e.target.value) || 0))),
    style: {
      width: 54,
      padding: '3px 8px',
      textAlign: 'right',
      border: '1px solid var(--stone-200)',
      borderRadius: 6,
      fontFamily: 'var(--font-mono)',
      fontSize: 11
    }
  }) : /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      color: 'var(--stone-500)',
      minWidth: 28,
      textAlign: 'right',
      fontFeatureSettings: '"tnum" 1'
    }
  }, value.toFixed(1)));
}
window.ProfileScreen = ProfileScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/ProfileScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/SessionCard.jsx
try { (() => {
/* global React, Card, Badge, VoteBar, Icons */
const {
  Calendar,
  Pin,
  Clock,
  Trash,
  ArrowRt,
  Lock
} = Icons;
function SessionCard({
  session,
  onClick,
  onDelete,
  isStaff,
  dimmed,
  locked,
  lockedHint
}) {
  const [hover, setHover] = React.useState(false);
  const past = !!dimmed;
  const accent = past ? 'var(--stone-200)' : 'var(--pitch-600)';
  return /*#__PURE__*/React.createElement(Card, {
    accent: accent,
    hoverable: true,
    style: {
      position: 'relative',
      cursor: 'pointer',
      opacity: past ? 0.92 : 1,
      transition: 'opacity .15s'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 18
    },
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    onClick: onClick
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      background: past ? 'var(--stone-100)' : 'var(--pitch-50)',
      color: past ? 'var(--stone-600)' : 'var(--pitch-800)',
      borderRadius: 8,
      padding: '4px 10px'
    }
  }, /*#__PURE__*/React.createElement(Calendar, {
    size: 12,
    sw: 1.75
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: '0.005em'
    }
  }, session.dateLabel)), isStaff && hover && /*#__PURE__*/React.createElement("button", {
    onClick: e => {
      e.stopPropagation();
      onDelete && onDelete(session);
    },
    style: {
      padding: 6,
      borderRadius: 8,
      border: 'none',
      background: 'transparent',
      color: 'var(--stone-400)',
      cursor: 'pointer',
      display: 'flex'
    },
    onMouseEnter: e => {
      e.currentTarget.style.background = 'var(--red-50)';
      e.currentTarget.style.color = 'var(--red-500)';
    },
    onMouseLeave: e => {
      e.currentTarget.style.background = 'transparent';
      e.currentTarget.style.color = 'var(--stone-400)';
    }
  }, /*#__PURE__*/React.createElement(Trash, {
    size: 14
  }))), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: 15,
      fontWeight: 600,
      color: past ? 'var(--stone-700)' : 'var(--stone-900)',
      margin: '0 0 6px',
      letterSpacing: '-0.005em',
      transition: 'color .15s'
    }
  }, session.name), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 3,
      fontSize: 12,
      color: past ? 'var(--stone-400)' : 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Pin, {
    size: 12
  }), " ", session.location), !past && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Clock, {
    size: 12
  }), " ", session.time, " \xB7 ", session.duration, "h")), !past && session.poll && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14,
      paddingTop: 12,
      borderTop: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: 11,
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Availability"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: "green"
  }, "\u25CF ", session.poll.yes, " Yes"), /*#__PURE__*/React.createElement(Badge, {
    tone: "red"
  }, session.poll.no, " No"), session.poll.closed && /*#__PURE__*/React.createElement(Badge, {
    tone: "stone"
  }, "Closed"))), /*#__PURE__*/React.createElement(VoteBar, {
    yes: session.poll.yes,
    total: session.poll.yes + session.poll.no
  })), past && session.winner && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 12,
      paddingTop: 10,
      borderTop: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 12,
      color: 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--amber-600)',
      fontWeight: 600
    }
  }, session.winner), /*#__PURE__*/React.createElement("span", null, "won")), /*#__PURE__*/React.createElement(ArrowRt, {
    size: 12,
    color: "var(--stone-400)"
  }))), locked && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      background: 'rgba(255,255,255,0.55)',
      backdropFilter: 'blur(2px)',
      WebkitBackdropFilter: 'blur(2px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      background: 'rgba(255,255,255,0.96)',
      border: '1px solid var(--stone-200)',
      borderRadius: 9999,
      padding: '5px 12px',
      fontSize: 12,
      fontWeight: 500,
      color: 'var(--stone-700)',
      boxShadow: 'var(--shadow-sm)'
    }
  }, /*#__PURE__*/React.createElement(Lock, {
    size: 12,
    sw: 1.75
  }), lockedHint || 'Sign in to view')));
}
window.SessionCard = SessionCard;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/SessionCard.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/SessionDetailScreen.jsx
try { (() => {
/* global React, Card, Badge, Button, Eyebrow, RatingBar, VoteBar, Avatar, PlayerChip, StatColumn, Icons */
const {
  Pin,
  Clock,
  Calendar: Cal,
  Check,
  Close,
  Share,
  Refresh,
  ChevRt: ChevRtIc
} = Icons;

/* ────────── Session Detail (now includes Team Balance / Draft) ──────────
   Visibility:
   • Member  — sees teams read-only
   • Staff   — can auto-balance, move players between teams + pool, share line-ups
*/
function SessionDetailScreen({
  session,
  players,
  currentUser,
  onBack
}) {
  const [vote, setVote] = React.useState(session.userVote || null);
  const isStaff = !!currentUser?.is_staff;

  // ── Pool / teams (in-page draft) ──────────────────────────────────────
  // Each player gets a derived "rating" so the skill-gap meter has something to compute.
  const withRatings = React.useMemo(() => players.map(p => ({
    ...p,
    rating: ((p.batting || 3) + (p.bowling || 3) + (p.fielding || 3)) / 3
  })), [players]);
  const [teamA, setTeamA] = React.useState(() => withRatings.slice(0, 5));
  const [teamB, setTeamB] = React.useState(() => withRatings.slice(5, 10));
  const [pool, setPool] = React.useState(() => withRatings.slice(10));
  const mean = arr => arr.length ? arr.reduce((s, p) => s + p.rating, 0) / arr.length : 0;
  const rA = mean(teamA),
    rB = mean(teamB);
  const gap = Math.abs(rA - rB);
  const yes = (session.poll?.yes || 0) + (vote === 'yes' && !session.userVote ? 1 : 0);
  const no = (session.poll?.no || 0) + (vote === 'no' && !session.userVote ? 1 : 0);
  const moveTo = (player, target) => {
    if (!isStaff) return;
    const remove = (arr, p) => arr.filter(x => x.username !== p.username);
    setTeamA(target === 'A' ? [...remove(teamA, player), player] : remove(teamA, player));
    setTeamB(target === 'B' ? [...remove(teamB, player), player] : remove(teamB, player));
    setPool(target === 'pool' ? [...remove(pool, player), player] : remove(pool, player));
  };
  const autoBalance = () => {
    if (!isStaff) return;
    const all = [...teamA, ...teamB, ...pool].sort((a, b) => b.rating - a.rating);
    const A = [],
      B = [];
    // snake-draft: A B B A A B B A …
    all.forEach((p, i) => {
      const round = Math.floor(i / 2);
      const aTurn = round % 2 === 0 ? i % 2 === 0 : i % 2 === 1;
      if (aTurn && A.length < 6) A.push(p);else if (B.length < 6) B.push(p);else (A.length <= B.length ? A : B).push(p);
    });
    setTeamA(A.slice(0, 6));
    setTeamB(B.slice(0, 6));
    setPool(all.filter(p => !A.slice(0, 6).includes(p) && !B.slice(0, 6).includes(p)));
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1024,
      margin: '0 auto',
      padding: '28px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: onBack,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: 'var(--stone-500)',
      cursor: 'pointer',
      width: 'fit-content',
      textDecoration: 'none'
    }
  }, "\u2190 Back to dashboard"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 60,
      background: 'linear-gradient(90deg, var(--pitch-800), var(--pitch-600))'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 22px 22px',
      marginTop: -22
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 54,
      height: 54,
      borderRadius: 14,
      background: '#fff',
      border: '1px solid var(--stone-100)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: 'var(--shadow-md)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 20,
      fontWeight: 600,
      color: 'var(--stone-900)',
      lineHeight: 1,
      letterSpacing: '-0.02em'
    }
  }, session.dateDay), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      fontWeight: 500,
      color: 'var(--stone-500)',
      letterSpacing: '0.06em',
      marginTop: 2
    }
  }, session.dateMonth)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: session.poll?.closed ? 'stone' : 'green'
  }, session.poll?.closed ? 'Poll closed' : '● Poll open'), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Share, {
      size: 13,
      sw: 1.75
    })
  }, "Share"))), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 20,
      fontWeight: 600,
      color: 'var(--stone-900)',
      margin: '0 0 6px',
      letterSpacing: '-0.015em'
    }
  }, session.name), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 14,
      fontSize: 12,
      color: 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Pin, {
    size: 13
  }), session.location), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Clock, {
    size: 13
  }), session.time, " \xB7 ", session.duration, "h"), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(Cal, {
    size: 13
  }), session.dateLabel)))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(SectionHeader, {
    title: "Cost split"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 22px',
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)'
    }
  }, /*#__PURE__*/React.createElement(StatColumn, {
    first: true,
    label: "\u25CF Hall fee",
    value: "\u20AC72",
    dot: "var(--stone-400)"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Players",
    value: players.length,
    dot: "var(--sky-500)"
  }), /*#__PURE__*/React.createElement(StatColumn, {
    label: "\u25CF Per player",
    value: `€${(72 / players.length).toFixed(2)}`,
    dot: "var(--pitch-500)"
  }))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 22px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "Availability poll"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: "green"
  }, "\u25CF ", yes, " Yes"), /*#__PURE__*/React.createElement(Badge, {
    tone: "red"
  }, no, " No"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 18
    }
  }, /*#__PURE__*/React.createElement(VoteBar, {
    yes: yes,
    total: yes + no
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: vote === 'yes' ? 'success' : 'secondary',
    onClick: () => setVote('yes'),
    style: {
      flex: 1,
      justifyContent: 'center',
      padding: '9px 14px'
    },
    icon: /*#__PURE__*/React.createElement(Check, {
      size: 14,
      sw: 1.75
    })
  }, "I'm in"), /*#__PURE__*/React.createElement(Button, {
    variant: vote === 'no' ? 'danger' : 'secondary',
    onClick: () => setVote('no'),
    style: {
      flex: 1,
      justifyContent: 'center',
      padding: '9px 14px'
    },
    icon: /*#__PURE__*/React.createElement(Close, {
      size: 14,
      sw: 1.75
    })
  }, "Can't make it")))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 22px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: 'var(--stone-500)',
      margin: 0
    }
  }, "Team balance \xB7 ", isStaff ? 'Draft' : 'Read-only'), isStaff && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Refresh, {
      size: 12,
      sw: 1.75
    }),
    onClick: autoBalance
  }, "Auto-balance"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(Share, {
      size: 12,
      sw: 1.75
    })
  }, "Share line-ups"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 22px',
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr',
      alignItems: 'center',
      columnGap: 18,
      borderBottom: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement(TeamMeter, {
    name: "Team A",
    tone: "pitch",
    rating: rA,
    count: teamA.length
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 5,
      minWidth: 110
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Skill gap"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 600,
      color: gap < 0.15 ? 'var(--emerald-700)' : 'var(--stone-900)',
      letterSpacing: '-0.01em',
      fontFeatureSettings: '"tnum" 1',
      lineHeight: 1
    }
  }, gap.toFixed(2)), /*#__PURE__*/React.createElement(Badge, {
    tone: gap < 0.15 ? 'green' : gap < 0.5 ? 'amber' : 'red'
  }, gap < 0.15 ? 'Balanced' : gap < 0.5 ? 'Close' : 'Uneven')), /*#__PURE__*/React.createElement(TeamMeter, {
    name: "Team B",
    tone: "amber",
    rating: rB,
    count: teamB.length
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 18px',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(TeamSlot, {
    name: "Team A",
    tone: "pitch",
    players: teamA,
    otherTeam: "B",
    editable: isStaff,
    onMoveTo: moveTo
  }), /*#__PURE__*/React.createElement(TeamSlot, {
    name: "Team B",
    tone: "amber",
    players: teamB,
    otherTeam: "A",
    editable: isStaff,
    onMoveTo: moveTo
  })), (isStaff || pool.length > 0) && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 18px 18px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginBottom: 8
    }
  }, "Available pool \xB7 ", pool.length), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 12px',
      border: '1px dashed var(--stone-200)',
      borderRadius: 10,
      background: 'var(--stone-50)',
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6,
      minHeight: 36
    }
  }, pool.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-400)',
      padding: '6px 4px'
    }
  }, "Everyone assigned."), pool.map(p => /*#__PURE__*/React.createElement(PoolChip, {
    key: p.username,
    player: p,
    editable: isStaff,
    onAddA: () => moveTo(p, 'A'),
    onAddB: () => moveTo(p, 'B')
  }))))));
}
function SectionHeader({
  title
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 22px',
      borderBottom: '1px solid var(--stone-100)'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: 'var(--stone-500)',
      margin: 0
    }
  }, title));
}
function TeamMeter({
  name,
  tone,
  rating,
  count
}) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: accent
    }
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-900)',
      letterSpacing: '-0.005em'
    }
  }, name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-500)',
      letterSpacing: '0.04em'
    }
  }, count, " players \xB7 avg ", rating.toFixed(2))));
}
function TeamSlot({
  name,
  tone,
  players,
  otherTeam,
  editable,
  onMoveTo
}) {
  const accent = tone === 'amber' ? 'var(--amber-500)' : 'var(--pitch-600)';
  const captain = players[0];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--stone-100)',
      borderRadius: 12,
      background: '#fff',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 14px',
      borderBottom: '1px solid var(--stone-100)',
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: accent
    }
  }), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: 'var(--stone-800)',
      margin: 0,
      letterSpacing: '-0.005em'
    }
  }, name), captain && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      color: 'var(--stone-400)',
      marginLeft: 'auto',
      letterSpacing: '0.04em'
    }
  }, "C \xB7 @", captain.username)), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 10,
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      minHeight: 180
    }
  }, players.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      fontSize: 12,
      color: 'var(--stone-400)',
      padding: '30px 0'
    }
  }, "No players yet"), players.map(p => /*#__PURE__*/React.createElement("div", {
    key: p.username,
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '7px 10px',
      border: '1px solid var(--stone-100)',
      borderRadius: 8,
      background: '#fff'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 9,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: p,
    size: 24
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 500,
      color: 'var(--stone-800)'
    }
  }, p.username), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      letterSpacing: '0.04em'
    }
  }, p.role, " \xB7 ", p.rating.toFixed(2)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(RatingBar, {
    value: p.rating,
    compact: true
  }), editable && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    onClick: () => onMoveTo(p, otherTeam),
    title: `Swap to Team ${otherTeam}`,
    style: {
      width: 20,
      height: 20,
      borderRadius: 5,
      border: '1px solid var(--stone-200)',
      background: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement(ChevRtIc, {
    size: 11,
    sw: 2
  })), /*#__PURE__*/React.createElement("button", {
    onClick: () => onMoveTo(p, 'pool'),
    title: "Back to pool",
    style: {
      width: 20,
      height: 20,
      borderRadius: 5,
      border: '1px solid var(--stone-200)',
      background: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: 'var(--stone-400)'
    }
  }, /*#__PURE__*/React.createElement(Close, {
    size: 11,
    sw: 2
  }))))))));
}
function PoolChip({
  player,
  editable,
  onAddA,
  onAddB
}) {
  const roleToneMap = {
    batsman: {
      bg: 'var(--sky-100)',
      bd: '#bae6fd',
      fg: 'var(--sky-800)'
    },
    bowler: {
      bg: 'var(--red-50)',
      bd: 'var(--red-100)',
      fg: 'var(--red-800)'
    },
    allrounder: {
      bg: 'var(--purple-100)',
      bd: '#e9d5ff',
      fg: 'var(--purple-800)'
    },
    keeper: {
      bg: '#fff',
      bd: 'var(--stone-200)',
      fg: 'var(--stone-800)'
    }
  };
  const t = roleToneMap[player.role] || roleToneMap.keeper;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: editable ? '3px 3px 3px 8px' : '3px 8px',
      background: t.bg,
      color: t.fg,
      border: `1px solid ${t.bd}`,
      borderRadius: 8,
      fontSize: 12,
      fontWeight: 500,
      letterSpacing: '0.005em'
    }
  }, /*#__PURE__*/React.createElement("span", null, player.username), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      opacity: 0.7
    }
  }, "\xB7 ", player.rating.toFixed(1)), editable && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      gap: 2,
      marginLeft: 4
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onAddA,
    title: "Send to Team A",
    style: poolBtn('var(--pitch-700)')
  }, "A"), /*#__PURE__*/React.createElement("button", {
    onClick: onAddB,
    title: "Send to Team B",
    style: poolBtn('var(--amber-600)')
  }, "B")));
}
function poolBtn(bg) {
  return {
    width: 18,
    height: 18,
    borderRadius: 5,
    border: 'none',
    background: bg,
    color: '#fff',
    fontSize: 10,
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
    lineHeight: 1
  };
}
window.SessionDetailScreen = SessionDetailScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/SessionDetailScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/SupportScreen.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
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

const {
  Heart,
  Server,
  Database,
  Trophy,
  Ball,
  ChevRt,
  ChevDown,
  ArrowRt,
  Copy,
  Check,
  Plus
} = Icons;

/* tinted "what your donation funds" tile */
const FUND_TINTS = {
  pitch: {
    bg: 'var(--pitch-50)',
    fg: 'var(--pitch-700)'
  },
  sky: {
    bg: 'var(--sky-100)',
    fg: 'var(--sky-800)'
  },
  amber: {
    bg: 'var(--amber-50)',
    fg: 'var(--amber-800)'
  },
  emerald: {
    bg: 'var(--emerald-100)',
    fg: 'var(--emerald-800)'
  },
  red: {
    bg: 'var(--red-50)',
    fg: 'var(--red-800)'
  },
  stone: {
    bg: 'var(--stone-50)',
    fg: 'var(--stone-600)'
  }
};
const FUND_ICON = {
  server: Server,
  db: Database,
  cup: Trophy,
  ball: Ball,
  heart: Heart
};
function FundItem({
  tint = 'stone',
  title,
  body,
  icon = 'heart'
}) {
  const t = FUND_TINTS[tint] || FUND_TINTS.stone;
  const Glyph = FUND_ICON[icon] || Heart;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12,
      background: t.bg,
      borderRadius: 12,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      color: t.fg,
      flexShrink: 0,
      paddingTop: 1
    }
  }, /*#__PURE__*/React.createElement(Glyph, {
    size: 20,
    sw: 1.75
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-800)',
      letterSpacing: '-0.005em'
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--stone-500)',
      lineHeight: 1.4,
      marginTop: 2
    }
  }, body)));
}

/* a single bank-detail row with a copy button */
function CopyRow({
  label,
  value,
  mono = false
}) {
  const [copied, setCopied] = React.useState(false);
  const copy = () => {
    try {
      navigator.clipboard.writeText(value);
    } catch (e) {}
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
      background: 'var(--stone-50)',
      borderRadius: 10,
      padding: '10px 14px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-800)',
      fontFamily: mono ? 'var(--font-mono)' : 'inherit',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      marginTop: 2
    }
  }, value)), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    style: {
      flexShrink: 0,
      minWidth: 62
    },
    onClick: copy
  }, copied ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Check, {
    size: 13
  }), "Copied") : 'Copy'));
}

/* How-to-donate block (club bank account) */
function HowToDonate({
  bank
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--stone-200)',
      borderRadius: 10,
      padding: 16,
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: 'var(--stone-800)',
      margin: 0
    }
  }, "How to donate"), /*#__PURE__*/React.createElement(Badge, {
    tone: "pitch"
  }, "SEPA transfer")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      color: 'var(--stone-600)',
      margin: 0,
      lineHeight: 1.5
    }
  }, "Every donation goes to the club's bank account below. Send any amount by bank transfer and it will automatically be added to the tally."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(CopyRow, {
    label: "Account holder",
    value: bank.holder
  }), /*#__PURE__*/React.createElement(CopyRow, {
    label: "IBAN",
    value: bank.iban,
    mono: true
  }), /*#__PURE__*/React.createElement(CopyRow, {
    label: "Reference",
    value: bank.reference
  })), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "md",
    style: {
      width: '100%'
    }
  }, /*#__PURE__*/React.createElement(ArrowRt, {
    size: 16
  }), " Or donate online"));
}

/* Overlapping faces — for collapsed campaign headers + the featured summary.
   Newest-first; we reverse the z-order so the latest face sits on top. */
function AvatarStack({
  donations,
  max = 5,
  size = 24
}) {
  const shown = donations.slice(0, max);
  const extra = donations.length - shown.length;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center'
    }
  }, shown.map((d, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      marginLeft: i === 0 ? 0 : -size * 0.32,
      borderRadius: '50%',
      boxShadow: '0 0 0 2px #fff',
      display: 'inline-flex',
      zIndex: shown.length - i,
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: {
      name: d.name
    },
    size: size
  }))), extra > 0 && /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: -size * 0.32,
      width: size,
      height: size,
      borderRadius: '50%',
      background: 'var(--stone-100)',
      color: 'var(--stone-600)',
      boxShadow: '0 0 0 2px #fff',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: Math.round(size * 0.34),
      fontWeight: 700,
      position: 'relative'
    }
  }, "+", extra));
}
const LATEST_TAG = {
  fontSize: 9,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  color: 'var(--amber-800)',
  background: 'var(--amber-100)',
  padding: '1px 6px',
  borderRadius: 9999
};
const AUTO_TAG = {
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  background: 'var(--stone-100)',
  color: 'var(--stone-500)',
  padding: '1px 6px',
  borderRadius: 4
};

/* ── Style 1 · Wall — celebratory horizontal rail of faces (default) ── */
function SupporterGrid({
  donations
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "supporter-rail",
    style: {
      display: 'flex',
      gap: 10,
      overflowX: 'auto',
      paddingBottom: 4,
      scrollSnapType: 'x proximity',
      WebkitOverflowScrolling: 'touch'
    }
  }, donations.map((d, i) => {
    const latest = i === 0;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        flex: '0 0 132px',
        scrollSnapAlign: 'start',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
        textAlign: 'center',
        padding: '14px 10px',
        borderRadius: 14,
        background: latest ? 'var(--amber-50)' : 'var(--stone-50)',
        border: `1px solid ${latest ? 'var(--amber-100)' : 'transparent'}`
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        borderRadius: '50%',
        boxShadow: latest ? '0 0 0 2px var(--amber-400)' : 'none'
      }
    }, /*#__PURE__*/React.createElement(Avatar, {
      user: {
        name: d.name
      },
      size: 42
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        width: '100%',
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--stone-800)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, d.name), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: 'var(--stone-400)',
        marginTop: 1
      }
    }, d.date)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--emerald-700, #047857)',
        fontFeatureSettings: '"tnum" 1'
      }
    }, "\u20AC", d.amount.toFixed(2)), latest ? /*#__PURE__*/React.createElement("span", {
      style: LATEST_TAG
    }, "Latest") : d.source === 'bank' ? /*#__PURE__*/React.createElement("span", {
      title: "Auto-imported from the linked bank account",
      style: {
        fontSize: 9,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--stone-400)'
      }
    }, "auto") : null);
  }));
}

/* ── Style 2 · Honor list — rows, latest gently lifted ── */
function SupporterList({
  donations
}) {
  return /*#__PURE__*/React.createElement("ul", {
    style: {
      listStyle: 'none',
      margin: 0,
      padding: 0
    }
  }, donations.map((d, i) => {
    const latest = i === 0;
    return /*#__PURE__*/React.createElement("li", {
      key: i,
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 12px',
        borderRadius: 12,
        background: latest ? 'var(--amber-50)' : 'transparent',
        borderTop: !latest && i > 0 ? '1px solid var(--stone-100)' : 'none'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        borderRadius: '50%',
        boxShadow: latest ? '0 0 0 2px var(--amber-400)' : 'none'
      }
    }, /*#__PURE__*/React.createElement(Avatar, {
      user: {
        name: d.name
      },
      size: 34
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        minWidth: 0,
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 14,
        fontWeight: 600,
        color: 'var(--stone-800)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, d.name), latest && /*#__PURE__*/React.createElement("span", {
      style: LATEST_TAG
    }, "Latest"), !latest && d.source === 'bank' && /*#__PURE__*/React.createElement("span", {
      title: "Auto-imported from the linked bank account",
      style: AUTO_TAG
    }, "auto")), d.note && /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        color: 'var(--stone-400)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, d.note)), /*#__PURE__*/React.createElement("div", {
      style: {
        textAlign: 'right',
        flexShrink: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--stone-900)',
        fontFeatureSettings: '"tnum" 1'
      }
    }, "\u20AC", d.amount.toFixed(2)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: 'var(--stone-400)'
      }
    }, d.date)));
  }));
}

/* ── Style 3 · Featured — latest backer spotlit with their note as a quote ── */
function SupporterFeatured({
  donations
}) {
  const [top, ...rest] = donations;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 14,
      alignItems: 'flex-start',
      padding: 16,
      borderRadius: 14,
      background: 'var(--amber-50)',
      border: '1px solid var(--amber-100)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      borderRadius: '50%',
      flexShrink: 0,
      boxShadow: '0 0 0 3px var(--amber-400)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    user: {
      name: top.name
    },
    size: 52
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0,
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--amber-800)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Latest supporter"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 8,
      flexWrap: 'wrap',
      marginTop: 3
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 16,
      fontWeight: 700,
      color: 'var(--stone-900)'
    }
  }, top.name), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 15,
      fontWeight: 700,
      color: 'var(--emerald-700, #047857)',
      fontFeatureSettings: '"tnum" 1'
    }
  }, "\u20AC", top.amount.toFixed(2))), top.note ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-600)',
      fontStyle: 'italic',
      margin: '6px 0 0',
      lineHeight: 1.5
    }
  }, "\u201C", top.note, "\u201D") : /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: '6px 0 0'
    }
  }, "Thanks for backing the club, ", top.name.split(' ')[0], "."))), rest.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      marginTop: 14,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(AvatarStack, {
    donations: rest,
    max: 7,
    size: 30
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)'
    }
  }, "joined by ", rest.length, " other", rest.length === 1 ? '' : 's')));
}

/* Always-visible supporter shoutout — warm thank-you line + chosen layout */
function Supporters({
  donations,
  count,
  justLogged,
  style = 'wall'
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--stone-100)',
      paddingTop: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: donations.length ? 4 : 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      color: 'var(--amber-500)'
    }
  }, /*#__PURE__*/React.createElement(Heart, {
    size: 15
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: 'var(--stone-800)'
    }
  }, "Supporters"), /*#__PURE__*/React.createElement(Badge, {
    tone: "green"
  }, count)), donations.length > 0 && /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: 'var(--stone-500)',
      margin: '0 0 14px',
      lineHeight: 1.5
    }
  }, "Thank you to the ", count, " ", count === 1 ? 'player' : 'players and friends', " backing this \u2014 every euro keeps the club on the pitch."), justLogged && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement(Alert, {
    tone: "success"
  }, "Logged \u20AC", justLogged.amount.toFixed(2), " from ", justLogged.name, ". \uD83D\uDE4F")), !donations.length ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      color: 'var(--stone-400)',
      textAlign: 'center',
      padding: '12px 0',
      margin: 0
    }
  }, "Be the first to support this. \uD83C\uDFCF") : style === 'list' ? /*#__PURE__*/React.createElement(SupporterList, {
    donations: donations
  }) : style === 'featured' ? /*#__PURE__*/React.createElement(SupporterFeatured, {
    donations: donations
  }) : /*#__PURE__*/React.createElement(SupporterGrid, {
    donations: donations
  }));
}

/* Log-donation form (staff log for anyone; members log their own) */
function LogDonation({
  user,
  onLog
}) {
  const [open, setOpen] = React.useState(false);
  const [amount, setAmount] = React.useState('');
  const [name, setName] = React.useState('');
  const [note, setNote] = React.useState('');
  const [anon, setAnon] = React.useState(false);
  const isStaff = user.is_staff;
  const submit = e => {
    e.preventDefault();
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return;
    const display = anon ? 'Anonymous' : isStaff ? name || 'Club donor' : user.name;
    onLog({
      name: display,
      amount: amt,
      note,
      date: 'today',
      source: 'manual'
    });
    setAmount('');
    setName('');
    setNote('');
    setAnon(false);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--stone-100)',
      paddingTop: 16
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(o => !o),
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: 'transparent',
      border: 'none',
      cursor: 'pointer',
      padding: 0,
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: 'var(--stone-800)'
    }
  }, isStaff ? 'Log a donation' : 'Add your donation'), /*#__PURE__*/React.createElement(Badge, {
    tone: isStaff ? 'stone' : 'green'
  }, isStaff ? 'Staff' : 'You')), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      color: 'var(--stone-400)',
      transform: open ? 'rotate(180deg)' : 'none',
      transition: 'transform .15s'
    }
  }, /*#__PURE__*/React.createElement(ChevDown, {
    size: 16
  }))), open && /*#__PURE__*/React.createElement("form", {
    onSubmit: submit,
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      marginTop: 12
    }
  }, isStaff && /*#__PURE__*/React.createElement(Input, {
    label: "\u2026or external donor name",
    placeholder: "e.g. Local sponsor",
    value: name,
    onChange: e => setName(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Input, {
    label: "Amount (\u20AC)",
    placeholder: "25.00",
    inputMode: "decimal",
    value: amount,
    onChange: e => setAmount(e.target.value)
  }), /*#__PURE__*/React.createElement(Input, {
    label: "Date",
    placeholder: "2026-06-15"
  })), /*#__PURE__*/React.createElement(Input, {
    label: "Note",
    placeholder: "Optional",
    value: note,
    onChange: e => setNote(e.target.value)
  }), /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      cursor: 'pointer',
      padding: '2px 0'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: anon,
    onChange: e => setAnon(e.target.checked),
    style: {
      width: 16,
      height: 16,
      accentColor: 'var(--pitch-700)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      color: 'var(--stone-700)'
    }
  }, "Show as \u201CAnonymous\u201D on the wall")), !isStaff && /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12,
      color: 'var(--stone-400)',
      margin: 0
    }
  }, "Recorded under ", user.name, " \u2014 tick anonymous to hide your name on the wall."), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "md",
    style: {
      width: '100%'
    },
    type: "submit"
  }, isStaff ? 'Log donation' : 'Add my donation')));
}

/* One fundraiser as a collapsible card */
function CampaignCard({
  campaign,
  bank,
  user,
  closed = false,
  onLog,
  supporterStyle = 'wall'
}) {
  const [open, setOpen] = React.useState(!closed);
  const [justLogged, setJustLogged] = React.useState(null);
  const accent = closed ? 'var(--stone-200)' : 'var(--pitch-600)';
  const handleLog = d => {
    setJustLogged(d);
    setOpen(true);
    onLog && onLog(campaign.id, d);
  };
  return /*#__PURE__*/React.createElement(Card, {
    accent: accent,
    style: {
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(o => !o),
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
      background: 'transparent',
      border: 'none',
      cursor: 'pointer',
      padding: '14px 18px',
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      color: 'var(--stone-400)',
      flexShrink: 0,
      transform: open ? 'rotate(90deg)' : 'none',
      transition: 'transform .15s'
    }
  }, /*#__PURE__*/React.createElement(ChevRt, {
    size: 16
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 7,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      minWidth: 0,
      color: closed ? 'var(--stone-500)' : 'var(--stone-800)',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, campaign.title), /*#__PURE__*/React.createElement(Badge, {
    tone: closed ? 'stone' : 'green',
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: closed ? 'var(--stone-400)' : 'var(--emerald-500)'
    }
  }), closed ? 'Closed' : 'Active')), campaign.donations && campaign.donations.length > 0 && /*#__PURE__*/React.createElement(AvatarStack, {
    donations: campaign.donations,
    max: 5,
    size: 22
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      fontFeatureSettings: '"tnum" 1',
      color: closed ? 'var(--stone-600)' : 'var(--stone-900)'
    }
  }, "\u20AC", campaign.raised.toFixed(2), campaign.goal && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--stone-400)',
      fontWeight: 400
    }
  }, " / \u20AC", campaign.goal.toFixed(2))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-400)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginTop: 2
    }
  }, campaign.supporterCount, " supporter", campaign.supporterCount === 1 ? '' : 's'))), open && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '4px 18px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: 20,
      borderTop: '1px solid var(--stone-100)'
    }
  }, campaign.goal && /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      gap: 12,
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Raised so far"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 30,
      fontWeight: 700,
      color: 'var(--stone-900)',
      lineHeight: 1,
      fontFeatureSettings: '"tnum" 1',
      marginTop: 4
    }
  }, "\u20AC", campaign.raised.toFixed(2))), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      color: 'var(--stone-500)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em'
    }
  }, "Goal"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: 'var(--stone-500)',
      fontFeatureSettings: '"tnum" 1',
      marginTop: 4
    }
  }, "\u20AC", campaign.goal.toFixed(2)))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 10,
      borderRadius: 9999,
      background: 'var(--stone-100)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      borderRadius: 9999,
      background: 'var(--emerald-500)',
      width: `${campaign.progressPct}%`,
      transition: 'width .5s'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginTop: 8,
      fontSize: 12,
      color: 'var(--stone-500)'
    }
  }, /*#__PURE__*/React.createElement("span", null, campaign.supporterCount, " supporter", campaign.supporterCount === 1 ? '' : 's'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      color: 'var(--emerald-700, #047857)'
    }
  }, campaign.progressPct, "%"))), !campaign.isDefault && campaign.blurb && /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      color: 'var(--stone-600)',
      lineHeight: 1.5,
      margin: campaign.goal ? 0 : '12px 0 0'
    }
  }, campaign.blurb), !campaign.isDefault && campaign.fundItems && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, minmax(0,1fr))',
      gap: 12
    }
  }, campaign.fundItems.map((f, i) => /*#__PURE__*/React.createElement(FundItem, _extends({
    key: i
  }, f)))), /*#__PURE__*/React.createElement(Supporters, {
    donations: campaign.donations,
    count: campaign.supporterCount,
    justLogged: justLogged,
    style: supporterStyle
  }), /*#__PURE__*/React.createElement(HowToDonate, {
    bank: bank
  }), !closed && user && /*#__PURE__*/React.createElement(LogDonation, {
    user: user,
    onLog: handleLog
  })));
}
function SupportScreen({
  user,
  general,
  activeCampaigns = [],
  closedCampaigns = [],
  bank,
  onLog,
  supporterStyle = 'wall'
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 768,
      margin: '0 auto',
      padding: '28px 24px 64px'
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Eyebrow, {
    accent: "var(--amber-500)"
  }, "Support the club"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 24,
      fontWeight: 700,
      color: 'var(--stone-900)',
      margin: '0',
      letterSpacing: '-0.02em',
      lineHeight: 1.2
    }
  }, "Back Indian Cricket Ghent"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14,
      color: 'var(--stone-600)',
      margin: '8px 0 0',
      lineHeight: 1.6,
      maxWidth: 560
    }
  }, "ICG runs on the goodwill of its players \u2014 every euro keeps the nets up, the balls fresh, and the hall booked through the winter block.")), general && general.fundItems && /*#__PURE__*/React.createElement("section", {
    style: {
      margin: '24px 0 32px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, minmax(0,1fr))',
      gap: 12
    }
  }, general.fundItems.map((f, i) => /*#__PURE__*/React.createElement(FundItem, _extends({
    key: i
  }, f))))), user && user.is_staff && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'flex-end',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm"
  }, /*#__PURE__*/React.createElement(Plus, {
    size: 14
  }), "Target fundraiser")), activeCampaigns.map(c => /*#__PURE__*/React.createElement(CampaignCard, {
    key: c.id,
    campaign: c,
    bank: bank,
    user: user,
    onLog: onLog,
    supporterStyle: supporterStyle
  })), general && /*#__PURE__*/React.createElement(CampaignCard, {
    campaign: general,
    bank: bank,
    user: user,
    onLog: onLog,
    supporterStyle: supporterStyle
  }), closedCampaigns.length > 0 && /*#__PURE__*/React.createElement("section", {
    style: {
      marginTop: 32
    }
  }, /*#__PURE__*/React.createElement(Eyebrow, null, "Previous fundraisers"), closedCampaigns.map(c => /*#__PURE__*/React.createElement(CampaignCard, {
    key: c.id,
    campaign: c,
    bank: bank,
    user: user,
    closed: true,
    supporterStyle: supporterStyle
  }))));
}
window.SupportScreen = SupportScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/SupportScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/indcric_web/tweaks-panel.jsx
try { (() => {
// tweaks-panel.jsx
// Reusable Tweaks shell + form-control helpers.
//
// Owns the host protocol (listens for __activate_edit_mode / __deactivate_edit_mode,
// posts __edit_mode_available / __edit_mode_set_keys / __edit_mode_dismissed) so
// individual prototypes don't re-roll it. Ships a consistent set of controls so you
// don't hand-draw <input type="range">, segmented radios, steppers, etc.
//
// Usage (in an HTML file that loads React + Babel):
//
//   const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
//     "primaryColor": "#D97757",
//     "palette": ["#D97757", "#29261b", "#f6f4ef"],
//     "fontSize": 16,
//     "density": "regular",
//     "dark": false
//   }/*EDITMODE-END*/;
//
//   function App() {
//     const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
//     return (
//       <div style={{ fontSize: t.fontSize, color: t.primaryColor }}>
//         Hello
//         <TweaksPanel>
//           <TweakSection label="Typography" />
//           <TweakSlider label="Font size" value={t.fontSize} min={10} max={32} unit="px"
//                        onChange={(v) => setTweak('fontSize', v)} />
//           <TweakRadio  label="Density" value={t.density}
//                        options={['compact', 'regular', 'comfy']}
//                        onChange={(v) => setTweak('density', v)} />
//           <TweakSection label="Theme" />
//           <TweakColor  label="Primary" value={t.primaryColor}
//                        options={['#D97757', '#2A6FDB', '#1F8A5B', '#7A5AE0']}
//                        onChange={(v) => setTweak('primaryColor', v)} />
//           <TweakColor  label="Palette" value={t.palette}
//                        options={[['#D97757', '#29261b', '#f6f4ef'],
//                                  ['#475569', '#0f172a', '#f1f5f9']]}
//                        onChange={(v) => setTweak('palette', v)} />
//           <TweakToggle label="Dark mode" value={t.dark}
//                        onChange={(v) => setTweak('dark', v)} />
//         </TweaksPanel>
//       </div>
//     );
//   }
//
// ─────────────────────────────────────────────────────────────────────────────

const __TWEAKS_STYLE = `
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom right;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:default;padding:4px 6px;line-height:1.2;
    overflow-wrap:anywhere}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;box-sizing:border-box;min-width:0;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}

  .twk-chips{display:flex;gap:6px}
  .twk-chip{position:relative;appearance:none;flex:1;min-width:0;height:46px;
    padding:0;border:0;border-radius:6px;overflow:hidden;cursor:default;
    box-shadow:0 0 0 .5px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.06);
    transition:transform .12s cubic-bezier(.3,.7,.4,1),box-shadow .12s}
  .twk-chip:hover{transform:translateY(-1px);
    box-shadow:0 0 0 .5px rgba(0,0,0,.18),0 4px 10px rgba(0,0,0,.12)}
  .twk-chip[data-on="1"]{box-shadow:0 0 0 1.5px rgba(0,0,0,.85),
    0 2px 6px rgba(0,0,0,.15)}
  .twk-chip>span{position:absolute;top:0;bottom:0;right:0;width:34%;
    display:flex;flex-direction:column;box-shadow:-1px 0 0 rgba(0,0,0,.1)}
  .twk-chip>span>i{flex:1;box-shadow:0 -1px 0 rgba(0,0,0,.1)}
  .twk-chip>span>i:first-child{box-shadow:none}
  .twk-chip svg{position:absolute;top:6px;left:6px;width:13px;height:13px;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
`;

// ── useTweaks ───────────────────────────────────────────────────────────────
// Single source of truth for tweak values. setTweak persists via the host
// (__edit_mode_set_keys → host rewrites the EDITMODE block on disk).
function useTweaks(defaults) {
  const [values, setValues] = React.useState(defaults);
  // Accepts either setTweak('key', value) or setTweak({ key: value, ... }) so a
  // useState-style call doesn't write a "[object Object]" key into the persisted
  // JSON block.
  const setTweak = React.useCallback((keyOrEdits, val) => {
    const edits = typeof keyOrEdits === 'object' && keyOrEdits !== null ? keyOrEdits : {
      [keyOrEdits]: val
    };
    setValues(prev => ({
      ...prev,
      ...edits
    }));
    window.parent.postMessage({
      type: '__edit_mode_set_keys',
      edits
    }, '*');
    // Same-window signal so in-page listeners (deck-stage rail thumbnails)
    // can react — the parent message only reaches the host, not peers.
    window.dispatchEvent(new CustomEvent('tweakchange', {
      detail: edits
    }));
  }, []);
  return [values, setTweak];
}

// ── TweaksPanel ─────────────────────────────────────────────────────────────
// Floating shell. Registers the protocol listener BEFORE announcing
// availability — if the announce ran first, the host's activate could land
// before our handler exists and the toolbar toggle would silently no-op.
// The close button posts __edit_mode_dismissed so the host's toolbar toggle
// flips off in lockstep; the host echoes __deactivate_edit_mode back which
// is what actually hides the panel.
function TweaksPanel({
  title = 'Tweaks',
  noDeckControls = false,
  children
}) {
  const [open, setOpen] = React.useState(false);
  const dragRef = React.useRef(null);
  // Auto-inject a rail toggle when a <deck-stage> is on the page. The
  // toggle drives the deck's per-viewer _railVisible via window message;
  // state is mirrored from the same localStorage key the deck reads so
  // the control reflects reality across reloads. The mechanism is the
  // message — authors who want custom placement can post it directly
  // and pass noDeckControls to suppress this one.
  const hasDeckStage = React.useMemo(() => typeof document !== 'undefined' && !!document.querySelector('deck-stage'), []);
  // deck-stage enables its rail in connectedCallback, but this panel can
  // mount before that element has upgraded. The initial read catches the
  // common case; the listener covers mounting first. (Older deck-stage.js
  // copies still wait for the host's __omelette_rail_enabled postMessage —
  // same listener handles those.)
  const [railEnabled, setRailEnabled] = React.useState(() => hasDeckStage && !!document.querySelector('deck-stage')?._railEnabled);
  React.useEffect(() => {
    if (!hasDeckStage || railEnabled) return undefined;
    const onMsg = e => {
      if (e.data && e.data.type === '__omelette_rail_enabled') setRailEnabled(true);
    };
    window.addEventListener('message', onMsg);
    return () => window.removeEventListener('message', onMsg);
  }, [hasDeckStage, railEnabled]);
  const [railVisible, setRailVisible] = React.useState(() => {
    try {
      return localStorage.getItem('deck-stage.railVisible') !== '0';
    } catch (e) {
      return true;
    }
  });
  const toggleRail = on => {
    setRailVisible(on);
    window.postMessage({
      type: '__deck_rail_visible',
      on
    }, '*');
  };
  const offsetRef = React.useRef({
    x: 16,
    y: 16
  });
  const PAD = 16;
  const clampToViewport = React.useCallback(() => {
    const panel = dragRef.current;
    if (!panel) return;
    const w = panel.offsetWidth,
      h = panel.offsetHeight;
    const maxRight = Math.max(PAD, window.innerWidth - w - PAD);
    const maxBottom = Math.max(PAD, window.innerHeight - h - PAD);
    offsetRef.current = {
      x: Math.min(maxRight, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(maxBottom, Math.max(PAD, offsetRef.current.y))
    };
    panel.style.right = offsetRef.current.x + 'px';
    panel.style.bottom = offsetRef.current.y + 'px';
  }, []);
  React.useEffect(() => {
    if (!open) return;
    clampToViewport();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', clampToViewport);
      return () => window.removeEventListener('resize', clampToViewport);
    }
    const ro = new ResizeObserver(clampToViewport);
    ro.observe(document.documentElement);
    return () => ro.disconnect();
  }, [open, clampToViewport]);
  React.useEffect(() => {
    const onMsg = e => {
      const t = e?.data?.type;
      if (t === '__activate_edit_mode') setOpen(true);else if (t === '__deactivate_edit_mode') setOpen(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({
      type: '__edit_mode_available'
    }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);
  const dismiss = () => {
    setOpen(false);
    window.parent.postMessage({
      type: '__edit_mode_dismissed'
    }, '*');
  };
  const onDragStart = e => {
    const panel = dragRef.current;
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    const sx = e.clientX,
      sy = e.clientY;
    const startRight = window.innerWidth - r.right;
    const startBottom = window.innerHeight - r.bottom;
    const move = ev => {
      offsetRef.current = {
        x: startRight - (ev.clientX - sx),
        y: startBottom - (ev.clientY - sy)
      };
      clampToViewport();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };
  if (!open) return null;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("style", null, __TWEAKS_STYLE), /*#__PURE__*/React.createElement("div", {
    ref: dragRef,
    className: "twk-panel",
    "data-noncommentable": "",
    style: {
      right: offsetRef.current.x,
      bottom: offsetRef.current.y
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-hd",
    onMouseDown: onDragStart
  }, /*#__PURE__*/React.createElement("b", null, title), /*#__PURE__*/React.createElement("button", {
    className: "twk-x",
    "aria-label": "Close tweaks",
    onMouseDown: e => e.stopPropagation(),
    onClick: dismiss
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "twk-body"
  }, children, hasDeckStage && railEnabled && !noDeckControls && /*#__PURE__*/React.createElement(TweakSection, {
    label: "Deck"
  }, /*#__PURE__*/React.createElement(TweakToggle, {
    label: "Thumbnail rail",
    value: railVisible,
    onChange: toggleRail
  })))));
}

// ── Layout helpers ──────────────────────────────────────────────────────────

function TweakSection({
  label,
  children
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "twk-sect"
  }, label), children);
}
function TweakRow({
  label,
  value,
  children,
  inline = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: inline ? 'twk-row twk-row-h' : 'twk-row'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label), value != null && /*#__PURE__*/React.createElement("span", {
    className: "twk-val"
  }, value)), children);
}

// ── Controls ────────────────────────────────────────────────────────────────

function TweakSlider({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label,
    value: `${value}${unit}`
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    className: "twk-slider",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange(Number(e.target.value))
  }));
}
function TweakToggle({
  label,
  value,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-row twk-row-h"
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "twk-toggle",
    "data-on": value ? '1' : '0',
    role: "switch",
    "aria-checked": !!value,
    onClick: () => onChange(!value)
  }, /*#__PURE__*/React.createElement("i", null)));
}
function TweakRadio({
  label,
  value,
  options,
  onChange
}) {
  const trackRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);
  // The active value is read by pointer-move handlers attached for the lifetime
  // of a drag — ref it so a stale closure doesn't fire onChange for every move.
  const valueRef = React.useRef(value);
  valueRef.current = value;

  // Segments wrap mid-word once per-segment width runs out. The track is
  // ~248px (280 panel − 28 body pad − 4 seg pad), each button loses 12px
  // to its own padding, and 11.5px system-ui averages ~6.3px/char — so 2
  // options fit ~16 chars each, 3 fit ~10. Past that (or >3 options), fall
  // back to a dropdown rather than wrap.
  const labelLen = o => String(typeof o === 'object' ? o.label : o).length;
  const maxLen = options.reduce((m, o) => Math.max(m, labelLen(o)), 0);
  const fitsAsSegments = maxLen <= ({
    2: 16,
    3: 10
  }[options.length] ?? 0);
  if (!fitsAsSegments) {
    // <select> emits strings — map back to the original option value so the
    // fallback stays type-preserving (numbers, booleans) like the segment path.
    const resolve = s => {
      const m = options.find(o => String(typeof o === 'object' ? o.value : o) === s);
      return m === undefined ? s : typeof m === 'object' ? m.value : m;
    };
    return /*#__PURE__*/React.createElement(TweakSelect, {
      label: label,
      value: value,
      options: options,
      onChange: s => onChange(resolve(s))
    });
  }
  const opts = options.map(o => typeof o === 'object' ? o : {
    value: o,
    label: o
  });
  const idx = Math.max(0, opts.findIndex(o => o.value === value));
  const n = opts.length;
  const segAt = clientX => {
    const r = trackRef.current.getBoundingClientRect();
    const inner = r.width - 4;
    const i = Math.floor((clientX - r.left - 2) / inner * n);
    return opts[Math.max(0, Math.min(n - 1, i))].value;
  };
  const onPointerDown = e => {
    setDragging(true);
    const v0 = segAt(e.clientX);
    if (v0 !== valueRef.current) onChange(v0);
    const move = ev => {
      if (!trackRef.current) return;
      const v = segAt(ev.clientX);
      if (v !== valueRef.current) onChange(v);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    ref: trackRef,
    role: "radiogroup",
    onPointerDown: onPointerDown,
    className: dragging ? 'twk-seg dragging' : 'twk-seg'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-seg-thumb",
    style: {
      left: `calc(2px + ${idx} * (100% - 4px) / ${n})`,
      width: `calc((100% - 4px) / ${n})`
    }
  }), opts.map(o => /*#__PURE__*/React.createElement("button", {
    key: o.value,
    type: "button",
    role: "radio",
    "aria-checked": o.value === value
  }, o.label))));
}
function TweakSelect({
  label,
  value,
  options,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("select", {
    className: "twk-field",
    value: value,
    onChange: e => onChange(e.target.value)
  }, options.map(o => {
    const v = typeof o === 'object' ? o.value : o;
    const l = typeof o === 'object' ? o.label : o;
    return /*#__PURE__*/React.createElement("option", {
      key: v,
      value: v
    }, l);
  })));
}
function TweakText({
  label,
  value,
  placeholder,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("input", {
    className: "twk-field",
    type: "text",
    value: value,
    placeholder: placeholder,
    onChange: e => onChange(e.target.value)
  }));
}
function TweakNumber({
  label,
  value,
  min,
  max,
  step = 1,
  unit = '',
  onChange
}) {
  const clamp = n => {
    if (min != null && n < min) return min;
    if (max != null && n > max) return max;
    return n;
  };
  const startRef = React.useRef({
    x: 0,
    val: 0
  });
  const onScrubStart = e => {
    e.preventDefault();
    startRef.current = {
      x: e.clientX,
      val: value
    };
    const decimals = (String(step).split('.')[1] || '').length;
    const move = ev => {
      const dx = ev.clientX - startRef.current.x;
      const raw = startRef.current.val + dx * step;
      const snapped = Math.round(raw / step) * step;
      onChange(clamp(Number(snapped.toFixed(decimals))));
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-num"
  }, /*#__PURE__*/React.createElement("span", {
    className: "twk-num-lbl",
    onPointerDown: onScrubStart
  }, label), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: value,
    min: min,
    max: max,
    step: step,
    onChange: e => onChange(clamp(Number(e.target.value)))
  }), unit && /*#__PURE__*/React.createElement("span", {
    className: "twk-num-unit"
  }, unit));
}

// Relative-luminance contrast pick — checkmarks drawn over a swatch need to
// read on both #111 and #fafafa without per-option configuration. Hex input
// only (#rgb / #rrggbb); named or rgb()/hsl() colors fall through to "light".
function __twkIsLight(hex) {
  const h = String(hex).replace('#', '');
  const x = h.length === 3 ? h.replace(/./g, c => c + c) : h.padEnd(6, '0');
  const n = parseInt(x.slice(0, 6), 16);
  if (Number.isNaN(n)) return true;
  const r = n >> 16 & 255,
    g = n >> 8 & 255,
    b = n & 255;
  return r * 299 + g * 587 + b * 114 > 148000;
}
const __TwkCheck = ({
  light
}) => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 14 14",
  "aria-hidden": "true"
}, /*#__PURE__*/React.createElement("path", {
  d: "M3 7.2 5.8 10 11 4.2",
  fill: "none",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  stroke: light ? 'rgba(0,0,0,.78)' : '#fff'
}));

// TweakColor — curated color/palette picker. Each option is either a single
// hex string or an array of 1-5 hex strings; the card adapts — a lone color
// renders solid, a palette renders colors[0] as the hero (left ~2/3) with the
// rest stacked in a sharp column on the right. onChange emits the
// option in the shape it was passed (string stays string, array stays array).
// Without options it falls back to the native color input for back-compat.
function TweakColor({
  label,
  value,
  options,
  onChange
}) {
  if (!options || !options.length) {
    return /*#__PURE__*/React.createElement("div", {
      className: "twk-row twk-row-h"
    }, /*#__PURE__*/React.createElement("div", {
      className: "twk-lbl"
    }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("input", {
      type: "color",
      className: "twk-swatch",
      value: value,
      onChange: e => onChange(e.target.value)
    }));
  }
  // Native <input type=color> emits lowercase hex per the HTML spec, so
  // compare case-insensitively. String() guards JSON.stringify(undefined),
  // which returns the primitive undefined (no .toLowerCase).
  const key = o => String(JSON.stringify(o)).toLowerCase();
  const cur = key(value);
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-chips",
    role: "radiogroup"
  }, options.map((o, i) => {
    const colors = Array.isArray(o) ? o : [o];
    const [hero, ...rest] = colors;
    const sup = rest.slice(0, 4);
    const on = key(o) === cur;
    return /*#__PURE__*/React.createElement("button", {
      key: i,
      type: "button",
      className: "twk-chip",
      role: "radio",
      "aria-checked": on,
      "data-on": on ? '1' : '0',
      "aria-label": colors.join(', '),
      title: colors.join(' · '),
      style: {
        background: hero
      },
      onClick: () => onChange(o)
    }, sup.length > 0 && /*#__PURE__*/React.createElement("span", null, sup.map((c, j) => /*#__PURE__*/React.createElement("i", {
      key: j,
      style: {
        background: c
      }
    }))), on && /*#__PURE__*/React.createElement(__TwkCheck, {
      light: __twkIsLight(hero)
    }));
  })));
}
function TweakButton({
  label,
  onClick,
  secondary = false
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: secondary ? 'twk-btn secondary' : 'twk-btn',
    onClick: onClick
  }, label);
}
Object.assign(window, {
  useTweaks,
  TweaksPanel,
  TweakSection,
  TweakRow,
  TweakSlider,
  TweakToggle,
  TweakRadio,
  TweakSelect,
  TweakText,
  TweakNumber,
  TweakColor,
  TweakButton
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/indcric_web/tweaks-panel.jsx", error: String((e && e.message) || e) }); }

})();
