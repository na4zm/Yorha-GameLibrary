import customtkinter as ctk
import mysql.connector
from mysql.connector import Error
from tkinter import messagebox
import webbrowser
import threading
import re
import os

# Database Configuration (UPDATE THESE WITH YOUR CREDENTIALS)
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'database': 'game_library_db'
}

# ---------------------------------------------------------------------------
# Query Loader – reads queries.sql and builds a dict keyed by [query_name]
# ---------------------------------------------------------------------------
def load_queries(sql_file="queries.sql"):
    """Parse queries.sql and return a dict of {name: sql_string}."""
    queries = {}
    sql_path = os.path.join(os.path.dirname(__file__), sql_file)
    with open(sql_path, "r") as f:
        content = f.read()

    # Split on -- [name] markers
    blocks = re.split(r"--\s*\[(\w+)\]", content)
    # blocks: ['preamble', 'name1', 'sql1', 'name2', 'sql2', ...]
    it = iter(blocks[1:])  # skip leading preamble
    for name, sql in zip(it, it):
        queries[name.strip()] = sql.strip().rstrip(";")
    return queries

Q = load_queries()  # Global query dictionary


def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to connect: {e}")
        return None


class GameLibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YoRHa Game Library")
        self.geometry("1100x800")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.current_user_id = None
        self.current_username = None
        self.current_user_is_dev = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.show_auth_frame()

    # --- AUTHENTICATION (LOGIN & REGISTER) ---
    def show_auth_frame(self, is_login=True):
        if hasattr(self, 'main_container'):
            self.main_container.destroy()
        if hasattr(self, 'auth_frame'):
            self.auth_frame.destroy()

        self.auth_frame = ctk.CTkFrame(self, corner_radius=15)
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_text = "Login to YoRHa" if is_login else "Create Account"
        ctk.CTkLabel(self.auth_frame, text=title_text, font=("Arial", 28, "bold")).pack(pady=(30, 20), padx=40)

        self.username_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Username", width=250, height=40)
        self.username_entry.pack(pady=10, padx=40)

        self.password_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Password", show="*", width=250, height=40)
        self.password_entry.pack(pady=10, padx=40)

        if is_login:
            ctk.CTkButton(self.auth_frame, text="Login", width=250, height=40, command=self.login).pack(pady=(20, 10))
            ctk.CTkButton(self.auth_frame, text="Need an account? Register", fg_color="transparent",
                          command=lambda: self.show_auth_frame(is_login=False)).pack(pady=(0, 20))
        else:
            self.email_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Email", width=250, height=40)
            self.email_entry.pack(pady=10, padx=40)

            self.dev_checkbox = ctk.CTkCheckBox(self.auth_frame, text="Register as Admin / Dev account")
            self.dev_checkbox.pack(pady=10, padx=40)

            ctk.CTkButton(self.auth_frame, text="Register", width=250, height=40, command=self.register).pack(pady=(20, 10))
            ctk.CTkButton(self.auth_frame, text="Back to Login", fg_color="transparent",
                          command=lambda: self.show_auth_frame(is_login=True)).pack(pady=(0, 20))

    def login(self):
        username, password = self.username_entry.get(), self.password_entry.get()

        login_btn = self.auth_frame.winfo_children()[3]
        login_btn.configure(text="Authenticating...", state="disabled")

        def login_db_thread():
            conn = get_db_connection()
            user = None
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(Q["login"], (username, password))
                user = cursor.fetchone()
                conn.close()
            self.after(0, lambda: process_login_result(user))

        def process_login_result(user):
            if user:
                self.current_user_id = user['user_id']
                self.current_username = user['username']
                self.current_user_is_dev = bool(user.get('is_developer', False))
                self.auth_frame.destroy()
                self.build_main_ui()
            else:
                login_btn.configure(text="Login", state="normal")
                messagebox.showerror("Error", "Invalid credentials.")

        threading.Thread(target=login_db_thread, daemon=True).start()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        email = self.email_entry.get().strip()
        is_dev = self.dev_checkbox.get()

        if not username or not password:
            return messagebox.showwarning("Warning", "Username and Password required.")

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(Q["register"], (username, password, email, is_dev))
                conn.commit()
                messagebox.showinfo("Success", "Account created! You can now log in.")
                self.show_auth_frame(is_login=True)
            except Error:
                messagebox.showerror("Error", "Username might already exist.")
            finally:
                conn.close()

    # --- MAIN APPLICATION UI ---
    def build_main_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.main_container, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(self.sidebar, text="YoRHa", font=("Arial", 28, "bold"), text_color="#dce4ee").pack(pady=(30, 30))

        self.nav_btn("Browse Games", lambda: self.load_view("browse"))
        self.nav_btn("My Library", lambda: self.load_view("library"))
        self.nav_btn("Favorites", lambda: self.load_view("favorites"))

        if self.current_user_is_dev:
            self.nav_btn("Add New Game (Admin)", lambda: self.load_view("add_game"))

        self.nav_btn("Profile Settings", lambda: self.load_view("profile"))

        role_tag = "(Admin)" if self.current_user_is_dev else "(User)"
        self.sidebar_user_label = ctk.CTkLabel(self.sidebar, text=f"{self.current_username} {role_tag}", text_color="gray")
        self.sidebar_user_label.pack(side="bottom", pady=(0, 10))

        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#ab3c3c", hover_color="#8a3030",
                      command=self.logout).pack(side="bottom", pady=20, padx=20)

        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.current_view = "browse"
        self.load_view("browse")

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.current_user_is_dev = False
        self.show_auth_frame()

    def nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"), anchor="w", command=command, height=35, font=("Arial", 14))
        btn.pack(fill="x", pady=5, padx=15)

    def load_view(self, view_name):
        self.current_view = view_name
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if view_name == "browse":
            self.render_browse()
        elif view_name == "library":
            self.render_library()
        elif view_name == "favorites":
            self.render_favorites()
        elif view_name == "add_game":
            self.render_add_game()
        elif view_name == "profile":
            self.render_profile()

    # --- UI COMPONENTS ---
    def create_game_card(self, parent, game, view_type="browse"):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#2b2b2b")
        card.pack(fill="x", pady=15, ipady=20)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=30, anchor="center")

        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.pack(anchor="w", fill="x", pady=(0, 5))

        ctk.CTkLabel(title_frame, text=game['title'], font=("Arial", 24, "bold"), text_color="#ffffff").pack(side="left")

        dev_name = game.get('developer_name', 'Unknown')
        ctk.CTkLabel(info_frame, text=f"{game['genre']}  •  {dev_name}", font=("Arial", 16), text_color="#a1a1a1").pack(anchor="w")

        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=30, anchor="center")

        fav_text = "★" if game.get('is_favorite') else "☆"
        fav_color = "#e6b800" if game.get('is_favorite') else "gray"
        ctk.CTkButton(action_frame, text=fav_text, width=40, height=40, fg_color="transparent", text_color=fav_color,
                      font=("Arial", 28), hover_color="#3a3a3a",
                      command=lambda g_id=game['game_id'], fav=game.get('is_favorite'): self.toggle_favorite(g_id, fav)).pack(side="left", padx=(0, 15))

        if game.get('link'):
            ctk.CTkButton(action_frame, text="🌐 Store Page", width=120, height=40, font=("Arial", 14, "bold"),
                          fg_color="#444444", hover_color="#5a5a5a",
                          command=lambda url=game['link']: webbrowser.open(url)).pack(side="left", padx=(0, 15))

        ctk.CTkButton(action_frame, text="💬 Read Reviews", width=130, height=40, font=("Arial", 14, "bold"),
                      fg_color="#5c437a", hover_color="#45325c",
                      command=lambda g=game: self.open_read_reviews_window(g)).pack(side="left", padx=(0, 15))

        if game.get('is_owned'):
            if view_type in ("library", "favorites"):
                ctk.CTkButton(action_frame, text="Write Review", width=120, height=40, font=("Arial", 14, "bold"),
                              fg_color="#3b8ed0", hover_color="#2a6a9b",
                              command=lambda g=game: self.open_review_window(g)).pack(side="right")
            else:
                ctk.CTkLabel(action_frame, text="In Library", font=("Arial", 16, "bold"), text_color="#a1a1a1").pack(side="right", padx=10)
        else:
            ctk.CTkButton(action_frame, text="Add", width=120, height=40, font=("Arial", 14, "bold"),
                          fg_color="#2da346", hover_color="#248238",
                          command=lambda g_id=game['game_id']: self.add_to_library(g_id)).pack(side="right")

        return card

    # --- Read Reviews Window ---
    def open_read_reviews_window(self, game):
        read_win = ctk.CTkToplevel(self)
        read_win.title(f"Reviews - {game['title']}")
        read_win.geometry("550x500")
        read_win.attributes('-topmost', True)

        ctk.CTkLabel(read_win, text=f"Reviews for {game['title']}", font=("Arial", 20, "bold"), text_color="#ffffff").pack(pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(read_win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(Q["get_reviews"], (game['game_id'],))
            reviews = cursor.fetchall()
            conn.close()

            if not reviews:
                ctk.CTkLabel(scroll, text="No reviews yet. Be the first to write one!", font=("Arial", 14), text_color="gray").pack(pady=40)
            else:
                for rev in reviews:
                    rev_frame = ctk.CTkFrame(scroll, fg_color="#3a3a3a", corner_radius=8)
                    rev_frame.pack(fill="x", pady=8, ipady=10, ipadx=15)

                    date_str = rev['review_date'].strftime('%Y-%m-%d') if rev['review_date'] else ''
                    header_text = f"@{rev['username']}  •  {date_str}"
                    ctk.CTkLabel(rev_frame, text=header_text, font=("Arial", 12, "bold"), text_color="#a1a1a1", anchor="w").pack(fill="x")
                    ctk.CTkLabel(rev_frame, text=rev['review_text'], font=("Arial", 14), text_color="#ffffff", justify="left", wraplength=450, anchor="w").pack(fill="x", pady=(8, 0))

    # --- Write Review Popup Window ---
    def open_review_window(self, game):
        review_win = ctk.CTkToplevel(self)
        review_win.title(f"Review - {game['title']}")
        review_win.geometry("500x400")
        review_win.attributes('-topmost', True)
        review_win.grab_set()

        ctk.CTkLabel(review_win, text=f"Write a review for {game['title']}", font=("Arial", 20, "bold"), text_color="#ffffff").pack(pady=(20, 10))

        textbox = ctk.CTkTextbox(review_win, width=400, height=200, font=("Arial", 14))
        textbox.pack(pady=10)

        def submit_review():
            review_content = textbox.get("1.0", "end-1c").strip()
            if not review_content:
                messagebox.showwarning("Warning", "Review cannot be empty.", parent=review_win)
                return

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(Q["insert_review"], (self.current_user_id, game['game_id'], review_content))
                    conn.commit()
                    messagebox.showinfo("Success", "Review saved successfully!", parent=review_win)
                    review_win.destroy()
                except Error as e:
                    messagebox.showerror("Database Error", f"Could not save review: {e}", parent=review_win)
                finally:
                    conn.close()

        ctk.CTkButton(review_win, text="Submit Review", width=200, height=40, font=("Arial", 14, "bold"),
                      fg_color="#3b8ed0", hover_color="#2a6a9b", command=submit_review).pack(pady=15)

    # --- VIEWS & DATABASE LOGIC ---
    def fetch_and_display_games(self, title, query_key, parent_frame, view_type="browse"):
        header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text=title, font=("Arial", 30, "bold"), text_color="#ffffff").pack(side="left")

        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(side="right")

        ctk.CTkLabel(search_frame, text="Search:", font=("Arial", 16, "bold"), text_color="#a1a1a1").pack(side="left", padx=(0, 10))

        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Title or Genre...", width=250, height=35, textvariable=search_var)
        search_entry.pack(side="left")

        scroll_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        loading_label = ctk.CTkLabel(scroll_frame, text="Fetching data from server...", font=("Arial", 16, "italic"), text_color="gray")
        loading_label.pack(pady=40)

        def fetch_data_thread():
            conn = get_db_connection()
            games_data = []
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(Q[query_key], (self.current_user_id, self.current_user_id))
                games_data = cursor.fetchall()
                conn.close()
            self.after(0, lambda: render_ui_with_data(games_data))

        def render_ui_with_data(games_data):
            loading_label.destroy()

            self.all_card_widgets = []
            for game in games_data:
                card_widget = self.create_game_card(scroll_frame, game, view_type)
                self.all_card_widgets.append({'data': game, 'widget': card_widget})

            no_results_label = ctk.CTkLabel(scroll_frame, text="No matching games found.", font=("Arial", 16), text_color="gray")

            def process_search():
                search_query = search_var.get().lower()
                visible_count = 0
                for item in self.all_card_widgets:
                    game = item['data']
                    card = item['widget']
                    if search_query in game['title'].lower() or search_query in game['genre'].lower():
                        card.pack(fill="x", pady=15, ipady=20)
                        visible_count += 1
                    else:
                        card.pack_forget()

                if visible_count == 0 and games_data:
                    no_results_label.pack(pady=40)
                else:
                    no_results_label.pack_forget()

            self.search_timer = None

            def delayed_search(event=None):
                if self.search_timer:
                    self.after_cancel(self.search_timer)
                self.search_timer = self.after(250, process_search)

            search_entry.bind("<KeyRelease>", delayed_search)

            if not games_data:
                ctk.CTkLabel(scroll_frame, text="Nothing to see here yet!", font=("Arial", 16)).pack(pady=40)
            else:
                process_search()

        threading.Thread(target=fetch_data_thread, daemon=True).start()

    def render_browse(self):
        self.fetch_and_display_games("Browse Games", "browse_games", self.content_frame, "browse")

    def render_library(self):
        self.fetch_and_display_games("My Collection", "library_games", self.content_frame, "library")

    def render_favorites(self):
        self.fetch_and_display_games("My Favorites", "favorite_games", self.content_frame, "favorites")

    def toggle_favorite(self, game_id, is_currently_favorited):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                if is_currently_favorited:
                    cursor.execute(Q["remove_from_favorites"], (self.current_user_id, game_id))
                else:
                    cursor.execute(Q["add_to_favorites"], (self.current_user_id, game_id))
                conn.commit()
                self.load_view(self.current_view)
            except Error:
                messagebox.showerror("Error", "Could not update favorites.")
            finally:
                conn.close()

    def add_to_library(self, game_id):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(Q["add_to_library"], (self.current_user_id, game_id))
                conn.commit()
                messagebox.showinfo("Success", "Game added to your library!")
                self.load_view(self.current_view)
            except Error:
                messagebox.showerror("Error", "Could not add game to library.")
            finally:
                conn.close()

    def render_add_game(self):
        ctk.CTkLabel(self.content_frame, text="Add Game to Database", font=("Arial", 30, "bold"), text_color="#ffffff").pack(anchor="w", pady=(0, 20))

        form = ctk.CTkFrame(self.content_frame, corner_radius=10, fg_color="#2b2b2b")
        form.pack(fill="x", pady=10, ipady=30)

        title_entry = ctk.CTkEntry(form, placeholder_text="Game Title", width=350, height=40)
        title_entry.pack(pady=10)

        genre_entry = ctk.CTkEntry(form, placeholder_text="Genre", width=350, height=40)
        genre_entry.pack(pady=10)

        dev_entry = ctk.CTkEntry(form, placeholder_text="Developer / Studio Name", width=350, height=40)
        dev_entry.pack(pady=10)

        link_entry = ctk.CTkEntry(form, placeholder_text="Store URL (Steam/Epic) - Optional", width=350, height=40)
        link_entry.pack(pady=10)

        def submit_game():
            t = title_entry.get().strip()
            g = genre_entry.get().strip()
            d_name = dev_entry.get().strip()
            link_url = link_entry.get().strip()

            if not t or not d_name:
                return messagebox.showwarning("Incomplete", "Please fill Title and Developer.")

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(Q["get_developer_by_name"], (d_name,))
                    dev_result = cursor.fetchone()

                    if dev_result:
                        d_id = dev_result[0]
                    else:
                        cursor.execute(Q["insert_developer"], (d_name,))
                        d_id = cursor.lastrowid

                    cursor.execute(Q["insert_game"], (t, g, 0.00, d_id, link_url if link_url else None))
                    conn.commit()
                    messagebox.showinfo("Success", f"{t} successfully added!")
                    self.load_view("browse")
                except Error as e:
                    messagebox.showerror("Database Error", f"Could not add game: {e}")
                finally:
                    conn.close()

        ctk.CTkButton(form, text="Publish Entry", width=350, height=45, font=("Arial", 16, "bold"), command=submit_game).pack(pady=20)

    def render_profile(self):
        ctk.CTkLabel(self.content_frame, text="Profile Settings", font=("Arial", 30, "bold"), text_color="#ffffff").pack(anchor="w", pady=(0, 20))

        form = ctk.CTkFrame(self.content_frame, corner_radius=10, fg_color="#2b2b2b")
        form.pack(fill="x", pady=10, ipady=30)

        conn = get_db_connection()
        current_email = ""
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(Q["get_user_email"], (self.current_user_id,))
            user = cursor.fetchone()
            if user and user['email']:
                current_email = user['email']
            conn.close()

        ctk.CTkLabel(form, text="Update Account Information", font=("Arial", 18), text_color="#a1a1a1").pack(pady=(10, 20))

        user_entry = ctk.CTkEntry(form, placeholder_text="Username", width=350, height=40)
        user_entry.insert(0, self.current_username)
        user_entry.pack(pady=10)

        email_entry = ctk.CTkEntry(form, placeholder_text="Email Address", width=350, height=40)
        email_entry.insert(0, current_email)
        email_entry.pack(pady=10)

        pass_entry = ctk.CTkEntry(form, placeholder_text="New Password (leave blank to keep current)", show="*", width=350, height=40)
        pass_entry.pack(pady=10)

        def save_profile():
            new_user = user_entry.get().strip()
            new_email = email_entry.get().strip()
            new_pass = pass_entry.get().strip()

            if not new_user or not new_email:
                return messagebox.showwarning("Warning", "Username and Email cannot be empty.")

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    if new_pass:
                        cursor.execute(Q["update_user_with_password"], (new_user, new_email, new_pass, self.current_user_id))
                    else:
                        cursor.execute(Q["update_user_without_password"], (new_user, new_email, self.current_user_id))
                    conn.commit()
                    self.current_username = new_user

                    role_tag = "(Admin)" if self.current_user_is_dev else "(User)"
                    self.sidebar_user_label.configure(text=f"{self.current_username} {role_tag}")

                    messagebox.showinfo("Success", "Profile updated successfully!")
                except Error:
                    messagebox.showerror("Error", "Could not update. Username or Email might already exist.")
                finally:
                    conn.close()

        ctk.CTkButton(form, text="Save Changes", width=350, height=45, font=("Arial", 16, "bold"), fg_color="#3b8ed0", command=save_profile).pack(pady=30)


if __name__ == "__main__":
    app = GameLibraryApp()
    app.mainloop()
