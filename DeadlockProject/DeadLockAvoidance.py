# Deadlock avoidance (smokers dilemma)
import threading
import math
import random
import time

POSSIBLE = ["paper", "tobacco", "lighter"]
RESOURCES = []

rw_mutex = threading.Semaphore(1)
mutex = threading.Semaphore(1)


class Smoker:
    def __init__(self, name, resource):
        self.name = name
        self.resource = resource
        self.confirm = True

    def checkAvailableResources(self):
        global POSSIBLE, RESOURCES, rw_mutex, mutex, read_count
        
        mutex.acquire()
        print(time.ctime(), ">", self.name, "is checking. I have", self.resource)
        mutex.release()
        
        for i in RESOURCES:
            if i == self.resource:
                self.confirm = False

        if len(RESOURCES) == 0:
            self.confirm = False

    def grabRequiredResources(self):
        global POSSIBLE, RESOURCES, rw_mutex, mutex, read_count
        if self.confirm == True:
            rw_mutex.acquire()
            mutex.acquire()
            print(time.ctime(), ">>", self.name, "is smoking")
            mutex.release()
            RESOURCES = []
            rw_mutex.release()

            time.sleep(9)
        else:
            self.confirm = True

    def trySmoking(self):
        i_loop = 0
        while i_loop <= 10:
            self.checkAvailableResources()
            self.grabRequiredResources()
            i_loop += 1
            time.sleep(2)


class Dealer:
    def __init__(self):
        pass

    def dealResources(self):
        global POSSIBLE, RESOURCES, rw_mutex, mutex, read_count
        i_loop = 0
        while i_loop <= 10:
            if len(RESOURCES) == 0: 
                rw_mutex.acquire()
                RESOURCES = random.sample(POSSIBLE, 2)
                mutex.acquire()
                print(time.ctime(), "These are the dealt resources:", RESOURCES)
                mutex.release()
                rw_mutex.release()
            time.sleep(4)
            i_loop += 1
            
        


def main():
    global POSSIBLE, RESOURCES, rw_mutex, mutex, read_count

    smoker1 = Smoker("Uno", POSSIBLE[0])
    smoker2 = Smoker("Dos", POSSIBLE[1])
    smoker3 = Smoker("Tres", POSSIBLE[2])
    dealer1 = Dealer()

    t1 = threading.Thread(target = smoker1.trySmoking)
    t2 = threading.Thread(target = smoker2.trySmoking)
    t3 = threading.Thread(target = smoker3.trySmoking)
    t4 = threading.Thread(target = dealer1.dealResources)
    threads = [t4, t1, t2, t3]

    for i in threads:
        i.start()
        
    for i in threads:
        i.join()

    return

if __name__ == "__main__":
    main()