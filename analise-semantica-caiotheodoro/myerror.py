import configparser
import inspect

config = None

class MyError():

  def __init__(self, et):
    self.config = configparser.RawConfigParser()
    self.config.read('ErrorMessages.properties')
    self.errorType = et
    self.messageList = []

  def newError(self, key, **data):
    message = ''
    if(key):
      message = self.config.get(self.errorType, key)
    if(data):
      message = message.format(*data['value'])
      
      if message not in self.messageList:
        
        self.messageList.append(message)
        return message
      else:
        return ''
    return message
    #print(message)
    #frame = inspect.stack()[1][0]

    #print(inspect.getframeinfo(frame).__getitem__(0))
    #print(inspect.getframeinfo(frame).__getitem__(1))


# le = MyError('LexerErrors')

# print(le.newError('ERR-LEX-001'))
