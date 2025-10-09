# 必要な道具（ライブラリ）を呼び出す
import discord
from discord.ext import tasks
import requests
import asyncio
import os
import re
from datetime import date
from dotenv import load_dotenv

# Webサーバー機能のための道具
from flask import Flask
from threading import Thread

# .envファイルから環境変数を読み込む
load_dotenv()

# ---------------------------------------------------------------
# --- 設定エリア ---
# ---------------------------------------------------------------

# 1. 秘密の鍵 (Renderの環境変数で設定)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
NOTIFICATION_USER_ID = os.getenv('NOTIFICATION_USER_ID')
API_KEYS = {
    'Toei': os.getenv('ODPT_TOKEN_TOEI'),
    'Tobu': os.getenv('ODPT_TOKEN_CHALLENGE'),
    'JR-East': os.getenv('ODPT_TOKEN_CHALLENGE'),
    'YokohamaMunicipal': os.getenv('ODPT_TOKEN_TOEI'),
}

# --- 複数路線対応のための設定エリア ---
LINE_CONFIG = {
    'Mita': {
        'operator': 'Toei',
        'api_name': 'Toei.Mita',
        'jp_name': '都営三田線',
        'timetable': {
            # ここには君が作った三田線の定期運用リストを入れよう！
            ('odpt.TrainType:Toei.Local', 'NishiTakashimadaira'),
            ('odpt.TrainType:Toei.Local', 'Takashimadaira'),
            ('odpt.TrainType:Toei.Local', 'ShirokaneTakanawa'),
            ('odpt.TrainType:Toei.Local', 'Ebina'),
            ('odpt.TrainType:Toei.Local', 'Shonandai'),
            ('odpt.TrainType:Toei.Local', 'ShinYokohama'),
            ('odpt.TrainType:Toei.Local', 'Yamato'),
            ('odpt.TrainType:Toei.Local', 'Hiyoshi'),
            ('odpt.TrainType:Toei.Local', 'MusashiKosugi'),
            ('odpt.TrainType:Toei.Local', 'Nishiya'),

    # --- 急行 (Express) ---
            ('odpt.TrainType:Toei.Express', 'Ebina'),
            ('odpt.TrainType:Toei.Express', 'Shonandai'),
            ('odpt.TrainType:Toei.Express', 'ShinYokohama'),
            ('odpt.TrainType:Toei.Express', 'Yamato'),
            ('odpt.TrainType:Toei.Express', 'Hiyoshi'),
            ('odpt.TrainType:Toei.Express', 'Nishiya'),
        },
        'type_dict': { # ★三田線専用の種別辞書！
            'odpt.TrainType:Toei.Local': '各停',
            'odpt.TrainType:Toei.Express': '急行',
        }
    },
    'Shinjuku': {
        'operator': 'Toei',
        'api_name': 'Toei.Shinjuku',
        'jp_name': '都営新宿線',
        'timetable': {
            # ここは新宿線の定期運用リスト（君が後でカスタムしてね！）
            # --- 各停 (Local) ---
            ('odpt.TrainType:Toei.Local', 'KeioTamaCenter'), # 各停 京王多摩センター
            ('odpt.TrainType:Toei.Local', 'Hashimoto'),      # 各停 橋本
            ('odpt.TrainType:Toei.Local', 'Sasazuka'),       # 各停 笹塚
            ('odpt.TrainType:Toei.Local', 'Wakabadai'),      # 各停 若葉台
            ('odpt.TrainType:Toei.Local', 'Shinjuku'),       # 各停 新宿
            ('odpt.TrainType:Toei.Local', 'Motoyawata'),     # 各停 本八幡
            ('odpt.TrainType:Toei.Local', 'Ojima'),          # 各停 大島
            ('odpt.TrainType:Toei.Local', 'Mizue'),          # 各停 瑞江
            ('odpt.TrainType:Toei.Local', 'Iwamotocho'),     # 各停 岩本町

            # --- 急行 (Express) ---
            ('odpt.TrainType:Toei.Express', 'KeioTamaCenter'), # 急行 京王多摩センター
            ('odpt.TrainType:Toei.Express', 'Hashimoto'),      # 急行 橋本
            ('odpt.TrainType:Toei.Express', 'Sasazuka'),       # 急行 笹塚
            ('odpt.TrainType:Toei.Express', 'Motoyawata'),     # 急行 本八幡
            ('odpt.TrainType:Toei.Express', 'Ojima'),          # 急行 大島
        },
        'type_dict': { # ★新宿線専用の種別辞書！
            'odpt.TrainType:Toei.Local': '各停',
            'odpt.TrainType:Toei.Express': '急行',
        }
    },
    'Oedo': {
        'operator': 'Toei',
        'api_name': 'Toei.Oedo',
        'jp_name': '都営大江戸線',
        'timetable': {
            # 種別はすべて 'Local' として扱う
            ('odpt.TrainType:Toei.Local', 'Hikarigaoka'),      # 光が丘
            ('odpt.TrainType:Toei.Local', 'Tochomae'),        # 都庁前
            ('odpt.TrainType:Toei.Local', 'ShinOkachimachi'), # 新御徒町
            ('odpt.TrainType:Toei.Local', 'Shiodome'),        # 汐留
            ('odpt.TrainType:Toei.Local', 'KiyosumiShirakawa'), # 清澄白河
        },
        'type_dict': { # ★大江戸線専用の種別辞書！
            'odpt.TrainType:Toei.Local': '大江戸線', #
        }
    },
    'Asakusa': {
        'operator': 'Toei',
        'api_name': 'Toei.Asakusa',
        'jp_name': '都営浅草線',
        'timetable': {
            # --- エアポート快特 (AirportRapidLimitedExpress) ---
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'Sogosando'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'KeiseiNarita'),

            # --- 快特 (RapidLimitedExpress) ---
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'KeikyuKurihama'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'Misakiguchi'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'ShibayamaChiyoda'),

            # --- 急行 (Express) ---
            ('odpt.TrainType:Toei.Express', 'HanedaAirportTerminal1and2'), # エアポート急行はこれ
            ('odpt.TrainType:Toei.Express', 'ZushiHayama'),

            # --- 普通 (Local) ---
            ('odpt.TrainType:Toei.Local', 'NishiMagome'),
            ('odpt.TrainType:Toei.Local', 'Sengakuji'),
            ('odpt.TrainType:Toei.Local', 'Shinagawa'),
            ('odpt.TrainType:Toei.Local', 'ImbaNihonIdai'),
            ('odpt.TrainType:Toei.Local', 'InzaiMakinohara'),
            ('odpt.TrainType:Toei.Local', 'Oshiage'),
            ('odpt.TrainType:Toei.Local', 'KeiseiTakasago'),
            ('odpt.TrainType:Toei.Local', 'Aoto'),

            # --- 特急 (LimitedExpress) ---
            ('odpt.TrainType:Toei.LimitedExpress', 'Misakiguchi'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KeikyuKurihama'),
            ('odpt.TrainType:Toei.LimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.LimitedExpress', 'Miurakaigan'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KanazawaBunko'), 
            ('odpt.TrainType:Toei.LimitedExpress', 'KeiseiTakasago'),
            ('odpt.TrainType:Toei.LimitedExpress', 'Aoto'),
            ('odpt.TrainType:Toei.LimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.LimitedExpress', 'ShibayamaChiyoda'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.LimitedExpress', 'ImbaNihonIdai'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KanagawaShimmachi'),

            # --- アクセス特急 ---
            ('odpt.TrainType:Toei.AccessExpress', 'NaritaAirportTerminal1'),

            # --- 快速 ---
            ('odpt.TrainType:Toei.Rapid', 'KeiseiSakura'),
            ('odpt.TrainType:Toei.Rapid', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.Rapid', 'Aoto'),
            ('odpt.TrainType:Toei.Rapid', 'KeiseiNarita'),
            
            # --- 通勤特急 ---
            ('odpt.TrainType:Toei.CommuterLimitedExpress', 'NaritaAirportTerminal1'),
        },
        'type_dict': { # ★浅草線専用の種別辞書！
            'odpt.TrainType:Toei.Local': '普通',
            'odpt.TrainType:Toei.Express': '急行',
            'odpt.TrainType:Toei.Rapid': '快速',
            'odpt.TrainType:Toei.LimitedExpress': '特急', # 都営線の特急
            'odpt.TrainType:Toei.RapidLimitedExpress': '快特',
            'odpt.TrainType:Toei.AirportRapidLimitedExpress': '士快特', # 都営線のエアポート快特
            'odpt.TrainType:Toei.AccessExpress': 'アク特',
            'odpt.TrainType:Toei.CommuterLimitedExpress': '通特',
        },
        'conditional_timetable': [
            {
                'operation': ('odpt.TrainType:Toei.Local', 'Asakusabashi'),
                'allowed_numbers': ['2428T', '2406T']
            }
        ]
    },
    'Tojo': {
        'operator': 'Tobu',
        'api_name': 'Tobu.Tojo', # 東上線のAPI名
        'jp_name': '東武東上線',
        'handover_stations': {
            'Wakoshi': ['MotomachiChukagai', 'ShinKiba', 'Shonandai', 'Ebina', 'MusashiKosugi'] # 和光市で乗り換えるのが自然な行き先
        },
        'station_order': [
            'Ikebukuro', 'KitaIkebukuro', 'ShimoItabashi', 'Oyama', 'NakaItabashi', 
            'Tokiwadai', 'KamiItabashi', 'TobuNerima', 'ShimoAkatsuka', 'Narimasu', 
            'Wakoshi', 'Asaka', 'Asakadai', 'Shiki', 'Yanasegawa', 'Mizuhodai', 
            'Tsuruse', 'Fujimino', 'KamiFukuoka', 'Shingashi', 'Kawagoe', 'Kawagoeshi',
            'Kasumigaseki', 'Tsurugashima', 'Wakaba', 'Sakado', 'KitaSakado', 'Takasaka',
            'HigashiMatsuyama', 'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi',
            'TobuTakezawa', 'MinamiYorii', 'Obusuma', 'Hachigata', 'Tamayodo', 'Yorii'
        ],
        'ignore_disappearances': [
            {
                'destination': 'Shiki', 
                'last_seen_at': ['Asaka', 'Asakadai']
            },
            {
                'destination': 'Kawagoeshi', 
                'last_seen_at': ['Kawagoe', 'Shingashi']
            },
            {
                'destination': 'Narimasu', 
                'last_seen_at': ['ShimoAkatsuka', 'TobuNerima']
                
            },
            {
                'destination': 'Yorii', 
                'last_seen_at': ['Tamayodo']
            },
            {
                'destination': ['MotomachiChukagai', 'ShinKiba', 'Shonandai', 'Ebina', 'MusashiKosugi'], 
                'last_seen_at': ['Wakoshi', 'Asaka']
            },
            {
                'destination': 'Ikebukuro', 
                'last_seen_at': ['ShimoAkatsuka', 'TobuNerima', 'KamiItabashi', 'Tokiwadai', 'NakaItabashi','Oyaam', 'ShimoItabashi', 'KitaIkebukuro']
            }
        ],
        'timetable': {
            # ★ここに、君がこれから作る東上線の定期運用リストを入れる！
            # --- 川越特急 ---
            ('odpt.TrainType:Tobu.KawagoeLimitedExpress', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.KawagoeLimitedExpress', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.KawagoeLimitedExpress', 'Ogawamachi'),

            # --- 快速急行 ---
            ('odpt.TrainType:Tobu.RapidExpress', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.RapidExpress', 'MotomachiChukagai'),
            ('odpt.TrainType:Tobu.RapidExpress', 'Shonandai'),
            ('odpt.TrainType:Tobu.RapidExpress', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.RapidExpress', 'Ogawamachi'),
            
            # --- TJライナー ---
            ('odpt.TrainType:Tobu.TJ-Liner', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.TJ-Liner', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.TJ-Liner', 'Ogawamachi'),

            # --- 急行 ---
            ('odpt.TrainType:Tobu.Express', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.Express', 'MotomachiChukagai'),
            ('odpt.TrainType:Tobu.Express', 'Shonandai'),
            ('odpt.TrainType:Tobu.Express', 'Kawagoeshi'),
            ('odpt.TrainType:Tobu.Express', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.Express', 'Ogawamachi'),

            # --- 準急 ---
            ('odpt.TrainType:Tobu.SemiExpress', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.SemiExpress', 'Kawagoeshi'),
            ('odpt.TrainType:Tobu.SemiExpress', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.SemiExpress', 'Ogawamachi'),

            # --- 普通 ---
            ('odpt.TrainType:Tobu.Local', 'Ikebukuro'),
            ('odpt.TrainType:Tobu.Local', 'ShinKiba'),
            ('odpt.TrainType:Tobu.Local', 'Shonandai'),
            ('odpt.TrainType:Tobu.Local', 'MusashiKosugi'),
            ('odpt.TrainType:Tobu.Local', 'MotomachiChukagai'),
            ('odpt.TrainType:Tobu.Local', 'Narimasu'),
            ('odpt.TrainType:Tobu.Local', 'Shiki'),
            ('odpt.TrainType:Tobu.Local', 'KamiFukuoka'),
            ('odpt.TrainType:Tobu.Local', 'Kawagoeshi'),
            ('odpt.TrainType:Tobu.Local', 'ShinrinKoen'),
            ('odpt.TrainType:Tobu.Local', 'Ogawamachi'),
            ('odpt.TrainType:Tobu.Local', 'Yorii'),
        },
        'type_dict': {
            # ★東上線専用の種別辞書
            'odpt.TrainType:Tobu.Local': '普通',
            'odpt.TrainType:Tobu.SemiExpress': '準急',
            'odpt.TrainType:Tobu.Express': '急行',
            'odpt.TrainType:Tobu.RapidExpress': '快急',
            'odpt.TrainType:Tobu.TJ-Liner': 'TJライナー',
            'odpt.TrainType:Tobu.KawagoeLimitedExpress': '川越特急',
        }
    },
    'KeihinTohoku': {
        'operator': 'JR-East',
        'api_name': 'JR-East.KeihinTohoku',
        'jp_name': '京浜東北線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'MinamiUrawa'),
            ('odpt.TrainType:JR-East.Local', 'Akabane'),
            ('odpt.TrainType:JR-East.Local', 'HigashiJujo'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Kamata'),
            ('odpt.TrainType:JR-East.Local', 'Tsurumi'),
            ('odpt.TrainType:JR-East.Local', 'HigashiKanagawa'),
            ('odpt.TrainType:JR-East.Local', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Local', 'Isogo'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Rapid', 'Omiya'),
            ('odpt.TrainType:JR-East.Rapid', 'MinamiUrawa'),
            ('odpt.TrainType:JR-East.Rapid', 'HigashiJujo'),
            ('odpt.TrainType:JR-East.Rapid', 'Kamata'),
            ('odpt.TrainType:JR-East.Rapid', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Rapid', 'Isogo'),
            ('odpt.TrainType:JR-East.Rapid', 'Ofuna'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '各駅停車',
            'odpt.TrainType:JR-East.Rapid': '快速',
        },
        'conditional_timetable': [
            {
                'operation': ('odpt.TrainType:JR-East.Local', 'Ueno'),
                'allowed_numbers': ['2328B', '2316A']
            }
        ]
    },
    'ChuoRapid': {
        'operator': 'JR-East',
        'api_name': 'JR-East.ChuoRapid',
        'jp_name': '中央快速線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Tokyo'), # 各停・普通はLocal
            ('odpt.TrainType:JR-East.Local', 'MusashiKoganei'),
            ('odpt.TrainType:JR-East.Local', 'Kokubunji'),
            ('odpt.TrainType:JR-East.Local', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Local', 'Ome'),
            ('odpt.TrainType:JR-East.Local', 'Toyoda'),
            ('odpt.TrainType:JR-East.Local', 'Hachioji'),
            ('odpt.TrainType:JR-East.Local', 'Takao'),
            ('odpt.TrainType:JR-East.Local', 'Otsuki'),
            ('odpt.TrainType:JR-East.Local', 'Kawaguchiko'),
            ('odpt.TrainType:JR-East.Local', 'Kofu'),
            ('odpt.TrainType:JR-East.Local', 'Kobuchizawa'),
            ('odpt.TrainType:JR-East.Local', 'Matsumoto'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),

            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.Rapid', 'Mitaka'),
            ('odpt.TrainType:JR-East.Rapid', 'MusashiKoganei'),
            ('odpt.TrainType:JR-East.Rapid', 'Kokubunji'),
            ('odpt.TrainType:JR-East.Rapid', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Ome'),
            ('odpt.TrainType:JR-East.Rapid', 'Toyoda'),
            ('odpt.TrainType:JR-East.Rapid', 'Hachioji'),
            ('odpt.TrainType:JR-East.Rapid', 'Takao'),
            ('odpt.TrainType:JR-East.Rapid', 'Otsuki'),

            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Takao'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Otsuki'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Kawaguchiko'),
            
            ('odpt.TrainType:JR-East.OmeSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.OmeSpecialRapid', 'Ome'),
            
            ('odpt.TrainType:JR-East.CommuterRapid', 'Takao'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Ome'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Otsuki'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Kawaguchiko'),

            ('odpt.TrainType:JR-East.CommuterSpecialRapid', 'Tokyo'),

            ('odpt.TrainType:JR-East.LimitedExpress', 'Tokyo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Chiba'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Kawaguchiko'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Kofu'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ryuo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Matsumoto'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Hakuba'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '各停', # 各停も普通もLocal
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.ChuoSpecialRapid': '中央特快',
            'odpt.TrainType:JR-East.OmeSpecialRapid': '青梅特快',
            'odpt.TrainType:JR-East.CommuterRapid': '通勤快速',
            'odpt.TrainType:JR-East.CommuterSpecialRapid': '通勤特快',
            'odpt.TrainType:JR-East.LimitedExpress': '特急',
        },
        'conditional_timetable': [
            {
                'operation': ('odpt.TrainType:JR-East.Rapid', 'Kokubunji'),
                'allowed_numbers': ['2245T']
            },
            {
                'operation': ('odpt.TrainType:JR-East.Local', 'Kokubunji'),
                'allowed_numbers': ['2245T']
            }
        ]        
    },
    'Saikyo': {
        'operator': 'JR-East',
        'api_name': 'JR-East.Saikyo',
        'jp_name': '埼京線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Kawagoe'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'MusashiUrawa'),
            ('odpt.TrainType:JR-East.Local', 'Akabane'),
            ('odpt.TrainType:JR-East.Local', 'Ikebukuro'),
            ('odpt.TrainType:JR-East.Local', 'Shinjuku'),
            ('odpt.TrainType:JR-East.Local', 'Osaki'),
            ('odpt.TrainType:JR-East.Local', 'ShinKiba'),
            ('odpt.TrainType:JR-East.Local', 'Ebina'),

            ('odpt.TrainType:JR-East.Rapid', 'Kawagoe'),
            ('odpt.TrainType:JR-East.Rapid', 'Omiya'),
            ('odpt.TrainType:JR-East.Rapid', 'ShinKiba'),
            ('odpt.TrainType:JR-East.Rapid', 'Ebina'),

            ('odpt.TrainType:JR-East.CommuterRapid', 'Kawagoe'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Omiya'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Shinjuku'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'ShinKiba'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '各駅停車',
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.CommuterRapid': '通勤快速',
        },
        'conditional_timetable': [
            {
                'operation': ('odpt.TrainType:JR-East.CommuterRapid', 'Shinjuku'),
                'allowed_numbers': ['618S', '886S']
            }
        ]
    },
    'ShonanShinjuku': {
        'operator': 'JR-East',
        'api_name': 'JR-East.ShonanShinjuku',
        'jp_name': '湘南新宿ﾗｲﾝ',
        'timetable': {
            #普通
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Local', 'Zushi'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),

            #快速
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Rapid', 'Kozu'),
            ('odpt.TrainType:JR-East.Rapid', 'Odawara'),
            ('odpt.TrainType:JR-East.Rapid', 'Zushi'),

            #特快
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'),

            #特急成田エクスプレス・きぬがわ・湘南
            ('odpt.TrainType:JR-East.LimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ohuna'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Odawara'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'TobuNikko'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'KinugawaOnsen'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '普通',
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.SpecialRapid': '特別快速',
            'odpt.TrainType:JR-East.LimitedExpress': '特急',
        }
    },
    'Utsunomiya': {
        'operator': 'JR-East',
        'api_name': 'JR-East.Utsunomiya',
        'jp_name': '宇都宮線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Nikko'),
            ('odpt.TrainType:JR-East.Local', 'Kuroiso'),
            ('odpt.TrainType:JR-East.Local', 'Karasuyama'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'TobuNikko'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'KinugawaOnsen'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Local', 'Zushi'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Zushi'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '普通',
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.LimitedExpress': '特急',
        }
    },
    'Takasaki': {
        'operator': 'JR-East',
        'api_name': 'JR-East.Takasaki',
        'jp_name': '高崎線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'ShimMaebashi'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ueno'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Konosu'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Honjo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Takasaki'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'NaganoharaKusatsuguchi'),
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.Rapid', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Rapid', 'Kozu'),
            ('odpt.TrainType:JR-East.Rapid', 'Odawara'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '普通',
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.LimitedExpress': '特急',
        }
    },
    'Tokaido': {
        'operator': 'JR-East',
        'api_name': 'JR-East.Tokaido',
        'jp_name': '東海道線',
        'timetable': {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.Local', 'Mito'),
            ('odpt.TrainType:JR-East.Local', 'Katsuta'),
            ('odpt.TrainType:JR-East.Local', 'Takahagi'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'ShimMaebashi'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Matsudo'),
            ('odpt.TrainType:JR-East.Rapid', 'Toride'),
            ('odpt.TrainType:JR-East.Rapid', 'Narita'),
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Odawara'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Tokyo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Iwaki'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Katsuta'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Sendai'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Takamatsu'),
            ('odpt.TrainType:JR-East.SleeperLimitedExpress', 'Tokyo'),
        },
        'type_dict': {
            'odpt.TrainType:JR-East.Local': '普通',
            'odpt.TrainType:JR-East.Rapid': '快速',
            'odpt.TrainType:JR-East.SpecialRapid': '特別快速',
            'odpt.TrainType:JR-East.LimitedExpress': '特急',
        }
    },
    'Blue': {
        'operator': 'YokohamaMunicipal',
        'api_name': 'YokohamaMunicipal.Blue',
        'jp_name': 'ﾌﾞﾙｰﾗｲﾝ',
        'timetable': {
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Azamino'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Kaminagaya'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Kamiooka'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Nippa'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'ShinYokohama'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Odoriba'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Shonandai'),
            ('odpt.TrainType:YokohamaMunicipal.Rapid', 'Azamino'),
            ('odpt.TrainType:YokohamaMunicipal.Rapid', 'Shonandai'),
        },
        'type_dict': {
            'odpt.TrainType:YokohamaMunicipal.Local': '普通',
            'odpt.TrainType:YokohamaMunicipal.Rapid': '快速',
        }
    },
    'Green': {
        'operator': 'YokohamaMunicipal',
        'api_name': 'YokohamaMunicipal.Green',
        'jp_name': 'ｸﾞﾘｰﾝﾗｲﾝ',
        'timetable': {
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Hiyoshi'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'CenterKita'),
            ('odpt.TrainType:YokohamaMunicipal.Local', 'Nakayama'),
        },
        'type_dict': {
            'odpt.TrainType:YokohamaMunicipal.Local': '普通',
        }
    },
}

# --- 翻訳辞書エリア ---
# 駅名を日本語に翻訳するための辞書
STATION_DICT = {
    # --- 都営三田線 ---
    'Mita': '三田', 'Shibakoen': '芝公園', 'Onarimon': '御成門', 'Uchisaiwaicho': '内幸町',
    'Hibiya': '日比谷', 'Otemachi': '大手町', 'Jimbocho': '神保町', 'Suidobashi': '水道橋',
    'Kasuga': '春日', 'Hakusan': '白山', 'Sengoku': '千石', 'Sugamo': '巣鴨',
    'NishiSugamo': '西巣鴨', 'ShinItabashi': '新板橋', 'ItabashiKuyakushomae': '板橋区役所前',
    'ItabashiHoncho': '板橋本町', 'Motosunuma': '本蓮沼', 'ShimuraSakaue': '志村坂上',
    'ShimuraSanchome': '志村三丁目', 'Hasune': '蓮根', 'Nishidai': '西台',
    'Takashimadaira': '高島平', 'NishiTakashimadaira': '西高島平',

    # --- 東京メトロ南北線 ---
    'Shirokanedai': '白金台', 'ShirokaneTakanawa': '白金高輪', 'Meguro': '目黒',

    # --- 東急目黒線・東急新横浜線 ---
    'FudoMae': '不動前', 'MusashiKoyama': '武蔵小山', 'NishiKoyama': '西小山',
    'Senzoku': '洗足', 'Okurayama': '大倉山', 'Okusawa': '奥沢', 'DenEnChofu': '田園調布',
    'Tamagawa': '多摩川', 'ShinMaruko': '新丸子', 'Motosumiyoshi': '元住吉',
    'MusashiKosugi': '武蔵小杉', 'Hiyoshi': '日吉', 'ShinTsunashima': '新綱島', 'ShinYokohama': '新横浜',

    # --- 相鉄新横浜線・相鉄本線・相鉄いずみ野線 ---
    'HazawaYokohamaKokudai': '羽沢横浜国大', 'Nishiya': '西谷', 'Tsurugamine': '鶴ヶ峰',
    'Futamatagawa': '二俣川', 'Kibogaoka': '希望ヶ丘', 'Yamato': '大和', 'Kashiwadai': 'かしわ台',
    'Ebina': '海老名', 'MinamiMakigahara': '南万騎が原', 'RyokuenToshi': '緑園都市', 'IzumiChuo': 'いずみ中央',
    'Izumino': 'いずみ野', 'Yumegaoka': 'ゆめが丘', 'Shonandai': '湘南台',

    # --- 都営新宿線 ---
    'Shinjuku': '新宿', 'ShinjukuSanchome': '新宿三丁目', 'Akebonobashi': '曙橋',
    'Ichigaya': '市ヶ谷', 'Kudanshita': '九段下', 'Jimbocho': '神保町', 'Ogawamachi': '小川町',
    'Iwamotocho': '岩本町', 'BakuroYokoyama': '馬喰横山', 'Hamacho': '浜町', 'Morishita': '森下',
    'Kikukawa': '菊川', 'Sumiyoshi': '住吉', 'NishiOjima': '西大島', 'Ojima': '大島',
    'HigashiOjima': '東大島', 'Funabori': '船堀', 'Ichinoe': '一之江', 'Mizue': '瑞江',
    'Shinozaki': '篠崎', 'Motoyawata': '本八幡',

    # --- 京王新線・京王線 ---
    'Hatsudai': '初台', 'Hatagaya': '幡ヶ谷', 'Sasazuka': '笹塚', 'Daitabashi': '代田橋',
    'Meidaimae': '明大前', 'Sakurajosui': '桜上水', 'ChitoseKarasuyama': '千歳烏山',
    'Tsutsujigaoka': 'つつじヶ丘', 'Chofu': '調布', 'Fuchu': '府中',
    'Takahatafudo': '高幡不動', 'Kitano': '北野', 'KeioHachioji': '京王八王子',
    'Takaosanguchi': '高尾山口', 'Inagi': '稲城', 'Wakabadai': '若葉台', 'KeioNagayama': '京王永山',
    'KeioTamaCenter': '京王多摩センター', 'MinamiOsawa': '南大沢', 'Hashimoto': '橋本',

    # --- 都営大江戸線 ---
    'Tochomae': '都庁前', 'ShinjukuNishiguchi': '新宿西口', 'HigashiShinjuku': '東新宿',
    'WakamatsuKawada': '若松河田', 'UshigomeYanagicho': '牛込柳町', 'UshigomeKagurazaka': '牛込神楽坂',
    'Iidabashi': '飯田橋', 'Kasuga': '春日', 'HongoSanchome': '本郷三丁目', 'UenoOkachimachi': '上野御徒町',
    'ShinOkachimachi': '新御徒町', 'Kuramae': '蔵前', 'Ryogoku': '両国', 'Morishita': '森下',
    'KiyosumiShirakawa': '清澄白河', 'MonzenNakacho': '門前仲町', 'Tsukishima': '月島',
    'Kachidoki': '勝どき', 'Tsukijishijo': '築地市場', 'Shiodome': '汐留', 'Daimon': '大門',
    'Akabanebashi': '赤羽橋', 'AzabuJuban': '麻布十番', 'Roppongi': '六本木', 'AoyamaItchome': '青山一丁目',
    'KokuritsuKyogijo': '国立競技場', 'Yoyogi': '代々木', 'Shinjuku': '新宿',
    'NishiShinjukuGochome': '西新宿五丁目', 'NakanoSakaue': '中野坂上', 'HigashiNakano': '東中野',
    'Nakai': '中井', 'OchiaiMinamiNagasaki': '落合南長崎', 'ShinEgota': '新江古田',
    'Nerima': '練馬', 'Toshimaen': '豊島園', 'NerimaKasugacho': '練馬春日町', 'Hikarigaoka': '光が丘',

    # --- 都営浅草線 ---
    'NishiMagome': '西馬込', 'Magome': '馬込', 'Nakanobu': '中延', 'Togoshi': '戸越',
    'Gotanda': '五反田', 'Takanawadai': '高輪台', 'Sengakuji': '泉岳寺', 'Mita': '三田',
    'Daimon': '大門', 'Shimbashi': '新橋', 'HigashiGinza': '東銀座', 'Takaracho': '宝町',
    'Nihombashi': '日本橋', 'Ningyocho': '人形町', 'HigashiNihombashi': '東日本橋',
    'Asakusabashi': '浅草橋', 'Kuramae': '蔵前', 'Asakusa': '浅草', 'HonjoAzumabashi': '本所吾妻橋',
    'Oshiage': '押上',

    # --- [直通先] 京急線 ---
    'Shinagawa': '品川', 'KeikyuKamata': '京急蒲田', 'HanedaAirportTerminal1and2': '羽田空港',
    'KeikyuKawasaki': '京急川崎', 'KanagawaShimmachi': '神奈川新町', 'Yokohama': '横浜',
    'Kamiooka': '上大岡', 'KanazawaBunko': '金沢文庫', 'ZushiHayama': '逗子・葉山',
    'Hemmi': '逸見', 'Horinouchi': '堀ノ内', 'Uraga': '浦賀', 'KeikyuKurihama': '京急久里浜',
    'Miurakaigan': '三浦海岸', 'Misakiguchi': '三崎口',

    # --- [直通先] 京成線・北総線・芝山鉄道線 ---
    'Yahiro': '八広', 'Aoto': '青砥', 'KeiseiTakasago': '京成高砂', 'KeiseiKoiwa': '京成小岩',
    'Ichikawamama': '市川真間', 'HigashiNakayama': '東中山', 'KeiseiFunabashi': '京成船橋',
    'Funabashikeibajo': '船橋競馬場', 'KeiseiTsudanuma': '京成津田沼', 'Yachiyodai': '八千代台',
    'KeiseiOwada': '京成大和田', 'KeiseiUsui': '京成臼井', 'Sogosando': '宗吾参道',
    'KeiseiNarita': '京成成田', 'HigashiNarita': '東成田', 'NaritaAirportTerminal2and3': '空港第２ビル',
    'NaritaAirportTerminal1': '成田空港', 'Yagiri': '矢切', 'HigashiMatsudo': '東松戸',
    'ShinKamagaya': '新鎌ヶ谷', 'NishiShiroi': '西白井', 'ChibaNewtownChuo': '千葉ニュータウン中央',
    'InzaiMakinohara': '印西牧の原', 'ImbaNihonIdai': '印旛日本医大', 'NaritaYukawa': '成田湯川',

    # --- [追加] 東武東上線 ---
    'Ikebukuro': '池袋', 'KitaIkebukuro': '北池袋', 'ShimoItabashi': '下板橋', 
    'Oyama': '大山', 'NakaItabashi': '中板橋', 'Tokiwadai': 'ときわ台', 
    'KamiItabashi': '上板橋', 'TobuNerima': '東武練馬', 'ShimoAkatsuka': '下赤塚', 
    'Narimasu': '成増', 'Wakoshi': '和光市', 'Asaka': '朝霞', 'Asakadai': '朝霞台', 
    'Shiki': '志木', 'Yanasegawa': '柳瀬川', 'Mizuhodai': 'みずほ台', 
    'Tsuruse': '鶴瀬', 'Fujimino': 'ふじみ野', 'KamiFukuoka': '上福岡', 
    'Shingashi': '新河岸', 'Kawagoe': '川越', 'Kawagoeshi': '川越市', 
    'Kasumigaseki': '霞ヶ関', 'Tsurugashima': '鶴ヶ島', 'Wakaba': '若葉', 
    'Sakado': '坂戸', 'KitaSakado': '北坂戸', 'Takasaka': '高坂', 
    'HigashiMatsuyama': '東松山', 'ShinrinKoen': '森林公園', 'Tsukinowa': 'つきのわ', 
    'MusashiRanzan': '武蔵嵐山', 'Ogawamachi': '小川町', 'TobuTakezawa': '東武竹沢', 
    'Obusuma': '男衾', 'MinamiYorii': 'みなみ寄居', 'Hachigata': '鉢形', 'Tamayodo': '玉淀', 'Yorii': '寄居',
    
    # --- [直通先] 東京メトロ 副都心線・有楽町線 ---
    'ChikatetsuNarimasu': '地下鉄成増', 'KotakeMukaihara': '小竹向原', 
    'Ikebukuro': '池袋', # 東上線と重複するけどOK
    'ShinjukuSanchome': '新宿三丁目', 'Shibuya': '渋谷', 'Ichigaya': '市ヶ谷', 
    'GinzaItchome': '銀座一丁目', 'Toyosu': '豊洲', 'ShinKiba': '新木場',

    # --- [直通先] 東急東横線・みなとみらい線 ---
    'Jiyugaoka': '自由が丘', 'MusashiKosugi': '武蔵小杉', 'Kikuna': '菊名', 
    'Yokohama': '横浜', 'MotomachiChukagai': '元町・中華街',

    # --- [追加] JR中央快速線 ---
    'Tokyo': '東京', 'Kanda': '神田', 'Ochanomizu': '御茶ノ水', 'Yotsuya': '四ツ谷', 
    'Shinjuku': '新宿', 'Nakano': '中野', 'Koenji': '高円寺', 'Asagaya': '阿佐ヶ谷', 
    'Ogikubo': '荻窪', 'NishiOgikubo': '西荻窪', 'Kichijoji': '吉祥寺', 'Mitaka': '三鷹', 
    'MusashiSakai': '武蔵境', 'HigashiKoganei': '東小金井', 'MusashiKoganei': '武蔵小金井', 
    'Kokubunji': '国分寺', 'NishiKokubunji': '西国分寺', 'Kunitachi': '国立', 
    'Tachikawa': '立川', 'Hino': '日野', 'Toyoda': '豊田', 'Hachioji': '八王子', 
    'NishiHachioji': '西八王子', 'Takao': '高尾', 'Sagamiko': '相模湖', 'Fujino': '藤野', 
    'Uenohara': '上野原', 'Shiotsu': '四方津', 'Yanagawa': '梁川', 'Torisawa': '鳥沢', 
    'Saruhashi': '猿橋', 'Otsuki': '大月',

    # --- [追加] JR青梅線・五日市線 ---
    'NishiTachikawa': '西立川', 'HigashiNakagami': '東中神', 'Nakagami': '中神', 
    'Akishima': '昭島', 'Haijima': '拝島', 'Ushihama': '牛浜', 'Fussa': '福生', 
    'Hamura': '羽村', 'Ozaku': '小作', 'Kabe': '河辺', 'HigashiOme': '東青梅', 
    'Ome': '青梅', 'Miyanohira': '宮ノ平', 'Hinatawada': '日向和田', 'Ishigamimae': '石神前', 
    'Futamatao': '二俣尾', 'Ikusabata': '軍畑', 'Sawai': '沢井', 'Mitake': '御嶽', 
    'Kawai': '川井', 'Kori': '古里', 'Hatonosu': '鳩ノ巣', 'Shiromaru': '白丸', 
    'Okutama': '奥多摩', 'Kumagawa': '熊川', 'HigashiAkiru': '東秋留', 
    'Akigawa': '秋川', 'MusashiHikida': '武蔵引田', 'MusashiMasuko': '武蔵増戸', 
    'MusashiItsukaichi': '武蔵五日市',

    # --- [追加] 富士急行線 ---
    'Fujisan': '富士山', 'FujikyuHighland': '富士急ハイランド', 'Kawaguchiko': '河口湖',

    # --- [追加] JR中央本線・篠ノ井線・大糸線 (主要駅) ---
    'Kofu': '甲府', 'Ryuo': '竜王', 'Nirasaki': '韮崎', 'Kobuchizawa': '小淵沢', 'Chino': '茅野', 
    'KamiSuwa': '上諏訪', 'ShimoSuwa': '下諏訪', 'Okaya': '岡谷', 'Shiojiri': '塩尻', 
    'Matsumoto': '松本', 'ShinanoOmachi': '信濃大町', 'Hakuba': '白馬', 'MinamiOtari': '南小谷',
    'Nagano': '長野', 

    # --- [追加] JR臨時列車用 (主要駅) ---
    'Hitachi': '日立', 'Ashikaga': '足利', 'HigashiTokorozawa': '東所沢', 'EchigoYuzawa': '越後湯沢',  
    'Ujiie': '氏家', 'TobuNikko': '東武日光', 'Nikko': '日光', 'KinugawaOnsen': '鬼怒川温泉',
    'ShimoImaichi': '下今市', 'Tokamachi': '十日町', 'HokukyuTokamachi': 'ほくほく線十日町',
    'Takamatsu': '高松','Izumoshi': '出雲市','Okayama': '岡山',   

    # --- [追加] JR総武線・房総各線 (主要駅) ---
    'Kinshicho': '錦糸町', 'Funabashi': '船橋', 'Tsudanuma': '津田沼', 'Chiba': '千葉', 
    'Soga': '蘇我', 'Kisarazu': '木更津', 'Kimitsu': '君津', 'Tateyama': '館山', 'Chikura': '千倉', 
    'AwaKamogawa': '安房鴨川', 'Oami': '大網', 'Mobara': '茂原', 'KazusaIchinomiya': '上総一ノ宮', 
    'Ohara': '大原', 'Katsuura': '勝浦', 'Sakura': '佐倉', 'Narita': '成田', 'Sawara': '佐原',  
    'NaritaAirport': '成田空港', 'Choshi': '銚子', 'KashimaJingu': '鹿島神宮',

    # --- [追加] JR京浜東北線 ---
    'Omiya': '大宮', 'SaitamaShintoshin': 'さいたま新都心', 'Yono': '与野', 'KitaUrawa': '北浦和',
    'Urawa': '浦和', 'MinamiUrawa': '南浦和', 'Warabi': '蕨', 'NishiKawaguchi': '西川口',
    'Kawaguchi': '川口', 'Akabane': '赤羽', 'HigashiJujo': '東十条', 'Oji': '王子',
    'KamiNakazato': '上中里', 'Tabata': '田端', 'Nippori': '日暮里', 'Uguisudani': '鶯谷',
    'Ueno': '上野', 'Okachimachi': '御徒町', 'Akihabara': '秋葉原', 'Kanda': '神田',
    'Tokyo': '東京', 'Yurakucho': '有楽町', 'Shimbashi': '新橋', 'Hamamatsucho': '浜松町',
    'Tamachi': '田町', 'TakanawaGateway': '高輪ゲートウェイ', 'Shinagawa': '品川',
    'Oimachi': '大井町', 'Omori': '大森', 'Kamata': '蒲田', 'Kawasaki': '川崎',
    'Tsurumi': '鶴見', 'ShinKoyasu': '新子安', 'HigashiKanagawa': '東神奈川', 'Yokohama': '横浜',
    'Sakuragicho': '桜木町', 'Kannai': '関内', 'Ishikawacho': '石川町', 'Yamate': '山手',
    'Negishi': '根岸', 'Isogo': '磯子', 'ShinSugita': '新杉田', 'Yokodai': '洋光台',
    'Konandai': '港南台', 'Honjo': '本郷台', 'Ofuna': '大船',

    # --- [追加] JR埼京線・川越線・りんかい線 ---
    'Kawagoe': '川越', 'NishiKawagoe': '西川越', 'Matoba': '的場', 'Kasahata': '笠幡',
    'MusashiTakahagi': '武蔵高萩', 'Komagawa': '高麗川', 'MinamiFuruya': '南古谷',
    'Sashiogi': '指扇', 'Nisshin': '日進', 'Omiya': '大宮', 'KitaYono': '北与野',
    'YonoHommachi': '与野本町', 'MinamiYono': '南与野', 'NakaUrawa': '中浦和',
    'MusashiUrawa': '武蔵浦和', 'KitaToda': '北戸田', 'Toda': '戸田', 'TodaKoen': '戸田公園',
    'UkimaFunado': '浮間舟渡', 'KitaAkabane': '北赤羽', 'Akabane': '赤羽', 'Jujo': '十条',
    'Itabashi': '板橋', 'Ikebukuro': '池袋', 'Shinjuku': '新宿', 'Shibuya': '渋谷',
    'Ebisu': '恵比寿', 'Osaki': '大崎', 'Oimachi': '大井町', 'ShinagawaSeaside': '品川シーサイド',
    'TennozuIsle': '天王洲アイル', 'TokyoTeleport': '東京テレポート',
    'KokusaiTenjijo': '国際展示場', 'Shinonome': '東雲', 'ShinKiba': '新木場',

    # --- [追加] JR東日本 湘南新宿ライン関連路線 ---

    # 両毛線 (前橋～高崎)
    'Maebashi': '前橋', 'ShinMaebashi': '新前橋', 'Ino': '井野', 'Takasakitonyamachi': '高崎問屋町', 'Takasaki': '高崎',

    # 高崎線 (高崎～大宮)
    # Takasakiは上記にあり
    'Kuragano': '倉賀野', 'Shinmachi': '新町', 'Jimbohara': '神保原', 'Honjo': '本庄', 'Okabe': '岡部', 'Fukaya': '深谷',
    'Okarina': '岡部', 'Kagohara': '籠原', 'Kumagaya': '熊谷', 'Gyoda': '行田', 'Fukiage': '吹上', 'KitaKonosu': '北鴻巣',
    'Konosu': '鴻巣', 'Kitamoto': '北本', 'Okegawa': '桶川', 'KitaAgeo': '北上尾', 'Ageo': '上尾', 'Miyahara': '宮原',
    # Omiyaは他路線で追加済み

    # 宇都宮線 (宇都宮～大宮)
    'Utsunomiya': '宇都宮', 'Suzumenomiya': '雀宮', 'Ishibashi': '石橋', 'Jichiidai': '自治医大', 'Koganei': '小金井',
    'Nogi': '野木', 'Mamada': '間々田', 'Oyama': '小山', 'Koga': '古河', 'Kurihashi': '栗橋', 'HigashiWashinomiya': '東鷲宮',
    'Kuki': '久喜', 'Shiraoka': '白岡', 'Hasuda': '蓮田', 'HigashiOmiya': '東大宮', 'Toro': '土呂',
    
    # --- [追加] JR宇都宮線 (北部) ---
    'Okamoto': '岡本', 'Hoshakuji': '宝積寺', 'Ujiie': '氏家', 'Kamasusaka': '蒲須坂',
    'Kataoka': '片岡', 'Yaita': '矢板', 'Nozaki': '野崎', 'NishiNasuno': '西那須野',
    'Nasushiobara': '那須塩原', 'Kuroiso': '黒磯',

    # --- [追加] JR日光線 ---
    'Tsuruta': '鶴田', 'Kanuma': '鹿沼', 'Fubasami': '文挟', 'ShimotsukeOsawa': '下野大沢',
    'Imaichi': '今市', 'Nikko': '日光',

    # --- [追加] JR烏山線 ---
    'ShimotsukeHanaoka': '下野花岡', 'Niita': '仁井田', 'Konoyama': '鴻野山',
    'Ogane': '大金', 'Karasuyama': '烏山',

    # 湘南新宿ライン・横須賀線 (大宮～久里浜)
    # Omiya, Akabane, Ikebukuro, Shinjuku, Shibuya, Ebisuは他路線で追加済み
    'NishiOi': '西大井', 'MusashiKosugi': '武蔵小杉', 'ShinKawasaki': '新川崎', 'Yokohama': '横浜', 'Hodogaya': '保土ケ谷',
    'HigashiTotsuka': '東戸塚', 'Totsuka': '戸塚', 'Ofuna': '大船', 'KitaKamakura': '北鎌倉', 'Kamakura': '鎌倉',
    'Zushi': '逗子', 'HigashiZushi': '東逗子', 'Taura': '田浦', 'Yokosuka': '横須賀', 'Kinugasa': '衣笠', 'Kurihama': '久里浜',

    # 東海道線 (横浜～沼津)
    # Yokohama, Totsuka, Ofunaは上記にあり
    'Fujisawa': '藤沢', 'Tsujido': '辻堂', 'Chigasaki': '茅ヶ崎', 'Hiratsuka': '平塚', 'Oiso': '大磯', 'Ninomiya': '二宮',
    'Kozu': '国府津', 'Kamonomiya': '鴨宮', 'Odawara': '小田原', 'Hayakawa': '早川', 'Nebukawa': '根府川', 'Manazuru': '真鶴',
    'Yugawara': '湯河原', 'Atami': '熱海', 'Kannami': '函南', 'Mishima': '三島', 'Numazu': '沼津',

    # 伊東線 (熱海～伊東)
    # Atamiは上記にあり
    'Kinomiya': '来宮', 'IzuTaga': '伊豆多賀', 'Ajiro': '網代', 'Usami': '宇佐美', 'Ito': '伊東',

    # --- [追加] JR常磐線 ---
    # 上野～大津港 (全駅)
    'Ueno': '上野', 'Nippori': '日暮里', 'Mikawashima': '三河島', 'MinamiSenju': '南千住',
    'KitaSenju': '北千住', 'Ayase': '綾瀬', 'Kameari': '亀有', 'Kanamachi':'金町',
    'Matsudo': '松戸', 'KitaMatsudo': '北松戸', 'Mabashi': '馬橋', 'ShinMatsudo': '新松戸',
    'KitaKogane': '北小金', 'Kashiwa': '柏', 'KitaKashiwa': '北柏', 'Abiko': '我孫子',
    'Tennoji': '天王台', 'Toride': '取手', 'Fujishiro': '藤代', 'Ryugasakishi': '龍ケ崎市',
    'Ushiku': '牛久', 'HitachinoUshiku': 'ひたち野うしく', 'Arakawaoki': '荒川沖',
    'Tsuchiura': '土浦', 'Kandatsu': '神立', 'Takahama': '高浜', 'Ishioka': '石岡',
    'Hatori': '羽鳥', 'Iwama': '岩間', 'Tomobe': '友部', 'Uchihara': '内原', 'Akatsuka': '赤塚',
    'Kairakuen': '偕楽園', 'Mito': '水戸', 'Katsuta': '勝田', 'Sawa': '佐和',
    'Tokai': '東海', 'Omika': '大甕', 'HitachiTaga': '常陸多賀', 'Hitachi': '日立',
    'Ogitsu': '小木津', 'Ju-O': '十王', 'Takahagi': '高萩', 'MinamiNakago': '南中郷',
    'Isohara': '磯原', 'Otsuko': '大津港',

    # 大津港～仙台 (主要駅)
    'Nakoso': '勿来', 'Ueda': '植田', 'Izumi': '泉', 'Yumoto': '湯本', 'Iwaki': 'いわき',
    'Hirono': '広野', 'Tomioka': '富岡', 'Okuma': '大熊', 'Futaba': '双葉', 'Namie': '浪江',
    'Odaka': '小高', 'Haranomachi': '原ノ町', 'Soma': '相馬', 'Shinchi': '新地',
    'Watari': '亘理', 'Iwanuma': '岩沼', 'Natori': '名取', 'MinamiSendai': '南仙台',
    'Nagame': '長町', 'Sendai': '仙台',

    # --- [追加] 横浜市営地下鉄 ---
    # ブルーライン
    'Shonandai': '湘南台', 'ShimoIida': '下飯田', 'Tateba': '立場', 'Nakada': '中田', 
    'Odoriba': '踊場', 'Totsuka': '戸塚', 'Maioka': '舞岡', 'Shimonagaya': '下永谷', 'Kaminagaya': '上永谷', 
    'KonanChuo': '港南中央', 'Kamiooka': '上大岡', 'Gumyoji': '弘明寺', 'Maita': '蒔田', 
    'Yoshinocho': '吉野町', 'Bandobashi': '阪東橋', 'IsezakiChojamachi': '伊勢佐木長者町',
    'Kannai': '関内', 'Sakuragicho': '桜木町', 'Takashimacho': '高島町', 'Yokohama': '横浜', 
    'MitsuzawaShimocho': '三ツ沢下町', 'MitsuzawaKamicho': '三ツ沢上町', 'Katakuracho': '片倉町',
    'KishineKoen': '岸根公園', 'ShinYokohama': '新横浜', 'KitaShinYokohama': '北新横浜', 
    'Nippa': '新羽', 'Nakamachidai': '仲町台', 'CenterMinami': 'センター南',
    'CenterKita': 'センター北', 'Nakagawa': '中川', 'Azamino': 'あざみ野',

    # グリーンライン
    'Nakayama': '中山', 'Kawawacho': '川和町', 'TsuzukiFureainooka': '都筑ふれあいの丘',
    'KitaYamata': '北山田', 'HigashiYamata': '東山田', 'Takata': '高田', 
    'HiyoshiHoncho': '日吉本町', 'Hiyoshi': '日吉',
}

# 停車駅パターンを定義する辞書（最終完成版）
STOPPING_PATTERNS = {
    'Shinjuku': {
        'odpt.TrainType:Toei.Express': [
            'Shinjuku', 'Ichigaya', 'Jimbocho', 'BakuroYokoyama', 'Morishita', 'Ojima', 
            'Funabori', 'Motoyawata'
        ],
    },
    'Asakusa': {
        'odpt.TrainType:Toei.AirportLimitedExpress': [
            'Sengakuji', 'Mita', 'Daimon', 'Shimbashi', 'Nihombashi', 'HigashiNihombashi', 
            'Asakusa', 'Oshiage'
        ],
    },
    'Tojo': {
        'odpt.TrainType:Tobu.SemiExpress': [
            'Ikebukuro', 'KamiItabashi', 'Narimasu', 'Wakoshi', 'Asaka', 'Asakadai', 
            'Shiki', 'Yanasegawa', 'Mizuhodai', 'Tsuruse', 'Fujimino', 'KamiFukuoka', 
            'Shingashi', 'Kawagoe', 'Kawagoeshi', 'Kasumigaseki', 'Tsurugashima', 
            'Wakaba', 'Sakado', 'KitaSakado', 'Takasaka', 'HigashiMatsuyama', 
            'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi'
        ],
        'odpt.TrainType:Tobu.Express': [
            'Ikebukuro', 'Narimasu', 'Wakoshi', 'Asaka', 'Asakadai', 'Shiki', 
            'Fujimino', 'Kawagoe', 'Kawagoeshi', 'Kasumigaseki', 'Tsurugashima', 
            'Wakaba', 'Sakado', 'KitaSakado', 'Takasaka', 'HigashiMatsuyama', 
            'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi'
        ],
        'odpt.TrainType:Tobu.RapidExpress': [
            'Ikebukuro', 'Wakoshi', 'Asakadai', 'Kawagoe', 'Kawagoeshi', 'Kasumigaseki', 
            'Tsurugashima', 'Wakaba', 'Sakado', 'KitaSakado', 'Takasaka', 
            'HigashiMatsuyama', 'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi'
        ],
        'odpt.TrainType:Tobu.KawagoeLimitedExpress': [
            'Ikebukuro', 'Asakadai', 'Kawagoe', 'Kawagoeshi', 'Sakado', 'HigashiMatsuyama',
            'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi'
        ],
        'odpt.TrainType:Tobu.TJ-Liner': [
            'Ikebukuro', 'Fujimino', 'Kawagoe', 'Kawagoeshi', 'Sakado', 'HigashiMatsuyama', 
            'ShinrinKoen', 'Tsukinowa', 'MusashiRanzan', 'Ogawamachi'
        ],
    },
}

# 5. チェック間隔
CHECK_INTERVAL_SECONDS = 120

# ---------------------------------------------------------------
# --- Renderを眠らせないためのWebサーバー機能 ---
# ---------------------------------------------------------------
app = Flask('')
@app.route('/')
def home():
    return "I'm alive"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ---------------------------------------------------------------
# --- プログラム本体 ---
# ---------------------------------------------------------------

# グローバル変数（記憶を保持するため）
last_check_date = None
notified_rare_trains = {line: set() for line in LINE_CONFIG.keys()}
previous_trains_by_line = {line: set() for line in LINE_CONFIG.keys()}

# APIから電車の情報を取得する関数
def get_trains_from_api(operator_name):
    token = API_KEYS.get(operator_name)
    if not token:
        print(f"エラー: {operator_name}用のAPIキーが設定されていません。")
        return None
    
    if operator_name in ["Tobu", "JR-East"]:
        base_url = "https://api-challenge.odpt.org/api/v4/odpt:Train"
    else:
        base_url = "https://api.odpt.org/api/v4/odpt:Train"
        
    target_url = f"{base_url}?odpt:operator=odpt.Operator:{operator_name}&acl:consumerKey={token}"
    
    try:
        response = requests.get(target_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"エラー発生！{operator_name}のAPIから情報を取得できませんでした。エラー内容: {e}")
        return None

# 運行情報の「文字」を取得するための関数（アップグレード版）
def get_train_information(operator_name, line_api_name):
    token = API_KEYS.get(operator_name)
    if not token: return None

    if operator_name in ["Tobu", "JR-East"]:
        base_url = "https://api-challenge.odpt.org/api/v4/odpt:TrainInformation"
    else:
        base_url = "https://api.odpt.org/api/v4/odpt:TrainInformation"
        
    target_url = f"{base_url}?odpt:operator=odpt.Operator:{operator_name}&acl:consumerKey={token}"
    
    try:
        response = requests.get(target_url)
        info_data = response.json()
        if info_data:
            # ↓↓↓↓↓↓↓↓↓★ここが改造ポイント！↓↓↓↓↓↓↓↓↓
            # 全ての運行情報をループで確認
            for info in info_data:
                # 探している路線の情報が見つかったら、その情報だけを返す
                if info.get("odpt:railway") == f"odpt.Railway:{line_api_name}":
                    return info.get("odpt:trainInformationText", {}).get("ja")
            # ↑↑↑↑↑↑↑↑↑↑★ここまで改造！↑↑↑↑↑↑↑↑↑↑
        return "平常運転" # 該当路線の情報が見つからなければ平常運転とみなす
    except Exception as e:
        print(f"エラー発生！{operator_name}の運行情報APIから情報を取得できませんでした。")
        return None

# 運行情報テキストから「運転見合わせ区間」を抜き出す専門家（最終FIX版）
def extract_incident_section(text):
    if text is None:
        return None, None
    
    # 探し出すパターンのリスト（「しております」に対応）
    patterns = [
        # パターン1：「〇〇～〇〇駅間の上下線で運転を見合わせ(し?)て(います/おります)」
        r'([^\s～]+)～([^\s～]+)駅間の上下線で運転を見合わせ(?:ています|し?ております)',
        
        # パターン2：「〇〇～〇〇駅間で運転を見合わせ(し?)て(います/おります)」
        r'([^\s～]+)～([^\s～]+)駅間で運転を見合わせ(?:ています|し?ております)',
        
        # パターン3：「〇〇～〇〇間で運転を見合わせ(し?)て(います/おります)」
        r'([^\s～]+)～([^\s～]+)間で運転を見合わせ(?:ています|し?ております)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # パターンに一致した場合、1番目と2番目の駅名を返す
            return match.group(1), match.group(2)
    
    # どのパターンにも一致しなかった場合は何も返さない
    return None, None
    
# 全路線の情報を整理する関数
def get_all_trains_by_line():
    all_trains_data = []
    operators_to_fetch = {config['operator'] for config in LINE_CONFIG.values()}
    for operator in operators_to_fetch:
        api_data = get_trains_from_api(operator)
        if api_data:
            all_trains_data.extend(api_data)
    if not all_trains_data:
        return None

    trains_by_line = {line: set() for line in LINE_CONFIG.keys()}
    for train in all_trains_data:
        required_keys = ["odpt:railway", "odpt:trainNumber", "odpt:trainType", "odpt:fromStation", "odpt:railDirection"]
        if not all(key in train and train.get(key) for key in required_keys): continue
        
        line_api_name_full = train["odpt:railway"].split(':')[-1]
        line_key = None
        for key, config in LINE_CONFIG.items():
            if config['api_name'] == line_api_name_full:
                line_key = key
                break
        
        if line_key and line_key in trains_by_line:
            train_number = train["odpt:trainNumber"]
            train_type = train["odpt:trainType"]
            from_station = train["odpt:fromStation"].split('.')[-1]
            to_station_full = train.get("odpt:toStation")
            to_station = to_station_full.split('.')[-1] if to_station_full else None
            destination_station_list = train.get("odpt:destinationStation")
            destination_name = destination_station_list[-1].split('.')[-1] if destination_station_list else None
            rail_direction = train["odpt:railDirection"]
            trains_by_line[line_key].add((train_number, train_type, destination_name, from_station, to_station, rail_direction))
    return trains_by_line

# Discordに接続するための準備
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Botが起動しました！ ユーザー名: {client.user}')
    check_train_info.start()

# 判定ロジックをまとめたヘルパー関数
def is_operation_rare(operation, train_number, timetable, conditional_timetable):
    # 判定1：通常の定期運用リストに載っているか？
    if operation in timetable:
        return False # 定期運用なので、珍しくない

    # 判定2：条件付きリストに載っているか？
    is_conditionally_safe = False
    for rule in conditional_timetable:
        if rule['operation'] == operation:
            if train_number in rule['allowed_numbers']:
                is_conditionally_safe = True
                break
    
    if is_conditionally_safe:
        return False # 条件付きで定期運用なので、珍しくない

    # どちらでもなければ、珍しい運用
    return True

@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_train_info():
    # --- 準備：グローバル変数を呼び出す ---
    global last_check_date, previous_trains_by_line, notified_rare_trains
    
    # --- STEP 1: 日付が変更されたかチェック ---
    today = date.today()
    if last_check_date != today:
        print(f"日付が変わりました。({last_check_date} -> {today}) 通知履歴をリセットします。")
        for key in notified_rare_trains:
            notified_rare_trains[key].clear()
        last_check_date = today

    print(f"{CHECK_INTERVAL_SECONDS}秒ごとに全路線の運行情報をチェックします...")
    
    # --- STEP 2: 全路線の最新情報を取得 ---
    all_trains_by_line = get_all_trains_by_line()
    if all_trains_by_line is None:
        return

    # --- STEP 3: 路線ごとに、一つずつチェックを開始 ---
    for line_key, config in LINE_CONFIG.items():
        # この路線で使う設定を読み込む
        line_jp_name = config['jp_name']
        timetable = config.get('timetable', set())
        conditional_timetable = config.get('conditional_timetable', [])
        type_dict = config.get('type_dict', {})
        handover_stations = config.get('handover_stations', {})
        station_order = config.get('station_order', [])
        ignore_rules = config.get('ignore_disappearances', [])
        current_trains = all_trains_by_line.get(line_key, set())
        
        # --- このサイクルで通知すべき珍しい電車をすべて集めるための箱 ---
        final_rare_trains_to_notify = set()

        # --- STEP 4: 「消滅検知」と思考プロセス (東上線限定) ---
        if line_key == 'Tojo':
            previous_trains = previous_trains_by_line.get(line_key, set())
            previous_train_numbers = {train[0] for train in previous_trains}
            current_train_numbers = {train[0] for train in current_trains}
            disappeared_train_numbers = previous_train_numbers - current_train_numbers
            
            disappeared_trains_full_data = {train for train in previous_trains if train[0] in disappeared_train_numbers}

            truly_disappeared_trains = set()
            for train in disappeared_trains_full_data:
                _, _, destination_en, from_station_en, to_station_en, _ = train
                if from_station_en == destination_en or to_station_en == destination_en: continue
                is_normal_handover = False
                for station, valid_dests in handover_stations.items():
                    if from_station_en == station and destination_en in valid_dests:
                        is_normal_handover = True
                        break
                if is_normal_handover: continue
                is_ignored = False
                for rule in ignore_rules:
                    if destination_en == rule['destination'] and from_station_en in rule['last_seen_at']:
                        is_ignored = True
                        break
                if is_ignored: continue
                truly_disappeared_trains.add(train)
            
            if truly_disappeared_trains:
                train_info_text = get_train_information(config['operator'], config['api_name'])
                incident_section = extract_incident_section(train_info_text)
                inv_station_dict = {v: k for k, v in STATION_DICT.items()}

                for train in truly_disappeared_trains:
                    train_number, train_type_en, destination_en, from_station_en, to_station_en, rail_direction = train
                    
                    predicted_dest_en = destination_en
                    predicted_type_en = train_type_en
                    
                    is_subway_related = train_number[-1] in ['T', 'K', 'S']
                    is_normal_delay = train_info_text and "遅れ" in train_info_text and "運転を見合わせ" not in train_info_text

                    if is_normal_delay:
                        if train_type_en == 'odpt.TrainType:Tobu.Express':
                            predicted_type_en = 'odpt.TrainType:Tobu.SemiExpress'
                        if is_subway_related:
                            if destination_en == 'Shinrinkoen':
                                predicted_dest_en = inv_station_dict.get('坂戸')
                            elif destination_en == 'Kawagoeshi':
                                predicted_dest_en = inv_station_dict.get('上福岡')
                    elif train_info_text and "運転を見合わせています" in train_info_text and "直通運転も中止しています" in train_info_text:
                        if destination_en in handover_stations.get('Wakoshi', []):
                            if incident_section in ["上板橋～成増", "池袋～和光市"]:
                                predicted_dest_en = inv_station_dict.get('志木')
                            else:
                                try:
                                    s1_jp, s2_jp = incident_section.split('～')
                                    idx_s1 = station_order.index(inv_station_dict[s1_jp])
                                    idx_s2 = station_order.index(inv_station_dict[s2_jp])
                                    if 'Inbound' in rail_direction: predicted_dest_en = station_order[max(idx_s1, idx_s2)]
                                    elif 'Outbound' in rail_direction: predicted_dest_en = station_order[min(idx_s1, idx_s2)]
                                except Exception: pass
                    elif train_info_text and "直通運転を中止しています" in train_info_text:
                        if destination_en in handover_stations.get('Wakoshi', []):
                            predicted_dest_en = inv_station_dict.get('志木')
                    elif incident_section and station_order:
                        try:
                            s1_jp, s2_jp = incident_section.split('～')
                            idx_from = station_order.index(from_station_en)
                            idx_s1 = station_order.index(inv_station_dict[s1_jp])
                            idx_s2 = station_order.index(inv_station_dict[s2_jp])
                            section_start_idx = min(idx_s1, idx_s2)
                            section_end_idx = max(idx_s1, idx_s2)
                            if 'Inbound' in rail_direction and idx_from > section_end_idx:
                                predicted_dest_en = station_order[section_end_idx]
                            elif 'Outbound' in rail_direction and idx_from < section_start_idx:
                                predicted_dest_en = station_order[section_start_idx]
                        except Exception: pass
                    
                    predicted_operation = (predicted_type_en, predicted_dest_en)
                    
                    if is_operation_rare(predicted_operation, train_number, timetable, conditional_timetable):
                        final_rare_trains_to_notify.add((train, predicted_type_en, predicted_dest_en))

        # --- STEP 5: 通常の「珍運用」を検知 (全路線) ---
        for train in current_trains:
            train_number, train_type_en, destination_en, _, _, _ = train
            current_operation = (train_type_en, destination_en)

            if is_operation_rare(current_operation, train_number, timetable, conditional_timetable):
                if not any(train_number == t[0][0] for t in final_rare_trains_to_notify):
                    final_rare_trains_to_notify.add((train, train_type_en, destination_en))
        
        # --- STEP 6: 最終的な通知処理 ---
        new_rare_trains_to_notify = set()
        for train_data in final_rare_trains_to_notify:
            train_number = train_data[0][0]
            if train_number not in notified_rare_trains[line_key]:
                new_rare_trains_to_notify.add(train_data)

        if new_rare_trains_to_notify:
            user = await client.fetch_user(NOTIFICATION_USER_ID)
            if user:
                message_parts = []
                for train_data in new_rare_trains_to_notify:
                    original_train, final_type_en, final_dest_en = train_data
                    train_number, _, _, from_station_en, to_station_en, rail_direction = original_train
                    
                    is_subway_related = train_number[-1] in ['T', 'K', 'S']
                    train_type_jp = type_dict.get(final_type_en, final_type_en)
                    
                    destination_jp = STATION_DICT.get(final_dest_en)
                    if destination_jp is None:
                        if final_dest_en is None:
                            if line_key in ['Saikyo', 'ShonanShinjuku']:
                                destination_jp = '蛇窪信号所'
                            elif is_subway_related:
                                destination_jp = "地下鉄方面"
                            else:
                                destination_jp = "行先不明"
                        else:
                            destination_jp = final_dest_en # 辞書にない場合はAPI名をそのまま使う
                    
                    from_station_jp = STATION_DICT.get(from_station_en, from_station_en)
                    
                    if to_station_en:
                        to_station_jp = STATION_DICT.get(to_station_en, to_station_en)
                        location_text = f"{from_station_jp}→{to_station_jp}を走行中"
                    else:
                        from_station_jp = STATION_DICT.get(from_station_en, from_station_en)
                        if 'Local' in final_type_en:
                            location_text = f"{from_station_jp}に停車中"
                        else:
                            line_patterns = STOPPING_PATTERNS.get(line_key, {})
                            if final_type_en in line_patterns:
                                if from_station_en in line_patterns[final_type_en]:
                                    location_text = f"{from_station_jp}に停車中"
                                else:
                                    location_text = f"{from_station_jp}を通過中"
                            else:
                                location_text = f"{from_station_jp}に停車中"

                    line1 = f"[{line_jp_name}] {train_type_jp} {destination_jp}行き ({train_number})"
                    train_info = f"{line1}\n{location_text}"
                    if line_key == 'Tojo' and original_train in truly_disappeared_trains:
                        train_info += "\n※行先情報は予測のため不正確な場合があります。"
                    message_parts.append(train_info)
                
                final_body = "\n\n".join(message_parts)
                await user.send(final_body)

                for train_data in new_rare_trains_to_notify:
                    notified_rare_trains[line_key].add(train_data[0][0])
                print(f"[{line_jp_name}] 通知を送信しました: {new_rare_trains_to_notify}")

        # --- STEP 7: 短期記憶の更新 (東上線限定) ---
        if line_key == 'Tojo':
            previous_trains_by_line[line_key] = current_trains
    

# Botを起動する
try:
    keep_alive()
    client.run(DISCORD_BOT_TOKEN)
except Exception as e:
    print(f"Botの起動に失敗しました: {e}")
