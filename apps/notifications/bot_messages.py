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
    """Full command reference — every command, its aliases, and an example."""
    return (
        "🏏 *IndCric Bot — Commands*\n"
        "\n"
        "*RSVP to a session*\n"
        "✅ *YES* / ❌ *NO* — reply to the latest poll\n"
        "_(also: Y, N, 1, 2, ✅, ❌)_\n"
        "*YES <id>* / *NO <id>* — RSVP to a specific session\n"
        "_e.g. YES 42_\n"
        "\n"
        "*Your money*\n"
        "💰 *BALANCE* — wallet balance + what you owe\n"
        "_(also: BAL, WALLET)_\n"
        "\n"
        "*Session info*\n"
        "📊 *STATUS* — who's in / out for the open poll\n"
        "_(also: POLL, WHO, COUNT)_\n"
        "\n"
        "*Other*\n"
        "❓ *HELP* — show this message  _(also: ?)_"
    )


def no_active_poll():
    return (
        "📭 No active session poll right now.\n"
        "I'll message you when the next one opens."
    )


def rsvp_confirmation(choice, session_name, date_str):
    mark = "✅" if choice == "yes" else "❌"
    opposite = "NO" if choice == "yes" else "YES"
    return (
        f"{mark} Got it — recorded *{choice.upper()}* for *{session_name}* ({date_str}).\n"
        f"Changed your mind? Reply *{opposite}* to switch."
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


def status(session_name, date_str, yes_names, no_names, yes_count, no_count):
    return "\n".join([
        f"🏏 *{session_name}* ({date_str})",
        "",
        f"✅ *IN* ({yes_count}): {yes_names}",
        f"❌ *OUT* ({no_count}): {no_names}",
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
