import sqlite3
import cx_Oracle
import mysql.connector
import webbrowser
import sqlparse
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.metrics import dp
from kivy.uix.codeinput import CodeInput
from pygments.lexers.sql import SqlLexer
from kivy.uix.popup import Popup
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.slider import MDSlider
from kivy.uix.switch import Switch


class SQLAdminApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.database_type = "SQLite"
        
        self.main_layout = MDBoxLayout(orientation="horizontal", spacing=10)

        # **📂 Sidebar - Database & Tables Tree Structure**
        self.sidebar = MDBoxLayout(orientation="vertical", size_hint=(0.3, 1), padding=10)
        self.db_label = MDLabel(text="📂 Databases & Tables", bold=True, halign="center")
        self.tree_view = TreeView()

        self.sidebar.add_widget(self.db_label)
        self.sidebar.add_widget(self.tree_view)

        # Swipe gesture to hide/show sidebar
        self.sidebar.bind(on_touch_move=self.on_swipe)
        
        self.main_layout.add_widget(self.sidebar)

        # **📌 Main Content**
        content_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)

        # **⚙️ Menu Dots**
        self.menu_button = MDIconButton(icon="dots-vertical", pos_hint={"right": 1})
        menu_items = [
            {"text": "🐞 Report Bug", "on_release": lambda x: self.report_bug()},
            {"text": "📤 Send to a Friend", "on_release": lambda x: self.send_to_friend()},
            {"text": "ℹ️ About", "on_release": lambda x: self.show_about()},
            {"text": "⚙️ Settings", "on_release": lambda x: self.show_settings()},
        ]
        self.menu = MDDropdownMenu(caller=self.menu_button, items=menu_items, width_mult=4)
        self.menu_button.bind(on_release=self.open_menu)

        # **Code Box for SQL Queries with Line Numbers**
        self.query_input = CodeInput(lexer=SqlLexer(), hint_text="Write your SQL Query here", size_hint_y=None, height=150)

        # **Buttons**
        button_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        self.run_button = MDRaisedButton(text="Run Query", on_press=self.execute_query)
        self.format_query_button = MDRaisedButton(text="Format Query", on_press=self.format_query)
        self.show_tables_button = MDRaisedButton(text="Show Tables", on_press=self.show_tables)

        button_layout.add_widget(self.run_button)
        button_layout.add_widget(self.format_query_button)
        button_layout.add_widget(self.show_tables_button)
        button_layout.add_widget(self.menu_button)

        # **Label for Messages**
        self.result_label = MDLabel(text="Results will appear here", theme_text_color="Secondary", halign="center", size_hint_y=None, height=30)

        # **Table for Query Results (Like phpMyAdmin)**
        self.scroll_view = MDScrollView()
        self.data_table = MDDataTable(size_hint=(1, 0.7), use_pagination=True, column_data=[("Column", dp(30))], row_data=[("No data",)])
        self.scroll_view.add_widget(self.data_table)

        # **Settings Panel**
        self.settings_panel = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        self.font_size_slider = MDSlider(min=12, max=30, value=16, step=1)
        self.font_size_slider.bind(value=self.adjust_font_size)
        self.theme_switch = Switch(active=False)
        self.theme_switch.bind(active=self.toggle_theme)

        self.settings_panel.add_widget(MDLabel(text="Font Size"))
        self.settings_panel.add_widget(self.font_size_slider)
        self.settings_panel.add_widget(MDLabel(text="Dark Theme"))
        self.settings_panel.add_widget(self.theme_switch)

        # **Add Components to Content Layout**
        content_layout.add_widget(button_layout)
        content_layout.add_widget(self.query_input)
        content_layout.add_widget(self.result_label)
        content_layout.add_widget(self.scroll_view)

        self.main_layout.add_widget(content_layout)

        # ✅ Connect to Database & Load Sidebar
        self.connect_to_database()
        self.load_sidebar()

        return self.main_layout

    def on_swipe(self, instance, touch):
        """Swipe gesture to hide or show the sidebar."""
        if touch.dx > 50:  # swipe right
            self.sidebar.width = 0.3  # Show Sidebar
        elif touch.dx < -50:  # swipe left
            self.sidebar.width = 0  # Hide Sidebar

    def open_menu(self, instance):
        """Open the dropdown menu when the menu button is pressed."""
        self.menu.open()

    def connect_to_database(self):
        """Connect to the selected database."""
        try:
            if self.database_type == "SQLite":
                self.conn = sqlite3.connect("database.db")
                self.cursor = self.conn.cursor()
                self.result_label.text = "✅ Connected to SQLite Database."
            elif self.database_type == "Oracle":
                dsn = cx_Oracle.makedsn("your_oracle_host", 1521, service_name="your_service")
                self.conn = cx_Oracle.connect(user="your_username", password="your_password", dsn=dsn)
                self.cursor = self.conn.cursor()
                self.result_label.text = "✅ Connected to Oracle Database!"
            elif self.database_type == "MySQL":
                self.conn = mysql.connector.connect(
                    host="your_mysql_host",
                    user="your_mysql_user",
                    password="your_mysql_password",
                    database="your_mysql_db"
                )
                self.cursor = self.conn.cursor()
                self.result_label.text = "✅ Connected to MySQL Database!"
        except Exception as e:
            self.result_label.text = f"❌ Database Connection Failed: {e}"

    def load_sidebar(self):
        """Load databases & tables into sidebar tree view."""
        self.tree_view.clear_widgets()
        if self.database_type == "SQLite":
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        elif self.database_type == "MySQL":
            self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()
        for table in tables:
            node = TreeViewLabel(text=table[0])  # TreeViewLabel creates a label node
            self.tree_view.add_node(node)

    def show_tables(self, instance):
        """Load and show tables in the sidebar."""
        self.load_sidebar()

    def execute_query(self, instance):
        """Execute the SQL query entered by the user."""
        query = self.query_input.text.strip()
        if not query:
            self.result_label.text = "⚠️ Please enter an SQL query."
            return

        # ✅ Fix: Convert `SHOW * FROM table_name;` to `SELECT * FROM table_name;`
        if query.lower().startswith("show * from"):
            table_name = query.split("from")[-1].strip(" ;")
            query = f"SELECT * FROM {table_name};"

        try:
            self.cursor.execute(query)
            if query.lower().startswith("select"):
                results = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                # Show columns and their values in the table
                self.data_table.column_data = [(col, dp(30)) for col in columns]
                self.data_table.row_data = results or [("No results",)]
            else:
                self.conn.commit()
            self.result_label.text = "✅ Query executed successfully."
        except Exception as e:
            self.result_label.text = f"❌ Error: {e}"

    def format_query(self, instance):
        """Format the SQL query for readability."""
        self.query_input.text = sqlparse.format(self.query_input.text, reindent=True, keyword_case="upper")

    def report_bug(self):
        """Open GitHub Issues Page."""
        webbrowser.open("https://github.com/YOUR_GITHUB_REPO/issues")

    def send_to_friend(self):
        """Show Share URL."""
        self.show_popup("📤 Share App", "Share this URL with friends:\nhttps://mishraharshit.vercel.app")

    def show_about(self):
        """Show About Section."""
        self.show_popup("ℹ️ About", "👨‍💻 Developed by: Harshit Mishra\n🏢 SecureCoder\n🌍 https://mishraharshit.vercel.app\n📧 mishra9759harshit@gmail.com")

    def show_settings(self):
        """Show Settings Panel."""
        self.show_popup("⚙️ Settings", "Settings: Font Size, Code Box Size, Output Box Size, Database Engine")

    def adjust_font_size(self, instance, value):
        """Adjust font size dynamically."""
        self.query_input.font_size = value
        self.result_label.font_size = value

    def toggle_theme(self, instance, value):
        """Toggle theme between light and dark."""
        if value:
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"

    def show_popup(self, title, message):
        """Show a popup with a message."""
        popup_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_label = MDLabel(text=message, halign="center")
        close_button = MDRaisedButton(text="Close", on_press=lambda x: popup.dismiss())

        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4))
        popup.open()


if __name__ == "__main__":
    SQLAdminApp().run()
