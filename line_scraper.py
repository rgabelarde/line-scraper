# Import required packages
# Basic Python Packages
import asyncio
import os
import re
import sys
import time
from typing import DefaultDict

# External Packages
import lxml
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver  # for webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def scrape_user(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(),
                              options=chrome_options)

    driver.get(url)

    # Scroll all the way down to the bottom in order to get all the
    # elements loaded (since weibo dynamically loads them).
    driver.execute_script(
        'window.scrollTo(0, document.documentElement.scrollHeight);')

    # Wait to load everything thus far.
    time.sleep(2)

    #Selenium hands the page source to Beautiful Soup
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    soup_user_pic = soup.find(class_='thumb_profile')
    user_img_url = soup_user_pic.find(class_='image_profile')['src']

    soup_user_info = soup.find(class_='profile_info')
    username = soup_user_info.h1.get_text()
    num_of_friends = soup_user_info.find(
        class_='profile_friends').get_text().split(' ')[-1]
    user_bio = soup_user_info.find(class_='profile_label').get_text()
    user_link = ''.join([
        link.get_text() for link in soup_user_info.find(
            class_='profile_info_text').find_all('a')
    ])

    soup_posts = soup.find(class_='content')
    mixed_media_url = "https://page.line.me" + soup_posts.find(
        id='plugin-media-225144988600299').a['href']

    soup_signboard = soup.find(id='plugin-signboard-77911391624927')
    signboard_url = 'https://page.line.me' + soup_signboard.find(
        class_='link')['href']
    signboard_title = soup_signboard.a.h2.get_text()
    signboard_text = soup_signboard.div.find(class_='text_desc').get_text()

    soup_categories = soup.find(id='plugin-showcase-77911021523596')
    categories_url = 'https://page.line.me' + soup_categories.find(
        class_='link')['href']
    categories_img_urls = [
        category['src'] for category in soup_categories.find(
            class_='view_type').find_all('img')
    ]
    categories_titles = [
        category.get_text() for category in soup_categories.find(
            class_='view_type').find_all(class_='collection_title')
    ]
    categories_desc = [
        category.get_text() for category in soup_categories.find(
            class_='view_type').find_all(class_='collection_detail')
    ]

    soup_hyperlinks = soup.find(id='plugin-info-6772949')
    hyperlinks = [link['href'] for link in soup_hyperlinks.find_all('a')]

    res = {
        'user_img_url': user_img_url,
        'username': username,
        'num_of_friends': num_of_friends,
        'user_bio': user_bio,
        'user_url': user_link,
        'mixed_media_url': mixed_media_url,
        'signboard_url': signboard_url,
        'signboard_title': signboard_title,
        'signboard_text': signboard_text,
        'categories_url': categories_url,
        'categories_img_urls': categories_img_urls,
        'categories_titles': categories_titles,
        'categories_desc': categories_desc,
        'hyperlinks': hyperlinks
    }
    return res


def scrape_media_urls(url, username):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('../webdrivers/chromedriver',
                              options=chrome_options)

    driver.get(url)

    # Scroll all the way down to the bottom in order to get all the
    # elements loaded (since weibo dynamically loads them).
    driver.execute_script(
        'window.scrollTo(0, document.documentElement.scrollHeight);')

    time.sleep(2)

    #Selenium hands the page source to Beautiful Soup
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    soup_photos = soup.find_all(class_='photo_item')
    soup_videos = soup.find_all(class_='photo_item ico_video')

    photos_urls = [
        'https://page.line.me' + photo.a['href'] for photo in soup_photos
    ]

    videos_urls = [
        'https://page.line.me' + video.a['href'] for video in soup_videos
    ]

    posts_df = pd.DataFrame({
        'post_url': photos_urls,
        'username': [username] * len(photos_urls),
        'post_type': ['photo'] * len(photos_urls)
    })

    video_info_df = pd.DataFrame({
        'post_url': videos_urls,
        'username': [username] * len(videos_urls),
        'post_type': ['video'] * len(videos_urls)
    })
    posts_df.update(video_info_df)

    print("done scraping mixed media urls")
    return posts_df


def scrape_media(url):
    res = {
        'username': "",
        'post_url': url,
        'post_desc': "",
        'num_of_likes': "",
        'num_of_comments': ""
    }

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('../webdrivers/chromedriver',
                              options=chrome_options)

    driver.get(url)

    # Scroll all the way down to the bottom in order to get all the
    # elements loaded (since weibo dynamically loads them).
    driver.execute_script(
        'window.scrollTo(0, document.documentElement.scrollHeight);')

    time.sleep(2)

    #Selenium hands the page source to Beautiful Soup
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    soup_view = soup.find(class_='viewer')
    if soup_view['data-js-gallery-mode'] is not None:
        soup_view['data-js-gallery-mode'] = 'info'

    soup_username = soup.find(class_='user_title')
    soup_post_desc = soup.find(class_='desc')
    soup_num_of_likes = soup.find(class_='btn_like')
    soup_num_of_comments = soup.find(class_='btn_comment')

    if soup_username is not None:
        res['username'] = soup_username.get_text()
    if soup_post_desc is not None:
        res['post_desc'] = soup_post_desc.get_text()
    if soup_num_of_likes is not None:
        res['num_of_likes'] = soup_num_of_likes.get_text().split(' ')[0]
    if soup_num_of_comments is not None:
        res['num_of_comments'] = soup_num_of_comments.get_text().split(' ')[0]
    return res


if __name__ == '__main__':
    input_df = pd.read_excel(r'./line_user_urls.xlsx')

    # Scrape user info from excel sheet of LINE user URLs
    users_info_df = pd.DataFrame(map(scrape_user, input_df['URL']))
    users_info_df.to_excel(r'line_user_info_output.xlsx', index=False)

    # Scrape users' mixed media info [NOTE: to optimise]
    posts_df = pd.DataFrame()
    for i, v in users_info_df.iterrows():
        posts_df = pd.concat(
            [posts_df,
             scrape_media_urls(v['mixed_media_url'], v['username'])])
    posts_df.drop_duplicates(keep="first", inplace=True)
    posts_df.to_excel(r'line_user_media_output.xlsx', index=False)

    # Scrape each mixed media info further (more info)
    media_info_df = pd.concat(
        [posts_df,
         pd.DataFrame(map(scrape_media, posts_df['post_url']))])
    media_info_df.drop_duplicates(keep="first", inplace=True)
    media_info_df.to_excel(r'line_media_output.xlsx', index=False)
