import jchat
import random
import unittest

def create_status_message(msg_id, site_id, operator, status, ts = None):
  timestamp = random.randint(1,15) if not ts else ts
  return {
      "id": str(msg_id),
      "site_id": site_id,
      "type": jchat.MSG_TYPE_SITE,
      "from": operator,
      "data": {
        "status": status
      },
      "timestamp": timestamp
  }

class JChatTest(unittest.TestCase):

  def test_process_status_online(self):
    return
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    chat.process(message)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    self.assertEqual(site.total_operators(), 1)

    operator = site.get_operator("op1")
    self.assertEqual(operator.status, jchat.STATUS_TYPE_ONLINE)

  def test_process_status_online_then_offline(self):
    return
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    message_offline = create_status_message(2, "123", "op1",
        jchat.STATUS_TYPE_OFFLINE)

    chat.process(message)
    chat.process(message_offline)

    self.assertEqual(chat.total_sites(), 1)

    site = chat.get_site("123")
    self.assertEqual(site.total_operators(), 1)

    operator = site.get_operator("op1")
    self.assertEqual(operator.status, jchat.STATUS_TYPE_OFFLINE)

  def test_site_not_updated_if_same_message_sent_twice(self):
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
    operator = site.get_operator("op1")
    self.assertEqual(site.last_updated, 1)
    self.assertEqual(operator.last_updated, 1)

if __name__ == '__main__':
  unittest.main()
