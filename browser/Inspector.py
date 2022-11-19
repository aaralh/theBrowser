from dataclasses import dataclass
import tkinter
from tkinter import ttk
from typing import List, Literal, Optional
from tkinter.messagebox import showinfo
from web.dom.CharacterData import CharacterData
from web.dom.DocumentType import DocumentType
from web.dom.Node import Node

@dataclass
class NetworkRequest:
    url: str
    request_type: Literal["GET", "POST"]
    response_code: int
    response_size: int


class Inspector:
    def __init__(self, url: str, browser, dom: Optional[DocumentType] = None) -> None:
        self.url = url
        self.browser = browser
        self.dom: Optional[DocumentType] = dom
        self.network_requests: List[NetworkRequest] = []
        self.inspector_window = tkinter.Tk(className=f'Inspector | {self.url}')
        self.inspector_window.rowconfigure(0, weight=1)
        self.inspector_window.columnconfigure(0, weight=1)

        self.tabControl = ttk.Notebook(self.inspector_window)
        self.elements = ttk.Frame(self.tabControl)
        self.elements.rowconfigure(0, weight=1)
        self.elements.columnconfigure(0, weight=1)

        self.network = ttk.Frame(self.tabControl)
        self.network.rowconfigure(0, weight=1)
        self.network.columnconfigure(0, weight=1)

        self.tabControl.add(self.elements, text='Elements')
        self.tabControl.add(self.network, text='Network')

        self.tabControl.pack(expand=1, fill="both")
        
        def on_closing():
            print("On close")
            from browser.globals import BrowserState
            BrowserState.remove_inspector(self)
            self.inspector_window.destroy()
        self.inspector_window.protocol("WM_DELETE_WINDOW", on_closing)
        network_columns = ('url', 'request_type', 'response_code', "response_size")

        self.network_treeview = ttk.Treeview(self.network, columns=network_columns, show='headings')
        self.elements_treeview = ttk.Treeview(self.elements)

        # define headings
        self.network_treeview.heading('url', text='Url')
        self.network_treeview.heading('request_type', text='Request type')
        self.network_treeview.heading('response_code', text='Response code')
        self.network_treeview.heading('response_size', text='Response size')
        
        #self.elements_treeview['columns'] = ['#1']

        self.elements_treeview.heading("#0", text="Element", anchor=tkinter.W)

        #self.elements_treeview.heading('#0', text='Element')


        def network_item_selected(event) -> None:
            for selected_item in self.network_treeview.selection():
                item = self.network_treeview.item(selected_item)
                record = item['values']
                # show a message
                showinfo(title='Information', message=','.join(record))


        self.network_treeview.bind('<<TreeviewSelect>>', network_item_selected)

        def element_item_selected(event) -> None:
            from browser.globals import BrowserState
            BrowserState.set_selected_elements(self.elements_treeview.selection())
            self.browser.redraw()

        self.elements_treeview.bind('<<TreeviewSelect>>', element_item_selected)

        self.network_treeview.grid(row=0, column=0, sticky='nsew')
        self.elements_treeview.grid(row=0, column=0, sticky='nsew')

        # add a scrollbar
        elements_treeview_scrollbar = ttk.Scrollbar(self.network, orient=tkinter.VERTICAL, command=self.elements_treeview.yview)
        self.network_treeview.configure(yscroll=elements_treeview_scrollbar.set)
        elements_treeview_scrollbar.grid(row=0, column=1, sticky='ns')

        elements_treeview_scrollbar = ttk.Scrollbar(self.network, orient=tkinter.VERTICAL, command=self.elements_treeview.yview)
        self.elements_treeview.configure(yscroll=elements_treeview_scrollbar.set)

        if self.dom:
            self.update_dom(dom)



    def update_network_view(self) -> None:
        for request in self.network_requests:
            self.network_treeview.insert('', tkinter.END, values=(request.url, request.request_type, request.response_code, request.response_size))

    def __add_node_to_elements_view(self, node: Node, id: str, parent_id: Optional[str]) -> None:
        if parent_id:
            if isinstance(node, CharacterData):
                # TODO: Update html tokenizer/parser to remove 'empty' CharacterData elements.
                if not node.data.isspace():
                    self.elements_treeview.insert(str(parent_id), tkinter.END, text=f"{node.data.strip()}", iid=id, open=False)
            else:
                self.elements_treeview.insert(str(parent_id), tkinter.END, text=f"<{node.name}>", iid=id, open=False)
            #parent_child_count = len(self.elements_treeview.get_children(str(parent_id)))
            #print("Child", parent_child_count)
            #self.elements_treeview.move(str(id), str(parent_id), parent_child_count)
        else:
           self.elements_treeview.insert('', tkinter.END, text=f"<{node.name}>", iid=id, open=False) 
        
        for child in node.children:
            self.__add_node_to_elements_view(child, str(child.id), id)

    def update_elements_view(self) -> None:
        if not self.dom: return
        for child in self.dom.children:
            self.__add_node_to_elements_view(child, str(child.id), None)

    def clear_elements_view(self) -> None:
        if not self.dom: return
        self.elements_treeview.delete(*self.elements_treeview.get_children())

    def update_url(self, url: str) -> None:
        self.url = url
        self.inspector_window.title(url)

    def update_dom(self, dom: DocumentType) -> None:
        if self.dom:
            self.clear_elements_view()
        self.dom = dom
        self.update_elements_view()


    def add_network_request(self, request: NetworkRequest) -> None:
        self.network_requests.append(request)
        self.update_network_view()
    
    def clear_network_requests(self) -> None:
        self.network_requests = []
        self.network_treeview.delete(*self.network_treeview.get_children())



    