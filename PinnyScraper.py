# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 10:46:30 2023

@author: jacob
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
from datetime import datetime, timedelta

leagues = {'World Championship Play - In':'https://www.pinnacle.com/en/esports/games/league-of-legends/world-championship-play-in/matchups/#all',
           'Worlds Qualifying Series':'https://www.pinnacle.com/en/esports/games/league-of-legends/world-championship-worlds-qualifying-series/matchups/#all'}

def startScraper():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    browser = webdriver.Chrome(executable_path="C:\ChromeDriver\chromedriver.exe")
    browser.get('chrome://settings/')
    browser.execute_script('chrome.settingsPrivate.setDefaultZoom(.25);')
    #Team names get abbreviated if your browser window is too small, so just zoom so far out that this issue cant happen
    return browser

def parseDate(pin_date, time):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if("TODAY" in pin_date.upper()):
        time = datetime.strptime(time, "%H:%M").time()
        return datetime.combine(today, time)
    elif ("TOMORROW" in pin_date.upper()):
        tomorrow = today + timedelta(days=1)
        time = datetime.strptime(time, "%H:%M").time()
        return datetime.combine(tomorrow, time)
    date_format = "%a, %b %d, %Y %H:%M"
    to_parse = f"{pin_date} {time}"
    return datetime.strptime(to_parse, date_format)

def stopScraper(browser):
    browser.quit()
    
def setAmericanOdds(browser):
    dropdown_class = 'style_dropdown__Ul5rd style_button__2IrNY style_dropDownButton__1xYlx'
    
    browser.find_element_by_xpath(f"//div[@class = '{dropdown_class}']").click()
    time.sleep(.5)
    browser.find_element_by_xpath("//li/a[text()='American Odds']").click()
    time.sleep(.5)

def scrapeMarket(browser):
    match_row_class = "style_row__3xXUg"
    matches = browser.find_elements_by_class_name(match_row_class)
    df_data = []
    for match in matches:
        data = []
        date = match.find_element_by_xpath("preceding-sibling::div[@class='style_dateBar__2KVv3']").text
        time = match.find_element_by_xpath(".//div[@class='style_matchupDate__1st0T']").text
        home_team, away_team = match.find_elements_by_xpath(".//div[@class='ellipsis style_gameInfoLabel__1Lt37']")
        home_moneyline, away_moneyline = match.find_elements_by_xpath(".//div[@class = 'style_buttons__1a73K style_moneyline__2CCDG']//span[@class = 'style_price__1-7o_']")
        spreads_totals = match.find_elements_by_xpath(".//button[@title]")
        spreads_totals_markets = ['HOME HANDICAP','AWAY HANDICAP','OVER','UNDER']
        spreads_totals_labels = ["NOT LISTED"]*4
        spreads_totals_prices = [-9999]*4
        
        for i in range(len(spreads_totals_labels)):
            try:
                label = spreads_totals[i].find_element_by_class_name("style_label__2zBJo").text
                price = spreads_totals[i].find_element_by_class_name("style_price__1-7o_").text
                spreads_totals_labels[i] = label
                spreads_totals_prices[i] = price
            except:
                pass
                # print(f"No data for {spreads_totals_markets[i]}, skipping...")
        timestamp = parseDate(date, time)
        home_listed = home_team.text.upper()
        away_listed = away_team.text.upper()
        data = [timestamp, home_listed, away_listed, home_moneyline.text, away_moneyline.text]
        for m in range(len(spreads_totals_markets)):
            data += [{spreads_totals_labels[m]:spreads_totals_prices[m]}]
        df_data.append(data)
    header = ['Game_Date','Home_Listed','Away_Listed','Home_ML','Away_ML'] + spreads_totals_markets
    return pd.DataFrame(df_data, columns = header)
def scrapeLeague(url,browser):
    browser.get(url)
    markets = browser.find_elements_by_xpath("//div[@class = 'style_filterBarContent__3pNIw']/button[contains(@id, 'period')]")
    dfs = []
    for market in markets:
        market.click()
        time.sleep(.25)
        marketName = market.text
        market_df = scrapeMarket(browser)
        market_df['Market'] = marketName
        market_df['AsOfTime'] = datetime.now()        
        dfs.append(market_df)
    return pd.concat(dfs)

def scrapeAllLeagues(browser):
    dfs = []
    for league, url in leagues.items():
        league_df = scrapeLeague(url,browser)
        league_df['League'] = league
        dfs.append(league_df)
    return pd.concat(dfs)

def run(browser):

    return scrapeAllLeagues(browser)


def scrapePerpetually():
    consecutive_failures = 0
    lastRun = datetime.now() - timedelta(minutes = 6)
    try:
        browser = startScraper()
        browser.get('https://www.pinnacle.com/en/esports/games/league-of-legends/')
        setAmericanOdds(browser)
        while(consecutive_failures < 3):
            now = datetime.now()
            if(lastRun + timedelta(minutes = 5) < now):
                try:
                    scraped_odds = run(browser)
                    lastRun = datetime.now()
                    consecutive_failures = 0
                except:
                    consecutive_failures += 1
            else:
                print("Last run too recent, sleeping for 30s...")
                time.sleep(30)
    except:
        return
    
scrapePerpetually()