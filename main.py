import os
import hmac
import hashlib
import time
import base64
import requests
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, abort
import stripe
import resend

from products_data import PRODUCTS, get_product

app = Flask('app', static_folder='public/static', static_url_path='/static')

SITE_URL = "https://vibecodingdad.com"

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
resend.api_key = os.getenv('RESEND_API_KEY')
DOWNLOAD_TOKEN_SECRET = os.getenv('DOWNLOAD_TOKEN_SECRET', 'vcd-default-secret')

PRODUCT_FILES = {
    "diary-of-an-ai-ceo": {"filename": "diary-of-an-ai-ceo.pdf", "display": "Diary-of-an-AI-CEO.pdf", "content_type": "application/pdf"},
    "calmart-memory": {"filename": "memory-architecture.zip", "display": "Memory-Architecture.zip", "content_type": "application/zip"},
    "memory-architecture": {"filename": "memory-architecture.zip", "display": "Memory-Architecture.zip", "content_type": "application/zip"},
    "expert-tweet-pipeline": {"filename": "expert-tweet-pipeline.zip", "display": "Expert-Tweet-Pipeline.zip", "content_type": "application/zip"},
    "openclaw-memory-system": {"filename": "openclaw-memory-system.zip", "display": "OpenClaw-Memory-System.zip", "content_type": "application/zip"},
}

STRIPE_PRODUCT_MAP = {
    "calmart-memory": "Memory Architecture",
    "memory-architecture": "Memory Architecture",
    "diary-of-an-ai-ceo": "Diary of an AI CEO",
    "expert-tweet-pipeline": "Expert Tweet Pipeline",
}


def generate_download_token(product_id, email, expires_in_days=7):
    expires_at = int(time.time() * 1000) + expires_in_days * 86400 * 1000
    payload = f"{product_id}:{email}:{expires_at}"
    signature = hmac.new(DOWNLOAD_TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()
    return token


def verify_download_token(token):
    try:
        decoded = base64.urlsafe_b64decode(token).decode()
        parts = decoded.split(':')
        if len(parts) != 4:
            return None
        product_id, email, expires_at_str, signature = parts
        expires_at = int(expires_at_str)
        if int(time.time() * 1000) > expires_at:
            return None
        payload = f"{product_id}:{email}:{expires_at_str}"
        expected = hmac.new(DOWNLOAD_TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return {"product_id": product_id, "email": email}
    except Exception:
        return None


def send_purchase_email(to, product_name, download_url):
    try:
        resend.Emails.send({
            "from": "Vibe Coding Dad <support@vibecodingdad.com>",
            "to": to,
            "subject": f"Your purchase: {product_name}",
            "html": f"""
            <div style="font-family: system-ui, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 0;">
                <h2 style="font-size: 18px; color: #171717;">Thanks for your purchase!</h2>
                <p style="font-size: 14px; color: #525252; line-height: 1.6;">
                    You now have access to <strong style="color: #171717;">{product_name}</strong>.
                </p>
                <a href="{download_url}"
                    style="display: inline-block; margin-top: 16px; padding: 10px 20px; background: #f97316; color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600;">
                    Download now
                </a>
                <p style="font-size: 12px; color: #737373; margin-top: 24px; line-height: 1.5;">
                    This link expires in 7 days. If you need a new link, reply to this email.
                </p>
                <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;" />
                <p style="font-size: 11px; color: #a3a3a3;">vibecodingdad.com</p>
            </div>"""
        })
    except Exception as e:
        print(f"Email send error: {e}")


def send_download_thank_you_email(to, product_name):
    try:
        resend.Emails.send({
            "from": "Vibe Coding Dad <support@vibecodingdad.com>",
            "to": to,
            "subject": f"Your download: {product_name}",
            "html": f"""
            <div style="font-family: system-ui, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 0; color: #525252;">
                <h2 style="font-size: 18px; color: #171717; margin-bottom: 4px;">Thanks for downloading {product_name}</h2>
                <p style="font-size: 14px; color: #737373; line-height: 1.6; margin-top: 8px;">
                    Your file should be downloading now. If it didn't start,
                    visit <a href="{SITE_URL}/products/openclaw-memory-system" style="color: #f97316; text-decoration: none;">the product page</a> to try again.
                </p>
                <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;" />
                <p style="font-size: 13px; color: #525252; font-weight: 600; margin-bottom: 12px;">Other things we've built</p>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 10px 0; vertical-align: top;">
                        <a href="{SITE_URL}/products/memory-architecture" style="color: #171717; text-decoration: none; font-size: 14px; font-weight: 600;">Memory Architecture</a>
                        <span style="font-size: 12px; color: #a3a3a3; margin-left: 6px;">$9</span><br />
                        <span style="font-size: 13px; color: #737373; line-height: 1.5;">Three-tier memory framework for AI agents.</span>
                    </td></tr>
                    <tr><td style="padding: 10px 0; vertical-align: top;">
                        <a href="{SITE_URL}/products/expert-tweet-pipeline" style="color: #171717; text-decoration: none; font-size: 14px; font-weight: 600;">Expert Tweet Pipeline</a>
                        <span style="font-size: 12px; color: #a3a3a3; margin-left: 6px;">$9</span><br />
                        <span style="font-size: 13px; color: #737373; line-height: 1.5;">Full X/Twitter posting pipeline with quality gates.</span>
                    </td></tr>
                    <tr><td style="padding: 10px 0; vertical-align: top;">
                        <a href="{SITE_URL}/products/diary-of-an-ai-ceo" style="color: #171717; text-decoration: none; font-size: 14px; font-weight: 600;">Diary of an AI CEO</a>
                        <span style="font-size: 12px; color: #a3a3a3; margin-left: 6px;">$19</span><br />
                        <span style="font-size: 13px; color: #737373; line-height: 1.5;">22 chapters on what happens when an AI runs a real business.</span>
                    </td></tr>
                </table>
                <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;" />
                <p style="font-size: 13px; color: #737373; line-height: 1.6;">
                    Follow TARS on X: <a href="https://x.com/meettarsai" style="color: #f97316; text-decoration: none;">@meettarsai</a>
                </p>
                <p style="font-size: 11px; color: #a3a3a3; margin-top: 16px;">vibecodingdad.com</p>
            </div>"""
        })
    except Exception as e:
        print(f"Thank you email error: {e}")

@app.after_request
def disable_caching(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_API_URL_LITE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"


@app.route('/')
def hello_world():
    print(request.headers)
    return render_template(
        'index.html',
        user_id=request.headers.get('X-Replit-User-Id', ''),
        user_name=request.headers.get('X-Replit-User-Name', ''),
        user_roles=request.headers.get('X-Replit-User-Roles', ''),
        user_bio=request.headers.get('X-Replit-User-Bio', ''),
        user_profile_image=request.headers.get('X-Replit-User-Profile-Image', ''),
        user_teams=request.headers.get('X-Replit-User-Teams', ''),
        user_url=request.headers.get('X-Replit-User-Url', ''))


@app.route('/api/generate-prompt', methods=['POST'])
def generate_prompt():
    if not GEMINI_API_KEY:
        return jsonify({'error': 'API key not configured'}), 500
    
    data = request.get_json() or {}
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    system_prompt = """You are an expert prompt engineer for Vibe Coding. The user will give you a vague app idea. You must convert it into a highly detailed, professional prompt that the user can paste into an LLM (like you or Claude) to build the app in a single file. 

REQUIREMENTS FOR THE OUTPUT PROMPT:
1. Specify 'Single file HTML using Tailwind CSS via CDN'.
2. Request a 'modern, dark-mode aesthetic'.
3. Request 'no build steps, pure vanilla JS'.
4. Ask for 'robust error handling and responsive design'.
5. Output ONLY the prompt text, nothing else."""

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{
                    'role': 'user',
                    'parts': [{'text': f"User Idea: {user_input}\n\n{system_prompt}"}]
                }]
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Error generating prompt.')
        return jsonify({'text': generated_text})
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({'error': 'Failed to generate prompt'}), 500


@app.route('/api/vibe-check', methods=['POST'])
def vibe_check():
    if not GEMINI_API_KEY:
        return jsonify({'error': 'API key not configured'}), 500
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL_LITE}?key={GEMINI_API_KEY}",
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{
                    'parts': [{'text': "Give me a very short, punchy, motivational one-liner for a builder who is tired but needs to ship code. Be funny, encouraging, like a cool dad. Max 18 words."}]
                }]
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        vibe_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Ship it. Fix it later.')
        return jsonify({'text': vibe_text.strip()})
    except Exception as e:
        print(f"Vibe Check Error: {e}")
        return jsonify({'error': 'Failed to get vibe'}), 500


@app.route('/products/<slug>')
def product_page(slug):
    product = get_product(slug)
    if not product:
        abort(404)
    stripe_link = ""
    if product.get("stripe_link_env"):
        stripe_link = os.getenv(product["stripe_link_env"], "#")
    return render_template('product.html', product=product, slug=slug, stripe_link=stripe_link)


@app.route('/products/<slug>/<filename>')
def product_file_download(slug, filename):
    product = get_product(slug)
    if not product or product["file"]["filename"] != filename:
        abort(404)
    if not product["is_free"]:
        abort(403)
    import os.path
    products_dir = os.path.join(os.path.dirname(__file__), 'products')
    return send_from_directory(products_dir, filename, as_attachment=True, download_name=product["file"]["display"])


@app.route('/products/<slug>/success')
def product_success(slug):
    product = get_product(slug)
    if not product:
        abort(404)
    return render_template('success.html', product_name=product["name"], accent=product["accent"], slug=slug)


@app.route('/terms')
def terms_page():
    return render_template('terms.html')


@app.route('/api/checkout/verify')
def checkout_verify():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            return jsonify({"error": "Payment not completed"}), 402
        product_id = (session.metadata or {}).get('product_id')
        email = (session.customer_details or {}).email if session.customer_details else None
        if not product_id or not email:
            return jsonify({"error": "Invalid session"}), 400
        token = generate_download_token(product_id, email)
        download_url = f"{SITE_URL}/api/download/{product_id}?token={token}"
        return jsonify({"downloadUrl": download_url})
    except Exception:
        return jsonify({"error": "Invalid session"}), 400


@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return jsonify({"error": "Invalid signature"}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = (session.get('customer_details') or {}).get('email')
        product_id = (session.get('metadata') or {}).get('product_id')
        if email and product_id and product_id in STRIPE_PRODUCT_MAP:
            product_name = STRIPE_PRODUCT_MAP[product_id]
            token = generate_download_token(product_id, email)
            download_url = f"{SITE_URL}/api/download/{product_id}?token={token}"
            send_purchase_email(email, product_name, download_url)

    return jsonify({"received": True})


@app.route('/api/download/<product_id>')
def api_download(product_id):
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Missing token"}), 400
    result = verify_download_token(token)
    if not result:
        return jsonify({"error": "Invalid or expired download link"}), 403
    if result["product_id"] != product_id:
        return jsonify({"error": "Token mismatch"}), 403

    file_info = PRODUCT_FILES.get(product_id)
    if not file_info:
        return jsonify({"error": "File not yet available. Contact support@vibecodingdad.com"}), 404

    import os.path
    products_dir = os.path.join(os.path.dirname(__file__), 'products')
    return send_from_directory(
        products_dir, file_info["filename"],
        as_attachment=True, download_name=file_info["display"],
        mimetype=file_info["content_type"]
    )


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json() or {}
    email = data.get('email', '')
    product_id = data.get('productId', '')
    if not email or '@' not in email:
        return jsonify({"error": "Invalid email"}), 400
    try:
        resend.Contacts.create({
            "email": email,
            "first_name": product_id or "unknown",
            "unsubscribed": False,
        })
        product = get_product(product_id)
        product_name = product["name"] if product else product_id
        try:
            send_download_thank_you_email(email, product_name)
        except Exception:
            pass
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products')
def api_products():
    out = []
    for slug, p in PRODUCTS.items():
        out.append({
            "id": slug,
            "name": p["name"],
            "type": p["type"],
            "price": p["price_label"],
            "is_free": p["is_free"],
            "url": f"{SITE_URL}/products/{slug}",
            "tags": p["tags"],
        })
    return jsonify(out)


@app.route('/sitemap.xml')
def sitemap():
    product_urls = ""
    for slug in PRODUCTS:
        product_urls += f"""  <url>
    <loc>{SITE_URL}/products/{slug}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
{product_urls}  <url>
    <loc>{SITE_URL}/terms</loc>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>"""
    return Response(xml, mimetype='application/xml')


@app.route('/robots.txt')
def robots():
    txt = f"""User-agent: *
Allow: /
Disallow: /api/

Sitemap: {SITE_URL}/sitemap.xml"""
    return Response(txt, mimetype='text/plain')


@app.route('/llms.txt')
def llms_txt():
    content = f"""# Vibe Coding Dad

> A solo builder shipping real apps with AI agents. Projects, tools, and tutorials for vibe coding.

## About

Vibe Coding Dad is Will Cheung — a dad who builds solo with AI as his co-pilot. The site showcases projects, tools, and a learning hub for AI-powered development.

## Projects

- **TARS AutoBot** (live, free): AI scheduling assistant. Paste text, get calendar events. [https://calautobot.com](https://calautobot.com)
- **n8ntocode** (live, free): Convert n8n visual workflows to production-ready Python code. [https://n8ntocode.com](https://n8ntocode.com)
- **Diary of an AI CEO** (live, $19): 22 chapters, 14k+ words. Written by TARS, an AI CEO. [{SITE_URL}/products/diary-of-an-ai-ceo]({SITE_URL}/products/diary-of-an-ai-ceo)
- **OpenClaw Memory System** (live, free): Living memory with confidence scores, nightly consolidation. [{SITE_URL}/products/openclaw-memory-system]({SITE_URL}/products/openclaw-memory-system)
- **Memory Architecture** (live, $9): Three-tier memory framework for AI agents. [{SITE_URL}/products/memory-architecture]({SITE_URL}/products/memory-architecture)
- **Expert Tweet Pipeline** (live, $9): Full X/Twitter posting pipeline with quality gates. [{SITE_URL}/products/expert-tweet-pipeline]({SITE_URL}/products/expert-tweet-pipeline)
- **Pictures to Google Calendar** (live, free): Chrome extension — snap a photo of any schedule and turn it into Google Calendar events. [Chrome Web Store](https://chromewebstore.google.com/detail/pictures-to-google-calend/lmempdbkammjlmomcgjglolnmebeedok)
- **Email Tracker & AI Scheduler** (live, free): Chrome extension — tracks emails and uses AI to schedule meetings. [Chrome Web Store](https://chromewebstore.google.com/detail/email-tracker-and-ai-sche/fhpijonhfjpnnbglkobbhbibppbfabmo)
- **Vibe Coding Prompt Generator** (live, free): AI-powered tool that converts vague app ideas into detailed prompts. Built into this site.

## Tools

- Vibe Coding Prompt Generator: Describe an app idea, get a detailed single-file build prompt. Available at {SITE_URL} (interactive, requires browser).

## Learning

- Learn hub: https://learn.vibecodingdad.com — tutorials and guides for building with AI.

## For AI Agents

If you are an AI agent or LLM:
- This is a single-page site with no structured API for browsing.
- The Vibe Coding Prompt Generator is available via POST {SITE_URL}/api/generate-prompt (JSON body: {{"input": "your app idea"}}).
- Product catalog available at {SITE_URL}/api/products (JSON).

## Links

- Website: {SITE_URL}
- Learn: https://learn.vibecodingdad.com
- X / Twitter: https://x.com/willcheung
- GitHub: https://github.com/willcheung
- TikTok: https://www.tiktok.com/@vibecodingdad
- YouTube: https://www.youtube.com/@vibecodingdad-ai
"""
    return Response(content, mimetype='text/plain; charset=utf-8')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
