from CollideObjectBase import SphereCollideObject
from panda3d.core import Loader, NodePath, Vec3
from direct.task.Task import TaskManager
from typing import Callable
from direct.task import Task
import sys
from SpaceJamClasses import Missile
from direct.gui.OnscreenImage import OnscreenImage

class Player(SphereCollideObject):
    def __init__(self, loader: Loader, taskMgr: TaskManager, accept: Callable[[str, Callable], None], modelPath: str, parentNode: NodePath, nodeName: str,
            texPath: str, posVec: Vec3, posHpr: Vec3, scaleVec: float):
        super(Player, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 8)
        self.taskMgr = taskMgr
        self.accept = accept
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setHpr(posHpr)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.render = parentNode
        self.loader = loader

        self.reloadTime = .25
        self.missileDistance = 4000 #Until missile explodes
        self.missileBay = 1 #Ammo

        self.taskMgr.add(self.CheckIntervals, "checkMissiles", 34)
        self.EnableHUD()

        self.setKeyBindings()

    def quit(self):
        sys.exit()

    def Upwards(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveUpwards, "upward-thrust")
        else:
            self.taskMgr.remove("upward-thrust")

    def Downwards(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveDownwards, "downward-thrust")
        else:
            self.taskMgr.remove("downward-thrust")

    def Forward(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveForward, "forward-thrust")
        else:
            self.taskMgr.remove("forward-thrust")

    def Backward(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveBackward, "backward-thrust")
        else:
            self.taskMgr.remove("backward-thrust")

    def Leftward(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveLeftward, "leftward-thrust")
        else:
            self.taskMgr.remove("leftward-thrust")

    def Rightward(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.MoveRightward, "rightward-thrust")
        else:
            self.taskMgr.remove("rightward-thrust")
    
    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftTurn, "left-turn")
        else:
            self.taskMgr.remove("left-turn")

    def RightTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightTurn, "right-turn")
        else:
            self.taskMgr.remove("right-turn")
    
    def MoveUpwards(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() - rate)
        return task.cont

    def MoveDownwards(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return task.cont

    def MoveForward(self, task):
        speed = 5
        trajectory = self.render.getRelativeVector(self.modelNode, Vec3.up())
        trajectory.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * speed)
        return task.cont

    def MoveBackward(self, task):
        speed = 5
        trajectory = self.render.getRelativeVector(self.modelNode, Vec3.up())
        trajectory.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() - trajectory * speed)
        return task.cont

    def MoveLeftward(self, task):
        rate = .5
        self.modelNode.setR(self.modelNode.getR() + rate)
        return task.cont

    def MoveRightward(self, task):
        rate = .5
        self.modelNode.setR(self.modelNode.getR() - rate)
        return task.cont
    
    def ApplyLeftTurn(self, task):
        # half a degree every frame
        rate = .5
        self.modelNode.setH(self.modelNode.getH() - rate)
        return task.cont

    def ApplyRightTurn(self, task):
        # half a degree every frame
        rate = .5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return task.cont

    def Fire(self):
        if self.missileBay:
            travRate = self.missileDistance
            aim = self.render.getRelativeVector(self.modelNode, Vec3.up()) # Direction spaceship is facing.
            aim.normalize() # Normalizing a vector makes it consistent all the time.
            fireSolution = aim * travRate
            inFront = aim * 150
            travVec = fireSolution + self.modelNode.getPos()
            self.missileBay -= 1
            tag = "Missile" + str(Missile.missileCount)

            posVec = self.modelNode.getPos() + inFront # Spawn missle infront of the nose of the ship
            currentMissile = Missile(self.loader, "./Assets/Spaceships/Phaser/Phaser/phaser.egg", self.render, tag, posVec, 4.0)

            # fluid = 1 makes collisions be checked between the last interval and this interval to make 
            # sure there's nothing in-between both checks that wasn't hit
            Missile.intervals[tag] = currentMissile.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1)
            Missile.intervals[tag].start()
        else:
            # If not reloading, reload.
            if not self.taskMgr.hasTaskNamed("reload"):
                print("Initializing reload...")
                # Call reload method, no delay
                self.taskMgr.doMethodLater(0, self.Reload, "reload")
                return Task.cont

    def Reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay += 1
            print("Reload complete.")
            if self.missileBay > 1:
                self.missileBay = 1
            return Task.done
        elif task.time <= self.reloadTime:
            print("Reload processing...")
            return Task.cont

    def CheckIntervals(self, task):
        for i in Missile.intervals:
            if not Missile.intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()
                del Missile.intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                print(i + " has reached the end of its fire solution.")
                break
        return Task.cont

    def EnableHUD(self):
        self.Hud = OnscreenImage(image = "./Assets/Spaceships/target.png", pos = Vec3(0, 0, 0), scale = 0.1)
        self.Hud.setTransparency(1)
    
    def setKeyBindings(self):
        # key bindings for ship movement
        self.accept("escape", self.quit)
        self.accept("f", self.Fire)
        self.accept("arrow_up", self.Upwards, [1])
        self.accept("arrow_up-up", self.Upwards, [0])
        self.accept("arrow_down", self.Downwards, [1])
        self.accept("arrow_down-up", self.Downwards, [0])
        self.accept("w", self.Forward, [1])
        self.accept("w-up", self.Forward, [0])
        self.accept("s", self.Backward, [1])
        self.accept("s-up", self.Backward, [0])
        self.accept("a", self.Leftward, [1])
        self.accept("a-up", self.Leftward, [0])
        self.accept("d", self.Rightward, [1])
        self.accept("d-up", self.Rightward, [0])
        self.accept("arrow_left", self.LeftTurn, [1])
        self.accept("arrow_left-up", self.LeftTurn, [0])
        self.accept("arrow_right", self.RightTurn, [1])
        self.accept("arrow_right-up", self.RightTurn, [0])