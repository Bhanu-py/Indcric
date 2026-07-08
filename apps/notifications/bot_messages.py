"""Centralised copy for the WhatsApp bot's free-text replies.

These are the messages the bot composes in code. (The session-invite and
reminder messages instead use Meta-approved *templates* — see services.py and
Meta Business Manager — and can't be restyled from here.)

WhatsApp text formatting cheatsheet:
  *bold*   _italic_   ~strike~   ```monospace```

Keep replies short, scannable on a phone, and consistent in voice. Named
'bot_messages' (not 'messages') to avoid confusion with django.contrib.messages.
"""
from django.conf import settings


def _site_url():
    return getattr(settings, 'SITE_URL', 'https://indcric.onrender.com').rstrip('/')


def not_recognised():
    """Reply when an inbound number isn't tied to any IndCric profile."""
    return (
        "I couldn't recognize your number. Please add your WhatsApp number to "
        "your IndCric profile and try again.\n"
        f"Don't have a profile yet? Sign up here: {_site_url()}/"
    )


def help_text():
    """Short, friendly command reference. Kept simple on purpose — the
    session-id form (YES 42) is only used by the tap-to-RSVP group links, so
    we don't ask users to type ids."""
    return (
        "🏏 *IndCric Bot*\n"
        "\n"
        "Just reply with:\n"
        "📅 *Saturday*, *Sunday*, or *Both* — RSVP to the current poll\n"
        "💰 *BALANCE* — your wallet + what you owe\n"
        "🗂️ *HISTORY* — your last games + wallet\n"
        "📊 *STATUS* — Saturday/Sunday/Both counts\n"
        "🏆 *SCORE* — live score of the current match\n"
        "❓ *HELP* — show this message\n"
        "\n"
        "Playing a *specific* game? Just tap the poll options in the group message — no need to type anything."
    )


def no_active_poll():
    return (
        "📭 No active session poll right now.\n"
        "I'll message you when the next one opens."
    )


def rsvp_recorded(choice, session_name, date_str, yes_names, no_names, both_names):
    """Confirmation for a vote, with the updated poll tally shown above it."""
    label = {'yes': 'Saturday', 'no': 'Sunday', 'all': 'Both'}.get(
        choice, choice.title() if choice else 'Vote'
    )
    return (
        status(session_name, date_str, yes_names, no_names, both_names)
        + "\n\n"
        + f"✅ You're *{label}* for this one. Reply with *Saturday*, *Sunday*, or *Both* to switch."
    )


def balance(wallet_total, unpaid_rows):
    """Wallet + outstanding payments reply.

    unpaid_rows: iterable of (session_name, amount) tuples, already ordered.
    """
    unpaid_rows = list(unpaid_rows)
    lines = [f"💰 *Wallet balance: €{wallet_total:.2f}*"]
    if unpaid_rows:
        lines.append("")
        lines.append("*Outstanding*")
        for name, amount in unpaid_rows:
            lines.append(f"• {name}: €{amount:.2f}")
        total_due = sum((amount for _, amount in unpaid_rows), start=0)
        lines.append("")
        lines.append(f"*Total due: €{total_due:.2f}*")
    else:
        lines.append("")
        lines.append("✅ You're all settled — no outstanding payments.")
    return "\n".join(lines)


def history(games, career, wallet_total):
    """Recent-games reply: per-match batting/bowling line + result + cost, then a
    career summary and wallet balance.

    games: list of dicts {session, match, date, runs, balls, wickets, won,
           amount (None ok), paid (None ok)}, newest first.
    career: apps.matches.scoring.career_stats(user) output.
    """
    if not games:
        return (
            "🏏 No games on record yet.\n"
            "Your match history shows here once you've played a scored match."
        )
    lines = [f"🏏 *Your last {len(games)} game{'' if len(games) == 1 else 's'}*", ""]
    for g in games:
        head = f"*{g['session']}*"
        if g['date']:
            head += f" · {g['date']}"
        if g['won'] is True:
            head += " · 🏆 won"
        elif g['won'] is False:
            head += " · lost"
        lines.append(head)
        bits = [g['match']]
        if g['runs'] or g['balls']:
            bits.append(f"🏏 {g['runs']} ({g['balls']})")
        if g['wickets']:
            bits.append(f"🎳 {g['wickets']} wkt{'' if g['wickets'] == 1 else 's'}")
        amt = f"€{g['amount']:.2f}" if g['amount'] is not None else "€—"
        bits.append(f"{amt} {'paid' if g['paid'] else 'due'}")
        lines.append("   " + " · ".join(bits))
    b, bo = career['batting'], career['bowling']
    summary = f"📊 *Career:* {career['matches']} game{'' if career['matches'] == 1 else 's'}"
    if b['innings']:
        summary += f" · {b['runs']} runs (HS {b['hs_label']})"
    if bo['wickets']:
        summary += f" · {bo['wickets']} wkts"
        if bo['best']:
            summary += f" (best {bo['best']})"
    lines += ["", summary, f"💰 *Wallet: €{wallet_total:.2f}*"]
    return "\n".join(lines)


def status(session_name, date_str, yes_names, no_names, both_names):
    """Poll counts + voter lists, one name per line."""
    def block(mark, label, names):
        head = f"{mark} *{label}* ({len(names)})"
        if not names:
            return f"{head}\n• —"
        return head + "\n" + "\n".join(f"• {n}" for n in names)

    total = len(yes_names) + len(no_names) + len(both_names)
    return "\n".join([
        f"🏏 *{session_name}* ({date_str})",
        f"📊 *{total} voted* · Saturday {len(yes_names)} · Sunday {len(no_names)} · Both {len(both_names)}",
        "",
        block("🟢", "SATURDAY", yes_names),
        "",
        block("🔵", "SUNDAY", no_names),
        "",
        block("🟣", "BOTH", both_names),
    ])


def unknown(echo=""):
    """Fallback when the message couldn't be parsed. Echoes the user's input
    and follows it with the full command list so they don't have to type HELP
    after a typo."""
    seen = f" — you sent: _{echo}_" if echo else ""
    return f"🤔 I didn't catch that{seen}.\n\n" + help_text()


def no_recent_session():
    return "📭 No sessions yet — nothing to score."


def match_not_started(session_name, date_str):
    return (
        f"🏏 *{session_name}* ({date_str})\n"
        "\n"
        "Match hasn't started yet — no scoring entered."
    )


def score(session_name, date_str, match_blocks):
    """Live score reply.

    match_blocks: list of dicts with keys:
      - name (str)
      - innings (list[str], one line per innings; empty if not started)
      - winner (str or None)
    """
    out = [f"🏆 *{session_name}* ({date_str})", ""]
    for m in match_blocks:
        out.append(f"*{m['name']}*")
        if not m['innings']:
            out.append("• Not started")
        else:
            for line in m['innings']:
                out.append(f"• {line}")
        if m.get('winner'):
            out.append(f"🏅 Winner: *{m['winner']}*")
        out.append("")
    return "\n".join(out).rstrip()
