#!/usr/bin/env python3
# vim: set foldmethod=indent foldnestmax=2:


import i3ipc
import curses
import math
import json

#create connection object
i3 = i3ipc.Connection()

#initialize screen
win = curses.initscr()
curses.noecho()
curses.cbreak()
curses.curs_set(0)#hidden cursor
win.keypad(True)
windowHeight = curses.LINES - 1
windowWidth = curses.COLS - 1
cL = []
WORKSPACE_WIDTH = 16
HALF_BLOCK = 9616
FULL_BLOCK = 9608
WIN_COLOR_KEY = {0:4, 1:1, 2:7, 3:6, 4:0, 5:5, 6:4 }#val: cL index
CON_COLOR_KEY = {0:0, 1:5, 2:4, 3:1, 4:7, 5:6, 6:0 }#key: depth
MOVE_COMMANDS = {
    "w":"up",
    "a":"left",
    "s":"down",
    "d":"right"
}#for i3 comm


class Window:
    def __init__(self,tainer,depth,parent):
        self.id = tainer.id
        self.name = tainer.name
        if self.name is None: self.name = "no attribute"
        self.layout = tainer.layout
        self.window_class = tainer.window_class
        if self.window_class is None: self.window_class = "no attribute"
        self.instance = tainer.window_instance
        if self.instance is None: self.instance = "no attribute"

        #for i in [self.id,self.name,self.layout,self.window_class,self.instance]:
        #    if i is None: i = "no attribute"
        self.select = False
        self.depth = depth
        self.children = []
        self.parent = parent
        self.pos = [None,None]
        self.width = None

    def selectW(self):
        self.select = True
        self.printW()

    def deselectW(self):
        self.select = False
        self.printW()

    def printW(self,p_y=None,p_x=None,width=None):
        if p_y is not None:
            self.pos[0] = p_y
        if p_x is not None:
            self.pos[1] = p_x
        if width is not None:
            self.width = width
        if self.pos[0] is None or self.pos[1] is None or self.width is None:
            win.addstr(windowHeight,0,"Window printed at null location",cL[2])
            return 0
        win.addstr(*self.pos, shortName(self.name,self.width-1)+
                chr(HALF_BLOCK),self.color())
        win.addstr(self.pos[0]+1,self.pos[1], 
                shortName(self.window_class,self.width-5)+
                "["+self.layout[0]+self.layout[-1]+"]"+chr(FULL_BLOCK),
                self.color())
        return 2#lines added

    def color(self):
        color = cL[WIN_COLOR_KEY[self.depth]]
        if self.select:
            color = color | curses.A_BOLD
        return color

class Selection:
    def __init__(self,workspaces):
        self.workspaces = workspaces
        self.workspace = 0
        self.selected = self.workspaces[self.workspace]
        self.workspaces[self.workspace].selectW()

    def printInfo(self,p_y,width):
        lines = [   ("Selected Window:",cL[13]), (self.selected.name,cL[9]),
                    ("-Layout: ",cL[10]), (self.selected.layout,cL[9]),
                    ("-Class: ",cL[10]), (self.selected.window_class,cL[9]),
                    ("-Instance: ",cL[10]), (self.selected.instance,cL[9]),
                    ("-ID: ",cL[10]), (str(self.selected.id),cL[9]),
                    ("-Children: ",cL[10]), (str(len(self.selected.children)),cL[9])
                ]
        #p_x = max([len(i) for (i,j) in lines])
        win.addstr(p_y,1," = i3 =",cL[11] | curses.A_BOLD)
        #lines = [(shortName(i,min([p_x,windowWidth-3]))+"  ",j) for (i,j) in lines]
        for i in range(0,len(lines),2):
            p_y += 1
            if p_y >= windowHeight:
                break
            (name,color) = lines[i+1]
            if name == "no attribute" or name == "0": color = cL[10]
            lines[i+1] = (shortName(name,width-len(lines[i][0])),color)
            win.addstr(p_y,1,*(lines[i]))
            win.addstr(*(lines[i+1]))

    def printActions(self,p_y,width):
        lines = [   ("Move Selection: ", "<arrow keys>", "wcl"),
                    ("Shift Window: ", "w a s d", "wcl"),
                    ("Kill Parent: ", "k", "wcl"),
                ]
        win.addstr(p_y,width+1," = Commands =",cL[8] | curses.A_BOLD)
        for i in lines:
            p_y += 1
            if p_y >= windowHeight:
                break
            win.addstr(p_y,width+1,i[0],cL[13])
            win.addstr(i[1],cL[10] )

    def move(self,key):
        window = self.selected
        #win.addstr(windowHeight,0,key,window.color())
        #win.addstr(" w"+str(self.workspace),cL[2])
        if key == "UP":
            if window.parent is not None: 
                window.deselectW()
                window.parent.selectW()
                self.selected = window.parent
            else: return
        elif key == "DOWN":
            if len(window.children) > 0:
                window.deselectW()
                window.children[0].selectW()
                self.selected = window.children[0]
            else: return 
        else:
            if window.parent is not None:
                window = window.parent
                oldIndex = 0 
                while window.children[oldIndex] != self.selected:
                    oldIndex += 1
                newIndex = oldIndex
                if key == "LEFT": newIndex -= 1
                else: newIndex += 1
                if newIndex < 0: newIndex = len(window.children) - 1
                elif newIndex >= len(window.children): newIndex = 0
                self.selected.deselectW()
                self.selected = window.children[newIndex]
                self.selected.selectW()
            else:
                if key == "LEFT": self.workspace -= 1
                else: self.workspace += 1
                if self.workspace < 0: self.workspace = len(self.workspaces) - 1
                elif self.workspace >= len(self.workspaces): self.workspace = 0
                window.deselectW()
                self.selected = self.workspaces[self.workspace]
                self.selected.selectW()
    
    def shift(self,key):
        windowid = self.selected.id
        moves = "wasd"
        cmd_string = "[con_id="+str(windowid)+"] move "+MOVE_COMMANDS[key]
        win.addstr(windowHeight-2,0,cmd_string,self.selected.color())
        i3reply = i3.command(cmd_string)
        return i3reply

class WindowContainer(Window):
    def __init__(self,tainer,depth,parent):
        Window.__init__(self,tainer,depth,parent)
        for i in tainer.nodes:
            if len(i.nodes) == 0: 
                child = Window(i,depth+1,self)
            else:
                child = WindowContainer(i,depth+1,self)
            self.addKids(child)
    
    def printW(self,p_y=None,p_x=None,width=None):#returns height of printed area
        height = 0
        if p_y is not None:
            self.pos[0] = p_y
        if p_x is not None:
            self.pos[1] = p_x
        if width is not None:
            self.width = width
        if self.pos[0] is None or self.pos[1] is None or self.width is None:
            win.addstr(windowHeight,0,"Container printed at null location",cL[2])
            return 0
        if self.parent is None:#workspace
            win.addstr(*self.pos, shortName(" workspace "+self.name,self.width), self.color())
            height += 1
        if self.layout == "splith":
            sub_width = self.width // len(self.children)
            end_width = self.width % len(self.children)
            sub_height = []
            for i in range(len(self.children)):
                if i == len(self.children):#if last child include width remainder
                    win_width = sub_width + end_width
                else: win_width = sub_width
                sub_height.append(
                    self.children[i].printW(self.pos[0] + height, 
                        self.pos[1] + (i*sub_width), win_width)
                    )
            height += max(sub_height)
        elif self.layout == "splitv":
            for i in self.children:
                height += i.printW(self.pos[0] + height, self.pos[1], self.width)
        elif self.layout == "tabbed":
            win.addstr(*self.pos, shortName(" tabs ",self.width),self.color())
            height += 1
            for i in self.children:
                win.addstr(self.pos[0] + height,self.pos[1],">",self.color())
                height += i.printW(self.pos[0] + height, self.pos[1]+1, self.width-1)
        elif self.layout == "stacked":
            win.addstr(*self.pos, shortName(" stack ",self.width),self.color())
            height += 1
            for i in self.children:
                win.addstr(self.pos[0] + height,self.pos[1],"-",self.color())
                height += i.printW(self.pos[0] + height, self.pos[1]+1, self.width-1)
        #win.addstr(p_y,p_x, shortName(self.name,width-1)+
        #        chr(HALF_BLOCK),self.color())
        #win.addstr(p_y+1,p_x, shortName(self.window_class,width-5)+
        #        "["+self.layout[0]+self.layout[-1]+"]"+chr(FULL_BLOCK),
        #        self.color())
        return height 

    def addKids(self,child):
        self.children.append(child)
    
    def color(self):
        color = cL[CON_COLOR_KEY[self.depth]]
        if self.select:
            color = color | curses.A_BOLD
        return color

def colorInit():
    curses.start_color()
    if curses.has_colors():
        #win.addstr(0,1,"# of colors: "+str(curses.COLORS) )
        #win.addstr(1,1,"# of color pairs: "+str(curses.COLOR_PAIRS) )
        cL.extend([curses.color_pair(0),curses.A_STANDOUT])
        foreList = [7,0,5,6,3,4]
        for i in range(1,len(foreList)+1):
            item = foreList[i-1]
            curses.init_pair(i,item,i)
            cL.append(curses.color_pair(i))
        for i in range(1,len(foreList)+1):
            curses.init_pair(i+7,i,0)
            cL.append(curses.color_pair(i+7))
        #for j in range(0,1):
        win.move(0,5)
        for i in range(len(cL)):
            #ij = (len(cL)//2) * j + i
            item = cL[i]
            if len(str(i)) == 1: cStr = " C" 
            else: cStr = "C"
            win.addstr(cStr,item | curses.A_BOLD)
            win.addstr("#"+str(i),item)
    return cL

#return a string rendering of name with length dim_x characters
def shortName(name,dim_x):
    if name is None:
        return "*".ljust(dim_x)
    elif name is not str:
        name = str(name)
    if len(name) < dim_x:
        return name.ljust(dim_x)
    elif len(name) == dim_x:
        return name
    else:
        if dim_x > 8:
            return name[0:3]+".."+name[-(dim_x-5):]
        elif dim_x > 4:
            return name[0]+".."+name[-(dim_x-3):]
        else:
            return name[0:dim_x]

#clear line p_y
def clearLine(p_y):
    win.move(p_y,0)
    win.clrtoeol()

#return height of workspace layout diagram appended to list of workspaces
def initWorksPrint(p_y,p_x):
    #get the tree from i3, add each workspace to wList
    tree = i3.get_tree()
    wConList = tree.nodes[1].nodes[1].nodes#list of workspaces
    wList = []
    for i in wConList:
        i_window = WindowContainer(i, 0, None)
        wList.append(i_window)
    
    #calculate workspace width and spread
    works_width = max(
        [1<<exponent for exponent in 
            range(math.ceil(math.log2(windowWidth//len(wList))))
        ]
    )#max power of two s.t < windowWidth // # of workspaces
    works_spread = windowWidth // len(wList)

    #print workspace layout diagram and calculate height
    heights = []
    for i in range(len(wList)):
        height = wList[i].printW(p_y,p_x,works_width)
        heights.append(height)
        p_x += works_spread
    wList.append(max(heights))
    return wList

def masterInit():
    win.move(1,0)
    win.clrtobot()
    workspaces = initWorksPrint(1,1)
    p_y = workspaces.pop()
    p_x = 1
    selection = Selection(workspaces)#select first workspace
    win.addstr(p_y + 2,0,shortName(" ",windowWidth),cL[1])#line below diagram
    selection.printInfo(p_y + 3,windowWidth//2)#print i3 window data as list
    selection.printActions(p_y + 3,windowWidth//2)
    return selection,p_y,p_x

def main():
    cL = colorInit()
    selection,p_y,p_x = masterInit()
    while True: #input loop
        key = win.getkey()
        if key == 'q':
            break
        #elif (key == curses.KEY_UP or key == curses.KEY_DOWN
        #        or key == curses.KEY_LEFT or key == curses.KEY_RIGHT):
        if len(key) > 1:
            if key[4:] in "UPDOWNLEFTRIGHT":
                selection.move(key[4:])
                selection.printInfo(p_y + 3,windowWidth//2)
                continue
        elif key in "wasd":
            command_return = selection.shift(key)
            print_ret = "|".join(str(x) for x in command_return)
            win.addstr(p_y + 2,1,print_ret,cL[1])
        else:
            win.addstr(p_y + 2,1,"unclassified input: "+key,cL[6])
            continue
        selection,p_y,p_x = masterInit()

    curses.nocbreak()
    win.keypad(False)
    curses.echo()
    curses.endwin()

if windowHeight < 20 or windowWidth < 70:
    win.move(windowHeight//2 - 2, windowWidth//2 - 20)
    win.addstr('Window Size: ' + str(windowHeight) + ' cols, ' + str(windowWidth) + ' rows')
    win.move(windowHeight//2 - 1, windowWidth//2 - 20)
    win.addstr('resize to at least 20 x 70 and press any key')
    win.refresh()
    win.getch()
    curses.nocbreak()
    win.keypad(False)
    curses.echo()
    curses.endwin()
else:
    main()

#wrap up
focused = tree.find_focused()
curses.nocbreak()
win.keypad(False)
curses.echo()
curses.endwin()
