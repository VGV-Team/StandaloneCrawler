from multiprocessing import Process, Lock, Event, active_children
from page_retrieval import PageRetrieval
import time
import datetime
from database_interface import DatabaseInterface

USE_MULTITHREADING = True
NUMBER_OF_THREADS = 4
FRESH_START = True



def should_process_run():
    text = input()
    if text == "q":
        return False
    else:
        return True

def crawler_thread(thread_name, database_lock, stop_callback, db):
    print("Starting: " + thread_name)
    pr = PageRetrieval(thread_name, database_lock, stop_callback, db)
    pr.run()
    print("Finishing: " + thread_name)


def run_threads(N, database_lock, stop_callback, db):
    print(N)
    start_time = time.time()
    print("Start time:", datetime.datetime.fromtimestamp(start_time))
    for i in range(N):
        try:
            t = Process(target=crawler_thread, args=[("Thread-" + str(i)), database_lock, stop_callback, db])
            t.daemon = True
            t.start()
        except:
            print("Error: unable to start thread")


    time.sleep(NUMBER_OF_THREADS*2)
    print("All threads started, type 'q' to finish. If all threads did not start then enter some random non 'q' "
          "character first and hit enter.")
    while should_process_run():
        pass
    stop_callback.set()
    while len(active_children()) > 1:
        print("Waiting for " + str(len(active_children()) - 1) + " threads.")
        time.sleep(5)

    end_time = time.time()
    running_time = end_time - start_time

    print("Start time:", datetime.datetime.fromtimestamp(start_time))
    print("End time:", datetime.datetime.fromtimestamp(end_time))
    print("Ran for ", "%.2f" % round(running_time / 60, 2), " minutes.")
    print("That is ", "%.2f" % round(running_time / 3600, 2), " hours.")

    return


if __name__ == '__main__':
    database_lock = Lock()
    stop_callback = Event()
    db = DatabaseInterface(database_lock)
    db_init = PageRetrieval("init", database_lock, stop_callback, db)
    if FRESH_START:
        db_init.initialize_database()
    if USE_MULTITHREADING:
        run_threads(NUMBER_OF_THREADS, database_lock, stop_callback, db)
    else:
        db_init.run()

    print("All threads finished.")
