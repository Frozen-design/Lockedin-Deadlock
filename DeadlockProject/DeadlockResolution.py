# Deadlock avoidance (smokers dilemma)
import threading
import math
import random
import time
import collections

POSSIBLE = ["paper", "tobacco", "lighter"]
RESOURCES = dict(paper = 1, tobacco = 1, lighter = 1)
TABLE = []

rw_mutex = threading.Semaphore(1)
mutex = threading.Semaphore(1)

def atomicPrint(printString):
    global mutex
    mutex.acquire()
    print(printString)
    mutex.release()

class Smoker:
    def __init__(self, name, resource):
        global POSSIBLE, STATUS, TABLE, rw_mutex
        self.name = name
        self.resource = resource
        self.resourceCount = self.acquireAllResources(self.resource)
        self.desire = POSSIBLE.copy().remove(self.resource)
        self.status = "waiting"

    def acquireAllResources(self, need):
        global RESOURCES
        count = RESOURCES[need]
        RESOURCES[need] = 0
        return count
    
    def acquireNResources(self, need, value):
        rw_mutex.acquire()
        global RESOURCES
        count = RESOURCES[need]
        RESOURCES[need] = 0
        rw_mutex.release()
        return count

    def checkAvailableResources(self):
        global POSSIBLE, TABLE, rw_mutex
        self.status = "checking"
        while self.status != "acquired":
            atomicPrint(time.ctime(), ">", self.name, "is checking. I have", self.resource, "I need", self.desire)
            if collections.Counter(TABLE) == collections.Counter(self.desire) and self.resourceCount > 0:
                self.status = "acquired"
            #Simulate time taken to check materials
            time.sleep(2)

    def grabRequiredResources(self):
        global POSSIBLE, TABLE, rw_mutex
        if self.status == "acquired":
            rw_mutex.acquire()
            
            self.status = "smoking"
            atomicPrint(time.ctime(), ">>", self.name, "is smoking")
            for i in self.desire:
                TABLE.remove(self.desire[i])

            rw_mutex.release()

            #Simulate time taken to smoke.
            time.sleep(10)
            self.status = "waiting"

    def trySmoking(self):
        self.checkAvailableResources()
        self.grabRequiredResources()



class Dealer:
    def __init__(self):
        pass

    def dealResources(self):
        global POSSIBLE, TABLE, rw_mutex, mutex
        i_loop = 0
        while i_loop <= 10:
            if len(TABLE) == 0: 
                rw_mutex.acquire()

                TABLE = random.sample(POSSIBLE, 2)
                atomicPrint(time.ctime(), "These are the dealt resources:", TABLE)

                rw_mutex.release()
            time.sleep(4)
            i_loop += 1
            
        


def main():
    global POSSIBLE, TABLE, rw_mutex

    smoker1 = Smoker("Uno", POSSIBLE[0], 1)
    smoker2 = Smoker("Dos", POSSIBLE[1], 1)
    smoker3 = Smoker("Tres", POSSIBLE[2], 1)
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