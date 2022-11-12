import main
import rpyc
import configs

rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True
conn = rpyc.classic.connect(configs.SERVER_HOST)

class MyService(rpyc.Service):
    def exposed_get_main_message_logs(self):
        return main.message_logs

# Start the rpyc server
from rpyc.utils.server import ThreadedServer
from threading import Thread
protocol_config = {"allow_all_attrs": True, "allow_setattr": True, "allow_delattr": True}
server = ThreadedServer(MyService, port = configs.SERVER_PORT, protocol_config = protocol_config)
t = Thread(target = server.start)
t.daemon = True
t.start()

# The main logic
main = main.mamieBot()
main.run()
