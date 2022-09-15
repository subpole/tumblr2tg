import asyncio
import aiocron
import requests
import json
import random
from bs4 import BeautifulSoup as soup

print("@@@@@@@@@@@@@@@@@@@@@@@@@@ start @@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
def save_seen_posts():
    with open('seen_posts.json', 'w') as outfile:
        outfile.write(json.dumps({'post_id': SEEN_POSTS}))

def get_seen_posts():
    try:
        with open('seen_posts.json') as json_file:
            try:
                data = json.load(json_file)
                seen_posts = data['post_id']
            except:
                seen_posts = {}
    except:
        seen_posts = {}
    return seen_posts

def get_channels_to_send(conf):
    tumblr_api_token = conf['tumblr']['api_token'] 
    base_tumblr_url = 'https://api.tumblr.com/v2/'
    channels_to_send = []

    for channel_id, conf in conf['config']['channels'].items():
        sources = []
        for source in conf['tumblr_sources']:
            if source['type'] == 'tag':
                url = f"{base_tumblr_url}tagged?tag={source['name']}&api_key={tumblr_api_token}"

            elif source['type'] == 'blog':
                url = f"{base_tumblr_url}blog/{source['name']}/posts?api_key={tumblr_api_token}"
            source['url'] = url
            sources.append(source)

        channel_conf = {
            'channel_id': channel_id,
            'cron': conf['cron'],
            'tumblr_sources': sources,
        }
        channels_to_send.append(channel_conf)
        if channel_id not in SEEN_POSTS:
            SEEN_POSTS[channel_id] = []
    return channels_to_send

# Getting conf data
try:
    with open('config.json') as json_file:
        config = json.load(json_file)
except FileNotFoundError:
    print('Create config.json file!!!!')
    open('config.json', 'a')

TG_ADMIN_ID = config['config']['admin']
TG_BOT_TOKEN = config['telegram']['bot_token']
TUMBLR_API_TOKEN = config['tumblr']['api_token']

SEEN_POSTS = get_seen_posts()
CHANNELS_TO_SEND = get_channels_to_send(config)

def send_post_to_tg(post={},channel={'channel_id': TG_ADMIN_ID}):
    request_to_make = get_message_request_data(post, channel['channel_id'])

    for rq in request_to_make:
        response = requests.post(rq['url'], data=rq['params'])
        response = json.dumps(response.json())
        print("#################request made#######################")
        print(response[0:235])
        # print(response)

    SEEN_POSTS[channel['channel_id']].append(post['id_string'])
    save_seen_posts()

# ------------------------------------ Functions for posts ------------------------------------
def get_post_from_tumblr(ts='',channel={}):
    rand_source = random.choice(channel['tumblr_sources'])
    url = rand_source['url']

    # Checks if url needs timestamp
    if ts != '':
        url = rand_source['url'] + f'&before={ts}'

    # Makes get request to tumbrl
    response = requests.get(url)
    response = json.dumps(response.json())
    response = json.loads(response)

    if response['meta']['status'] in range(200,299):
        # Saves lists of posts from get request
        if rand_source['type'] == 'tag':
            posts_list = response['response']
        elif rand_source['type'] == 'blog':
            posts_list = response['response']['posts']

        # Gets new post to send
        post_to_send = {}
        for post in posts_list:
            if post['id_string'] not in SEEN_POSTS[channel['channel_id']]:
                post_to_send = post
                break

        # If all posts from petition are already sent it calls
        # itself to check the post made before the posts from 
        # this request
        if not post_to_send and len(posts_list)>0:
            post_to_send = get_post_from_tumblr(ts=posts_list[-1]['timestamp'],channel=channel)
    else:
        print(response['meta'])
    
    print("@@@@@@@@@@@@@@@@new post found@@@@@@@@@@@@@@@@@@")
    print(f"https://api.tumblr.com/v2/blog/{post['blog_name']}/posts?id={post['id']}&api_key={TUMBLR_API_TOKEN}")
    
    return post_to_send

def get_message_caption(post):
    post_content, disable_preview = get_post_caption(post)
    post_tags = get_post_tag(post)
    post_url =  f"<a href='{post['short_url']}'>Original post</a>"

    return f'{post_content}{post_tags}{post_url}', disable_preview

def get_post_caption(post):
    caption = ''
    disable_preview = True
    if post['type'] in ['text','photo', 'video']:
        if 'title' in post:
            print("title2")
            if post['title']:
                caption += f"<b>{post['title']}</b>\n\n"
        if 'video_url' in post:
            disable_preview = False
            caption+=f"<a href='{post['video_url']}'>Video</a>\n\n"
        if 'video' in post:
            if 'youtube' in post['video']:
                disable_preview = False
                url_id = post['video']['youtube']['video_id']
                caption += f"<a href='https://www.youtube.com/watch?v={url_id}'>YouTube video</a>\n\n"
        
        if 'caption' in post:
            print('caption')
            body = soup(post['caption'], 'html.parser')
            body_elements = body.find_all()      
        elif 'body' in post:
            print("body")
            body = soup(post['body'], 'html.parser')
            body_elements = body.find_all()
        elif 'trail' in post:
            print("trail")
            if len(post['trail']) > 0:
                trail = soup(post['trail'][0]['content'], 'html.parser')
                body_elements = trail.find_all('p')
                body_elements = body_elements[0]
            
        for element in body_elements:
            if element.name == 'h1' or element.name == 'h2':
                print("title")
                caption += f"<b>{element.text}</b>\n\n"
            if element.name == 'iframe' :
                print('iframe')
                disable_preview = False
                caption += f"<a href='{element.attrs['src']}'>YouTube video</a>\n"
            if element.name == 'figure' :
                print("figure")
                if 'data-npf' in element.attrs:
                    url = json.loads(element.attrs['data-npf'])['url']
                    disable_preview = False
                    caption+=f"<a href='{url}'>Video</a>\n\n"
            if element.name == 'p':
                print("p")
                if element == body_elements[-1]:
                    caption += str(element).replace('<p>','').replace('</p>','').replace('<br/>','\n').replace('\n','')+'\n'
                else: 
                    if element.text:
                        if element.text[len(element.text)-1] == ':':
                            caption += str(element).replace('<p>','').replace('</p>','').replace('<br/>','\n').replace('\n','')+'\n'
                        else:
                            caption += str(element).replace('<p>','').replace('</p>','').replace('<br/>','\n').replace('\n','').strip()+'\n\n'
                    else:
                        caption += str(element).replace('<p>','').replace('</p>','').replace('<br/>','\n').replace('\n','')+'\n\n'
    elif post['type'] == 'audio':
        try:
            caption =  f'{post["track_name"]} - {post["artist"]}\n\n'
        except:
            pass
    elif post['type'] == 'answer':
        asking_name = soup(post['asking_name'], 'html.parser')
        question = soup(post['question'], 'html.parser')
        answer = soup(post['answer'], 'html.parser')
        caption = f'<b>{asking_name.text}:</b>\n{question.text}\n\n<b>Answer:</b>\n{answer.text}\n\n'
        
    return caption+"\n", disable_preview

def get_post_tag(post):
    tag_str = f"#{post['blog_name']} "
    symbols_to_replace = [
        ["'",''],
        ['"', ''],
        ['`', ''],
        ['-', '_'],
        ['!', ''],
        ['¡', ''],
        ['?', ''],
        ['¿', ''],
        ['(', ''],
        [')', ''],
        ['%', ''],
        ['*', ''],
        ['.', ''],
        [',', ''],
        ['\u2019', ''],
        ['|',''],
        ['/',''],
        ['[',''],
        [']',''],
        [':',''],
        [';',''],
        ['+',''],
        ['\\',''],
        ['',''],
        ['',''],
    ]
    if post["type"] == "audio":
        tag_str += "#music "
    if len(post["tags"]) != 0:
        for tag in post["tags"]:
            tag = tag.replace(" ", "_")
            tag_str += f'#{tag} '
    
    tag_str+="\n\n"
    
    # Replace all symbols that break hashtags in telegram
    for symbol in symbols_to_replace:
        tag_str = tag_str.replace(symbol[0], symbol[1])
    
    return tag_str

def get_message_img_url(post):
    url_list = {
        'gif': [],
        'img': []
    }

    urls = []
    if "caption" in post:
        try:
            print("caption2")
            body_tags = soup(post["caption"], 'html.parser')
            img_in_body = body_tags.find_all("img")
            for img in img_in_body:
                urls.append(img["src"])
        except:
            pass
    elif "body" in post:
        try:
            body_tags = soup(post["body"], 'html.parser')
            img_in_body = body_tags.find_all("img")
            for img in img_in_body:
                urls.append(img["src"])
        except:
            pass
    if "photos" in post:
        for img in post["photos"]:
            urls.append(img["original_size"]["url"])
        
    for url in urls:        
        if url.split('.')[-1] == 'gif':
            url_list['gif'].append(url)
        else:
            url_list['img'].append(url)
            
    return url_list

def get_message_request_data(post, channelId):
    caption, disable_preview = get_message_caption(post)

    request_to_make = []
    if post['type'] in ['text','photo', 'video', 'answer']:
        url_list = get_message_img_url(post)
        # Sends a message because the post has no images
        if len(url_list['gif'])+len(url_list['img']) == 0:
            request_url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage' 
            gif_params = {
                'chat_id': channelId,
                'text': caption,
                'parse_mode':'HTML',
                'disable_web_page_preview': disable_preview,
            }
            request_to_make.append({'url':request_url,'params':gif_params})
        # Sends an image 
        else:
            request_url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup' 
            request_url_for_gifs = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendAnimation'
            
            # Telegram does not accept caption with too many characters
            if len(caption) > 700 and len(url_list['gif'])+len(url_list['img']) > 1:
                print('large caption')
                caption_for_img = f"<a href='{post['short_url']}'>Original post</a>"
            else:
                caption_for_img = caption
                 
            for url in url_list['gif']:
                gif_params = {
                    'chat_id': channelId,
                    'animation': url,
                    'caption': caption_for_img,
                    'parse_mode':'HTML',
                    'disable_web_page_preview': disable_preview
                }
                request_to_make.append({'url':request_url_for_gifs,'params':gif_params})
                
                    
            img_params = {
                'chat_id': channelId,
                'media': [],
                'disable_web_page_preview': disable_preview
            }
            
            for url in url_list['img']:
                img_params['media'].append({
                    'type': 'photo',
                    'media': url,
                    'caption': caption_for_img,
                    'parse_mode':'HTML'
                })
            img_params['media'] = json.dumps(img_params['media'])
            
            request_to_make.append({'url':request_url,'params':img_params})

            # When to images are sent in telegram they don't show the caption unless 
            # the images is open, so the bot sends another message with the caption 
            # when the post has 2 images or more
            if len(url_list['img']) > 1:
                request_url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage' 

                gif_params = {
                    'chat_id': channelId,
                    'text': caption,
                    'parse_mode':'HTML',
                    'disable_web_page_preview': disable_preview
                }

                request_to_make.append({'url':request_url,'params':gif_params})
    elif post['type'] == 'audio':
        request_url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup'

        gif_params = {
            'chat_id': channelId,
            'media': [
                {
                'type': 'audio',
                'media': post['audio_url'],
                'caption': caption,
                'parse_mode': 'HTML',
                }
            ],
            'disable_web_page_preview': True
        }

        gif_params['media'] = json.dumps(gif_params['media'])
        request_to_make.append({'url':request_url,'params':gif_params})

    elif post['type'] == 'video':
        pass

    return request_to_make
# ------------------------------------              ------------------------------------
def get_post_via_id(id, blog):
    tumblr_api_token = config['tumblr']['api_token'] 
    base_tumblr_url = 'https://api.tumblr.com/v2/'

    url = f'{base_tumblr_url}blog/{blog}/posts?id={id}&api_key={tumblr_api_token}'
    response = requests.get(url)
    response = json.dumps(response.json())

    response = json.loads(response)
    # print(response['response']['posts'][0])
    print(url)
    print(response)
    return response['response']['posts'][0]

def add_chat(ch):
    pass
    @aiocron.crontab(ch['cron'])
    async def attime():
        new_post = get_post_from_tumblr(channel=ch)
        if len(new_post) != 0:
            send_post_to_tg(post=new_post,channel=ch)

def main():
    for channel in CHANNELS_TO_SEND:
        add_chat(channel)

    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()