# force/views.py

from django.shortcuts import render
import google.generativeai as genai
from django.conf import settings
import json
from django.http import JsonResponse

def chat_view(request):
    """
    يعرض صفحة الدردشة الرئيسية.
    """
    return render(request, 'chat.html')

def ask_gemini(request):
    """
    يتلقى الطلبات من الواجهة الأمامية، يتصل بـ Gemini API، ويعيد الإجابة.
    """
    # 1. التحقق من مفتاح API وإعداده
    try:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return JsonResponse({'error': 'مفتاح API الخاص بـ Gemini غير مهيأ في الإعدادات.'}, status=500)
        genai.configure(api_key=api_key)
    except AttributeError:
        return JsonResponse({'error': 'مفتاح API الخاص بـ Gemini غير موجود في ملف الإعدادات.'}, status=500)

    # 2. استخلاص البيانات من الطلب
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
        history = data.get('history', []) 
        user_name = data.get('userName', 'المستخدم')
        ai_name = data.get('aiName', 'المساعد')

        if not prompt:
            return JsonResponse({'error': 'الطلب (prompt) فارغ.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'طلب JSON غير صالح.'}, status=400)

    # 3. معالجة الطلب باستخدام Gemini
    try:
        # تعليمات النظام المحسّنة لجعل المحادثة أكثر ذكاءً وطبيعية
        system_instruction = (
            f"أنت مساعد افتراضي اسمك '{ai_name}'، ومهمتك هي الدردشة مع المستخدم '{user_name}'. "
            "لازم تتكلم بالدارجة الجزائرية (العاصمية) برك، ممنوع تستعمل لغة أخرى. خليك خفيف الظل وصديق وفي. "
            "استعمل إيموجيات باش تكون الهدرة تاعك حية ومعبرة، بصح متكثرش بزاف. "
            "جاوب على الأسئلة بطريقة مختصرة ومفيدة، ومتعاودش نفس الهدرة لي قلتها من قبل، ديما جيب حاجة جديدة. "
            f"كي تهدر على روحك قول '{ai_name}' وكي تهدر مع المستخدم عيطلو باسمو '{user_name}'. "
            "تفاعل معاه كأنك صاحبو ماشي روبوت."
        )

        # إضافة سياق للطلبات القصيرة جداً
        prompt_with_context = prompt
        if len(prompt.split()) <= 3 and history:
            # البحث عن آخر رسالة طويلة للمستخدم لتوفير سياق
            last_user_topic_entry = next((item["parts"][0] for item in reversed(history) if item["role"] == "user" and len(item["parts"][0].split()) > 3), None)
            if last_user_topic_entry:
                prompt_with_context = f"بناءً على هذا السياق: '{last_user_topic_entry}', هذا هو سؤالي: '{prompt}'"

        # إعداد النموذج وبدء المحادثة
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_instruction
        )
        chat = model.start_chat(history=history)
        response = chat.send_message(
            prompt_with_context,
            generation_config={
                "temperature": 0.7, # زيادة طفيفة للإبداع
                "top_p": 0.9,
                "top_k": 40
            }
        )

        ai_response = response.text.strip()

        # التعامل مع الردود الفارغة بطريقة أفضل
        if not ai_response:
            ai_response = f"سمحلي يا {user_name}، مفهمتش سؤالك مليح. تقدر تعاود تصيغو بطريقة وحدوخرا؟ 🤔"

        return JsonResponse({'response': ai_response})

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return JsonResponse({
            'error': 'حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا.',
            'details': str(e)
        }, status=500)