class ChannelExporter:   
    def __init__(self, slack_token):        
        if slack_token != "TEST":
            self._client = "dummy"                    
        else:
            self._client = None

    @property
    def client(self):
        return self._client


x = ChannelExporter("NOT-TEST")
print(x)

y = ChannelExporter("TEST")
print(y)