import json
from typing import List
import telebot
import re
import requests
import folium
import imgkit
import os
from folium import utilities
from playwright.async_api import async_playwright
import asyncio


API_KEY = 'AIzaSyBKVifTlAJaYDLJp3XqxvoafpJrwxSmgpg'
bot: telebot.TeleBot = telebot.TeleBot('7124496647:AAGWgXSdPflprdi2i-srWjNr5iuBgbEnulY')


@bot.message_handler(commands=['start'])
def main(message) -> None:
    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}, I am a bot that can analyze messages and show road hazards. ')


@bot.message_handler(commands=['map'])
def send_map(message):
    asyncio.run(save_screenshot_from_map())
    with open("screenshot.jpg", 'rb') as html_file:
        bot.send_photo(message.chat.id, html_file)

@bot.message_handler(func=lambda message: True)
def analyze_message(message) -> None:
    """Перевіряємо та зберігаємо адреси"""
    found_addresses: List[str] = extract_addresses(message.text)
    if found_addresses:
        save_message(message.text)
        test()
        bot.reply_to(message, "Message with address saved!")
    else:
        bot.reply_to(message, "No address found in the message.")


def extract_addresses(text: str) -> List[str]:
    """Витягуємо повідомлення та перевіряємо наявність адрес"""
    address_pattern: str = r'((?:\b(?:м\.|місто|с\.|селище|село|вул(?:иця)?|вулиця|пров\.|провулок|пл\.|площа|бул\.|бульвар|просп\.|проспект|пер\.|перехрестя|шосе|туп\.|тупик|алея|пр-т\.|проїзд|наб\.|набережна|город|пром\.|променад|пр\.|провулок)\.?\s*)+[А-ЯҐЄІЇа-яґєії.,\s\d]+(?:\s*(?:кв\.)?\s*\d+)?)'
    matches_with_context: str = re.findall(address_pattern, text, re.IGNORECASE)
    return matches_with_context


def save_message(message_text: str) -> None:
    """Зберігає повідомлення у JSON файлі"""
    try:
        with open("messages.json", "r", encoding="utf-8") as file:
            all_messages: List[str] = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        all_messages: List[str] = []

    all_messages.append({"message": message_text})

    with open("messages.json", "w", encoding="utf-8") as file:
        json.dump(all_messages, file, ensure_ascii=False, indent=4)
        
        
"""Функція нанесення міток на карту"""
   
def get_geolocation(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK' and 'results' in data:
            location = data['results'][0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            print(f"adress= {address} || x= {latitude} y= {longitude}")
            return latitude, longitude
        else:
            print(f"No results found for address: {address}")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def add_marker_to_map(map, coordinates, label=None):
    folium.Marker(coordinates, popup=label).add_to(map)

# Завантаження даних з JSON-файлу
def test():
    with open('messages.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

# Створення карти
    mymap = folium.Map(location=[50.6199, 26.2516],zoom_start=10)

    # Проходимо по всіх адресах з файлу і ставимо мітки на карту
    for item in data:
        address = item['message']
        coordinates = get_geolocation(address, API_KEY)
        if coordinates:
            label = "Мітка"  
            add_marker_to_map(mymap, coordinates, label)


    mymap.save('map.html') 

async def save_screenshot_from_map():
    html = ''
    with open("map.html", "r", encoding="utf-8") as file:
        html = file.read()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        with utilities.temp_html_filepath(html) as fname:
            await page.goto(f'file:///C:/Users/drlys/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/telegram-bot/map.html')
        await page.screenshot(path='screenshot.jpg', type='jpeg', full_page=True)
        await browser.close()


bot.polling(none_stop=True)
