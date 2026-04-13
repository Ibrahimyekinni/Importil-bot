# Utility helper functions


async def notify_user_approved(bot, telegram_id: int):
    """
    Sends an approval notification to a user after Dekel approves them
    from the dashboard. Called directly from the Flask dashboard route.
    """
    await bot.send_message(
        chat_id=telegram_id,
        text=(
            "✅ Great news! Your Importil access has been approved by Dekel.\n\n"
            "You can now send me any product name or photo to check customs "
            "compliance into Israel. 🇮🇱\n\n"
            "Try it now — just type a product name!"
        )
    )
