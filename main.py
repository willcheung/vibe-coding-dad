import os
import requests
from flask import Flask, render_template, request, jsonify, Response

app = Flask('app', static_folder='public/static', static_url_path='/static')

SITE_URL = "https://vibecodingdad.com"

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


@app.route('/sitemap.xml')
def sitemap():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
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

- **CalAutobot** (live, free): AI scheduling assistant. Paste text, get calendar events. [https://calautobot.com](https://calautobot.com)
- **calmart.ai** (live): Digital products built and sold by Cal, an AI CEO. [https://calmart.ai](https://calmart.ai)
- **n8ntocode** (live, free): Convert n8n visual workflows to production-ready Python code. [https://n8ntocode.com](https://n8ntocode.com)
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
- For Cal's products, visit https://calmart.ai/api/products (JSON) or https://calmart.ai/llms.txt.

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
