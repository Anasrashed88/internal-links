import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from openai import OpenAI

# إعداد واجهة Streamlit
st.set_page_config(page_title="مُوَلّد الروابط الداخلية (SEO Internal Linker)", layout="wide")
st.title("🔗 أداة توليد الروابط الداخلية الذكية")

# الشريط الجانبي للمفاتيح والإعدادات
with st.sidebar:
    api_key = st.text_input("أدخل مفتاح OpenAI API Key:", type="password")
    max_links = st.slider("الحد الأقصى للروابط:", min_value=1, max_value=3, value=3)

# دالة جلب روابط المتجر من Sitemap
def fetch_sitemap_urls(store_url):
    urls = []
    # تجربة مسارات خريطة الموقع الشائعة
    sitemap_paths = ["/sitemap.xml", "/sitemap_products_1.xml", "/wp-sitemap.xml"]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    for path in sitemap_paths:
        target_sitemap = urljoin(store_url, path)
        try:
            res = requests.get(target_sitemap, headers=headers, timeout=5)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                # استخراج الروابط من XML
                for elem in root.iter():
                    if elem.tag.endswith('loc') and elem.text:
                        # تصفية الروابط لتجنب صفحات الدعم والسياسات
                        u = elem.text.strip()
                        if any(x in u for x in ['/product', '/category', '/p/', '/c/', '/collection']):
                            urls.append(u)
                        elif len(urls) < 100: # روابط عامة إضافية
                            urls.append(u)
                if urls:
                    break
        except Exception:
            continue
            
    # إرجاع عينة مناسبة لتفادي استهلاك التوكنز
    return list(set(urls))[:60]

# دالة معالجة المقال عبر الذكاء الاصطناعي
def generate_internal_links(client, article_text, urls, max_links_count):
    urls_str = "\n".join(urls)
    
    prompt = f"""
    أنت خبير محترف في تحسين محركات البحث (SEO On-Page Specialist).
    
    المهمة:
    1. لديك نص المقال التالي.
    2. ولديك قائمة بروابط صفحات وتصنيفات المتجر.
    3. قم باختيار أنسب الروابط (بحد أقصى {max_links_count} روابط فقط) التي ترتبط تماماً بسياق المقال.
    4. أدرج الروابط داخل المقال بصيغة Markdown على شكل [الكلمة المفتاحية](الرابط).
    
    شروط هامة للـ SEO:
    - يجب أن يكون الـ Anchor Text (الكلمة المفتاحية) طبيعياً جداً، تجنب نصوص مثل "انقر هنا" أو "شاهد هذا".
    - وزّع الروابط على فقرات مختلفة (لا تجمعها في فقرة واحدة).
    - إذا لم تجد صلة منطقية لرابط معين، لا تضفه (الجودة أهم من العدد).
    - أرجع نص المقالة بالكامل بعد إضافة الروابط بدون أي مقدمات أو شروحات إضافية.

    قائمة الروابط المتاحة:
    {urls_str}

    نص المقالة:
    {article_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini", # أو gpt-4o للحصول على أعلى دقة سياقية
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# مدخلات المستخدم
store_url = st.text_input("🌐 رابط المتجر الإلكتروني (مثال: https://examplestore.com)")
article_content = st.text_area("📝 نص المقالة:", height=250)

if st.button("🚀 توليد الروابط الآن"):
    if not api_key:
        st.error("يرجى إدخال OpenAI API Key من الشريط الجانبي.")
    elif not store_url or not article_content:
        st.warning("يرجى إدخال رابط المتجر ونص المقالة.")
    else:
        with st.spinner("جاري استخراج صفحات المتجر وتحليل المقال..."):
            extracted_urls = fetch_sitemap_urls(store_url)
            
            if not extracted_urls:
                st.error("تعذر العثور على روابط من خريطة الموقع (sitemap.xml). تأكد أن الرابط صحيح أو خريطة الموقع عامة.")
            else:
                st.success(f"تم العثور على {len(extracted_urls)} صفحة من المتجر!")
                
                client = OpenAI(api_key=api_key)
                updated_article = generate_internal_links(client, article_content, extracted_urls, max_links)
                
                st.subheader("📄 المقال بعد إضافة الروابط:")
                st.markdown(updated_article)
                
                st.subheader("📋 كود المقال (Markdown / جاهز للنسخ):")
                st.code(updated_article, language="markdown")