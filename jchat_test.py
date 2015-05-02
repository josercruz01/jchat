import migrate_database
import jchat
import json
import random
import unittest

class MockMessage(object):
    def __init__(self, data, message_id, timestamp):
        self.content = json.dumps(data)
        self.message_id = message_id
        self.last_updated = timestamp

# Creates an operator online/offline message for testing.
def create_status_message(msg_id, site_id, operator, status, ts = None):
  timestamp = random.randint(1,15) if not ts else ts
  data = {
      "id": str(msg_id),
      "site_id": site_id,
      "type": jchat.MSG_TYPE_SITE,
      "from": operator,
      "data": {
        "status": status,
      },
      "timestamp": timestamp,
  }
  return MockMessage(data, msg_id, timestamp)

def create_user_message(msg_id, site_id, operator, message, ts = None):
  timestamp = random.randint(1,15) if not ts else ts
  data = {
      "id": str(msg_id),
      "site_id": site_id,
      "type": jchat.MSG_TYPE_MESSAGE,
      "from": operator,
      "data": {
        "message":message,
      },
      "timestamp": timestamp
  }
  return MockMessage(data, msg_id, timestamp)

class JChatTest(unittest.TestCase):

  def setUp(self):
    # Print all queries to stderr.
    migrate_database.cleanup()
    migrate_database.migrate()

  def test_process_status_online(self):
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    chat.process(message)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    self.assertEqual(jchat.total_operators(site), 1)

    operator = jchat.get_operator(site, "op1")
    self.assertEqual(operator.status, jchat.STATUS_TYPE_ONLINE)

  def test_process_status_online_two_operators(self):
    chat = jchat.JChat()
    message1 = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    message2 = create_status_message(2, "123", "op2", jchat.STATUS_TYPE_ONLINE)
    chat.process(message1)
    chat.process(message2)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    self.assertEqual(jchat.total_operators(site), 2)

    op1 = jchat.get_operator(site, "op1")
    self.assertEqual(op1.status, jchat.STATUS_TYPE_ONLINE)

    op2 = jchat.get_operator(site, "op2")
    self.assertEqual(op2.status, jchat.STATUS_TYPE_ONLINE)

  def test_process_status_online_then_offline(self):
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    message_offline = create_status_message(2, "123", "op1",
        jchat.STATUS_TYPE_OFFLINE)

    chat.process(message)
    chat.process(message_offline)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    self.assertEqual(jchat.total_operators(site), 1)

    operator = jchat.get_operator(site, "op1")
    self.assertEqual(operator.status, jchat.STATUS_TYPE_OFFLINE)

  def test_receiving_duplicate_site_message(self):
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1",
        jchat.STATUS_TYPE_ONLINE, 1)
    message2 = create_status_message(1, "123", "op1",
        jchat.STATUS_TYPE_ONLINE, 100)

    chat.process(message)
    chat.process(message)
    chat.process(message2)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    operator = jchat.get_operator(site, "op1")
    self.assertEqual(site.last_updated, 1)
    self.assertEqual(operator.last_updated, 1)

  def test_process_user_message_with_site_offline(self):
    chat = jchat.JChat()
    message = create_user_message(1, "site123", "v1", "hello")
    message2 = create_user_message(2, "site123", "v1", "hello2")
    chat.process(message)
    chat.process(message2)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("site123")
    self.assertEqual(jchat.total_operators(site), 0)
    self.assertEqual(jchat.total_visitors(site), 1)
    self.assertEqual(site.emails, 2)
    self.assertEqual(site.messages, 0)

  def test_process_user_message_with_site_online(self):
    chat = jchat.JChat()
    op1_online = create_status_message(1, "site123", "op1", 
        jchat.STATUS_TYPE_ONLINE, 1)
    message = create_user_message(2, "site123", "v1", "hello")

    chat.process(op1_online)
    chat.process(message)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("site123")
    self.assertEqual(jchat.total_operators(site), 1)
    self.assertEqual(jchat.total_visitors(site), 1)
    self.assertEqual(site.emails, 0)
    self.assertEqual(site.messages, 1)

if __name__ == '__main__':
  unittest.main()
