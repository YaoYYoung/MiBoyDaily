import asyncio
from pathlib import Path
from datetime import datetime
import os
import pytz
import aiohttp
import schedule
from aiohttp import ClientSession
from miservice import MiAccount, MiNAService, MiIOService, miio_command
import argparse

AM_I_HERE_COMMAND = "2-1078"
TIMEZONE = "Asia/Shanghai"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN is not set")

# change it to yours
REPO_NAME = "yihong0618/2024"
ACTION_ID = "81220935"


class MiBoyDaily:
    def __init__(self, account, password, here_did, speaker_did):
        self.mi_session = ClientSession()
        self.account = account
        self.password = password
        self.here_did = here_did
        self.speaker_did = speaker_did
        self.mi_token_home = Path.home() / ".mi.token"

    async def login_miboy(self):
        account = MiAccount(
            self.mi_session,
            self.account,
            self.password,
            str(self.mi_token_home),
        )
        # Forced login to refresh to refresh token
        await account.login("micoapi")
        self.mina_service = MiNAService(account)
        self.miio_service = MiIOService(account)

        # From xiaogpt
        hardware_data = await self.mina_service.device_list()
        # fix multi xiaoai problems we check did first
        # why we use this way to fix?
        # some videos and articles already in the Internet
        # we do not want to change old way, so we check if miotDID in `env` first
        # to set device id

        for h in hardware_data:
            if did := self.speaker_did:
                if h.get("miotDID", "") == str(did):
                    self.speaker_did = h.get("deviceID")
                    break
                else:
                    continue
            if h.get("hardware", "") == self.config.hardware:
                self.speaker_did = h.get("deviceID")
                break
        else:
            raise Exception(
                f"we have no hardware: {self.config.hardware} please use `micli mina` to check"
            )

    async def get_am_i_here(self):
        data = await miio_command(
            self.miio_service,
            self.here_did,
            AM_I_HERE_COMMAND,
        )
        return data

    async def close(self):
        await self.mi_session.close()

    async def say_good_morning_to_me(self, value):
        await self.mina_service.text_to_speech(self.speaker_did, value)

    async def call_github_action_workflow(self):
        """
        Trigger GitHub Actions workflow using REST API
        """
        url = f"https://api.github.com/repos/{REPO_NAME}/actions/workflows/{ACTION_ID}/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}",
        }
        # GitHub Actions API requires a ref
        data = {"ref": "main", "inputs": {"message": "hello"}}  # branch

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if (
                    response.status == 204
                ):  # GitHub API returns 204 No Content on success
                    print("Successfully triggered workflow")
                    return True
                else:
                    print(f"Failed to trigger workflow: {response.status}")
                    return False

    async def say_hello_to_me_when_i_am_back(self):
        await self.say_good_morning_to_me("早上好")


def parse_args():
    parser = argparse.ArgumentParser(description="MiBoyDaily automation script")
    parser.add_argument(
        "--account", type=str, required=True, help="Mi account email/phone"
    )
    parser.add_argument(
        "--password", type=str, required=True, help="Mi account password"
    )
    parser.add_argument(
        "--here-did", type=str, required=True, help="Device ID for presence detection"
    )
    parser.add_argument(
        "--speaker-did", type=str, required=True, help="Device ID for speaker"
    )
    return parser.parse_args()


async def morning_task(account, password, here_did, speaker_did):
    beijing_tz = pytz.timezone("Asia/Shanghai")
    miboy = MiBoyDaily(
        account=account, password=password, here_did=here_did, speaker_did=speaker_did
    )
    await miboy.login_miboy()

    while True:
        current_time = datetime.now(beijing_tz)
        current_hour = current_time.hour

        # if current hour is after 6 AM, stop the task
        if current_hour >= 6:
            print("After 6 AM, stopping...")
            await miboy.close()
            break

        if current_hour < 4:
            print("Before 4 AM, waiting...")
            await asyncio.sleep(60)
            continue

        data = await miboy.get_am_i_here()
        if data and data[0] == 1:
            # means I get up already
            print("I am up")
            await miboy.say_hello_to_me_when_i_am_back()
            await miboy.call_github_action_workflow()
            await miboy.close()
            break
        elif data and data[0] == 0:
            # means I am sleeping
            print("I am sleeping")
            await asyncio.sleep(5)
        else:
            print("other status")
            await asyncio.sleep(5)


async def back_home_task():
    pass


async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    args = parse_args()
    schedule.every().day.at("04:00", TIMEZONE).do(
        lambda: asyncio.create_task(
            morning_task(args.account, args.password, args.here_did, args.speaker_did)
        )
    )

    await run_schedule()


if __name__ == "__main__":
    print("starting...")
    asyncio.run(main())
