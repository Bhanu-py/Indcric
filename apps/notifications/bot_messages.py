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
        "✅ *YES* or ❌ *NO* — RSVP to the current poll\n"
        "💰 *BALANCE* — your wallet + what you owe\n"
        "🗂️ *HISTORY* — your last games + wallet\n"
        "📊 *STATUS* — who's in / out\n"
        "🏆 *SCORE* — live score of the current match\n"
        "❓ *HELP* — show this message\n"
        "\n"
        "Playing a *specific* game? Just tap the *YES/NO* link in the group message — no need to type anything."
    )


def no_active_poll():
    return (
        "📭 No active session poll right now.\n"
        "I'll message you when the next one opens."
    )


def rsvp_recorded(choice, session_name, date_str, yes_names, no_names):
    """Confirmation for an RSVP, with the updated poll tally shown above it so
    the voter sees the effect of their vote. yes_names / no_names are lists."""
    you_are = "IN" if choice == "yes" else "OUT"
    mark = "✅" if choice == "yes" else "❌"
    opposite = "NO" if choice == "yes" else "YES"
    return (
        status(session_name, date_str, yes_names, no_names)
        + "\n\n"
        + f"{mark} You're *{you_are}* for this one. Reply *{opposite}* to switch."
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


def history(rows, wallet_total):
    """Recent-games reply.

    rows: iterable of (session_name, date_str, amount, status) tuples, newest
    first. wallet_total is the user's overall wallet balance.
    """
    rows = list(rows)
    if not rows:
        return (
            "🏏 No games on record yet.\n"
            "Your match history shows here once you've played a confirmed session."
        )
    lines = [f"🏏 *Your last {len(rows)} game{'' if len(rows) == 1 else 's'}*", ""]
    for name, date_str, amount, status in rows:
        mark = "✅" if status == "paid" else "🔸"
        lines.append(f"{mark} {name} ({date_str}): €{amount:.2f} · {status}")
    lines.append("")
    lines.append(f"💰 *Wallet balance: €{wallet_total:.2f}*")
    return "\n".join(lines)


def status(session_name, date_str, yes_names, no_names):
    """Poll counts + voter lists, one name per line. yes_names / no_names are
    lists of display names."""
    def block(mark, label, names):
        head = f"{mark} *{label}* ({len(names)})"
        if not names:
            return f"{head}\n• —"
        return head + "\n" + "\n".join(f"• {n}" for n in names)

    return "\n".join([
        f"🏏 *{session_name}* ({date_str})",
        "",
        block("✅", "IN", yes_names),
        "",
        block("❌", "OUT", no_names),
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
