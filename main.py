from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import exc
from config import auth
import psycopg2

def set_engine(login=auth['login'], password=auth['password'], db_name='project_db'):
    return create_engine('postgresql+psycopg2://{}:{}@localhost/{}'.format(login, password, db_name))

def show_error(error_text: str, window_to_destroy):
    messagebox.showerror("Error", "{}".format(error_text))
    window_to_destroy.destroy()

try:
    engine = set_engine()
    cursor = engine.connect()
except sqlalchemy.exc.OperationalError:
    print("DEBUG:: Database doesn't exists or username/password incorrect")
else:
    print("DEBUG:: SQLalchemy connected to default database")


root = Tk()
root.geometry('400x250')
root.title('Senku app')
root.iconbitmap('Python-icon.ico')


#Database list managment
db_listbox = Listbox()
db_list = list()
for item in list(cursor.execute('select * from databases')):
    db_list.append(list(item)[0])
current_database = 0

for item in db_list:
    db_listbox.insert(END, item)

def create_database():
    def creation():
        if name.get():
            if name.get() in db_list:
                show_error("Such a database already exists", newWindow)
            else:
                try:
                    query = '''select create_db('{}');'''.format(name.get())
                    cursor.execute(query)
                    db_list.append(name.get())
                    db_listbox.insert(END, name.get())
                    newWindow.destroy()
                except psycopg2.errors.SqlclientUnableToEstablishSqlconnection:
                    print("DEBUG:: Error while creating database: сould not establish connection")
                    show_error("Could not establish connection", newWindow)
        else:
            show_error("The input field is empty", newWindow)

    newWindow = Toplevel(root)
    newWindow.title('Create new database')
    newWindow.geometry('250x150')

    name = StringVar()
    title = Label(newWindow, text='Enter database name')
    enter = Entry(newWindow, textvariable=name)
    create = Button(newWindow, text='Create database', width=16, command=creation)

    title.place(anchor=CENTER, x=125, y=25)
    enter.place(anchor=CENTER, x=125, y=50)
    create.place(anchor=CENTER, x=125, y=80)


def select_database():
    #global cursor
    global current_database
    try:
        index = db_listbox.curselection()[0]
        current_database = index
        messagebox.showinfo("Success", "You have successfully switched to '{}' database".format(db_list[index]))
        #print("DEBUG:: Trying to connect to database with name {}".format(db_list[index]))
        #engine = set_engine(db_name=db_list[index])
        #cursor = engine.connect()
    except IndexError:
        messagebox.showerror("Error", "No items selected")
    except sqlalchemy.exc.OperationalError:
        print("DEBUG:: Database {} doesn't exists or username/password incorrect".format(db_list[index]))
    else:
        print("DEBUG:: Switched to database with name - {}".format(db_list[index]))
    

def delete_database():
    try:
        index = db_listbox.curselection()[0]
        if index == 0:
            messagebox.showerror("Error", "Unable to drop 'mother' database")
            return
        query = '''select delete_db('{}');'''.format(db_list[index])
        cursor.execute(query)
        db_listbox.delete(index)
        db_list.remove(db_list[index])
    except IndexError:
        messagebox.showerror("Error", "No items selected")
    except:
        messagebox.showerror("Error", "Delete error")
        print("DEBUG:: Error deleting database with name - {}".format(db_list[index]))
    else:
        messagebox.showinfo("Success", "'{}' database was successfully deleted".format(db_list[index]))


def details():
    def open_table():
        try:
            index = db_listbox.curselection()[0]

        except IndexError:
            messagebox.showerror("Error", "No items selected")

    def clear_table():
        try:
            subindex = data_listbox.curselection()[0]
            if index == 0:
                messagebox.showerror("Error", "Unable to clear 'mother' database")
                return
            query = '''select clear_table('{}', '{}')'''.format(db_list[index], data_list[subindex])
            cursor.execute(query)
        except IndexError:
            messagebox.showerror("Error", "No items selected")
        else:
            messagebox.showinfo("Success", "Table '{}' from database '{}' was cleaned up successfully".format(data_list[subindex], db_list[index]))
            print("DEBUG:: Clear all rows table '{}' in database with name - {}".format(data_list[subindex], db_list[index]))

    
    try:
        index = db_listbox.curselection()[0]
        newWindow = Toplevel(root)
        newWindow.title('{}'.format(db_list[index]))
        newWindow.geometry('400x250')

        # ListBox
        data_listbox = Listbox(newWindow)
        data_list = list()
        for item in cursor.execute("select * from show_tables('{}');".format(db_list[index])):
            data_list.append(item[0])
        for item in data_list:
            data_listbox.insert(END, item)
        #data_listbox.bind('<<ListboxSelect>>', on_change)
    except IndexError:
        messagebox.showerror("Error", "No items selected")
    except:
        show_error("Error while opening database '{}'".format(db_list[index]), newWindow)


    # Buttons
    open_tbl = Button(newWindow, text='Open table')
    clear_tbl = Button(newWindow, text='Crear table', command=clear_table)
    search_in = Button(newWindow, text='Search in')
    alter_tuple = Button(newWindow, text='Alter tuple')

    # Places
    data_listbox.place(anchor=N, x=150, y=25)

    open_tbl.place(anchor=NW, x=250, y=25)
    clear_tbl.place(anchor=NW, x=250, y=55)
    search_in.place(anchor=NW, x=250, y=85)


def clear_all_tables():
    try:
        index = db_listbox.curselection()[0]
        if index == 0:
            messagebox.showerror("Error", "Unable to clear 'mother' database")
            return
        query = '''select clear_all_table('{}')'''.format(db_list[index])
        cursor.execute(query)
    except IndexError:
        messagebox.showerror("Error", "No items selected")
    else:
        messagebox.showinfo("Success", "'{}' database was cleaned up successfully".format(db_list[index]))
        print("DEBUG:: Clear all rows from all tables in database with name - {}".format(db_list[index]))


create_db = Button(text='Create database', command=create_database)
select_db = Button(text='Select database', command=select_database)
delete_db = Button(text='Delete database', command=delete_database)
detail_db = Button(text='Details',         command=details)
clear_db =  Button(text='Clear tables',    command=clear_all_tables)


db_listbox.place(anchor=N, x=150, y=25)
create_db.place(anchor=NW, x=250, y=25)
select_db.place(anchor=NW, x=250, y=55)
delete_db.place(anchor=NW, x=250, y=85)
detail_db.place(anchor=NW, x=250, y=115)
clear_db.place(anchor=NW, x=250, y=145)


root.mainloop()











    #def on_change(event):
    #    widget = event.widget
    #    selection = widget.curselection()
    #    if selection:
    #        text = widget.get(selection[0])
    #       tree.place(anchor=NW, x=50, y=25)
