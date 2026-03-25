import socket
import time

def test_timeout():
    print("Connecting to simulator on 127.0.0.1:5020...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 5020))
    print("Connected. Sleeping for 10 seconds without sending data...")
    
    start = time.time()
    # 模拟器应该在 5 秒后关闭连接
    data = s.recv(1024)
    end = time.time()
    
    if not data:
        print(f"Connection closed by server after {end - start:.2f} seconds.")
        if 4.5 <= (end - start) <= 6.5:
            print("SUCCESS: Timeout worked as expected.")
        else:
            print("FAILURE: Timeout took unexpected time.")
    else:
        print("Received unexpected data.")
    s.close()

if __name__ == "__main__":
    test_timeout()
