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
        'fetching_link': "🔍 Fetching product info from link... please wait",
        'error': "⚠️ Sorry, I couldn't complete the compliance check right now. Please try again in a moment or contact support.",
        'image_error': "⚠️ Sorry, I couldn't analyse the image right now. Please try again or send the product name as text instead.",
        'link_fetch_failed': "⚠️ I couldn't extract product details from that link (this site blocks automated reading).\n\n💡 Just copy the product name and specs from the page and send them as text — I'll give you an instant verdict!",
        'link_fetch_tip': "💡 Tip: Just type the product name or model number directly and I'll check it instantly!",
        'link_error': "⚠️ Sorry, something went wrong while processing that link. Please try again or type the product name directly.",
        'link_unclear': "⚠️ I couldn't extract enough product details from that link. Could you tell me the product name, model number, or frequency specs so I can give you an accurate verdict?",
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
        'analyzing_document': "📄 Reading document and checking compliance... please wait",
        'document_error': "⚠️ Sorry, I couldn't read that file. Please try a PDF or Word document, or just type the product details directly.",
        'ask_importer_type': "Are you importing as a private person or a company?",
        'ask_quantity': "How many units are you importing?",
        'invalid_quantity': "⚠️ Please enter a valid whole number (e.g. 3).",
        'private_limit_exceeded': "❌ Personal import is limited to 5 units maximum under Israeli law. We cannot process this request.",
        'commercial_license_required': "❌ This quantity requires a periodic commercial license with a hardware token. Please contact the Ministry of Communications directly at *6621.",
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
        'fetching_link': "🔍 מביא מידע מוצר מהקישור... אנא המתן",
        'error': "⚠️ מצטער, לא הצלחתי להשלים את הבדיקה כרגע. אנא נסה שוב או צור קשר עם התמיכה.",
        'image_error': "⚠️ מצטער, לא הצלחתי לנתח את התמונה. אנא נסה שוב או שלח את שם המוצר כטקסט.",
        'link_fetch_failed': "⚠️ לא הצלחתי לחלץ פרטי מוצר מהקישור הזה (האתר חוסם קריאה אוטומטית).\n\n💡 פשוט העתק את שם המוצר והמפרטים מהדף ושלח כטקסט — אתן לך פסיקה מיידית!",
        'link_fetch_tip': "💡 טיפ: פשוט הקלד את שם המוצר או מספר הדגם ישירות ואבדוק מיד!",
        'link_error': "⚠️ מצטער, משהו השתבש בעיבוד הקישור. אנא נסה שוב או הקלד את שם המוצר ישירות.",
        'link_unclear': "⚠️ לא הצלחתי לחלץ מספיק פרטי מוצר מהקישור. האם תוכל לספר לי את שם המוצר, מספר הדגם, או מפרטי התדר כדי שאוכל לתת לך פסיקה מדויקת?",
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
        'analyzing_document': "📄 קורא את המסמך ובודק תאימות... אנא המתן",
        'document_error': "⚠️ מצטער, לא הצלחתי לקרוא את הקובץ. אנא נסה PDF או מסמך Word, או פשוט הקלד את פרטי המוצר ישירות.",
        'ask_importer_type': "האם אתה מייבא כאדם פרטי או כחברה?",
        'ask_quantity': "כמה יחידות אתה מייבא?",
        'invalid_quantity': "⚠️ אנא הזן מספר שלם תקין (לדוגמה: 3).",
        'private_limit_exceeded': "❌ יבוא אישי מוגבל ל-5 יחידות לכל היותר על פי החוק הישראלי. לא ניתן לעבד בקשה זו.",
        'commercial_license_required': "❌ כמות זו מצריכה רישיון מסחרי תקופתי עם אסימון חומרה. אנא פנה ישירות למשרד התקשורת בטלפון *6621.",
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
