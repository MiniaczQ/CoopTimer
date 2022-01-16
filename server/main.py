import asyncio
import json
import os
import signal

from LineChecker import LineChecker
from LogsTracker import LogsTracker
from TimerServer import TimerServer


async def main() -> None:
    jsonDict = {}
    if os.path.isfile("coop_timer_server.json"):
        with open("coop_timer_server.json", "r") as jsonFile:
            jsonDict = json.load(jsonFile)
            jsonFile.close()

    path = os.path.join(jsonDict.get("logs", "logs"), "latest.log")

    lt = LogsTracker(path)
    ts = TimerServer(jsonDict.get("address", "127.0.0.1"), jsonDict.get(
        "port", 25564), jsonDict.get("password", None))

    lt.addChecker(LineChecker(ts.startTimer, "Set the time to 0"))
    lt.addChecker(LineChecker(ts.resetTimer, "Stopping the server"))

    ts.start()
    lt.start()

    stop_event = asyncio.Event()

    def handle_interrupt(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_interrupt)
    signal.signal(signal.SIGINT, handle_interrupt)

    await stop_event.wait()

    lt.stop()
    ts.kill()

if __name__ == "__main__":
    asyncio.run(main())