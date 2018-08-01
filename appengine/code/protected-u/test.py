import time
import hashlib
import sys



def timeString(current=0):
    t = int(time.time()/60 - current)
    result = []
    for i in range(0, 8):
        result.append(t >> (i*8)&0xff)
    result.reverse()
    result = ''.join(chr(i) for i in result)
    return result    


def hashID(id, time, salt):
    h = hashlib.sha256()
    h.update(id)
    h.update(time)
    h.update(salt)
    return h.hexdigest()   


def main():
    t = timeString()
    id = sys.argv[1]
    salt = sys.argv[2]
    print hashID(id, t, salt)


if __name__ == "__main__":
    main()