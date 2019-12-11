#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
#  Ctrl + Alt + L - форматирование кода
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


class ServerProtocol(LineOnlyReceiver):
    factory: 'Server'
    login: str = None

    def connectionMade(self):
        # Потенциальный баг для внимательных =)
        self.factory.clients.append(self)

    def connectionLost(self, reason=connectionDone):
        self.factory.clients.remove(self)
        self.factory.logins.remove(self.login)

    def lineReceived(self, line: bytes):
        content = line.decode()

        if self.login is not None:
            content = f"Message from {self.login}: {content}"

            if len(self.factory.messages) == 10:
                self.factory.messages.pop(0)

            self.factory.messages.append(content.encode())

            for user in self.factory.clients:
                if user is not self:
                    user.sendLine(content.encode())
        else:
            # login:admin -> admin
            if content.startswith("login:") and not self.factory.logins.__contains__(content.replace("login:", "")):
                self.login = content.replace("login:", "")
                self.factory.logins.append(self.login)
                self.sendLine("Welcome!".encode())
                if len(self.factory.messages) != 0:
                    self.send_history()
            else:
                if self.factory.logins.__contains__(content.replace("login:", "")):
                    login = content.replace("login:", "")
                    self.sendLine(f"Логин {login} занят, попробуйте другой".encode())
                    self.transport.loseConnection()
                else:
                    self.sendLine("Invalid login".encode())

    def send_history(self):
        self.sendLine("Here you can see history of out chat:".encode())
        for msg in self.factory.messages:
            self.sendLine(msg)


class Server(ServerFactory):
    protocol = ServerProtocol
    clients: list
    logins: list
    messages: list

    def startFactory(self):
        self.logins = []
        self.clients = []
        self.messages = []
        print("Server started")

    def stopFactory(self):
        print("Server closed")


reactor.listenTCP(1234, Server())
reactor.run()
