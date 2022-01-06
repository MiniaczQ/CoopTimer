from threading import Thread
import time
import socket
import tkinter as tk
import tkinter.font as tkFont
import os
import json
import clipboard
import global_hotkeys


class DragableWindow:
    def __init__(self):
        self.bind("<Button 1>", self.click)
        self.bind("<B1-Motion>", self.drag)
        self.hasBorder = True
        self.overrideredirect(0)
        self.x = 0
        self.y = 0
        self.ox, self.oy = self.winfo_x, self.winfo_y
        self.wm_attributes("-topmost", 1)

    def switchBorder(self, x=0):
        if self.hasBorder:
            self.hasBorder = False
            self.overrideredirect(1)
        else:
            self.hasBorder = True
            self.overrideredirect(0)

    def click(self, event):
        self.x, self.y = (event.x, event.y)

    def drag(self, event):
        x, y = (event.x-self.x, event.y-self.y)
        self.geometry(f"+{x+self.ox()}+{y+self.oy()}")


class TimerClient:
    def __init__(self, parent=None):
        self.parent = parent
        self.socket = None
        self.status = "disconnected"
        self.startTime = time.time()
        self.pauseTime = 0.0
        self.failed = False
        self.password = None
        self.connecting = False

    def getTime(self):
        if self.status in ["disconnected", "connecting", "stopped"]:
            return 0
        elif self.status == "paused":
            return self.pauseTime
        elif self.status == "running":
            return time.time()-self.startTime

    def isConnected(self):
        if self.status in ["disconnected", "connecting"]:
            return False
        else:
            return True

    def isConnecting(self):
        return self.connecting

    def connect(self, addr="127.0.0.1", port=25564):
        if not self.connecting:
            self.connecting = True
            try:
                if self.socket != None:
                    self.disconnect()

                self.socket = socket.socket()
                fails = 0
                for i in range(3):
                    #print("Connection attempt "+str(i+1))
                    try:
                        self.status = "connecting"
                        self.socket.connect((addr, port))
                        break
                    except:
                        fails += 1
                if fails == 3:
                    #print("Connection failed")
                    self.status = "disconnected"
                    self.failed = True
                else:
                    self.status = "stopped"
                    self.recvLoopThread = Thread(target=self.recvLoop)
                    self.recvLoopThread.start()
            except:
                self.disconnect()
            self.connecting = False

    def setPassword(self, password=None):
        self.password = password

    def disconnectionEvent(self):
        self.status = "disconnected"
        # print("Disconnected")
        try:
            self.socket.close()
        except:
            pass

    def getFailed(self):
        if self.failed:
            self.failed = False
            return True
        else:
            return False

    def startTimeEvent(self):
        if self.parent is not None:
            self.parent.startTimeEvent()

    def disconnect(self):
        if self.status != "disconnected":
            try:
                self.socket.send("quit".encode())
            except:
                pass

            self.disconnectionEvent()
        else:
            pass  # print("Already disconnected.")

    def reqPauseTimer(self):
        if self.password is not None and self.isConnected():
            self.socket.send((self.password+"pause").encode())

    def reqResetTimer(self):
        if self.password is not None and self.isConnected():
            self.socket.send((self.password+"reset").encode())

    def recvLoop(self):
        lSocket = self.socket
        while True:
            try:
                msg = lSocket.recv(1024).decode()
                print(msg)
                if msg == "end":
                    self.disconnectionEvent()
                    break
                else:
                    args = msg.split(":")
                    if args[0] == "stop":
                        self.status = "stopped"
                    elif args[0] == "paused":
                        self.status = "paused"
                        self.pauseTime = float(args[1])
                    elif args[0] == "running":
                        wasStopped = False
                        if self.status == "stopped":
                            wasStopped = True
                        self.status = "running"
                        self.startTime = time.time()-float(args[1])
                        if wasStopped:
                            self.startTimeEvent()

            except:
                self.disconnectionEvent()
                break


class TCApp(tk.Tk, DragableWindow):
    def __init__(self):
        tk.Tk.__init__(self)
        DragableWindow.__init__(self)
        self.title("Timer Client")
        self.config(bg="black", width=500, height=100)
        self.wm_attributes("-topmost", True)

        self.timerClient = TimerClient(self)

        self.label = tk.Label(
            self, text="DC", bg="black", fg="white")
        self.label.bind("<B3-Motion>", lambda *x: None)
        self.label.place(x=0, y=0)

        self.firstLoadDone = False
        self.loadSettings()

        self.rClickPos = [0, 0]
        self.controlsEnabled = False
        self.connectStartTime = time.time()

        self.bind("r", self.loadSettings)
        self.bind("R", self.loadSettings)

        self.bind("<Control-C>", self.copy)
        self.bind("<Control-c>", self.copy)
        self.bind("<Control-S>", self.save)
        self.bind("<Control-s>", self.save)
        self.bind("<B3-Motion>", self.rDrag)
        self.bind("<Button-3>", self.rClick)

        self.after(15, self.loop)

    def rDrag(self, pos):
        xDif = (pos.x - self.rClickPos.x)
        yDif = (pos.y - self.rClickPos.y)
        self.rClickPos = pos
        self.settings["textPos"][0] += xDif
        self.settings["textPos"][1] += yDif

        self.label.place(
            x=self.settings["textPos"][0], y=self.settings["textPos"][1])

    def rClick(self, pos):
        self.rClickPos = pos

    def copy(self, *x):
        clipboard.copy(self.convertSeconds(self.timerClient.getTime()))

    def loadSettings(self, *x):
        self.settings = {}
        jsonDict = {}
        if os.path.isfile("coop_timer_client.json"):
            with open("coop_timer_client.json", "r") as jsonFile:
                jsonDict = json.load(jsonFile)
                jsonFile.close()

        self.settings["size"] = jsonDict.get("size", [500, 100])

        self.settings["textPos"] = jsonDict.get("textPos", [0, 0])

        self.settings["fontName"] = jsonDict.get("fontName", "Minecraftia")
        self.settings["fontSize"] = jsonDict.get("fontSize", 50)

        self.settings["accuracy"] = jsonDict.get("accuracy", 3)

        self.settings["address"] = jsonDict.get("address", "127.0.0.1")
        self.settings["port"] = jsonDict.get("port", 25564)

        self.geometry(str(self.settings["size"][0]) + "x" +
                      str(self.settings["size"][1]))

        self.label.place(
            x=self.settings["textPos"][0], y=self.settings["textPos"][1])

        self.label.config(font=tkFont.Font(
            font=(self.settings["fontName"], self.settings["fontSize"], tkFont.NORMAL)))

        password = jsonDict.get("password", None)

        if password is not None:
            self.timerClient.setPassword(password)
            self.settings["password"] = password

        hotkeys = jsonDict.get("hotkeys", None)

        if hotkeys is not None:
            hotkeys["reset"] = hotkeys.get("reset", ["o"])
            hotkeys["pause"] = hotkeys.get("pause", ["p"])
            self.settings["hotkeys"] = hotkeys

        if self.firstLoadDone:
            if self.controlsEnabled:
                global_hotkeys.stop_checking_hotkeys()
                global_hotkeys.clear_hotkeys()

            if hotkeys is not None:
                self.controlsEnabled = True
                if hotkeys["reset"][-1] == hotkeys["pause"][-1] and len(hotkeys["reset"]) > len(hotkeys["pause"]):
                    global_hotkeys.register_hotkeys([
                        [hotkeys["pause"], self.timerClient.reqPauseTimer, None],
                        [hotkeys["reset"], self.timerClient.reqResetTimer, None]
                    ])
                else:
                    global_hotkeys.register_hotkeys([
                        [hotkeys["reset"], self.timerClient.reqResetTimer, None],
                        [hotkeys["pause"], self.timerClient.reqPauseTimer, None]
                    ])

            if not self.timerClient.isConnecting():
                Thread(target=self.connect).start()

            if self.controlsEnabled:
                global_hotkeys.start_checking_hotkeys()

    def connect(self):
        print("Attempting connection...")
        self.connectStartTime = time.time()
        self.timerClient.connect(
            addr=self.settings["address"], port=self.settings["port"])

    def save(self, *x):
        self.settings["size"] = [self.winfo_width(), self.winfo_height()]
        with open("coop_timer_client.json", "w+") as jsonFile:
            json.dump(self.settings, jsonFile, indent=4)
            jsonFile.close()

    def loop(self):
        self.after(1000//65, self.loop)
        if not self.firstLoadDone:
            self.firstLoadDone = True

        if self.timerClient.isConnected():
            self.label.config(text=self.convertSeconds(
                self.timerClient.getTime(), self.settings["accuracy"]))
        elif self.timerClient.isConnecting():

            self.label.config(
                text=[".", "..", "...", "....", ".....", "......", ".....", "....", "...", ".."][(int((time.time()-self.connectStartTime)*10) % 10)])
        else:
            self.label.config(text="DC")

    def startTimeEvent(self):
        pass

    @staticmethod
    def convertSeconds(seconds: float, accuracy=3):
        x = int(seconds*(10**accuracy))/10**accuracy
        if accuracy < 1:
            Seconds = str(int(x-(int(x)-(int(x) % 60))))
        else:
            Seconds = f"%.{str(accuracy)}f" % (x-(int(x)-(int(x) % 60)))
        if x % 60 < 10:
            Seconds = "0" + Seconds
        Minutes = str(int(x/(60)) % 60)
        Hours = str(int(x/(60*60)))

        if len(Minutes) < 2 and Hours != "0":
            Minutes = "0" + Minutes

        return ((Hours+":") if Hours != "0" else "")+Minutes+":"+Seconds


if __name__ == "__main__":
    tca = TCApp()
    tca.mainloop()
    tca.timerClient.disconnect()
