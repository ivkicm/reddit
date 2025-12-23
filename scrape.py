import requests
from datetime import datetime
import pytz
import os
import html

def get_reddit_posts():
    # r/boxoffice neue Beiträge
    url = "https://www.reddit.com/r/boxoffice/new.json?limit=15"
    
    # Reddit verlangt einen User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DashboardBot/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        posts = []
        tz = pytz.timezone('Europe/Berlin')
        
        for post in data['data']['children']:
            p = post['data']
            
            # Filter: Keine Werbung, keine Stickies
            if p.get('is_ad') or p.get('stickied'):
                continue
                
            # Bild-Logik
            image_url = None
            # 1. Prüfen ob es ein direktes Bild ist
            if p.get('post_hint') == 'image' or p.get('url', '').endswith(('.jpg', '.png', '.webp')):
                image_url = p.get('url')
            # 2. Prüfen ob es eine Vorschau gibt (wichtig für Links)
            elif 'preview' in p and 'images' in p['preview']:
                image_url = p['preview']['images'][0]['source']['url']
            
            # Reddit verschlüsselt & in URLs in der API oft als &amp;
            if image_url:
                image_url = html.unescape(image_url)

            dt = datetime.fromtimestamp(p['created_utc'], pytz.utc).astimezone(tz)
            
            posts.append({
                'title': p['title'],
                'author': p['author'],
                'image': image_url,
                'time_str': dt.strftime("%H:%M"),
                'time_obj': dt
            })
            
            if len(posts) >= 6: break # Wir brauchen nur 6 für 60 Sekunden
            
        return posts
    except Exception as e:
        print(f"Reddit Error: {e}")
        return []

def generate_html(posts):
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    slides_html = ""
    for i, item in enumerate(posts):
        active_class = "active" if i == 0 else ""
        
        # Falls kein Bild da ist, nutzen wir ein neutrales dunkles Hintergrundbild oder Farbe
        if item['image']:
            img_html = f'<img src="{item["image"]}" alt="Reddit Image">'
        else:
            img_html = '<div class="no-image-placeholder"><span>r/boxoffice</span></div>'

        slides_html += f"""
        <div class="slide {active_class}">
            <div class="image-container">
                {img_html}
                <div class="img-overlay"></div>
            </div>
            <div class="content-box">
                <div class="meta-line">
                    <span class="source">REDDIT r/BOXOFFICE</span>
                    <span class="pub-time">{item['time_str']} UHR</span>
                    <span class="author">u/{item['author']}</span>
                </div>
                <div class="title">{item['title']}</div>
            </div>
        </div>
        """

    html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit BoxOffice Radar XXL</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@800;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        body, html {{ 
            margin: 0; padding: 0; width: 100%; height: 100%; 
            background-color: black; color: white; font-family: 'Inter', sans-serif;
            overflow: hidden;
        }}
        
        .header-info {{
            position: fixed; top: 15px; right: 20px; z-index: 100;
            background: rgba(255, 69, 0, 0.9); color: white;
            padding: 5px 15px; border-radius: 8px;
            font-family: 'JetBrains Mono'; font-size: 1.3rem;
            font-weight: 800;
        }}

        .slide {{
            position: absolute; width: 100%; height: 100%;
            display: none; flex-direction: column;
        }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}

        .image-container {{ 
            width: 100%; height: 55vh; position: relative; overflow: hidden; background: #111;
        }}
        
        .image-container img {{ 
            width: 100%; height: 100%; 
            object-fit: contain; /* Contain bei Reddit besser, da Bilder oft versch. Formate haben */
            background: #050505;
        }}

        .no-image-placeholder {{
            width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
            background: #1a1a1a; font-size: 5rem; font-weight: 900; color: #333; text-transform: uppercase;
        }}

        .img-overlay {{
            position: absolute; bottom: 0; left: 0; width: 100%; height: 20%;
            background: linear-gradient(to top, black, transparent);
        }}

        .content-box {{ 
            flex: 1; padding: 25px 60px; 
            background: black;
            display: flex; flex-direction: column; justify-content: flex-start;
            padding-top: 30px;
        }}

        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #FF4500; font-weight: 900; font-size: 2.5rem; letter-spacing: 2px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 2.2rem; font-weight: 800; }}
        .author {{ color: #555; font-size: 1.8rem; font-weight: 700; }}

        .title {{ 
            font-size: 4rem; font-weight: 900; line-height: 1.1; 
            text-transform: uppercase; letter-spacing: -1px;
            display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
            color: #eee;
        }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
</head>
<body>
    <div class="header-info">STAND: {now}</div>
    {slides_html}

    <script>
        const slides = document.querySelectorAll('.slide');
        let current = 0;
        
        function nextSlide() {{
            if (slides.length <= 1) return;
            slides[current].classList.remove('active');
            current = (current + 1) % slides.length;
            slides[current].classList.add('active');
        }}

        setInterval(nextSlide, 10000); 
        setTimeout(() => {{ location.reload(); }}, 1800000);
    </script>
</body>
</html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    posts = get_reddit_posts()
    if posts:
        generate_html(posts)
