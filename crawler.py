import threading
import time
from page_retrieval import PageRetrieval

USE_MULTITHREADING = True


def crawler_thread(thread_name):
    print("Starting:" + thread_name)
    pr2 = PageRetrieval(thread_name, database_lock)
    pr2.run()
    print("Finishing:" + thread_name)


def run_threads(N):
    try:
        for i in range(N):
            t = threading.Thread(target=crawler_thread, args=[("Thread-" + str(i))])
            t.daemon = True  # set thread to daemon ('ok' won't be printed in this case)
            t.start()
    except:
        print("Error: unable to start thread")

    while 1:
        print("Waiting")
        time.sleep(1)


database_lock = threading.Lock()

db_init = PageRetrieval("init", database_lock)
db_init.initialize_database()

if USE_MULTITHREADING:
    run_threads(3)
else:
    db_init.run()

