MESSAGES = {
    'en': {
        'welcome_new': (
            "Welcome to Importil! 🛃\n\n"
            "I'm your AI-powered Israeli customs compliance assistant for Drivetech360.\n\n"
            "Your registration has been received. Dekel will approve your access shortly."
        ),
        'welcome_back': "Welcome back {username}! 👋\n\nYou're verified. Send me a product name or photo to check customs compliance into Israel. 🇮🇱",
        'pending': "⏳ Your account is pending approval. You'll be notified once your access is approved.",
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
        'refresh_success': "🔄 Document cache refreshed successfully! AI brain updated.\n💬 Conversation memory cleared.",
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
            "/status - Check your account & bot status\n"
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
        'exempt_product': (
            "✅ Good news! This product is exempt from Israeli Ministry of "
            "Communications approval under the Wireless Telegraph Exemption "
            "Regulations 2021.\n\n"
            "You do NOT need to file any request. Simply show this message to "
            "customs if asked.\n\n"
            "📋 Exemption basis: {category}\n\n"
            "💡 Keep a copy of your purchase invoice as supporting documentation."
        ),
        'status': (
            "🤖 *Importil — Status*\n\n"
            "🔌 Bot: ✅ Online\n"
            "🔐 Access: {access_status}\n"
            "🌐 Language: {language_label}\n"
            "📊 Queries run: {query_count}"
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
        'pending': "⏳ החשבון שלך ממתין לאישור. תקבל הודעה ברגע שהגישה שלך תאושר.",
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
        'refresh_success': "🔄 המטמון רוענן בהצלחה! המוח ה-AI עודכן.\n💬 זיכרון השיחה נוקה.",
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
            "/status - בדוק את סטטוס החשבון והבוט\n"
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
        'exempt_product': (
            "✅ חדשות טובות! מוצר זה פטור מאישור משרד התקשורת הישראלי "
            "בהתאם לתקנות הטלגרף האלחוטי (פטור) 2021.\n\n"
            "אינך צריך להגיש כל בקשה. פשוט הצג הודעה זו לפקיד המכס אם תתבקש.\n\n"
            "📋 בסיס הפטור: {category}\n\n"
            "💡 שמור עותק של חשבונית הרכישה שלך כתיעוד תומך."
        ),
        'status': (
            "🤖 *Importil — סטטוס*\n\n"
            "🔌 בוט: ✅ פעיל\n"
            "🔐 גישה: {access_status}\n"
            "🌐 שפה: {language_label}\n"
            "📊 שאילתות שבוצעו: {query_count}"
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


# ── Structured error messages ─────────────────────────────────────────────────
# Keyed by error_type. Each maps to a user-safe bilingual string.
# Raw Python errors are never shown; callers pass one of these keys instead.

_ERROR_MESSAGES = {
    'ai_unavailable': {
        'en': (
            "⚠️ Our AI analysis service is temporarily unavailable. "
            "Please try again in a few minutes."
        ),
        'he': (
            "⚠️ שירות הניתוח שלנו אינו זמין כרגע. "
            "אנא נסה שוב בעוד מספר דקות."
        ),
    },
    'invalid_input': {
        'en': (
            "⚠️ Please send a product name or description so I can check it. "
            "Your message was too short to analyse."
        ),
        'he': (
            "⚠️ אנא שלח שם מוצר או תיאור כדי שאוכל לבדוק. "
            "ההודעה שלך קצרה מדי לניתוח."
        ),
    },
    'unsupported_file': {
        'en': (
            "⚠️ I can only read PDF and Word (.docx) files. "
            "Please send a supported file type, or type the product details directly."
        ),
        'he': (
            "⚠️ אני יכול לקרוא רק קבצי PDF ו-Word (docx). "
            "אנא שלח סוג קובץ נתמך, או הקלד את פרטי המוצר ישירות."
        ),
    },
    'url_fetch_failed': {
        'en': (
            "⚠️ I couldn't retrieve content from that URL — the site may block "
            "automated reading.\n\n"
            "💡 Copy the product name and specs directly into the chat and I'll "
            "give you an instant verdict."
        ),
        'he': (
            "⚠️ לא הצלחתי לאחזר תוכן מה-URL הזה — האתר אולי חוסם קריאה אוטומטית.\n\n"
            "💡 העתק את שם המוצר והמפרטים ישירות לצ'אט ואתן לך פסיקה מיידית."
        ),
    },
    'document_too_large': {
        'en': (
            "⚠️ That file is too large to process (maximum 20 MB). "
            "Please send a smaller file or paste the key product specs as text."
        ),
        'he': (
            "⚠️ הקובץ גדול מדי לעיבוד (מקסימום 20 MB). "
            "אנא שלח קובץ קטן יותר או הדבק את מפרטי המוצר העיקריים כטקסט."
        ),
    },
    'ai_timeout': {
        'en': (
            "⏱️ The analysis is taking longer than expected. "
            "Please try again in a moment."
        ),
        'he': (
            "⏱️ הניתוח לוקח יותר זמן מהצפוי. "
            "אנא נסה שוב בעוד רגע."
        ),
    },
}

_FALLBACK_ERROR = {
    'en': "⚠️ Something went wrong. Please try again or send the product name as text.",
    'he': "⚠️ משהו השתבש. אנא נסה שוב או שלח את שם המוצר כטקסט.",
}


def get_error_message(error_type, language='en'):
    """
    Returns a user-safe, bilingual error string for the given error_type.
    Falls back to English, then to a generic message if the type is unknown.
    Never exposes raw Python exceptions to the caller.

    Supported error_type values:
        ai_unavailable    — Groq / AI backend is down or returned an error
        ai_timeout        — Groq call exceeded the 30-second timeout
        invalid_input     — query is empty or too short to analyse
        unsupported_file  — file MIME type is not PDF or DOCX
        url_fetch_failed  — neither meta-tag nor Firecrawl could read the URL
        document_too_large — file exceeds the 20 MB processing limit
    """
    entry = _ERROR_MESSAGES.get(error_type, _FALLBACK_ERROR)
    return entry.get(language) or entry.get('en') or _FALLBACK_ERROR['en']
