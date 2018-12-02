import time
import random
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from io import BytesIO
import json

def get_image(class_name):
    """
    下载并还原极验的验证图
    Args:
        class_name: 验证图所在的html标签的class name
    Returns:
        返回验证图
    Errors:
        IndexError: list index out of range. ajax超时未加载完成，导致image_slices为空
    """
    image_slices = driver.find_elements_by_class_name(class_name)
    if len(image_slices) == 0:
        print('No such a class')
    div_style=image_slices[0].get_attribute('style')
    image_url = re.findall("background-image: url\(\"(.*)\"\)",div_style)[0]
    image_url = image_url.replace("webp","jpg")
    
    location_list = []
    for image_slice in image_slices:
        location = {}
        img_style = image_slice.get_attribute('style')
        location['x'] = int(re.findall("background-position: (.*)px (.*)px;", img_style)[0][0])
        location['y'] = int(re.findall("background-position: (.*)px (.*)px;", img_style)[0][1])
        location_list.append(location)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
    response = requests.get(image_url, headers=headers)
    
    
    
    image = Image.open(BytesIO(response.content))
    image = recover_image(image,location_list)
    return image

def recover_image(image,location_list):
    """
    还原验证图像
    Args:
        image: 打乱的验证图像（PIL.Image数据类型）
        location_list: 验证图像每个碎片的位置
    Returns:
       还原过后的图像
    """
    new_im = Image.new('RGB', (312,116))
    im_list_upper = []  # 上半部分图像
    im_list_down = []   # 下半部分图像
    # 图像坐标系统为横轴左边为0，纵轴上面为0
    for location in location_list:
        if location['y'] == -58:
            # img.crop 参数为图像左上右下坐标
            im_list_upper.append(image.crop((abs(location['x']), 58, abs(location['x']) + 10, 116)))
        if location['y'] == 0:
            im_list_down.append(image.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))
    
    # 拼接上半部分
    x_offset = 0
    for im in im_list_upper:
        # img.paste 参数为图像和二元组，二元组为横坐标和纵坐标
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    # 拼接下半部分
    x_offset = 0
    for im in im_list_down:
        new_im.paste(im, (x_offset, 58))
        x_offset += im.size[0]
        
    return new_im


def get_diff_x(image1,image2):
    """
    计算验证图的缺口位置（x轴）
    两张原始图的大小都是相同的260*116，那就通过两个for循环依次对比每个像素点的RGB值，
    如果RGB三元素中有一个相差超过50则就认为找到了缺口的位置
    Args:
        image1: 图像1
        image2: 图像2
    Returns:
        x_offset
    """
    for x in range(0, 312):
        for y in range(0, 116):
            if not __is_similar(image1, image2, x, y):
                return x


def __is_similar(image1, image2, x_offset, y_offset):
    """
    判断image1, image2的[x, y]这一像素是否相似，如果该像素的RGB值相差都在50以内，则认为相似。
    Args:
        image1: 图像1
        image2: 图像2
        x_offset: x坐标
        y_offset: y坐标
    Returns:
       boolean
    """
    # img.getpixel 获取像素值
    pixel1 = image1.getpixel((x_offset, y_offset))
    pixel2 = image2.getpixel((x_offset, y_offset))
    for i in range(0, 3):
        if abs(pixel1[i] - pixel2[i]) >= 50:
            return False
    return True

def get_track(x_offset):

    track = []
    length = x_offset - 8
    x = random.randint(1, 4)
    
    while length - x > 4:
        track.append(x)
        length = length - x
        x = random.randint(1, 12)

    for i in range(length):
        track.append(1)
    return track

def simulate_drag(track):
    div_slider = driver.find_element_by_xpath('//*[@id="gc-box"]/div/div[3]/div[2]')
    # click_and_hold 点击鼠标左键，不松开, perform()执行所有动作
    ActionChains(driver).click_and_hold(on_element=div_slider).perform()
    
    for x in track:
        ActionChains(driver).move_to_element_with_offset(
            to_element = div_slider,
            xoffset = x+22,     # 滑块大小44*44，所以x+22
            yoffset = 0).perform()
        time.sleep(0.05)
    
    time.sleep(1)
    # release 在某个元素位置松开鼠标左键
    ActionChains(driver).release(on_element=div_slider).perform()
    time.sleep(1)
    dom_div_gt_info = driver.find_element_by_class_name('gt_info_type')
    return dom_div_gt_info.text

def logging(username,password):
    flag_success = False
    while not flag_success:
        image_full_bg = get_image("gt_cut_fullbg_slice")
        # 下载完整的验证图
        image_bg = get_image("gt_cut_bg_slice")
        # 下载有缺口的验证图
        diff_x = get_diff_x(image_full_bg, image_bg)
        track = get_track(diff_x)
        result = simulate_drag(track)
        print(result)
        
        if '验证通过' in result:
            flag_success = True
            print('成功')
        elif '验证失败:' in result:
            time.sleep(4)
            continue
        elif '再来一次' in result:
            time.sleep(4)
            continue
        else:
            break
        
username = '15827365779'
password = 'ly980620..'

driver = webdriver.Chrome()
driver.set_page_load_timeout(20)
driver.implicitly_wait(10)
driver.get("https://passport.bilibili.com/login")
input_id = driver.find_element_by_id("login-username")
input_keyword = driver.find_element_by_id("login-passwd")
input_id.send_keys(username)
time.sleep(1)
input_keyword.send_keys(password)
logging(username,password)

cookie_list = driver.get_cookies()
len(cookie_list)
cookie_dict = {}
for cookie in cookie_list:
    if 'name' in cookie and 'value' in cookie:
        cookie_dict[cookie['name']] = cookie['value']

with open('cookie_dict.txt', 'w') as f:
    json.dump(cookie_dict, f)
