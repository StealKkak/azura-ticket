import configparser
import os

from pathlib import Path

configPath = Path("config.ini")
config = configparser.ConfigParser()

if not configPath.exists():
    config["setting"] = {
        "api_only": False
    }

    with configPath.open("w", encoding="utf-8") as f:
        config.write(f)
        print("config.ini 파일이 생성되었습니다. 수정하고 다시 실행해주세요!")
        os.abort()

config.read(configPath, encoding="utf-8")

api_only = config["setting"].getboolean("api_only", False)