import threading
import time
import random
import networkx as nx
import matplotlib.pyplot as plt 

L2D   = lambda x, y: dict([(a, b) for a, b in zip(x, y)])
DSD   = lambda x, y: dict([(a[0], a[1] - b[1]) for a, b in zip(x.items(), y.items())])
DAD   = lambda x, y: dict([(a[0], a[1] + b[1]) for a, b in zip(x.items(), y.items())])
DABV0 = lambda x   : dict([(a[0], a[1]) if a[1] >= 0 else (a[0], 0) for a in x.items()])


RESOURCELIST = ["Guns", "Bullets", "Targets"]
RESOURCES = L2D(RESOURCELIST, [1 for x in RESOURCELIST])

printLock = threading.Lock()
updateLock = threading.Semaphore()

def waitPeriod(a: int):
    updateLock.release()
    time.sleep(a)
    updateLock.acquire()


class Process:
    def __init__(self, name, resource):
        self.name = name
        self.resource = resource
        self.status = "starting"
        self.timesRun = 1
        self.allocated = L2D(RESOURCELIST, [0 for x in RESOURCELIST])
        self.acquireN(resource, RESOURCES[resource])
        self.reserve = L2D(RESOURCELIST, [0 for x in RESOURCELIST])
        self.require = L2D(RESOURCELIST, [1 for x in RESOURCELIST])
        self.request = DABV0(DSD(self.require, self.allocated))

    def acquireN(self, resource, n):
        if RESOURCES[resource] < n:
            return False
        self.allocated[resource] += n
        RESOURCES[resource] -= n
        return True
        
    def releaseN(self, resource, n):
        if self.allocated[resource] < n:
            return False
        self.allocated[resource] -= n
        RESOURCES[resource] += n
        return True
    
    def run(self):

        if self.allocated == self.require:

            # Move to reserve
            for i in RESOURCELIST:
                self.reserve[i] += self.require[i]
                self.allocated[i] -= self.require[i]
            
            with printLock:
                print(self.name, "running\n Resources:", RESOURCES, "\n Required:", self.require, "\n Reserved:", self.reserve, "\n Allocated:", self.allocated, "\n Requested:", self.request)

            waitPeriod(3)
            
            with printLock:
                print(self.name, "is done running")

            #Move out of reserve
            for i in RESOURCELIST:
                self.reserve[i] -= self.require[i]
                self.allocated[i] += self.require[i]
            
            with printLock:
                print(self.name, "is finished\n Resources:", RESOURCES, "\n Required:", self.require, "\n Reserved:", self.reserve, "\n Allocated:", self.allocated, "\n Requested:", self.request)
    
    def check(self):
        updateLock.acquire()

        # Update what resources need to be requested
        self.request = DABV0(DSD(self.require, self.allocated))

        with printLock:
            print(self.name, "checking\n Resources:", RESOURCES, "\n Required:", self.require, "\n Reserved:", self.reserve, "\n Allocated:", self.allocated, "\n Requested:", self.request, "\n")

        if RESOURCES == self.request:
            with printLock:
                print(self.name, "started running")
            
            # Acquire all needed resources
            for i in RESOURCELIST:
                self.acquireN(i, self.request[i])

            # Move resources to reserve
            self.run()
            # Afterwards put resources into allocated

            # Release resources into the ether
            for i in RESOURCELIST:
                self.releaseN(i, self.request[i])

            # Decrease the Number of times that the process needs to run in order to complete.
            self.timesRun -= 1

            # Cooldown period after everything
            waitPeriod(5)
        # How long it took to check
        waitPeriod(1)
        updateLock.release()


        while self.timesRun > 0:
            self.check()

class Monitor:
    def __init__(self, *processList):
        self.processList = list(processList)
        self.maxResources = L2D(RESOURCELIST, [1 for x in RESOURCELIST])
        print(self.maxResources)
        pass

    def check(self):
        time.sleep(2)

        a = sum([a.timesRun for a in self.processList])
        while a > 0:
            updateLock.acquire()
            a = sum([a.timesRun for a in self.processList])
            if a == 0:
                return

            with printLock:
                print("Number of programs to run:", a)

            for j in self.processList:
                j.acquireN(j.resource, RESOURCES[j.resource])
                j.request = DABV0(DSD(j.require, j.allocated))

            with printLock:
                print("Monitor checking")
                print(RESOURCES)

            if a == 0:
                return

            savedResources = RESOURCES.copy()
            for i in self.processList:
                savedResources = DAD(savedResources, i.allocated)
            
            for i in savedResources.items():
                if i[1] < 1:
                    updateLock.release()
                    time.sleep(1)
                    continue

            updateLock.release()
            updateLock.acquire()

            isDeadlocked = not self.graphTheory()
            if isDeadlocked:
                with printLock:
                    print("Deadlocked: True")

                randomProcess = random.choice(self.processList)
                processRequest = randomProcess.request

                for i in self.processList:
                    for j in processRequest.items():

                        if i.resource != j[0]:
                            continue

                        i.releaseN(j[0], j[1])
                
                with printLock:
                    print(RESOURCES, randomProcess.name)

            waitPeriod(2)

            updateLock.release()

            

    def graphTheory(self):

        G = nx.DiGraph()

        processNodes = []
        for i in self.processList:
            processNodes.append(i.name)

        resourceNodes = []
        for i in RESOURCELIST:
            resourceNodes.append(f"{i}-{1}")
        
        allocatedEdges = []
        for i in self.processList:
            for j in i.allocated.items():
                if j[1] > 0:
                    for h in range(1, j[1]+1):
                        temp = [f"{j[0]}-{h}", i.name]
                        allocatedEdges.append(temp)

        requestEdges = []
        for i in self.processList:
            for j in i.request.items():
                if j[1] > 0:
                    for h in range(1, j[1]+1):
                        temp = [i.name, f"{j[0]}-{h}"]
                        requestEdges.append(temp)
        
        G.add_nodes_from(resourceNodes)
        G.add_nodes_from(processNodes)
        G.add_edges_from(allocatedEdges)
        G.add_edges_from(requestEdges)
        
        thing = nx.is_directed_acyclic_graph(G)
        del G
        return thing


def main():
    p1 = Process("P1", RESOURCELIST[0])
    p2 = Process("P2", RESOURCELIST[1])
    p3 = Process("P3", RESOURCELIST[2])
    mon = Monitor(p1, p2, p3)

    t1 = threading.Thread(target = p1.check)
    t2 = threading.Thread(target = p2.check)
    t3 = threading.Thread(target = p3.check)
    t4 = threading.Thread(target = mon.check)

    threadProcesses = [t1, t2, t3, t4]
    for i in threadProcesses:
        i.start()
    
    for i in threadProcesses:
        i.join()

    print("Finished")
    

if __name__ == "__main__":
    main()