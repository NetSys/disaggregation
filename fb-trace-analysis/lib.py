
def get_hadoop_id(long_name):
  long_name = long_name.strip()
  if long_name == "NOENTRY" or long_name == "\\N" or long_name == "/default-rack/DUMMY_HOST":
    return ""
  try:
    start = long_name.index("hadoop")
    end = long_name.index("\\",start)
    return long_name[start:end]
  except ValueError:
    try:
      s = long_name.rindex("/")
      return long_name[s+1:]
    except ValueError:
      print long_name
      return ""

