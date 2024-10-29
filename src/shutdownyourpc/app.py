import asyncio
import json
import os
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import paramiko

class ShutdownyourPC(toga.App):
    def startup(self):
        self.credentials_file = os.path.join(self.paths.cache, 'credentials.json')

        self.pc_list = self.load_pcs()  # Load the list of PCs
        self.password_visible = False  # Track password visibility

        # Main window setup
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.loader_label = toga.Label("Loading...", style=Pack(padding=10, color='white'))
        self.loader_label.visible = False  # Hide loader initially

        # List to display saved PCs
        self.pc_list_box = toga.Box(style=Pack(direction=COLUMN, padding=10, background_color='#343641'))
        self.update_pc_list()

        # Button to add a new PC
        self.add_button = toga.Button(
            'Add', on_press=self.add_pc, style=Pack(padding=5, background_color='green', color='white')
        )

        # Main layout
        self.main_box = toga.Box(
            children=[
                toga.Box(style=Pack(direction=ROW, alignment="center", padding=10, background_color='#343641'), children=[
                    toga.Label('Saved PCs:', style=Pack(flex=1, background_color='#343641', color="white")),
                    self.add_button  # "Add" button
                ]),
                self.pc_list_box  # List of saved PCs
            ],
            style=Pack(direction=COLUMN, padding=20, background_color='#343641')
        )

        self.pc_form_box = None  # Keep track of the input form
        self.current_pc = None  # Track the currently edited PC
        # Wrap the main_box in a ScrollContainer to allow scrolling
        self.scroll_container = toga.ScrollContainer(content=self.main_box)
        self.scroll_container.style.background_color = '#343641'  # Set the scroll container's background color

        # Set the main window's content
        menu_command_update = toga.Command(
            self.command_update, text="View update notes", shortcut=None
        )
        menu_command_important = toga.Command(
            self.command_important, text="IMPORTANT", shortcut=None
        )

        self.commands.add(menu_command_update, menu_command_important)
    
        self.main_window.content = self.scroll_container
        self.main_window.show()

        self.loading_box = None

        if not os.path.exists(self.credentials_file) or os.path.getsize(self.credentials_file) < 3:
            self.main_window.info_dialog(
                'Warning',
                'Please configure the SSH on your PC before using this application and connect to the same internet connection as your PC.'
            )

    def command_update(self, widget):
        self.main_window.info_dialog(
                'Notes',
                'No updates yet!'
            ) 
    def command_important(self, widget):
        self.main_window.info_dialog(
                'IMPORTANT!!!',
                '* Please ensure SSH is configured on the remote PC.\n\n'
                '* Have the same internet connection as your PC.\n\n'
                '* Do not delete the cache for this app because it contains the data abour your PCs'
            ) 

    def update_pc_list(self):
        """Updates the list of PCs displayed on the main page."""
        self.pc_list_box.children.clear()

        if not self.pc_list:
            self.pc_list_box.add(toga.Label('No PCs added.', style=Pack(padding=10, background_color='#343641', color='white')))
        else:
            for pc in self.pc_list:
                pc_row = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#343641'))

                pc_button = toga.Button(
                    pc['name'], on_press=lambda widget, pc=pc: self.edit_pc(pc),
                    style=Pack(padding=5, background_color='#2B4570', color='white', flex=1)
                )
                
                delete_button = toga.Button(
                    'Delete', on_press=lambda widget, pc=pc: self.delete_pc(pc),
                    style=Pack(padding=5, background_color='red', color='white')
                )

                # Add the PC name button and delete button to the row
                pc_row.add(pc_button)
                pc_row.add(delete_button)
                
                # Add the row to the pc_list_box
                self.pc_list_box.add(pc_row)

    def add_pc(self, widget):
        """Shows input fields to add a new PC with cleared values."""
        self.current_pc = None  # Reset the current PC to None for adding a new one
        # Show the form with empty fields for adding a new PC
        self.show_pc_form(pc={'name': '', 'host_ip': '', 'port': '22', 'username': '', 'password': ''}, password_visible=False)

    def edit_pc(self, pc):
        """Shows input fields to edit an existing PC."""
        self.current_pc = pc  # Set the current PC to the one being edited
        self.show_pc_form(pc)

    def show_pc_form(self, pc=None, password_visible=False):
        """Shows the form to add or edit a PC, while preserving the current input values."""
        
        if self.pc_form_box and pc:
            # If the form is already present, keep the input values
            pc['name'] = self.name_input.value
            pc['host_ip'] = self.host_ip_input.value
            pc['port'] = self.port_input.value
            pc['username'] = self.username_input.value
            pc['password'] = self.password_input.value

        # Clear any existing form
        if self.pc_form_box:
            self.main_box.remove(self.pc_form_box)

        self.pc_form_box = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=10, background_color='#343641', color="white"))

        # Input Fields (pre-filled with values if editing a PC, otherwise with the current values)
        self.name_input = toga.TextInput(placeholder='Enter PC Name', value=pc['name'] if pc else '', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))
        self.host_ip_input = toga.TextInput(placeholder='Enter Host IP', value=pc['host_ip'] if pc else '', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))
        self.port_input = toga.TextInput(placeholder='Enter Port', value=pc['port'] if pc else '22', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))
        self.username_input = toga.TextInput(placeholder='Enter Username', value=pc['username'] if pc else '', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))

        # Toggle between TextInput and PasswordInput for password visibility
        if password_visible:
            self.password_input = toga.TextInput(placeholder='Enter Password', value=pc['password'] if pc else '', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))
            self.show_password_button = toga.Button(
                'Hide password', on_press=lambda widget: self.show_pc_form(pc, password_visible=False),
                style=Pack(padding=5)
            )
        else:
            self.password_input = toga.PasswordInput(placeholder='Enter Password', value=pc['password'] if pc else '', style=Pack(padding=(0, 5),background_color='#424A4C', color='white'))
            self.show_password_button = toga.Button(
                'Show password', on_press=lambda widget: self.show_pc_form(pc, password_visible=True),
                style=Pack(padding=5)
            )

        # Save, Cancel, and Shutdown Buttons
        self.save_button = toga.Button(
            'Save', on_press=lambda widget: self.save_pc(pc),
            style=Pack(padding=10, background_color='green', color='white')
        )

        self.cancel_button = toga.Button(
            'Cancel', on_press=self.cancel_pc_form,
            style=Pack(padding=10, background_color='gray', color='white')
        )

        self.shutdown_button = toga.Button(
            'Shutdown PC', on_press=lambda widget: self.shutdown_pc(pc),
            style=Pack(padding=10, background_color='red', color='white')
        ) if pc and self.current_pc else None

        self.sleep_button = toga.Button(
            'Sleep PC', on_press=lambda widget: self.sleep_pc(pc),
            style=Pack(padding=10, background_color='#252526', color='white')
        ) if pc and self.current_pc else None

        # Add all components to the form box
        self.pc_form_box.add(toga.Label('PC Name:', style=Pack(padding=(0, 5),background_color='#343641', color='gray')))
        self.pc_form_box.add(self.name_input)
        self.pc_form_box.add(toga.Label('Host IP:', style=Pack(padding=(0, 5),background_color='#343641', color='gray')))
        self.pc_form_box.add(self.host_ip_input)
        self.pc_form_box.add(toga.Label('Port:', style=Pack(padding=(0, 5),background_color='#343641', color='gray')))
        self.pc_form_box.add(self.port_input)
        self.pc_form_box.add(toga.Label('Username:', style=Pack(padding=(0, 5),background_color='#343641', color='gray')))
        self.pc_form_box.add(self.username_input)
        self.pc_form_box.add(toga.Label('Password:', style=Pack(padding=(0, 5),background_color='#343641', color='gray')))
        self.pc_form_box.add(self.password_input)
        self.pc_form_box.add(self.show_password_button)
        self.pc_form_box.add(self.save_button)

        if self.sleep_button:
            self.pc_form_box.add(self.sleep_button)

        if self.shutdown_button:
            self.pc_form_box.add(self.shutdown_button)

        self.pc_form_box.add(self.cancel_button)

        # Update the main layout
        self.main_box.add(self.pc_form_box)
        # self.main_window.content = self.main_box



    def toggle_password_visibility(self, widget):
        """Toggles the visibility of the password input."""
        self.password_visible = not self.password_visible  # Toggle the visibility state
        self.show_pc_form(self.current_pc)  # Reload the form with current PC data

    def cancel_pc_form(self, widget):
        """Hides the PC input form and resets it."""
        if self.pc_form_box:
            self.main_box.remove(self.pc_form_box)  # Remove the form
            self.pc_form_box = None  # Clear the form box
            self.selected_pc = None  # Reset the selected PC


    def save_pc(self, old_pc=None):
        """Saves a new PC or updates an existing one, then hides the form."""
        name = self.name_input.value
        host_ip = self.host_ip_input.value
        port = self.port_input.value
        username = self.username_input.value
        password = self.password_input.value

        # Ensure that all fields have values
        if not (name and host_ip and port and username and password):
            self.main_window.error_dialog('Error', 'All fields must be filled.')
            return

        new_pc = {
            'name': name,
            'host_ip': host_ip,
            'port': port,
            'username': username,
            'password': password
        }

        if old_pc and old_pc in self.pc_list:
            # Update existing PC
            index = self.pc_list.index(old_pc)
            self.pc_list[index] = new_pc
        else:
            # Add new PC
            self.pc_list.append(new_pc)

        self.save_pcs()
        self.update_pc_list()
        self.cancel_pc_form(None)  # Hide the form after saving

    async def show_loader(self, message="Connecting..."):
        """Displays a full-screen loading label."""
        if self.loading_box is not None:
            return  # Avoid creating multiple loading boxes

        # Loading box with center-aligned text
        self.loading_box = toga.Box(
            style=Pack(direction=COLUMN, alignment="center", background_color='#343641')
        )
        loading_label = toga.Label(
            message,
            style=Pack(padding=(50, 0), color='yellow', text_align="center", font_size=16, background_color='#343641')
        )
        self.loading_box.add(loading_label)

        # Adjust the main window content to only show the loading box
        self.main_window.content = self.loading_box

        await asyncio.sleep(0)  # Allow UI to update

    async def hide_loader(self):
        """Restores the main UI after the loading screen."""
        if self.loading_box is not None:
            # Clear the loading box
            self.loading_box = None  
            # Restore the main window's original content
            self.main_window.content = self.scroll_container
        await asyncio.sleep(0)  # Allow UI to update

    async def perform_ssh_task(self, pc, command, desc):
        await self.show_loader("Executing SSH command...")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(pc['host_ip'], username=pc['username'], password=pc['password'], port=int(pc['port']))

            # Execute the SSH command
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                self.main_window.info_dialog('Error', f"Failed: {error}")
            else:
                if desc == "shutdown":
                    self.main_window.info_dialog('Success', 'PC shutdown successfully!')
                elif desc == "sleep":
                    self.main_window.info_dialog('Success', 'PC went to sleep successfully!')
                else:
                    self.main_window.info_dialog('Success', 'Command executed successfully!')
        except Exception as e:
            self.main_window.info_dialog('Error', f"Failed to connect: {str(e)}")
        finally:
            await self.hide_loader()  # Hide the loading screen after completion
            client.close()

    def shutdown_pc(self, pc):
        asyncio.ensure_future(self.perform_ssh_task(pc, 'shutdown /s /f /t 0', 'shutdown'))
       
    def sleep_pc(self, pc):
        """Initiates the SSH sleep command in the background."""
        asyncio.ensure_future(self.perform_ssh_task(pc, 'shutdown /h', 'sleep')) 

    def delete_pc(self, pc):
        """Delete the selected PC from the list and update the JSON file."""
        if pc in self.pc_list:
            self.pc_list.remove(pc)  # Remove the PC from the list
            self.save_pcs()  # Update the JSON file
            self.update_pc_list()  # Refresh the displayed list
            self.main_box.remove(self.pc_list_box)  # Remove the current list box
            self.pc_list_box = toga.Box(style=Pack(direction=COLUMN, padding=10, background_color='#343641'))  # Recreate it
            self.update_pc_list()  # Populate it again
            self.main_box.add(self.pc_list_box)  # Add the updated list box back

            # Update the main layout
            self.scroll_container = toga.ScrollContainer(content=self.main_box)
            self.scroll_container.style.background_color = '#343641'  # Set the scroll container's background color

            # Set the main window's content
            self.main_window.content = self.scroll_container


    def save_pcs(self):
        """Save the list of PCs to a JSON file."""
        with open(self.credentials_file, 'w') as f:
            json.dump(self.pc_list, f)

    def load_pcs(self):
        """Load the list of PCs from the JSON file."""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        return []

def main():
    return ShutdownyourPC()
