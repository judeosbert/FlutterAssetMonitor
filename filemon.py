#!/usr/bin/python3
import json
import sys
import os
import time
import pyperclip
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class Utils:
    def getClass(self, path):
        if "/" in path:
            splitName = path.split("/")
            if (os.path.isdir(path)):
                className = splitName[len(splitName) - 1]
            else:
                className = splitName[len(splitName) - 2]
            return className

    def getClassForDeletedPath(self, path):
        if "/" in path:
            splitName = path.split("/")
            if "." not in path:
                className = splitName[len(splitName) - 1]
            else:
                className = splitName[len(splitName) - 2]
            return className

    def getMemberValue(self, path):
        if ("/" in path):
            splitPath = path.split("/")
            return splitPath[len(splitPath) - 1]

    def getMemberName(self, path):
        if ("/" in path):
            nameParts = path.split("/")
            path = nameParts[len(nameParts) - 1]
        if ("." in path):
            nameParts = path.split(".")
            path = nameParts[0]
        return path

    def findClassIndex(self, parent, className):
        for i in range(len(parent)):
            memberClass = parent[i]
            if memberClass["name"] == className:
                return i
        return -1


class Templates:
    def __init__(self):
        self.utils = Utils()
        self.getLowercasedMemberName = lambda s: s[:1].lower() + s[1:] if s else ''
        self.invalidVariableNameSymbols = ["-", "@", "!", "~", "`", "\"", "#", "$", "%", "^", "&"
            , "*", "(", ")", "+", "=", "{", "[", "}", "]", "|", "\\", ";", ":", "'", "<", ",", ">", ".", "?", "/"]

    def getClassOpener(self, className):
        return "class " + className.capitalize() + " {\n"

    def getClassEnd(self):
        return "}\n"

    def getMemberDeclaration(self, memberName):
        formattedMemberName = self.utils.getMemberName(memberName)
        memberName = memberName.replace("../","")
        for symbol in self.invalidVariableNameSymbols:
            # print ("Replacing Symbol",symbol)
            formattedMemberName = formattedMemberName.replace(symbol, "")
            formattedMemberName = self.getLowercasedMemberName(formattedMemberName)
        return "static final String " + formattedMemberName + " = \"" + memberName + "\";\n"




class StructureManager:
    def __init__(self, writeFolder):
        self.utils = Utils()
        self.structurePath = writeFolder + "structure.json"
        if (not os.path.exists(self.structurePath)):
            file = open(self.structurePath, "w")
            file.close()
        self.assetManagerFilePath = writeFolder + "AssetManager.dart"
        self.templates = Templates()
        self.parseStructure()
        self.save()
        pass

    def parseStructure(self):
        file = open(self.structurePath, 'r')
        self.previousContents = file.read()
        if (len(self.previousContents) == 0):
            self.rootElement = []
            print("New File Found")
            return
        else:
            structJSON = json.loads(self.previousContents)
            self.rootElement = structJSON["classes"]
            file.close()
        print("Parsing Complete")

    def _refresh(self):
        self.parseStructure()

    def save(self):
        self.assetManagerFile = open(self.assetManagerFilePath, "w")
        numberOfClasses = len(self.rootElement)
        # print ("Number Of Classes",numberOfClasses)
        for i in range(numberOfClasses):
            className = self.rootElement[i]["name"]
            members = self.rootElement[i]["members"]
            self._writeClass(className, members)
        self.assetManagerFile.close()
        self._saveStructureJson()
        print ("--------------------------------------")

    def _saveStructureJson(self):
        file = open(self.structurePath, "w")
        finalStructure = {
            "classes": self.rootElement
        }
        json.dump(finalStructure, file, indent=4)
        file.close()
        print("Structure Saved")

    def _writeClass(self, className, members):

        print("Writing class ", className)
        self._write(self.templates.getClassOpener(className))
        for member in members:
            print("Writing memeber ", member)
            self._write(self.templates.getMemberDeclaration(member))
        self._write(self.templates.getClassEnd())

    def _write(self, content):
        self.assetManagerFile.write(content)

    def addMember(self, path):
        pyperclip.copy(path)
        splitPath = path.split("/")
        print(splitPath)
        parent = splitPath[len(splitPath) - 2]
        member = splitPath[len(splitPath) - 1]

        self.__addMember(parent, member,path)

    def __addMember(self, paramClassName, memberName,memberValue):
        for i in range(len(self.rootElement)):
            className = self.rootElement[i]["name"]
            print("Iterating through", className)
            if paramClassName == className:
                print("Class Found")
                if self._addMemberTo(memberName, i,memberValue):
                    self.save()
                    print("Declaration copied to clipboard")
                else:
                    pyperclip.copy("")
                break

    def __isClassExisting(self, className):
        for memberClass in self.rootElement:
            if memberClass["name"] == className:
                return True
        return False

        pass

    def add(self, path):
        newPath = os.path.relpath(path)
        if os.path.isdir(newPath):
            self.addClass(newPath)
        else:
            self.addMember(newPath)

    def addClass(self, path):
        className = self.utils.getClass(path)
        print ("Class name Found", className)
        print (self.rootElement)
        if not self.__isClassExisting(className):
            memberDeclaration = {
                'name': className,
                'members': []
            }
            declarationJSON = json.dumps(memberDeclaration)
            self.rootElement.append(eval(declarationJSON, {'__builtins__': {}}))
            print("After add", self.rootElement)
            self.save()
            print("New Class added")
        else:
            print("Duplicate class.Skipping")

    def _addMemberTo(self, memberName, atIndex,memberValue):
        classmemebers = self.rootElement[atIndex]["members"]
        print("Current Member Count", len(classmemebers))
        if (memberValue not in classmemebers):
            classmemebers.append(memberValue)
            print("Member Added. Length->", len(classmemebers))
            return True
        else:
            print("Member Already Exists.Skipping")
            return False

    def delete(self, path):
        print(repr(path), "Is Path", not "." in path)
        if not "." in path:
            print ("Class Deleted")
            className = self.utils.getClassForDeletedPath(path)
            self.__deleteClass(className)
        else:
            className = self.utils.getClassForDeletedPath(path)
            memberName = self.utils.getMemberValue(path)
            self.__deleteMember(className, memberName)
        self.save()

    def __deleteMember(self, classname, membervalue):
        classIndex = self.utils.findClassIndex(self.rootElement, classname)
        if classIndex == -1:
            print ("Class not found")
            return
        classToModify = self.rootElement[classIndex]
        try:
            classToModify["members"].remove(membervalue)
            self.save()
            print ("Member", membervalue, "Deleted in class", classToModify["name"])
        except ValueError:
            print ("Value not found. You might have hanging declaration")

    def __deleteClass(self, classname):
        classIndex = self.utils.findClassIndex(self.rootElement, classname)
        if classIndex == -1:
            print ("Class not found. Ignoring event")
            return
        removedClass = self.rootElement.pop(classIndex)
        print("Class Removed", removedClass["name"])

    def modify(self, classname, membervalue):

        pass


class FileMonEventHandler(PatternMatchingEventHandler):
    def __init__(self, structManager):
        self.structManager = structManager

    def on_created(self, event):
        self.structManager.add(event.src_path)
        print("hey, ", event.src_path, "has been created!")

    def on_deleted(self, event):
        print("what the f**k! Someone deleted ", event.src_path)
        self.structManager.delete(event.src_path)

    def on_modified(self, event):
        if os.path.isdir(event.src_path):
            print ("folder modified. Likely child update")
        # print("hey buddy, ",event.src_path," has been modified")

    def on_moved(self, event):
        print("ok ok ok, someone moved ", event.src_path, " to ", event.dest_path)
        self.structManager.delete(event.src_path)
        self.structManager.add(event.dest_path)


def main():
    watchFolder = sys.argv[1]
    writeFolder = sys.argv[2]

    if (len(sys.argv) == 4):
        cmd = sys.argv[3]
        if cmd == "init":
            # currentdir = os.getcwd()
            watchFolder = watchFolder + "/"
            writeFolder = writeFolder + "/"
            if (not os.path.exists(watchFolder)):
                os.mkdir(watchFolder)
            if (not os.path.exists(writeFolder)):
                os.mkdir(writeFolder)
    completeWriteFolder = os.path.abspath(writeFolder) + "/"
    os.chdir(writeFolder)
    relWatchFolder = os.path.relpath(watchFolder)

    print("Watching " + relWatchFolder)
    print("Writing to " + completeWriteFolder)
    print("**********----**********")

    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    structManager = StructureManager(completeWriteFolder)

    fileMonEventHandler = FileMonEventHandler(structManager)

    event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

    event_handler.on_created = fileMonEventHandler.on_created
    event_handler.on_deleted = fileMonEventHandler.on_deleted
    event_handler.on_modified = fileMonEventHandler.on_modified
    event_handler.on_moved = fileMonEventHandler.on_moved

    observer = Observer()
    observer.schedule(event_handler, relWatchFolder, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
