import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os
import html

def get_reddit_posts():
    # Wir nutzen den RSS-Feed, der wird seltener blockiert
    url = "https://www.reddit.com/r/boxoffice/new/.rss"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Feed laden
        feed = feedparser.parse(url)
        posts = []
        tz = pytz.timezone('Europe/Berlin')
        
        for entry in feed.entries:
            # Bild aus dem Content extrahieren (Reddit versteckt das im HTML des Feeds)
            image_url = None
            if 'summary' in entry:
                soup_content = BeautifulSoup(entry.summary, 'html.parser')
                img_tag = soup_content.find('img')
                if img_tag:
                    image_url = img_tag.get('src')
                
                # Check für Thumbnails, falls kein großes Bild da ist
                if not image_url:
                    thumb = soup_content.find('span', {'class': 'thumbnail'})
                    if thumb and thumb.find('img'):
                        image_url = thumb.find('img').get('src')

            # Zeit formatieren
            dt = datetime(*entry.updated_parsed[:6], tzinfo=pytz.utc).astimezone(tz)
            
            posts.append({
                'title': entry.title,
                'author': entry.author if 'author' in entry else 'r/boxoffice',
                'image': image_url,
                'time_str': dt.strftime("%H:%M"),
                'time_obj': dt
            })
            
            if len(posts) >= 6: break
            
        return posts
    except Exception as e:
        print(f"Reddit RSS Fehler: {e}")
        return []

def generate_html(news):
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz).strftime("%d.%m.%Y - %H:%M")
    
    if not news:
        slides_html = """
        <div class="slide active">
            <div class="content-box">
                <div class="title" style="color: #ff4500;">Reddit blockiert aktuell den Zugriff.<br>Versuche es in 30 Minuten erneut.</div>
            </div>
        </div>
        """
    else:
        slides_html = ""
        for i, item in enumerate(news):
            active_class = "active" if i == 0 else ""
            
            # Falls ein Bild da ist, zeigen wir es an
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
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; background-color: black; color: white; font-family: 'Inter', sans-serif; overflow: hidden; }}
        .header-info {{ position: fixed; top: 15px; right: 20px; z-index: 100; background: rgba(255, 69, 0, 0.9); color: white; padding: 5px 15px; border-radius: 8px; font-family: 'JetBrains Mono'; font-size: 1.3rem; font-weight: 800; }}
        .slide {{ position: absolute; width: 100%; height: 100%; display: none; flex-direction: column; }}
        .slide.active {{ display: flex; animation: fadeIn 0.8s ease-in; }}
        .image-container {{ width: 100%; height: 55vh; position: relative; overflow: hidden; background: #050505; }}
        .image-container img {{ width: 100%; height: 100%; object-fit: contain; object-position: center top; }}
        .no-image-placeholder {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #111; font-size: 5rem; font-weight: 900; color: #222; text-transform: uppercase; }}
        .img-overlay {{ position: absolute; bottom: 0; left: 0; width: 100%; height: 20%; background: linear-gradient(to top, black, transparent); }}
        .content-box {{ flex: 1; padding: 20px 60px; background: black; display: flex; flex-direction: column; justify-content: flex-start; padding-top: 30px; }}
        .meta-line {{ display: flex; gap: 30px; align-items: center; margin-bottom: 20px; }}
        .source {{ color: #FF4500; font-weight: 900; font-size: 2.8rem; letter-spacing: 2px; }}
        .pub-time {{ color: #ffffff; font-family: 'JetBrains Mono'; font-size: 2.8rem; font-weight: 800; }}
        .title {{ font-size: 4.2rem; font-weight: 900; line-height: 1.05; text-transform: uppercase; letter-spacing: -2px; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; color: #f0f0f0; }}
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
    data = get_reddit_posts()
    generate_html(data)
