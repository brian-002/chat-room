

import socket
import sys
import threading
from tkinter import *
import select
from tkinter.scrolledtext import ScrolledText

global writeLock
message = ''
send = threading.Event()
send_lock = threading.Lock()


class App:
    def __init__(self, master):
        connect_frame = Frame(master, relief=RAISED, borderwidth=1)
        connect_frame.pack(fill=X, expand=True)
        chat_frame = Frame(master, relief=RAISED, borderwidth=1)
        chat_frame.pack(fill=BOTH, expand=True)
        # self.connect_frame(connect_frame)
        self.chat_frame_setup(chat_frame)
        self.connect('vpn.aasoftwaresolutions.com', 9009)

    def connect_frame(self, frame):
        connect = Label(frame, text="Connect").grid(row=0, column=0, pady=(10, 5), padx=(5, 0))
        host = Label(frame, text="Host: ").grid(row=1, column=0, padx=(10, 3), pady=(0, 10))
        host_box = Entry(frame, background='white', width=45)
        host_box.grid(row=1, column=1, padx=(0, 10), pady=(0, 10))
        port = Label(frame, text="Port: ", width=10).grid(row=1, column=2, padx=(0, 3), pady=(0, 10))
        port_box = Entry(frame, background='white')
        port_box.grid(row=1, column=3, padx=(0, 15), pady=(0, 10))
        global connect_label
        connect_label = Label(frame, text="")
        connect_label.grid(row=2, column=0, padx=(5, 0), pady=(5, 10), columnspan=3)
        global connect_button
        connect_button = Button(
            frame, text="Connect", width=15, command=(lambda: self.connect(host_box.get(), port_box.get()))
        )
        connect_button.grid(row=2, column=3, padx=(5, 15), pady=(5, 10))

    def chat_frame_setup(self, frame):
        chat_label = Label(frame, text="Chat").grid(row=0, column=0, pady=(10, 5), padx=(5, 0))
        global chat_box
        global disconnect_button
        global send_button
        global type_box

        chat_box = ScrolledText(frame, font=('consolas', 10), undo=False, wrap='word', state=DISABLED)
        chat_box.grid(row=0, column=0, columnspan=1, rowspan=3, padx=(15, 15), pady=(10, 10))

        type_box = Text(frame, width=80, height=2)
        type_box.grid(row=4, column=0)

        button_frame = Frame(frame)
        disconnect_button = Button(
            button_frame, text="Disconnect", width=15, command=(lambda: self.disconnect())
        )
        disconnect_button.grid(row=0, column=1, padx=(0, 15), pady=(0, 15))
        send_button = Button(
            button_frame, text="Send", width=15, command=(lambda: self.send_message())
        )
        send_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 15))
        button_frame.grid(row=6, column=0)

    @staticmethod
    def send_message():
        global message
        global send
        text = type_box.get(1.0, END)
        text = text.strip()
        if text != '' and text != '\n' and text != ' ':
            message = text
            with writeLock:
                chat_box['state'] = NORMAL
                chat_box.insert(END, "<YOU>: " + text + '\n')
                chat_box['state'] = DISABLED
                type_box.delete(0.0, END)
                chat_box.see(END)

        global send_lock
        # send.set()
        send_lock.release()

    @staticmethod
    def connect(host, port):
        # connect_label.configure(text=("Attempting connection to " + host + " on port " + port + "."))
        chat_box['state'] = NORMAL
        chat_box.insert(END, 'Attempting connection to ' + str(host) + ' on port ' + str(port) + '...\n')
        chat_box['state'] = DISABLED
        chat_box.see(END)

        # attempt to connect
        global s
        global send
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)

        success = True
        try:
            int_port = int(port)
            s.connect((host, int_port))
        except:
            success = False
            chat_box['state'] = NORMAL
            chat_box.insert(END, 'Unable to connect to ' + str(host) + ' on port ' + str(port) + ', you know who to call.\n')
            chat_box['state'] = DISABLED
            chat_box.see(END)
            # connect_label.configure(text="Unable to connect to " + host + " on port " + port + ".")

        if success:
            chat_box['state'] = NORMAL
            chat_box.insert(END, 'Successfully connected to ' + str(host) + ' on port ' + str(port) + '!\n\n')
            chat_box['state'] = DISABLED
            chat_box.see(END)
            # connect_button.configure(state=DISABLED)
            # connect_label.configure(text="Connected to " + host + ".")
            send_thread = threading.Thread(target=send_msg, args=(s,)).start()
            recv_thread = threading.Thread(target=recv_msg, args=(s,)).start()


    @staticmethod
    def disconnect():
        chat_box['state'] = NORMAL
        chat_box.insert(END, "Disconnected from the chat, your messages will no longer be seen..." + '\n')
        chat_box['state'] = DISABLED
        s.close()
        # TODO change label in here
        # TODO send thread stop event signals here

        connect_button.configure(state=NORMAL)

    @staticmethod
    def acquire_lock():
        global send_lock
        send_lock.acquire()


def on_click(app):
    app.send_message()


def send_msg(sock_send):
    global send
    while True:
        send_lock.acquire()
        send.clear()
        sock_send.send(bytes("<" + socket.gethostname() + ">" + ": " + message, 'UTF-8'))
        send_lock.release()
        App.acquire_lock()


def recv_msg(sock):
    global writeLock
    while True:
        read_sockets, write_sockets, error_sockets = select.select([s], [], [])
        for loop_sock in read_sockets:
            if loop_sock == sock:
                data = loop_sock.recv(4096)
                if not data:
                    sys.exit()
                else:
                    chat_box['state'] = NORMAL
                    msg = str(data)
                    msg = msg.replace('b\'', '')
                    msg = msg.replace('\'', '')
                    chat_box.insert(END, msg + '\n')
                    chat_box['state'] = DISABLED
                    # type_box.delete(0.0, END)
                    chat_box.see(END)

if __name__ == "__main__":
    writeLock = threading.Lock()
    send_lock.acquire()
    root = Tk()
    root.title("ChatClient")
    app = App(root)
    root.bind("<Return>", lambda event: on_click(app))
    root.mainloop()
