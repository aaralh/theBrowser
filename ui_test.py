import tkinter

root = tkinter.Tk()
root.geometry('250x150')

frame1 = tkinter.Frame(root)
frame1.pack(side=tkinter.LEFT, anchor=tkinter.N)

frame2 = tkinter.Frame(
    frame1,
    height=30,
    width=60,
    highlightbackground="red",
    highlightthickness=1)
frame2.pack_propagate(0)
frame2.pack(side=tkinter.LEFT, anchor=tkinter.N, pady=0, padx=0)

frame3 = tkinter.Frame(
    frame2,
    height=30,
    width=60,
    highlightbackground="blue",
    highlightthickness=1)
frame3.pack_propagate(0)
frame3.pack(side=tkinter.LEFT, anchor=tkinter.N, pady=0, padx=0)

text_widget = tkinter.Label(frame3, text="Hello World!")  # type: ignore
text_widget.pack(side=tkinter.LEFT, anchor=tkinter.N)

root.mainloop()