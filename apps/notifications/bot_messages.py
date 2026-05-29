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
        "📊 *STATUS* — who's in / out\n"
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
    """Fallback when the message couldn't be parsed. Echoes the user's input."""
    seen = f" — you sent: _{echo}_" if echo else ""
    return (
        f"🤔 I didn't catch that{seen}.\n"
        "\n"
        "Reply *YES* / *NO* to RSVP, *STATUS* for who's playing, "
        "*BALANCE* for your wallet, or *HELP* to see everything I can do."
    )
