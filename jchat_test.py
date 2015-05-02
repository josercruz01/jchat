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
    chat = jchat.JChat()
    message = create_status_message(1, "123", "op1", jchat.STATUS_TYPE_ONLINE)
    chat._process_status(message)
    self.assertEqual(chat.total_sites(), 1)
    site = chat.get_site("123")
    operator = site.get_operator("op1")
    self.assertEqual(operator.status, jchat.STATUS_TYPE_ONLINE)


if __name__ == '__main__':
  unittest.main()
