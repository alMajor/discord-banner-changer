from PIL import ImageFont, ImageDraw, Image
import os
import datetime
import json
import base64
import requests
import time
import io
from pytz import timezone
import random
import math
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
DELAY = os.getenv("DELAY")
BASE_URL = os.getenv("BASE_URL")
TIMEZONE = os.getenv("TIMEZONE")
COLOR_COMPONENT_SIMILARITY_THRESHOLD = 50
COLOR_BRIGHTNESS_THRESHOLD = 0.8
COLOR_DARKNESS_THRESHOLD = 0.2



def _get_distance(a_x, a_y, b_x, b_y):
    return math.sqrt(math.pow(a_x - b_x, 2) + math.pow(a_y - b_y, 2))


def _mix_colors(colors, weights):
    assert len(colors) == len(weights)

    components = [[], [], []]

    for c in colors:
        for i, v in enumerate(c):
            components[i].append(v)

    color = [0, 0, 0]

    weights_sum = sum(weights)

    for i, v in enumerate(components):
        mixed_c = 0
        for ci, c in enumerate(v):
            mixed_c += c * weights[ci]

        mixed_c = mixed_c / weights_sum

        color[i] = int(mixed_c)

    return tuple(color)


def _get_random_color():
    def get_components():
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

    while True:
        color = get_components()

        if COLOR_DARKNESS_THRESHOLD < (color[0] + color[1] + color[2]) / (255 * 3) < COLOR_BRIGHTNESS_THRESHOLD:
            break

    return color


def _get_different_color(ref_color):
    is_similar = True

    while is_similar:
        new_color = _get_random_color()

        is_similar = False
        for i, v in enumerate(new_color):
            if abs(v - ref_color[i]) < COLOR_COMPONENT_SIMILARITY_THRESHOLD:
                is_similar = True

    return new_color


def _get_random_color_pt(w, h):
    axis = random.choice(['x', 'y'])

    if axis == 'x':
        return random.randint(0, w), 0, _get_random_color()

    return 0, random.randint(0, h), _get_random_color()

def color_contrast(color):
    d = 0     
    luminance = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])/255
    if luminance > 0.5:
        d = 0 # bright colors - black font
    else:
        d = 255 # dark colors - white font
    return (d, d, d)


def generate_gradient(width: int, height: int):
    w = int(width / 10)
    h = int(height / 10)

    pt = _get_random_color_pt(w, h)
    color_pts = [pt, (w - pt[0], h - pt[1], _get_different_color(pt[2]))]

    data = []

    for x in range(h):
        for y in range(w):
            colors = [pt[2] for pt in color_pts]

            distances = [_get_distance(x, y, pt[0], pt[1]) for pt in color_pts]

            min_dist = min(distances)
            max_dist = max(distances)

            weights = [min_dist + max_dist - d for d in distances]

            color = _mix_colors(colors, weights)
            fntcolor = color_contrast(color)
            data.append((color[0], color[1], color[2], 255))

    im = Image.new('RGBA', (w, h))
    im.putdata(data)
    
    return im,fntcolor

now_time = datetime.datetime.now(timezone(str(TIMEZONE)))
currtime = now_time.strftime('%I:00 %p')
currdate = now_time.strftime("%B %d, %Y")
currday = now_time.strftime("%A")


def center_text(img, W, H, font, text, color=(255, 255, 255)):
    draw = ImageDraw.Draw(img)
    text_width, text_height = draw.textsize(text, font)
    position = ((W-text_width)/2,(H-text_height)/2)
    draw.text(position, text, color, font=font)
    return img
    
def create_image(size):
    W, H = size
    fontsize = 1
    img_fraction = 0.6

    image,fontColor = generate_gradient(680,240)
    image = image.resize((680,240), Image.LANCZOS)
    output = io.BytesIO()
    image.save(output, 'png')
    output.seek(0)

    font = ImageFont.truetype("Monoton.ttf", fontsize)
    while font.getsize(currdate)[0] < img_fraction*image.size[0]:
        fontsize += 1
        font = ImageFont.truetype("Monoton.ttf", fontsize)
    fontsize -= 1

    MonoL = ImageFont.truetype("Monoton.ttf", fontsize)
    MonoS = ImageFont.truetype("Monoton.ttf", fontsize//2)
    DipL = ImageFont.truetype("dip.ttf", fontsize//3)
    DipS = ImageFont.truetype("dip.ttf", fontsize//5)


    center_text(image, W/4.12, H/3.8, DipL, "Hello i'm",fontColor)
    center_text(image, W/1.02, H/1.83, MonoL, 'Abdulrahman',fontColor)
    center_text(image, W/2.02, H*0.95, DipL, 'Hobbyist software developer.',fontColor)
    center_text(image, W*1.75, H/2.95, DipL, 'AKA: alMajor',fontColor)

    center_text(image, W*1.13, H*1.55, DipS, 'My local time:',fontColor)
    center_text(image, W*1.13, H*1.75, MonoS, ''+currtime+'',fontColor)
    center_text(image, W*2, H*1.87, DipS, 'Made with ♥ by alMajor',fontColor)
    return image

myImage = create_image((600,240))
myImage.save('banner.png', "PNG")

current = 0
while True:
    time.sleep(int(DELAY))
    if datetime.datetime.now().hour != current:
        current = datetime.datetime.now().hour
        myImage = create_image((600,240))

        myImage.save('banner.png', "PNG")
        with open("banner.png", "rb") as image_file:
            b64_image = base64.b64encode(image_file.read())

        payload = {
            "banner": f"data:image/{'.png'};base64,{b64_image.decode()}"
        }

        headers = {
            'Accept': '*/*',
            'Authorization': f'{str(TOKEN)}',
            'Content-Type': 'application/json'
        }
        r = requests.patch(f'{str(BASE_URL)}/users/@me', data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            print ('Changed!')
        else:
            print ('Error', r.status_code)




