MESSAGES = {
    'en': {
        'welcome_new': (
            "Welcome to Importil! 🛃\n\n"
            "I'm your AI-powered Israeli customs compliance assistant for Drivetech360.\n\n"
            "Your registration has been received. Dekel will approve your access shortly."
        ),
        'welcome_back': "Welcome back {username}! 👋\n\nYou're verified. Send me a product name or photo to check customs compliance into Israel. 🇮🇱",
        'pending': "⏳ Your account is pending approval. Dekel will notify you once you're verified.",
        'no_access': "⛔ You don't have access yet. Please wait for approval.",
        'link_success': "✅ Email linked successfully! Waiting for Dekel's approval.",
        'link_usage': "Please provide your email. Example: /link your@email.com",
        'analyzing_text': "🔍 Analyzing product compliance... please wait",
        'analyzing_image': "📸 Analyzing image... please wait",
        'analyzing_followup': "🔄 Processing your follow-up...",
        'error': "⚠️ Sorry, I couldn't complete the compliance check right now. Please try again in a moment or contact support.",
        'image_error': "⚠️ Sorry, I couldn't analyse the image right now. Please try again or send the product name as text instead.",
        'refresh_success': "🔄 Document cache refreshed successfully! AI brain updated.",
        'refresh_error': "❌ Failed to refresh the cache. Check logs for details.",
        'no_permission': "⛔ You don't have permission to do this.",
        'approved_notification': (
            "✅ Great news! Your Importil access has been approved by Dekel.\n\n"
            "You can now send me any product name or photo to check customs compliance into Israel. 🇮🇱\n\n"
            "Try it now — just type a product name!"
        ),
        'language_prompt': "🌐 Please choose your preferred language:\nבחר את השפה המועדפת עליך:",
        'language_set': "✅ Language set to English!",
        'help': (
            "Here's what I can do:\n\n"
            "/start - Register or check your status\n"
            "/link your@email.com - Link your email\n"
            "/language - Change language\n"
            "/help - Show this message\n\n"
            "Once approved, send me a product name or photo and I'll check if it's allowed into Israel. 🇮🇱"
        ),
        'new_user_admin': (
            "🆕 New importer registered!\n\n"
            "Name: @{username}\n"
            "Telegram ID: {telegram_id}\n\n"
            "Go to the dashboard to approve or reject them."
        ),
    },
    'he': {
        'welcome_new': (
            "ברוך הבא ל-Importil! 🛃\n\n"
            "אני העוזר החכם שלך לבדיקת תאימות מכס ישראלי עבור Drivetech360.\n\n"
            "הרישום שלך התקבל. דקל יאשר את הגישה שלך בקרוב."
        ),
        'welcome_back': "ברוך שובך {username}! 👋\n\nהחשבון שלך מאומת. שלח לי שם מוצר או תמונה לבדיקת תאימות יבוא לישראל. 🇮🇱",
        'pending': "⏳ החשבון שלך ממתין לאישור. דקל יודיע לך כאשר תאומת.",
        'no_access': "⛔ אין לך גישה עדיין. אנא המתן לאישור.",
        'link_success': "✅ האימייל קושר בהצלחה! ממתין לאישור דקל.",
        'link_usage': "אנא ספק את האימייל שלך. דוגמה: /link your@email.com",
        'analyzing_text': "🔍 בודק תאימות מוצר... אנא המתן",
        'analyzing_image': "📸 מנתח תמונה... אנא המתן",
        'analyzing_followup': "🔄 מעבד את ההמשך שלך...",
        'error': "⚠️ מצטער, לא הצלחתי להשלים את הבדיקה כרגע. אנא נסה שוב או צור קשר עם התמיכה.",
        'image_error': "⚠️ מצטער, לא הצלחתי לנתח את התמונה. אנא נסה שוב או שלח את שם המוצר כטקסט.",
        'refresh_success': "🔄 המטמון רוענן בהצלחה! המוח ה-AI עודכן.",
        'refresh_error': "❌ רענון המטמון נכשל. בדוק את הלוגים לפרטים.",
        'no_permission': "⛔ אין לך הרשאה לבצע פעולה זו.",
        'approved_notification': (
            "✅ חדשות טובות! הגישה שלך ל-Importil אושרה על ידי דקל.\n\n"
            "אתה יכול כעת לשלוח שם מוצר או תמונה לבדיקת תאימות יבוא לישראל. 🇮🇱\n\n"
            "נסה עכשיו — פשוט הקלד שם מוצר!"
        ),
        'language_prompt': "🌐 Please choose your preferred language:\nבחר את השפה המועדפת עליך:",
        'language_set': "✅ השפה הוגדרה לעברית!",
        'help': (
            "הנה מה שאני יכול לעשות:\n\n"
            "/start - הרשמה או בדיקת סטטוס\n"
            "/link your@email.com - קישור האימייל שלך\n"
            "/language - שינוי שפה\n"
            "/help - הצג הודעה זו\n\n"
            "לאחר אישור, שלח שם מוצר או תמונה ואבדוק אם מותר לייבא לישראל. 🇮🇱"
        ),
        'new_user_admin': (
            "🆕 New importer registered!\n\n"
            "Name: @{username}\n"
            "Telegram ID: {telegram_id}\n\n"
            "Go to the dashboard to approve or reject them."
        ),
    },
}


def get_message(key, language='en', **kwargs):
    """
    Returns the message string for the given key and language.
    Falls back to English if the key or language is not found.
    Formats the string with any provided keyword arguments.
    """
    msg = MESSAGES.get(language, MESSAGES['en']).get(key, MESSAGES['en'].get(key, ''))
    return msg.format(**kwargs) if kwargs else msg
