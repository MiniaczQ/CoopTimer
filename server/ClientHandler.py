import socket
from threading import Thread


class ClientHandler:
    def __init__(self, parent, c, addr) -> None:
        self.parent = parent
        self.clientSocket: socket.socket = c
        self.addr = addr
        self.running = True
        self.thread = Thread(target=self.loop)
        self.thread.start()

    def loop(self) -> None:
        try:
            while self.running:
                msg = self.clientSocket.recv(1024).decode()
                if msg == "quit":
                    self.running = False
                    self.send("end")
                elif self.parent.password is not None:
                    if msg == self.parent.password+"pause":
                        self.parent.togglePause()
                    elif msg == self.parent.password+"reset":
                        self.parent.resetTimer()
        except:
            pass
        self.detachFromClient()

    def detachFromClient(self) -> None:
        if self.parent is not None:
            self.parent.removeClient(self)
            self.parent = None

    def send(self, msg: str) -> None:
        self.clientSocket.send(msg.encode())

    def stop(self) -> None:
        self.running = False
        self.send("end")
        try:
            self.clientSocket.close()
        except:
            pass
        self.detachFromClient()