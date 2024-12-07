# Deadlock avoidance (smokers dilemma)
import threading
import random
import time

POSSIBLE = ["paper", "tobacco", "lighter"]
RESOURCES = dict(paper = 3, tobacco = 3, lighter = 3)

rw_mutex = threading.Semaphore(1)
mutex = threading.Semaphore(1)

def atomicPrint(printString):
    global mutex
    mutex.acquire()
    print(printString)
    mutex.release()

def createSmokerDict(needList = [0 for x in POSSIBLE]):
    global POSSIBLE
    desire = dict()
    for i, j  in zip(POSSIBLE, needList):
        desire[i] = j
    return desire

def isTrue(trueList, num = -1):
    if num <= 0:
        num = len(trueList)
    numTrue = 0
    for i in trueList:
        if i:
            numTrue += 1
    return numTrue >= num

class Smoker:
    def __init__(self, name, resource):
        global POSSIBLE, TABLE, rw_mutex
        self.name = name
        self.resource = resource
        self.status = "waiting"
        self.timesSmoked = 0

        self.allocated = createSmokerDict([0 for x in POSSIBLE])
        self.acquireAllResources(self.resource)

        self.need = createSmokerDict([1 if x != self.resource else 0 for x in POSSIBLE])
        self.needTotal = createSmokerDict([1 for x in POSSIBLE])

    def acquireAllResources(self, need):
        global RESOURCES
        if RESOURCES[need] <= 0:
            return
        self.allocated[need] = RESOURCES[need]
        RESOURCES[need] = 0
    
    def acquireNResources(self, need, value):
        global RESOURCES
        if RESOURCES[need] <= 0:
            return
        self.allocated[need] += value
        RESOURCES[need] -= value

    def releaseNResources(self, release, value):
        global RESOURCES
        if self.allocated[release] <= 0 or self.allocated[release] < value:
            return
        if self.status == "smoking" and self.allocated[release] <= self.needTotal[release]:
            return
        self.allocated[release] -= value
        RESOURCES[release] += value

    def checkAvailableResources(self):
        global POSSIBLE, RESOURCES, rw_mutex
        self.status = "checking"

        while self.status != "smoked":
            rw_mutex.acquire()
            atomicPrint(f"{time.ctime()} > {self.name} is checking. I have {self.allocated}. I need {self.need}")
            someIter = [a[0] == b[0] == c[0] and (a[1] + b[1]) >= c[1] for a, b, c in zip(RESOURCES.items(), self.allocated.items(), self.needTotal.items())]

            if isTrue(someIter):
                self.status = "smoking"

                #Acquire necessary resources
                self.acquireAllResources(self.resource)
                self.manageResources(self.acquireNResources)
                atomicPrint(f"{time.ctime()} >> I have {self.allocated}. {self.name} is smoking")
                rw_mutex.release()

                #Time to smoke.
                time.sleep(5)

                #Release resources
                rw_mutex.acquire()
                self.status = "smoked"
                self.timesSmoked += 1
                atomicPrint(f"{time.ctime()} >> {self.name} has finished smoking. Releasing: {self.need}")
                self.manageResources(self.releaseNResources)
                rw_mutex.release()

                #Exit checking loop
            else:
                self.status = "cannot acquire"
                rw_mutex.release()
                #time to check
            time.sleep(1)

        while self.timesSmoked < 1:
            self.checkAvailableResources()
            
    def manageResources(self, func):
        global POSSIBLE, RESOURCES, rw_mutex
        for i in self.need.items():
            func(i[0], i[1])

class Dealer:
    def __init__(self, *smokers):
        self.smokers = list(smokers)

    def addSmoker(self, smoker):
        self.smokers.append(smoker)
    
    def checkForDeadlock(self):
        global rw_mutex
        while True:
            rw_mutex.acquire()
            cannotAcquireList = [a.status == "cannot acquire" for a in self.smokers]
            smokedList = [a.status == "smoked" for a in self.smokers]
            if isTrue(smokedList):
                atomicPrint("Everyone finished smoking!")
                break

            if isTrue(cannotAcquireList, num = 1):
                # Update which smokers cannot acquire their resources
                cannotAcquireList = [a.status == "cannot acquire" for a in self.smokers]
                deadlockedSmokers = [b for a, b in zip(cannotAcquireList, self.smokers) if a]

                atomicPrint(f"{time.ctime()} >>> DEADLOCK")

                randomSmoker = random.choice(deadlockedSmokers)
                needOfSmoker = randomSmoker.need

                for j in self.smokers:
                    for i in needOfSmoker.items():
                        j.releaseNResources(i[0], i[1])
                
                atomicPrint(f"{time.ctime()} >>> Resources placed on table: {RESOURCES}")

            rw_mutex.release()
            time.sleep(2)
            
        


def main():
    global POSSIBLE, RESOURCES, rw_mutex
    random.seed()
    startTime = time.time()
    smoker1 = Smoker("Uno", POSSIBLE[0])
    smoker2 = Smoker("Dos", POSSIBLE[1])
    smoker3 = Smoker("Tres", POSSIBLE[2])
    dealer1 = Dealer(smoker1, smoker2, smoker3)

    t1 = threading.Thread(target = smoker1.checkAvailableResources)
    t2 = threading.Thread(target = smoker2.checkAvailableResources)
    t3 = threading.Thread(target = smoker3.checkAvailableResources)
    t4 = threading.Thread(target = dealer1.checkForDeadlock)
    threads = [t1, t2, t3, t4]

    for i in threads:
        i.start()
        
    for i in threads:
        i.join()

    print(f"Time taken: {time.time() - startTime}")

if __name__ == "__main__":
    main()