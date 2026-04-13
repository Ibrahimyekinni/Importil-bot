async def handle_help(update, context):
    """
    Handles the /help command.
    Sends the user a summary of all available bot commands and usage instructions.
    """
    help_text = (
        "Here's what I can do:\n\n"
        "/start - Register or check your status\n"
        "/link your@email.com - Link your email to your account\n"
        "/help - Show this message\n\n"
        "Once approved, just send me a product name or upload a photo "
        "and I'll check if it's allowed into Israel. 🇮🇱"
    )
    await update.message.reply_text(help_text)
