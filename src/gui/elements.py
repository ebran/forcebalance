import Tkinter as tk
import tkFileDialog as tkfile
import sys, os

import objects
from eventhandlers import _bindEventHandler

class ObjectViewer(tk.LabelFrame):
    def __init__(self,root):
        tk.LabelFrame.__init__(self, root, text="Loaded Objects")
        self.root = root

        self.calculation=None
        self.activeselection=None
        self.selectionchanged=tk.BooleanVar()
        self.selectionchanged.set(True)
        self.needUpdate=tk.BooleanVar()
        self.needUpdate.trace('r',self.update)

        self.content = tk.Text(self, cursor="arrow", state="disabled", width="30")
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)

        # bind scrollbar actions
        self.scrollbar.config(command = self.content.yview)
        self.content['yscrollcommand']=self.scrollbar.set

        # arrange and display list elements
        self.content.pack(side=tk.LEFT, fill=tk.Y)
        self.content.update()
        self.scrollbar.pack(side=tk.RIGHT,fill=tk.Y)

    def open(self, filename):
        """Parse forcebalance input file and add referenced objects"""
        if filename=='': return

        self.calculation = objects.CalculationObject(filename)
        self.update()

    def clear(self):
        self.calculation = None
        self.update()

    def update(self, *args):
        self.content["state"]= "normal"
        self.content.delete("1.0","end")
        self['text']="Objects"

        if self.calculation:
            self['text'] += " - " + self.calculation['options']['name']
            self.content.bind('<Button-1>', _bindEventHandler(self.select, object = self.calculation))
            
            self.content.insert("end",' ')
            l = tk.Label(self.content,text="General Options", bg="#DEE4FA")
            self.content.window_create("end",window = l)
            l.bind('<Button-1>', _bindEventHandler(self.select, object = [ self.calculation['options'] ]))
            self.content.insert("end",'\n')
                

            # Event handler to toggle whether targets list should be expanded
            def toggle(e):
                self.calculation['_expand_targets'] = not self.calculation['_expand_targets']
                self.needUpdate.get()

            targetLabel = tk.Label(self.content,text="Targets", bg="#FFFFFF")
            targetLabel.bind('<Button-1>', _bindEventHandler(self.select, object = self.calculation['targets']))
            
            targetLabel.bind("<Double-Button-1>", toggle)

            if self.calculation['_expand_targets']:
                self.content.insert("end",' ')
                self.content.window_create("end", window = targetLabel)
                self.content.insert("end",'\n')
                for target in self.calculation['targets']:
                    self.content.insert("end",'   ')
                    l=tk.Label(self.content, text=target['name'], bg="#DEE4FA")
                    self.content.window_create("end", window = l)
                    self.content.insert("end",'\n')
                    l.bind('<Button-1>', _bindEventHandler(self.select, object=[ target ]))
            else:
                self.content.insert("end",'+')
                self.content.window_create("end", window = targetLabel)
                self.content.insert("end",'\n')

            self.content.insert("end",' ')
            l=tk.Label(self.content, text="Forcefield", bg="#DEE4FA")
            self.content.window_create("end", window = l)
            l.bind('<Button-1>', _bindEventHandler(self.select, object=[ self.calculation['forcefield'] ]))
            self.content.insert("end",'\n\n')

        self.content["state"]="disabled"

    def select(self, e, object):
        for widget in self.content.winfo_children():
            if not widget['bg']=="#FFFFFF":
                widget["relief"]=tk.FLAT
                #widget['bg']='#DEE4FA'
        #e.widget['bg']='#4986D6'
        e.widget["relief"]="solid"
        self.activeselection=object
        self.selectionchanged.get() # reading this variable triggers a refresh

    def scrollUp(self, e):
        self.content.yview('scroll', -2, 'units')

    def scrollDown(self, e):
        self.content.yview('scroll', 2, 'units')

class DetailViewer(tk.LabelFrame):
    def __init__(self, root, opts=''):
        # initialize variables
        self.root = root
        self.printAll = tk.IntVar()
        self.printAll.set(False)
        self.currentObject = None # keep current object in case view needs refreshing
        self.currentElement= None # currently selected element within current object

        # Viewer GUI elements
        tk.LabelFrame.__init__(self, root, text="Details")
        self.content = tk.Text(self,cursor="arrow",state="disabled")
        self.content.tag_config("error", foreground="red")
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.helptext = tk.Text(self, width=70, state="disabled", bg="#F0F0F0", wrap=tk.WORD)

        # bind scrollbar actions
        self.scrollbar.config(command = self.content.yview)
        self.content['yscrollcommand']=self.scrollbar.set
        self.scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        self.root.bind_class("scrollable", "<Button-4>", self.scrollUp)
        self.root.bind_class("scrollable", "<Button-5>", self.scrollDown)

        # arrange and display list elements
        self.content.pack(side=tk.LEFT, fill=tk.Y)
        self.content.update()

        # right click context menu
        self.contextmenu = tk.Menu(self, tearoff=0)
        self.contextmenu.add_command(label="Add option", state="disabled")
        self.contextmenu.add_checkbutton(label="show all", variable=self.printAll)
        self.content.bind("<Button-3>", lambda e : self.contextmenu.post(e.x_root, e.y_root))
        self.content.bind("<Button-1>", lambda e : self.contextmenu.unpost())
        self.printAll.trace('w', lambda *x : self.load())

    def load(self,newObject=None):
        if newObject:
            self.currentObject = newObject
            self.printAll.set(0)    # reset view to only show values changed from default

        self['text']="Details"

        self.content["state"]="normal"
        self.content.delete("1.0","end")
        if self.currentObject and len(self.currentObject) ==1:   # if there is an object to display and it is not a collection
            self['text']+=" - %s" % self.currentObject[0]['name']
        else:
            self['text']+=" - %d Configured Targets" % len(self.currentObject)
        try:
            for object in self.currentObject:
                printValues = object.display(self.printAll.get())
                self.populate(printValues)
        except:
            self.content.insert("end", "Error trying to display <%s %s>\n" % (self.currentObject[0]['type'], self.currentObject[0]['name']), "error")
            from traceback import format_exc
            self.content.insert("end", format_exc(), "error")
        
        self.content["state"]="disabled"

    def populate(self, displayText):
        """Populate the view with information in displayText argument"""
        if type(displayText)==str:
            self.content.insert("end", displayText)
        if type(displayText)==tuple:
            for key in displayText[0].keys():
                frame = tk.Frame(self.content)
                frame.bindtags((key, "scrollable"))
                keylabel = tk.Label(frame, text=key, bg="#FFFFFF", padx=0, pady=0)
                keylabel.bindtags((key, "scrollable"))
                separator = tk.Label(frame, text=" : ", bg="#FFFFFF", padx=0, pady=0)
                separator.bindtags((key, "scrollable"))
                valuelabel = tk.Label(frame, text=displayText[0][key], bg="#FFFFFF", padx=0, pady=0)
                valuelabel.bindtags((key, "scrollable"))

                keylabel.pack(side=tk.LEFT)
                separator.pack(side=tk.LEFT)
                valuelabel.pack(side=tk.LEFT)

                self.content.window_create("end", window = frame)
                self.content.insert("end", '\n')

                # right click help popup
                self.root.bind_class(key, "<Button-3>", _bindEventHandler(self.showHelp, object = self.currentObject, option=key))

            if self.printAll.get():
                self.content.insert("end", "\n--- Default Values ---\n")
                for key in displayText[1].keys():
                    frame = tk.Frame(self.content)
                    frame.bindtags((key, "scrollable"))
                    keylabel = tk.Label(frame, text=key, bg="#FFFFFF", padx=0, pady=0)
                    keylabel.bindtags((key, "scrollable"))
                    separator = tk.Label(frame, text=" : ", bg="#FFFFFF", padx=0, pady=0)
                    separator.bindtags((key, "scrollable"))
                    valuelabel = tk.Label(frame, text=str(displayText[1][key]), bg="#FFFFFF", padx=0, pady=0)
                    valuelabel.bindtags((key, "scrollable"))

                    keylabel.pack(side=tk.LEFT)
                    separator.pack(side=tk.LEFT)
                    valuelabel.pack(side=tk.LEFT)

                    self.content.window_create("end", window = frame)
                    self.content.insert("end", '\n')

                    self.root.bind_class(key, "<Button-3>", _bindEventHandler(self.showHelp, object = self.currentObject, option=key))

        self.content.insert("end",'\n')

    def clear(self):
        self.currentObject=None
        self.load()

    def scrollUp(self, e):
        self.content.yview('scroll', -2, 'units')

    def scrollDown(self, e):
        self.content.yview('scroll', 2, 'units')

    def showHelp(self, e, object, option):
        self.helptext["state"]="normal"
        self.helptext.delete("1.0","end")

        # get message and calculate how high window should be
        helpmessage = object.getOptionHelp(option)
        height=0
        for line in object.getOptionHelp(option).splitlines():
            height += 1 + len(line)/70

        self.helptext.insert("end", helpmessage)
        self.helptext['height']=height
        self.helptext.place(x=e.x, y=e.y_root-self.root.winfo_y())
        self.root.bind("<Motion>", lambda e : self.helptext.place_forget())
        self.root.bind("<Button>", lambda e : self.helptext.place_forget())

class ConsoleViewer(tk.LabelFrame):
    def __init__(self, root):
        tk.LabelFrame.__init__(self, root, text="Console")
        
        self.console = tk.Text(self, state="disabled",cursor="arrow")
        self.console.pack(fill=tk.Y)
        self.stdout = sys.stdout
        sys.stdout = self

    def write(self, input):
        self.console['state']="normal"
        self.console.insert(tk.END, input)
        self.stdout.write(input)
        self.scrollDown()
        self.console['state']="disabled"

    def flush(self):
        self.stdout.flush()

    def scrollUp(self, *args):
        self.console.yview('scroll', -1, 'units')

    def scrollDown(self, *args):
        self.console.yview('scroll', 1, 'units')