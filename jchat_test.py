import jchat
import unittest

class JChatTest(unittest.TestCase):

  def test_process_status(self):
    chat = jchat.JChat()
    message = {
        "site_id": "123",
        "type": jchat.MSG_TYPE_SITE,
    }
    chat._process_status(message)
    self.assertEqual(len(chat.sites), 1)
    site = chat.sites["123"]
    self.assertIsNotNone(site)

if __name__ == '__main__':
  unittest.main()
