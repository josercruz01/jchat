import multiprocessing
import redis
import json
import signal
import traceback

DEBUG = False
SITE_ID_LABEL = "site:site_id:%s"

r = redis.StrictRedis(host='localhost', port=6379, db=7)

def printdebug(text, *args):
  if DEBUG:
    message = text % tuple(args)
    print message

def print_site(site_id):
  site_label = SITE_ID_LABEL % (site_id,)
  print "%s,messages=%s,emails=%s,operators=%s,visitors=%s" % (
      site_id,
      r.get(site_label + ":messages"),
      r.get(site_label + ":emails"),
      r.scard(site_label + ":operators"),
      r.scard(site_label + ":visitors"),
      )

def init_site(site_id):
  site_label = SITE_ID_LABEL % (site_id,)
  site_online = r.get(site_label)
  if site_online:
    return

  r.set(site_label, 1)
  r.set(site_label + ":messages", 0)
  r.set(site_label + ":emails", 0)
  r.set(site_label + ":online", 0)

def save_ordered_message(site_id, text, score, line):
  try:
    try:
      label = "messages:site_id:%s" % (site_id,)
      printdebug("Added line #%s (score=%s, label:%s)", line, score, label)
      r.zadd(label, score, text)
      r.zadd("site_ids", site_id, site_id)
    except Exception as e:
      print "Found exception %s" %(e,)
      traceback.print_exc()
      print ""
      raise e
  except KeyboardInterrupt:
      return

def init_worker():
 signal.signal(signal.SIGINT, signal.SIG_IGN)

def within_process_pool(fn):
  def wrapper(*args, **kwargs):
    pool = multiprocessing.Pool(5, init_worker)
    try:
      fn(pool, *args, **kwargs)
    except KeyboardInterrupt:
      print "Caught KeyboardInterrupt, terminating workers"
      pool.terminate()
      pool.join()
    else:
      pool.close()
      pool.join()
  return wrapper


@within_process_pool
def read_messages(pool, filename):
  with open(filename) as f:
    for line, text in enumerate(f):
      last_line = r.get("last_line")
      if last_line and line <= int(last_line):
        continue
      last_line = r.set("last_line", line)

      json_message = json.loads(text)
      score = int(json_message["timestamp"])
      site_id = json_message["site_id"]
      pool.apply_async(save_ordered_message, args=(site_id, text, score, line))

def process_single_site(site_id):
  try:
    try:
      site_messages_label = "messages:site_id:%s" % (site_id,)
      site_label = SITE_ID_LABEL % (site_id,)
      for message in r.zrange(site_messages_label, 0, -1):
        message = json.loads(message)
        message_id = message["id"]

        # Skip seen messages.
        message_label = "message:%s:seen" % (message_id,)
        message_seen = r.get(message_label)
        if message_seen:
          continue

        message_type = message["type"]
        init_site(site_id)

        user_id = message["from"]
        if message_type == "status":
          r.sadd(site_label + ":operators", user_id)
          if message["data"]["status"] == "online":
            r.sadd(site_label + ":online_ops", user_id)
          else:
            r.srem(site_label + ":online_ops", user_id)

        elif message_type == "message":
          r.sadd(site_label + ":visitors", user_id)
          if r.scard(site_label + ":online_ops") > 0:
            r.incr(site_label + ":messages")
          else:
            r.incr(site_label + ":emails")

        message_seen = r.set(message_label, 1)
    except Exception as e:
      print "Found exception %s" %(e,)
      traceback.print_exc()
      print ""
      raise e
  except KeyboardInterrupt:
      return

@within_process_pool
def process_messages(pool):
  for site_id in r.zrange("site_ids", 0, -1):
    pool.apply_async(process_single_site, args=(site_id,))

def print_all_output():
  for site_id in r.zrange("site_ids", 0, -1):
    print_site(site_id)

