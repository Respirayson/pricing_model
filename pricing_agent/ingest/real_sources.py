"""Real web sources for pricing data that can be scraped."""

from typing import List, Dict, Any


def get_real_pricing_sources() -> List[Dict[str, Any]]:
    """
    Get list of real pricing data sources that can be scraped.
    
    Returns:
        List of source configurations with real URLs
    """
    return [
        {
            'id': 'privacy_affairs_2022',
            'url': 'https://privacyaffairs.com/dark-web-price-index-2022/',
            'title': 'Privacy Affairs Dark Web Price Index 2022',
            'date': '2022-01-01',
            'description': 'Comprehensive dark web pricing data from Privacy Affairs'
        },
        {
            'id': 'privacy_affairs_2023',
            'url': 'https://privacyaffairs.com/dark-web-price-index-2023/',
            'title': 'Privacy Affairs Dark Web Price Index 2023',
            'date': '2023-01-01',
            'description': 'Updated dark web pricing data from Privacy Affairs'
        },
        {
            'id': 'comparitech_dark_web_prices',
            'url': 'https://www.comparitech.com/blog/information-security/dark-web-prices/',
            'title': 'Dark Web Prices for Stolen PayPal Accounts and Credit Cards',
            'date': '2021-01-20',
            'description': 'Analysis of dark web marketplace pricing by Comparitech'
        },
        {
            'id': 'crowdstrike_dark_web_explained',
            'url': 'https://www.crowdstrike.com/cybersecurity-101/the-dark-web-explained/',
            'title': 'The Dark Web Explained - CrowdStrike',
            'date': '2025-02-11',
            'description': 'CrowdStrike explanation of dark web with pricing information'
        },
        {
            'id': 'purplesec_ransomware_costs',
            'url': 'https://purplesec.us/resources/cyber-security-statistics/ransomware/',
            'title': 'Average Cost of Ransomware Attacks 2025',
            'date': '2025-05-24',
            'description': 'Ransomware attack costs and dark web pricing data'
        },
        {
            'id': 'socradar_dark_web_report_2024',
            'url': 'https://socradar.io/resources/report/socradar-2024-annual-dark-web-report/',
            'title': 'SOCRadar Dark Web Report 2024',
            'date': '2024-12-01',
            'description': 'SOCRadar comprehensive dark web threat intelligence report'
        },
        {
            'id': 'huntress_data_breach_stats',
            'url': 'https://www.huntress.com/blog/data-breach-statistics',
            'title': 'Data Breach Statistics 2025',
            'date': '2025-01-01',
            'description': 'Huntress data breach statistics and pricing analysis'
        },
        {
            'id': 'prey_project_dark_web_stats',
            'url': 'https://preyproject.com/blog/dark-web-statistics-trends',
            'title': 'Dark Web Statistics & Trends 2025',
            'date': '2025-01-01',
            'description': 'Prey Project analysis of dark web trends and pricing'
        },
        {
            'id': 'deepstrike_dark_web_data_pricing_2025',
            'url': 'https://deepstrike.io/blog/dark-web-data-pricing-2025',
            'title': 'Dark Web Price Index - DeepStrike',
            'date': '2024-01-01',
            'description': 'DeepStrike dark web pricing index and analysis'
        },
        {
            'id': 'moneyzine_dark_web_stats',
            'url': 'https://moneyzine.com/resources/dark-web-statistics/',
            'title': 'Essential Dark Web Statistics for 2025',
            'date': '2025-01-01',
            'description': 'MoneyZine comprehensive dark web statistics'
        }
    ]


def get_news_sources() -> List[Dict[str, Any]]:
    """
    Get list of news sources that report on dark web pricing.
    
    Returns:
        List of news source configurations
    """
    return [
        {
            'id': 'wired_china_surveillance',
            'url': 'https://www.wired.com/story/chineses-surveillance-state-is-selling-citizens-data-as-a-side-hustle/',
            'title': "China's Surveillance State Is Selling Citizen Data as a Side Hustle",
            'date': '2024-11-21',
            'description': 'WIRED article about Chinese surveillance data being sold on black markets'
        },
        {
            'id': 'reuters_china_data_breach',
            'url': 'https://www.reuters.com/world/china/hacker-claims-have-stolen-1-bln-records-chinese-citizens-police-2022-07-04/',
            'title': 'Hacker claims to have stolen 1 bln records of Chinese citizens',
            'date': '2022-07-04',
            'description': 'Reuters report on massive Chinese data breach'
        },
        {
            'id': 'guardian_china_data_breach',
            'url': 'https://www.theguardian.com/technology/2022/jul/04/hacker-claims-access-data-billion-chinese-citizens',
            'title': 'Hacker claims to have obtained data on 1 billion Chinese citizens',
            'date': '2022-07-04',
            'description': 'Guardian report on Chinese data breach'
        },
        {
            'id': 'wired_telegram_purged',
            'url': 'https://www.wired.com/story/telegram-purged-chinese-crypto-scam-markets-then-let-them-rebuild/',
            'title': 'Telegram Purged Chinese Crypto Scam Markets—Then They Regrouped',
            'date': '2025-06-23',
            'description': 'WIRED report on Telegram banning crypto scam markets'
        },
        {
            'id': 'wired_xinbi_guarantee',
            'url': 'https://www.wired.com/story/xinbi-guarantee-crypto-scam-hub/',
            'title': 'An $8.4 Billion Chinese Hub for Crypto Crime Is Hiding in Plain Sight',
            'date': '2025-05-13',
            'description': 'WIRED investigation into Chinese crypto crime marketplace'
        },
        {
            'id': 'wired_chinese_hackers',
            'url': 'https://www.wired.com/story/china-honkers-elite-cyber-spies/',
            'title': "How China's Patriotic 'Honkers' Became the Nation's Elite Cyberwarriors",
            'date': '2025-07-18',
            'description': 'WIRED analysis of Chinese hacker groups and their activities'
        },
        {
            'id': 'wired_us_charges_spies',
            'url': 'https://www.wired.com/story/us-charges-12-alleged-spies-in-chinas-freewheeling-hacker-for-hire-ecosystem/',
            'title': "US Charges 12 Alleged Spies in China's Freewheeling Cyberattack Campaign",
            'date': '2025-03-05',
            'description': 'WIRED report on US charges against Chinese cyber spies'
        },
        {
            'id': 'wired_biggest_black_market',
            'url': 'https://www.wired.com/story/the-internets-biggest-ever-black-market-shuts-down-after-a-telegram-purge/',
            'title': "The Internet's Biggest-Ever Black Market Just Shut Down",
            'date': '2025-05-14',
            'description': 'WIRED report on major dark web marketplace shutdown'
        },
        {
            'id': 'bloomberg_shanghai_police',
            'url': 'https://www.bloomberg.com/news/articles/2022-07-04/hackers-claim-theft-of-police-info-in-china-s-largest-data-leak',
            'title': "Hackers Claim Theft of Police Info in China's Largest Data Breach",
            'date': '2022-07-04',
            'description': 'Bloomberg report on Shanghai police data breach'
        },
        {
            'id': 'abc_net_au_china_data',
            'url': 'https://www.abc.net.au/news/2022-07-06/hacker-claims-to-have-stolen-1-billion-records-of-chinese-citize/101213964',
            'title': "'ChinaDan' hacker offers personal data on 1 billion Chinese citizens for sale",
            'date': '2022-07-05',
            'description': 'ABC Australia report on Chinese data breach'
        }
    ]


def get_all_scrapable_sources() -> List[Dict[str, Any]]:
    """
    Get all sources that can be scraped.
    
    Returns:
        Combined list of all scrapable sources
    """
    return get_real_pricing_sources() + get_news_sources()
