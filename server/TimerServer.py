from threading import Thread
import time
import socket
from ClientHandler import ClientHandler


class TimerServer:
    def __init__(self, addr="127.0.0.1", port=25564, password=None) -> None:
        self.addr = addr
        self.port = port
        self.password = password

        self.socket = socket.socket()

        self.clients = []
        self.running = False
        self.startTime = time.time()
        self.pauseTime = 0
        self.timerStatus = "stopped"

    def start(self) -> None:
        if not self.running:
            self.running = True

            self.socket.bind((self.addr, self.port))
            self.socket.listen(50)

            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.acceptConnectionsThread = Thread(
                target=self.acceptConnectionsLoop)
            self.acceptConnectionsThread.start()

    def togglePause(self) -> None:
        if self.timerStatus == "running":
            self.pauseTimer()
        else:
            self.startTimer()

    def startTimer(self) -> None:
        if self.timerStatus != "running":
            self.startTime = time.time() - self.pauseTime
            self.timerStatus = "running"
        self.updateClients()

    def resetTimer(self) -> None:
        if self.timerStatus != "stopped":
            self.pauseTime = 0
            self.timerStatus = "stopped"
        self.updateClients()

    def pauseTimer(self) -> None:
        if self.timerStatus == "running":
            self.pauseTime = time.time()-self.startTime
            self.timerStatus = "paused"
        self.updateClients()

    def updateClient(self, client) -> None:
        if self.timerStatus == "stopped":
            client.send("stop")
        else:
            client.send(self.timerStatus+":"+str(self.getTime()))

    def updateClients(self) -> None:
        for client in self.clients:
            self.updateClient(client)

    def sendToAll(self, msg) -> None:
        for client in self.clients:
            client.send(msg)

    def acceptConnectionsLoop(self) -> None:
        while self.running:
            try:
                c, addr = self.socket.accept()
                client = ClientHandler(self, c, addr)
                if self.running:
                    self.clients.append(client)
                    print("[Timer Server] Client '"+str(addr)+"' connected.")
                    self.updateClient(client)
            except:
                pass

    def setTime(self, x) -> None:
        self.pauseTime = x
        self.startTime = time.time()-x

    def getTime(self) -> float:
        if self.timerStatus == "stopped":
            return 0.0
        elif self.timerStatus == "running":
            return time.time()-self.startTime
        elif self.timerStatus == "paused":
            return self.pauseTime

    def kill(self) -> None:
        for i in self.clients:
            i.stop()
        self.running = False
        self.socket.close()

    def removeClient(self, client) -> None:
        try:
            self.clients.remove(client)
            print("[Timer Server] Client '"+str(client.addr)+"' disconnected.")
        except:
            pass
