from Exscript.protocols import Telnet
from multiprocessing import Process

class TelnetConfigurator(Process):
    def __init__(self, host_ip, router_telnet_port, router_config_file):
        super().__init__()
        self.connection = Telnet()
        self.host = host_ip
        self.port = router_telnet_port
        self.config = router_config_file

    def run(self):
        self.connection.connect(self.host, self.port)
        self.connection.send("configure terminal \r")
        with open(self.config, 'r') as f: 
            for config_line in f :
                self.connection.send(config_line+"\r")
        self.connection.send("exit\r")


