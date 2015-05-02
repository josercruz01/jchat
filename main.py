import jchat
import os.path
import sys

def usage():
  print "Usage:"
  print ("  python %s <filename>" % (sys.argv[0],))

def main():
  if len(sys.argv) <= 1:
    print "Error: did not specify input file"
    print ""
    usage()
    exit(0)

  input_file = sys.argv[1]
  if not os.path.isfile(input_file):
    print ("Error: file '%s' does not exists" % (input_file,))
    print ""
    usage()
    exit(0)

  chat = jchat.parse(input_file)
  chat.print_all()

if __name__ == "__main__":
  main()

