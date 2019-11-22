#!/usr/bin/python3
import json
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class Templates:
    def getClassOpener(self,className):
         return "class "+className+" {\n"
    
    def getClassEnd(self):
        return "}\n"    
    
    def getMemberDeclaration(self,memberName):
        return "static const String "+self._getMemberDeclarationName(memberName)+" = " +memberName +"\n"
    
    def _getMemberDeclarationName(self,memberName):
        if("/" in memberName):
            nameParts  = memberName.split("/")
            memberName = nameParts[len(nameParts)-1]
        if("." in memberName):
            nameParts = memberName.split(".")
            memberName = nameParts[0]
        return memberName
        

class StructureManager:
    def __init__(self,writeFolder):
        self.structurePath = writeFolder+"structure.json"
        if(not os.path.exists(self.structurePath)):
            file = open(self.structurePath,"w")
            file.close()
        self.assetManagerFilePath = writeFolder+"AssetManager.dart"
        self.templates = Templates()
        self.parseStructure()
        self.save()
        pass
    def parseStructure(self):
        file = open(self.structurePath,'r')
        self.previousContents = file.read()
        if(len(self.previousContents) == 0):
            self.rootElement = []
            print("New File Found")
            return;    
        else:
            structJSON = json.loads(self.previousContents)
            self.rootElement = structJSON["classes"]
            file.close()
        print("Parsing Complete")
    
    def _refresh(self):
        self.parseStructure()
        
    def save(self):
        self.assetManagerFile = open(self.assetManagerFilePath,"w")
        numberOfClasses = len(self.rootElement)
        #print ("Number Of Classes",numberOfClasses)
        for i in range(numberOfClasses):
            className = self.rootElement[i]["name"]
            members = self.rootElement[i]["members"]
            self._writeClass(className,members)
        self.assetManagerFile.close()
        self._saveStructureJson()
    
    def _saveStructureJson(self):
        file = open(self.structurePath,"w")
        finalStructure = {
            "classes":self.rootElement
        }
        json.dump(finalStructure,file,indent=4)
        print("Structure Saved")
            
    
    def _writeClass(self,className,members):
        
        print("Writing class ",className)
        self._write(self.templates.getClassOpener(className))
        for member in members:
            print("Writing memeber ",member)
            self._write(self.templates.getMemberDeclaration(member))
        self._write(self.templates.getClassEnd())
    
    def _write(self,content):
        self.assetManagerFile.write(content)
        
    def add(self,paramClassName,memberName):
        for i in range(len(self.rootElement)):
            className = self.rootElement[i]["name"]
            print("Iterating through",className)
            if paramClassName == className:
                print("Class Found")
                if self._addMemberTo(className,memberName,i):
                    self.save()
                break
        
    def addClass(self,className):
        if "/" in className:
            splitName = className.split("/")
            className = splitName[len(splitName) - 1]
        if className not in self.rootElement:
            memberDeclaration = {
                'name':className,
                'members':[]
            }
            declarationJSON = json.dumps(memberDeclaration)
            self.rootElement.append(eval(declarationJSON,{'__builtins__': {}}))
            print("After add",self.rootElement)
            self.save()
            print("New Class added")
        else:
            print("Duplicate class.Skipping")
    
    def _addMemberTo(self,className,memberName,atIndex):
         classmemebers = self.rootElement[atIndex]["members"]
         print("Current Member Count",len(classmemebers))
         if(memberName not in classmemebers):
            classmemebers.append(memberName)
            print("Member Added. Length->",len(classmemebers))
            return True
         else:
             print("Member Already Exists.Skipping")
             return False
            
    def delete(self,classname,membervalue):
        
        pass
    def modify(self,classname,membervalue):
        
        pass
    def _convert(self,list):
        it = iter(list)
        dct = dict(zip(it,it))
        return dct
        
        
class FileMonEventHandler(PatternMatchingEventHandler):
    def __init__(self,structManager):
        self.structManager = structManager
    
    def on_created(self,event):
        newPath = os.path.relpath(event.src_path)
        if(os.path.isdir(newPath)):
            self.structManager.addClass(newPath)        
        print("hey, ",newPath ,"has been created!")

    def on_deleted(self,event):
        print("what the f**k! Someone deleted {event.src_path}!")

    def on_modified(self,event):
        print("hey buddy, {event.src_path} has been modified")

    def on_moved(self,event):
        print("ok ok ok, someone moved {event.src_path} to {event.dest_path}")
        

def main():
    watchFolder = sys.argv[1]
    writeFolder = sys.argv[2]
    if(len(sys.argv)== 4 ):
        cmd  = sys.argv[3]
        if cmd == "init":
            currentdir = os.getcwd()
            watchFolder = currentdir+watchFolder+"/"
            writeFolder = currentdir+writeFolder+"/"
            if(not os.path.exists(watchFolder)):
                os.mkdir(watchFolder)
            if(not os.path.exists(writeFolder)):
                os.mkdir(writeFolder)
    completeWriteFolder = os.path.abspath(writeFolder)+"/"
    relWatchFolder = os.path.relpath(watchFolder)
    
    print("Watching " +relWatchFolder )
    print("Writing to " +completeWriteFolder)
    
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    structManager  = StructureManager(completeWriteFolder)
    
    fileMonEventHandler = FileMonEventHandler(structManager)
    
    event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    
    event_handler.on_created = fileMonEventHandler.on_created
    event_handler.on_deleted = fileMonEventHandler.on_deleted
    event_handler.on_modified = fileMonEventHandler.on_modified
    event_handler.on_moved = fileMonEventHandler.on_moved
    
    observer = Observer()
    observer.schedule(event_handler,relWatchFolder,recursive = True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()