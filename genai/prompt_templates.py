SYSTEM_PROMPT = """\
You write short cart reminder emails for an online shop.

Rules:
- Friendly and helpful, never pushy. 60 to 120 words.
- Greet the customer by first name and mention the products they left.
- Use only the facts given. Do not invent discounts, deadlines,
  stock levels, delivery promises or links.
- Plain text only: no markdown, no HTML, no placeholders like [Link].
- Put the greeting, each short paragraph and the sign-off on their own
  lines, separated by a blank line.
- Sign off as "The SmartCart Team".
- The subject line is under 60 characters and does not use all caps.
"""


def build_user_prompt(first_name, items, total, currency):
    lines = "\n".join(
        f"- {item['product_name']} x{item['quantity']}: "
        f"{currency}{item['subtotal']:,.2f}"
        for item in items
    )

    return (
        f"Customer first name: {first_name}\n"
        f"Items left in the cart:\n{lines}\n"
        f"Cart total: {currency}{total:,.2f}\n\n"
        "Write the reminder email."
    )


def fallback_email(first_name, items, total, currency):
    lines = "\n".join(
        f"- {item['product_name']} x{item['quantity']} "
        f"({currency}{item['subtotal']:,.2f})"
        for item in items
    )

    subject = f"{first_name}, you left something in your cart"

    body = (
        f"Hi {first_name},\n\n"
        f"You left these items in your cart:\n\n"
        f"{lines}\n\n"
        f"Total: {currency}{total:,.2f}\n\n"
        "They're still waiting for you whenever you're ready.\n\n"
        "The SmartCart Team"
    )

    return subject, body
