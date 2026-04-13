from bot.services.db_service import is_approved, save_query


async def handle_check(update, context):
    """
    Handles incoming messages (text or photo) for compliance checking.
    Only approved users can submit queries.
    Saves each query to the database and returns a placeholder response
    until the AI service is wired up.
    """
    telegram_id = update.effective_user.id

    # Block unapproved users before doing anything else
    if not is_approved(telegram_id):
        await update.message.reply_text(
            "⛔ You don't have access yet. Please wait for approval."
        )
        return

    if update.message.photo:
        # User sent a photo — grab the highest-resolution version (last in the list)
        photo = update.message.photo[-1]
        query_content = f"photo:{photo.file_id}"

        # Persist the query with a temporary 'pending' verdict
        save_query(
            telegram_id=telegram_id,
            query_type="photo",
            query_content=query_content,
            verdict="pending",
            full_response="AI analysis pending"
        )

        await update.message.reply_text(
            "📸 Photo received! Analyzing... (AI coming soon)"
        )

    elif update.message.text:
        # User sent a text message
        query_content = update.message.text

        # Persist the query with a temporary 'pending' verdict
        save_query(
            telegram_id=telegram_id,
            query_type="text",
            query_content=query_content,
            verdict="pending",
            full_response="AI analysis pending"
        )

        await update.message.reply_text(
            f"🔍 Checking: {query_content}... (AI coming soon)"
        )
