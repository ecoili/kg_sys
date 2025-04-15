import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64


class CaptchaGenerator:
    @staticmethod
    def generate_captcha():
        # 生成4位随机字符（字母+数字）
        chars = string.ascii_letters + string.digits
        captcha_text = ''.join(random.choice(chars) for _ in range(4))

        # 创建图片
        image = Image.new('RGB', (120, 40), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 使用字体（注意：需要实际字体文件）
        try:
            font = ImageFont.truetype('arial.ttf', 24)
        except:
            font = ImageFont.load_default(size=24)

        # 绘制文字（添加干扰）
        for i, char in enumerate(captcha_text):
            draw.text((10 + i * 25, 10), char, fill=(random.randint(0, 150),
                                                     random.randint(0, 150),
                                                     random.randint(0, 150)), font=font)

        # 添加干扰线和噪点
        for _ in range(5):
            x1 = random.randint(0, 120)
            y1 = random.randint(0, 40)
            x2 = random.randint(0, 120)
            y2 = random.randint(0, 40)
            draw.line((x1, y1, x2, y2), fill=(200, 200, 200))

        # 转为Base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return captcha_text, 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')
