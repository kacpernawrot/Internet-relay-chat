import tkinter.scrolledtext
from tkinter import *
from tkinter import messagebox
import socket
import threading
import time

BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"

FONT = "Helvetica 14"
FONT_BOLD = "Helvetica 13 bold"

class Client:
    def __init__(self, server="192.168.122.1", port=1234):
        self.connected = False
        self.server = server
        self.port = port
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.connection.connect((self.server, self.port))

    def get_response(self):
        response = self.connection.recv(256).decode('utf-8')
        if self.connected and response == "connected":
            return ""
        elif not self.connected and response == "connected":
            self.connected = True
        return response

    def send_cmd(self, cmd, message):
        command = "{} {}".format(cmd, message).encode("utf-8")
        self.connection.send(command)

    def send_message(self, message):
        self.send(message)

    def send(self, message):
        self.connection.send(message.encode('utf-8'))

class ChatApplication:
    def __init__(self):
        self.client = Client()
        self.channels = ['Alpha', 'Beta', 'Delta']
        self.private_channels = []
        self.text_area_list = []
        self.current_channel = ''
        self.start_window()

    #logging_window
    def start_window(self):
        self.loginWindow = Toplevel()
        self.loginWindow.title('IRC-CHAT-LOGGING')
        self.loginWindow.configure()
        screen_width = self.loginWindow.winfo_screenwidth()
        screen_height = self.loginWindow.winfo_screenheight()
        x = (screen_width - 400) / 2
        y = (screen_height - 320) / 2
        self.loginWindow.geometry('%dx%d+%d+%d' % (400, 320, x, y))

        Label(self.loginWindow, text='Internet Relay Chat', font=("Helvetica", 22, "bold")).place(x=80,y=40)

        self.server_ip_input = Entry(self.loginWindow, width=34)
        self.server_ip_input.place(x=110, y=110)
        self.server_ip_input.insert(0, '192.168.122.1')
        Label(self.loginWindow, text='Server IP').place(x=25, y=110)

        self.server_port_input = Entry(self.loginWindow, width=34)
        self.server_port_input.place(x=110, y=150)
        self.server_port_input.insert(0, '1234')
        Label(self.loginWindow, text='Server Port').place(x=25, y=150)

        self.login_btn = PhotoImage(file='login.png')
        self.nickButton = Button(self.loginWindow, image=self.login_btn, command=self.connect_to_server, bd = 0)
        self.nickButton.bind('<Return>', self.connect_to_server)
        self.nickButton.place(x=135, y=190)

        self.nick_input = Entry(self.loginWindow, width=34)
        self.nick_input.place(x=110, y=180)
        self.nick_input.focus_force()
        Label(self.loginWindow, text='Nick').place(x=25, y=180)

    #pop up before closing
    def close_popup(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            #inform server about disconnecting
            self.client.send_cmd("/exit","")
            window.destroy()
            exit()

    def connect_to_server(self, event=None):
        #collect info about user from login window
        nick = self.nick_input.get()
        self.client.server = self.server_ip_input.get()
        self.client.port = int(self.server_port_input.get())
        self.client.connect()
        try:
            self.client.connect()
        except (ConnectionRefusedError):
            messagebox.showinfo(title="Error!", message='Cannot connect to the server', icon='warning')
            return
        except (OSError):
            print('already connected')
            pass
        #server receives username from client
        self.client.send_cmd("/nick", nick)
        time.sleep(1)

        #collect information from the server whether it is working correctly
        response = self.client.get_response()

        if response[0:9] != 'connected':
            messagebox.showinfo(title="Error!", message=response, icon='warning')
            return

        #create IRC window
        self.setup_main_window()
        self.client_thread()
        self.loginWindow.destroy()

    #function that creates chat window
    def setup_main_window(self):
        window.update()
        window.deiconify()
        window.title("IRC CHAT")
        window.resizable(width=True, height=False)
        window.configure(width=500,height=520, bg=BG_COLOR)

        self.head_label = Label(window, bg=BG_COLOR, fg = TEXT_COLOR, text="INTERNET RELAY CHAT", font=FONT_BOLD, pady=10)
        self.head_label.place(relwidth=1)

        self.line = Label(window,width=480,bg=BG_GRAY)
        self.line.place(relwidth=1, rely=0.07, relheight=0.012)

        self.button_alpha = Button(window, text="ALPHA", height=5, width=8, fg=TEXT_COLOR, bg=BG_GRAY, font=FONT_BOLD, command=lambda: self.switch_channel(self.channels[0]))
        self.button_alpha.place(x=0,y=45)

        self.button_beta = Button(window, text="BETA", height=5, width=8, fg=TEXT_COLOR, bg=BG_GRAY, font=FONT_BOLD, command=lambda: self.switch_channel(self.channels[1]))
        self.button_beta.place(x=0, y=148)

        self.button_delta = Button(window, text="DELTA", height=5, width=8, fg=TEXT_COLOR, bg=BG_GRAY, font=FONT_BOLD, command=lambda: self.switch_channel(self.channels[2]))
        self.button_delta.place(x=0, y=251)

        self.button_help = Button(window, text="HELP", height=5, width=8, fg=TEXT_COLOR, bg=BG_GRAY, font=FONT_BOLD, command=lambda: self.print_help())
        self.button_help.place(x=0, y=355)

        self.button_send = Button(window, text="SEND", fg=TEXT_COLOR, bg=BG_GRAY, font=FONT_BOLD, width=4, height=2, pady=0, command=lambda: self.write())
        self.button_send.place(x=400,y=470)

        self.text_area0 = tkinter.scrolledtext.ScrolledText(window, wrap=WORD, height=24, width=46)
        self.text_area0.config(state="disabled")

        self.text_area1 = tkinter.scrolledtext.ScrolledText(window, wrap=WORD, height=24, width=46)
        self.text_area1.config(state="disabled")

        self.text_area2 = tkinter.scrolledtext.ScrolledText(window, wrap=WORD, height=24, width=46)
        self.text_area2.config(state="disabled")

        self.input_area = tkinter.Text(window, height=2, width=45, pady=2)
        self.input_area.place(x=5, y=470)

    #function supporting buttons to change channels
    def switch_channel(self, channel):
        if self.current_channel != channel:
            if channel == 'Alpha':
                self.current_channel = 'Alpha'
                self.text_area1.place_forget()
                self.text_area2.place_forget()
                for i in range(len(self.text_area_list)):
                    self.text_area_list[i].place_forget()
                self.text_area0.place(x=113, y=45)
                self.text_area0.delete('1.0', END)
                self.head_label = Label(window, bg=BG_COLOR, fg=TEXT_COLOR, text=channel, font=FONT_BOLD, pady=10)
                self.head_label.place(relwidth=1)
                self.line = Label(window, width=480, bg=BG_GRAY)
                self.line.place(relwidth=1, rely=0.07, relheight=0.012)
                self.join_channel(channel)
            elif channel == 'Beta':
                self.current_channel = 'Beta'
                self.text_area0.place_forget()
                self.text_area2.place_forget()
                for i in range(len(self.text_area_list)):
                    self.text_area_list[i].place_forget()
                self.text_area1.place(x=113, y=45)
                self.text_area1.delete('1.0', END)
                self.head_label = Label(window, bg=BG_COLOR, fg=TEXT_COLOR, text=channel, font=FONT_BOLD, pady=10)
                self.head_label.place(relwidth=1)
                self.line = Label(window, width=480, bg=BG_GRAY)
                self.line.place(relwidth=1, rely=0.07, relheight=0.012)
                self.join_channel(channel)
            elif channel == 'Delta':
                self.current_channel = 'Delta'
                self.text_area0.place_forget()
                self.text_area1.place_forget()
                for i in range(len(self.text_area_list)):
                    self.text_area_list[i].place_forget()
                self.text_area2.place(x=113, y=45)
                self.text_area2.delete('1.0', END)
                self.head_label = Label(window, bg=BG_COLOR, fg=TEXT_COLOR, text=channel,font=FONT_BOLD, pady=10)
                self.head_label.place(relwidth=1)
                self.line = Label(window, width=480, bg=BG_GRAY)
                self.line.place(relwidth=1, rely=0.07, relheight=0.012)
                self.join_channel(channel)

    def join_channel(self, channel):
        self.client.send_cmd("/c", channel)

    #function that retrieves entered data
    def get_text(self, scrolled_text):
        text = scrolled_text.get("1.0", 'end-1c')
        scrolled_text.delete('1.0', END)
        scrolled_text.focus_force()
        return text

    def create_text_area(self):
        self.text_area = tkinter.scrolledtext.ScrolledText(window, wrap=WORD,height=24, width=46)
        self.text_area.config(state="disabled")
        self.text_area_list.append(self.text_area)

    def print_help(self):
        message = '/h'
        self.client.send_message(message)

    #function that handles writing to server and visually creating private channels
    def write(self):
        message = self.get_text(self.input_area)

        if '/c' in message:
            channel_name = message.split(" ")[1]
            if channel_name not in self.channels:
                if channel_name not in self.private_channels:
                    self.create_text_area()
                    self.private_channels.append(channel_name)
                    self.text_area0.place_forget()
                    self.text_area1.place_forget()
                    self.text_area2.place_forget()
                    for i in range(len(self.private_channels)):
                        if self.private_channels[i] == channel_name:
                            self.text_area_list[i].place(x=113, y=45)
                            self.text_area_list[i].delete('1.0', END)
                            head_label = Label(window, bg=BG_COLOR, fg=TEXT_COLOR, text=channel_name, font=FONT_BOLD, pady=10)
                            head_label.place(relwidth=1)
                            self.line = Label(window, width=480, bg=BG_GRAY)
                            self.line.place(relwidth=1, rely=0.07, relheight=0.012)
                        else:
                            self.text_area_list[i].place_forget()
                    self.current_channel = channel_name
                else:
                    self.text_area0.place_forget()
                    self.text_area1.place_forget()
                    self.text_area2.place_forget()
                    for i in range(len(self.private_channels)):
                        if self.private_channels[i] == channel_name:
                            self.text_area_list[i].place(x=113, y=45)
                            self.text_area_list[i].delete('1.0', END)
                            head_label = Label(window, bg=BG_COLOR, fg=TEXT_COLOR, text=channel_name, font=FONT_BOLD,
                                               pady=10)
                            head_label.place(relwidth=1)
                        else:
                            self.text_area_list[i].place_forget()
                    self.current_channel = channel_name

        self.client.send_message(message)
        self.input_area.delete('1.0', END)

    #function that handles reading from server and displaying it in GUI
    def read(self):
        while True:
            response = self.client.get_response()
            print("Response:", response)
            if self.current_channel == "Alpha":
                self.append_text(self.text_area0,response)
            elif self.current_channel == "Beta":
                self.append_text(self.text_area1, response)
            elif self.current_channel == "Delta":
                self.append_text(self.text_area2, response)
            else:
                for i in range(len(self.private_channels)):
                    if self.current_channel == self.private_channels[i]:
                        self.append_text(self.text_area_list[i], response)

    def append_text(self, frame, text):
        frame.configure(state='normal')
        frame.insert(END, text + '\n')

    def client_thread(self):
        thread = threading.Thread(target=self.read)
        thread.start()

if __name__ == "__main__":
        window = Tk()
        app = ChatApplication()
        window.withdraw()
        window.protocol("WM_DELETE_WINDOW", app.close_popup)
        window.mainloop()




