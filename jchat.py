import json

# Constants
MSG_TYPE_SITE = "status"
MSG_TYPE_MESSAGE = "message"

STATUS_TYPE_ONLINE = "online"
STATUS_TYPE_OFFLINE = "offline"

# Represents an operator.
#
# Attributes:
#   operator_id: The id of this operator.
#   status: Wether the operator is online or offline.
class Operator(object):

  def __init__(self, operator_id, status):
    self.operator_id = operator_id
    self.status = status

# Represents a site.
#
# Attributes:
#   site_id: ID that represents the site.
#   messages: Number of messages sent to the site.
#   emails: Number of emails sent to the site.
#   operators: List of online operators of this site.
#   visitors: Number visitors of this site.
class Site(object):

  def __init__(self, site_id):
    self.site_id = site_id
    self.messages = 0
    self.emails = 0
    self.operators = {}
    self.visitors = 0

  # Returns an operator associated with the operator id.
  def get_operator(self, operator_id):
    return self.operators[operator_id]

# Represents the state of the current chat.
#
# Attributes:
#   sites: A list of all sites attached to this chat instance.
class JChat(object):

  def __init__(self):
    self.sites = {}

  def __str__(self):
    return "Number of sites= " + str(len(self.sites))

  # Processes a message. Depending on the type it either sends
  # the message to the site if the site is online or sends
  # an email otherwise.
  def process(self, message):
    message_type = message["type"]
    if message_type == MSG_TYPE_SITE:
      self._process_status(message)
    elif message_type == MSG_TYPE_MESSAGE:
      self._process_message(message)
    else:
      raise ValueError("Message type '%s' is not valid." % (message_type,))

  # Sends a message to the site if the site is online or sends an email
  # to the site othersise.
  def _process_message(self, message):
    pass

  # Marks a site as online/offline based on the message data.
  def _process_status(self, message):
    site_id = message["site_id"]
    operator_id = message["from"]
    status = message["data"]["status"]
    operator = Operator(operator_id, status)

    site = Site(site_id)
    site.operators[operator_id] = operator
    self.sites[site_id] = site

  def get_site(self, site_id):
    return self.sites[site_id]

  def total_sites(self):
    return len(self.sites)


# Parses an input file containing a list of JSON files that
# represent a message from either a site coming online or a client
# sending a chat message to a site.
# Method assumes input file has correct JSON on each line and throws
# an exception if this condition is not met.
#
# Raises:
#   ValueError: If the input file has not correct JSON messages.
def parse(filename):
  chat = JChat()

  with open(filename) as f:
    line_number = 0
    for message in f:
      line_number += 1
      json_message = None
      try:
        json_message = json.loads(message)
      except ValueError, e:
        raise ValueError("Error parsing file '%s' on line %s. Text '%s' is "
            " not valid JSON" % (filename, line_number, message), e)

      chat.process(json_message)

  return chat
