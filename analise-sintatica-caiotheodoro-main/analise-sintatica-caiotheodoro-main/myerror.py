import configparser
import inspect

config = None

class MyError():

  def __init__(self, et):
    self.config = configparser.RawConfigParser()
    with open('ErrorMessages.properties', encoding='utf-8') as f:
      self.config.read_file(f)
    self.errorType = et

  def newError(self, key, **data):
    message = ''

    if(key):
      message = self.config.get(self.errorType, key)
    if(data):
      for key, value in data.items():
        message = message + ", " f"{key}: {value}"

    return message

    #print(message)
    #frame = inspect.stack()[1][0]

    #print(inspect.getframeinfo(frame).__getitem__(0))
    #print(inspect.getframeinfo(frame).__getitem__(1))



# le = MyError('LexerErrors')

# print(le.newError('ERR-LEX-001'))

