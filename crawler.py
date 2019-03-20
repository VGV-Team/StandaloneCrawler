import threading
from page_retrieval import PageRetrieval
import time

USE_MULTITHREADING = True

database_lock = threading.Lock()
stop_callback = threading.Event()


def should_process_run():
    text = input()
    if text == "quit":
        return False
    else:
        return True

def crawler_thread(thread_name):
    print("Starting: " + thread_name)
    pr2 = PageRetrieval(thread_name, database_lock, stop_callback)
    pr2.run()
    print("Finishing: " + thread_name)


def run_threads(N):
    for i in range(N):
        try:
            t = threading.Thread(target=crawler_thread, args=[("Thread-" + str(i))])
            t.daemon = True
            t.start()
        except:
            print("Error: unable to start thread")

    print("All threads started, type 'quit' to finish.")
    while should_process_run():
        pass
    stop_callback.set()
    while threading.active_count() > 1:
        print("Waiting for " + str(threading.active_count() - 1) + " threads.")
        time.sleep(5)
    return


db_init = PageRetrieval("init", database_lock, stop_callback)
db_init.initialize_database()

if USE_MULTITHREADING:
    run_threads(10)
else:
    db_init.run()

print("All threads finished.")
