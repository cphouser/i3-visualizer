
def recTreePrint(tainer,depth,p_y,p_x):
    p_x = p_x + 1
    r_bound = 0
    for i in tainer.nodes:
        p_y = p_y + 1
        if i.name is None:
            i_name = "no name"
        else: i_name = i.name
        if i.window_class is None:
            i_window_class = "no class"
        else: i_window_class = i.window_class
        win.addstr(p_y,p_x,shortName(i_name,7)+"("+i.layout+")"+i_window_class,cL[depth])
        #if isinstance(i.name,str) and isinstance(i.type,str):
        #    win.addstr(p_y,p_x,shortName(i.layout,6)+shortName(i.name,6)+" ("+i.type+")",cL[depth])
        #elif isinstance(i.type,str):
        #    win.addstr(p_y,p_x,shortName(i.layout,6)+" ("+i.type+")",cL[depth])
        y_null,r_bound_new = win.getyx()
        r_bound = max([r_bound_new, r_bound])
        if len(i.nodes) > 0:
            p_y, r_bound_new = recTreePrint(i,depth+1,p_y,p_x)
            r_bound = max([r_bound_new, r_bound])
    return(p_y,r_bound)

def printWorks():
    tree = i3.get_tree()
    wList = tree.nodes[1].nodes[1].nodes#list of workspaces
    pos_y = 1
    pos_x = 1
    for i in wList:
        win.addstr(pos_y,pos_x,"   Workspace "+i.name+"  ",cL[1])
        parseTree(i,pos_y+1,pos_x, WORKSPACE_WIDTH)
        win.addstr(pos_y+20,pos_x,i.name+" - "+i.layout,cL[6])
        recTreePrint(i,3,pos_y+20, pos_x)
        pos_x +=  WORKSPACE_WIDTH+1
        
def parseTree(tainer,p_y,p_x,width):
    if len(tainer.nodes) == 0:
        f_width = width // 3
        f_end = width % 3 - 1
        if hasattr(tainer,'window_instance'): t_instance = tainer.window_instance
        else: t_instance = "no instance"
        win.addstr(p_y,p_x,
                shortName(tainer.name,f_width * 2)+
                shortName(tainer.window_class,f_width+f_end)+
                chr(HALF_BLOCK),cL[7])
        win.addstr(p_y+1,p_x,
                #shortName(tainer.type+"-"+tainer.layout,f_width)+
                shortName(tainer.window,f_width)+
                shortName(t_instance,2*f_width+f_end)+
                chr(FULL_BLOCK),cL[7])
        return p_y+2
    else:
        if tainer.layout == "splith":
            sub_width = width // len(tainer.nodes)
            for i in tainer.nodes:
                #win.addstr(p_y,p_x,shortName(i.name,sub_width-1)+"|",cL[5])
                #win.addstr(p_y+1,p_x,shortName(i.type,sub_width-2)+"_|",cL[5])
                parseTree(i,p_y,p_x, sub_width)
                p_x += sub_width
            return p_y
        elif tainer.layout == "splitv":
            for i in tainer.nodes:
                #win.addstr(p_y,p_x,shortName(i.name,width-1)+"|",cL[5])
                #win.addstr(p_y+1,p_x,shortName(i.type,width-2)+"_|",cL[5])
                np_y = parseTree(i,p_y,p_x, width)
                p_y = np_y
            #p_y += 2
            return p_y
        else:
            win.addstr(p_y,p_x,shortName(tainer.layout,width-1)+chr(HALF_BLOCK),cL[5])
            p_y += 1
            for i in tainer.nodes:
                win.addstr(p_y,p_x,">",cL[5])
                p_y = parseTree(i,p_y,p_x+1, width-1)
            return p_y
