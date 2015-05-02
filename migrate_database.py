import jchat
import os

TABLES = [jchat.Site, jchat.Visitor, jchat.Operator, jchat.Message]
def cleanup():
  for table in TABLES:
    table.drop_table(fail_silently=True)

def migrate():
    jchat.db.connect()
    jchat.db.create_tables(TABLES)

if __name__ == "__main__":
  cleanup()
  migrate()
