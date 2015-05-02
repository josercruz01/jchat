import json
import os

from peewee import *

db = SqliteDatabase(os.environ.get('JCHAT_DATABASE') or "test.db")

# Constants
MSG_TYPE_SITE = "status"
MSG_TYPE_MESSAGE = "message"

STATUS_TYPE_ONLINE = "online"
STATUS_TYPE_OFFLINE = "offline"

# Base Database Model.
class BaseModel(Model):
  class Meta:
    database = db

# Represents a message.
class Message(BaseModel):
  message_id = CharField(unique=True)

# Represents a site.
class Site(BaseModel):
  site_id = CharField(unique=True)
  messages = IntegerField(default=0)
  emails = IntegerField(default=0)
  last_updated = IntegerField(default=0)

# Represents an operator.
class Operator(BaseModel):
  operator_id = CharField()
  status = CharField()
  site = ForeignKeyField(Site, related_name='operators')
  last_updated = IntegerField(default=0)

# Represents a visitor.
class Visitor(BaseModel):
  visitor_id = CharField()
  site = ForeignKeyField(Site, related_name='visitors')

# Returns true if at least one operator is online for the site.
def is_online(site):
  online = (Operator.select().where(
      (Operator.site == site.id) &
      (Operator.status == STATUS_TYPE_ONLINE)
    ).count())
  return online > 0


# Return the total visitors connected to the site.
def total_visitors(site):
  total = (Visitor.select().where(
      Visitor.site == site.id
    ).count())
  return total

# Return the total operators connected to the site.
def total_operators(site):
    total = (Operator.select().where(
        Operator.site == site.id
      ).count())
    return total

# Returns an operator associated with the operator id.
def get_operator(site, operator_id):
  operator = Operator.get((Operator.site == site.id) & 
      (Operator.operator_id == operator_id))
  return operator

def site_str(site, operators, visitors):
  return "%s,messages=%s,emails=%s,operators=%s,visitors=%s" % (
      site.site_id,
      site.messages,
      site.emails,
      operators,# site.num_operators,
      visitors,#site.num_visitors,
      )

def all_sites():
  sites = Site.select()
  for site in sites:
    operators = site.operators.count()
    visitors = site.visitors.count()
    yield site_str(site, operators, visitors)

# Represents the state of the current chat.
#
# Attributes:
#   sites: A list of all sites attached to this chat instance.
class JChat(object):

  def __init__(self):
    db.connect()
    self.sites = {}

  def print_all(self):
    for site in all_sites():
      print site

  # Processes a message. Depending on the type it either sends
  # the message to the site if the site is online or sends
  # an email otherwise.
  def process(self, message):
    message_id = message["id"]
    try:
      Message.get(Message.message_id == message_id)
      return
    except DoesNotExist:
      db_message = Message.create(message_id=message_id)
      db_message.save()

    message_type = message["type"]
    if message_type == MSG_TYPE_SITE:
      self._process_status(message)
    elif message_type == MSG_TYPE_MESSAGE:
      self._process_message(message)
    else:
      raise ValueError("Message type '%s' is not valid." % (message_type,))

  # Returns or creates a site.
  def _get_or_create_site(self, site_id):
    try:
      return Site.get(Site.site_id == site_id)
    except DoesNotExist:
      site = Site.create(site_id=site_id, messages=0, emails=0)
      return site

  # Sends a message to the site if the site is online or sends an email
  # to the site othersise.
  def _process_message(self, message):
    site = self._get_or_create_site(message["site_id"])

    site.last_updated = message["timestamp"]
    if is_online(site):
      site.messages += 1
    else:
      site.emails +=1
    site.save()

    # Create visitor if not exists.
    visitor_id = message["from"]
    try:
      visitor = Visitor.get( (Visitor.visitor_id == visitor_id) &
          (Visitor.site == site.id)
          )
    except DoesNotExist:
      visitor = Visitor.create(site=site.id, visitor_id=visitor_id)
    visitor.save()


  # Marks a site as online/offline based on the message data.
  def _process_status(self, message):
    timestamp = message["timestamp"]

    site = self._get_or_create_site(message["site_id"])
    site.last_updated = timestamp
    site.save()

    # Create operator.
    operator_id = message["from"]
    status = message["data"]["status"]
    operator = None
    try:
      operator = Operator.get( (Operator.site == site.id) &
          (Operator.operator_id == operator_id)
          )
      operator.status = status
    except DoesNotExist:
      operator = Operator.create(operator_id=operator_id,
          site=site.id,
          status=status)

    operator.last_updated = timestamp
    operator.save()


  def get_site(self, site_id):
    site = Site.get(Site.site_id == site_id)
    return site

  def total_sites(self):
    return Site.select().count()

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
