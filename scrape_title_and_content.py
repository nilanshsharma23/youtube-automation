import json
import os
from pathlib import Path
import shutil
import requests
from bs4 import BeautifulSoup
from movie import generate_movie
import screenshot_post
import wave
from piper import PiperVoice

def scrape_subreddit_content(subreddit, limit = 10, comment_limit = 10):
    url = f"https://old.reddit.com/r/{subreddit}"
    headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}
    session = requests.session()
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    voice = PiperVoice.load("en_US-sam-medium.onnx")

    posts = []

    if not os.path.exists('videos'):
        os.makedirs('videos')

    post_count = 0
    for post in soup.find_all('div', class_='thing'):
        if post_count >= limit:
            break

        if "stickied" in post.get("class"):
            continue

        if not post.get("data-url").startswith("/r/"):
            continue
        
        post_response = session.get(f"https://old.reddit.com{post.get("data-url")}", headers=headers)
        post_soup = BeautifulSoup(post_response.content, 'html.parser')
        title = post_soup.find('a', class_="title").get_text()
        print("title:", title)

        comment_count = 0

        if not os.path.exists(f"posts/{post_count}/comments"):
            os.makedirs(f"posts/{post_count}/comments")

        with wave.open(f"posts/{post_count}/title.wav", "wb") as wav_file:
            voice.synthesize_wav(title, wav_file)
        
        comments = []

        for comment in post_soup.find_all('div', class_="comment"):
            if comment_count >= comment_limit:
                break

            if comment.find("div", class_="md").find("p") == None:
                continue

            if "child" in comment.parent.parent.get("class"):
                continue

            comment_content = comment.find("div", class_="md").find("p").get_text()
            comments.append(comment_content)
            
            with wave.open(f"posts/{post_count}/comments/{comment_count}.wav", "wb") as comment_wave_file:
                voice.synthesize_wav(comment_content, comment_wave_file)

            comment_count += 1
        
        post_content = {
            'title': title,
            'comments': comments,
        }

        posts.append(post_content)

        screenshot_post.screenshot_post(post.get("data-url"), post_count, limit)

        post_count += 1
    
    posts_json = {
        'posts': posts
    }

    Path('posts/data.json').write_text(json.dumps(posts_json))
    generate_movie()
    shutil.rmtree('posts/')