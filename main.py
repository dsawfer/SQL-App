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
                show_error("Such a database already exists", create_window)
            else:
                try:
                    query = '''select create_db('{}');'''.format(name.get())
                    cursor.execute(query)
                    db_list.append(name.get())
                    db_listbox.insert(END, name.get())
                    create_window.destroy()
                except psycopg2.errors.SqlclientUnableToEstablishSqlconnection:
                    print("DEBUG:: Error while creating database: сould not establish connection")
                    show_error("Could not establish connection", create_window)
        else:
            show_error("The input field is empty", create_window)

    create_window = Toplevel(root)
    create_window.title('Create new database')
    create_window.geometry('250x150')

    name = StringVar()
    title = Label(create_window, text='Enter database name')
    enter = Entry(create_window, textvariable=name)
    create = Button(create_window, text='Create database', width=16, command=creation)

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
        def refresh_table():
            table.delete(*table.get_children())
            rows.clear()
            for item in cursor.execute("select * from get_{}('{}','')".format(table_list[subindex], db_list[index])):
                rows.append(item)
            for row in rows:
                table.insert('', END, values=tuple(row))


        def search_in_table():
            if search_item.get():
                try:
                    table.delete(*table.get_children())
                    temp_rows = list()
                    for item in cursor.execute("select * from get_{}('{}','{}')".format(table_list[subindex], db_list[index], search_item.get())):
                        temp_rows.append(item)
                    for row in temp_rows:
                        table.insert('', END, values=tuple(row))
                except:
                     show_error("Something goes wrong", table_window)
            else:
                refresh_table()
                

        def delete_rows():
            try:
                if table_list[subindex] == 'finances':
                    messagebox.showerror("Error", "No rights to delete data from this table ({})".format(table_list[subindex]))
                    return
                for item in table.selection():
                    item_text = table.item(item)['values']
                    cursor.execute("select delete_rows('{}','{}','{}')".format(db_list[index], table_list[subindex], item_text[0]))
                    print('DEBUG:: Delete row with condition {}'.format(item_text[0]))
                refresh_table()
            except:
                messagebox.showerror("Error", "Error while deleting rows")

        
        def add_data_to_rows():
            try:
                def add_data_to_db():
                    for item in range(len(text_variables)):
                        if not text_variables[item].get():
                            messagebox.showerror("Error", "The input field is empty - {}".format(headings[item]))
                            return
                    try:
                        query_condition = ','.join("'''{}'''".format(i.get()) for i in text_variables)
                        cursor.execute("select insert_rows('{}','{}',array[{}])".format(db_list[index], table_list[subindex], query_condition))
                        #print("DEBUG:: query is {}".format(query_condition))
                        refresh_table()
                        add_window.destroy()
                    except:
                        messagebox.showerror("Error", "Error while additing rows")
        
                if table_list[subindex] == 'finances':
                    messagebox.showerror("Error", "No rights to add data to this table ({})".format(table_list[subindex]))
                    return

                # Window setup
                add_window = Toplevel(table_window)
                add_window.title('{}'.format(table_list[subindex]))
                add_window.geometry('300x350')

                # Entry
                entry_list = list()
                text_variables = list()
                labels_list = list()
                for item in range(len(headings)):
                    text_variables.append(StringVar())
                    entry_list.append(Entry(add_window, textvariable=text_variables[item]))
                    labels_list.append(Label(add_window, text='{} ({})'.format(headings[item], types[item])))

                # Buttons
                add_current_data = Button(add_window, text='Add data', command=add_data_to_db)

                # Places
                place_under_entry = len(entry_list)
                for item in range(len(entry_list)):
                    labels_list[item].grid(column=0, row=item, pady=5)
                    entry_list[item].grid(column=1, row=item, pady=5)
                add_current_data.grid(column=1, row=place_under_entry, pady=5)

                add_window.columnconfigure(0, weight=1)
                add_window.columnconfigure(1, weight=1)
                #add_window.rowconfigure(0, weight=1)
            except:
                show_error("Error while opening table '{}'".format(table_list[subindex]), add_window)


        def update_data_in_rows():
            try:
                def update_data_in_db():
                    for item in range(1, len(text_variables)):
                        if not text_variables[item].get():
                            messagebox.showerror("Error", "The input field is empty - {}".format(headings[item]))
                            return
                    query_condition = ','.join("'{}'".format(text_variables[i].get()) for i in range(1, len(text_variables)))
                    cursor.execute("select update_rows('{}','{}','{}',array[{}])".format(db_list[index], table_list[subindex], data[0], query_condition))
                    #print("DEBUG:: query is {}".format(query_condition))
                    refresh_table()
                    update_window.destroy()
        
                if table_list[subindex] == 'finances':
                    messagebox.showerror("Error", "No rights to update data in this table ({})".format(table_list[subindex]))
                    return
                
                # Window setup
                update_window = Toplevel(table_window)
                update_window.title('{}'.format(table_list[subindex]))
                update_window.geometry('300x350')

                # Entry
                data =  table.item(table.selection()[0])['values']
                entry_list = list()
                text_variables = list()
                labels_list = list()
                for item in range(len(headings)):
                    text_variables.append(StringVar(update_window, data[item]))
                    entry_list.append(Entry(update_window, textvariable=text_variables[item]))
                    labels_list.append(Label(update_window, text='{} ({})'.format(headings[item], types[item])))

                # Buttons
                add_current_data = Button(update_window, text='Update data', command=update_data_in_db)

                # Places
                place_under_entry = (len(entry_list) - 1)
                for item in range(1, len(entry_list)):
                    labels_list[item].grid(column=0, row=item-1, pady=5)
                    entry_list[item].grid(column=1, row=item-1, pady=5)
                add_current_data.grid(column=1, row=place_under_entry, pady=5)

                update_window.columnconfigure(0, weight=1)
                update_window.columnconfigure(1, weight=1)
                #add_window.rowconfigure(0, weight=1)
            except IndexError:
                messagebox.showerror("Error", "No items selected")
            except:
                show_error("Error while opening table '{}'".format(table_list[subindex]), update_window)


        try:
            # Window setup
            subindex = table_listbox.curselection()[0]
            table_window = Toplevel(details_window)
            table_window.title('{}'.format(table_list[subindex]))
            table_window.geometry('700x600')

            # Headings
            headings = list()
            types = list()
            if table_list[subindex] == 'projects':
                headings = ['project_ID', 'project_category', 'project_name', 'project_dev', 'project_release_date', 'project_cost']
                types = ['integer', 'varchar', 'text', 'varchar', 'date', 'integer']
            else:
                for item in cursor.execute("select * from show_table_data('{}','{}')".format(db_list[index], table_list[subindex])):
                    headings.append(item[0])
                    types.append(item[1])
            
            # Rows
            rows = list()
            for item in cursor.execute("select * from get_{}('{}','')".format(table_list[subindex], db_list[index])):
                rows.append(item)

            # Tree frame
            tree_frame = Frame(table_window)

            # Treeview
            table = ttk.Treeview(master=tree_frame, show="headings", selectmode="extended", height=200)

            # Scroll
            horScroll = ttk.Scrollbar(tree_frame)
            horScroll.configure(command=table.xview, orient=HORIZONTAL)
            
            # Treeview setup
            table.configure(xscrollcommand=horScroll.set)
            table["columns"] = headings
            table["displaycolumns"] = headings
            for head in headings:
                table.heading(head, text=head, anchor=CENTER)
                table.column(head, anchor=CENTER)
            for row in rows:
                table.insert('', END, values=tuple(row))

            # Buttons
            search_button = Button(tree_frame, text='Search', command=search_in_table)
            add_data = Button(tree_frame, text='Add data', command=add_data_to_rows)
            delete_data = Button(tree_frame, text='Delete data', command=delete_rows)
            update_data = Button(tree_frame, text='Update data', command=update_data_in_rows)

            # Entry
            search_item = StringVar()
            search_enter = ttk.Entry(tree_frame, width=40)
            if table_list[subindex] == 'divisions':
                search_item.set('division_name')
            elif table_list[subindex] == 'positions':
                search_item.set('position_name')
            elif table_list[subindex] == 'buildings':
                search_item.set('address')
            elif table_list[subindex] == 'employees':
                search_item.set('employee_nam')
            elif table_list[subindex] == 'clients':
                search_item.set('client_name')
            elif table_list[subindex] == 'categories':
                search_item.set('category_name')
            elif table_list[subindex] == 'projects':
                search_item.set('project_name')
            elif table_list[subindex] == 'sales':
                search_item.set('sale_ID')
            elif table_list[subindex] == 'finances':
                search_item.set('fiscal_year')
            else: 
                 search_item.set('unknown')
            search_enter.config(textvariable=search_item)

            # Places
            tree_frame.grid(column=0, row=0, sticky=N, pady=25)
            table.grid(column=0, row=0, columnspan=3, rowspan=2, sticky=N)
            horScroll.grid(column=0, row=3, columnspan=3, sticky=W + E)
            search_enter.grid(column=1, row=4, sticky=N, pady=12.5, ipadx=0)
            search_button.grid(column=1, row=5, sticky=N, pady=5, ipadx=0)
            add_data.grid(column=1, row=6, sticky=N, pady=5, ipadx=0)
            delete_data.grid(column=1, row=7, sticky=N, pady=5, ipadx=0)
            update_data.grid(column=1, row=8, sticky=N, pady=5, ipadx=0)

            table_window.columnconfigure(0, weight=1)
            table_window.rowconfigure(0, weight=1)
            tree_frame.columnconfigure(0, weight=1)
            tree_frame.columnconfigure(1, weight=1)
            tree_frame.columnconfigure(2, weight=1)
            tree_frame.columnconfigure(3, weight=1)
            tree_frame.columnconfigure(4, weight=1)
            tree_frame.rowconfigure(1, weight=1)
        except IndexError:
            messagebox.showerror("Error", "No items selected")
        except:
            show_error("Error while opening database '{}'".format(db_list[index]), details_window)


    def clear_table():
        try:
            subindex = table_listbox.curselection()[0]
            if table_list[subindex] == 'finances':
                messagebox.showerror("Error", "Auto-filled table, you do not have permission to clear'")
                return
            query = '''select clear_table('{}', '{}')'''.format(db_list[index], table_list[subindex])
            cursor.execute(query)
        except IndexError:
            messagebox.showerror("Error", "No items selected")
        else:
            messagebox.showinfo("Success", "Table '{}' from database '{}' was cleaned up successfully".format(table_list[subindex], db_list[index]))
            print("DEBUG:: Clear all rows table '{}' in database with name - {}".format(table_list[subindex], db_list[index]))

    
    try:
        index = db_listbox.curselection()[0]
        if index == 0:
            messagebox.showerror("Error", "No rights to view the database")
            return
        details_window = Toplevel(root)
        details_window.title('{}'.format(db_list[index]))
        details_window.geometry('400x250')

        # ListBox
        table_listbox = Listbox(details_window)
        table_list = list()
        for item in cursor.execute("select * from show_tables('{}');".format(db_list[index])):
            table_list.append(item[0])
        for item in table_list:
            table_listbox.insert(END, item)
        #table_listbox.bind('<<ListboxSelect>>', on_change)
    except IndexError:
        messagebox.showerror("Error", "No items selected")
    except:
        show_error("Error while opening database '{}'".format(db_list[index]), details_window)


    # Buttons
    open_tbl = Button(details_window, text='Open table', command=open_table)
    clear_tbl = Button(details_window, text='Crear table', command=clear_table)
    #search_in = Button(details_window, text='Search in')
    #alter_tuple = Button(details_window, text='Alter tuple')

    # Places
    table_listbox.place(anchor=N, x=150, y=25)
    open_tbl.place(anchor=NW, x=250, y=25)
    clear_tbl.place(anchor=NW, x=250, y=55)
    #search_in.place(anchor=NW, x=250, y=85)


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
clear_db =  Button(text='Clear database',  command=clear_all_tables)


db_listbox.place(anchor=N, x=150, y=25)
create_db.place(anchor=NW, x=250, y=25)
# select_db.place(anchor=NW, x=250, y=55)
delete_db.place(anchor=NW, x=250, y=55)
detail_db.place(anchor=NW, x=250, y=85)
clear_db.place(anchor=NW, x=250, y=115)


root.mainloop()
