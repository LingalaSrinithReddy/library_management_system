import sqlite3
import csv
import json

class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                available INTEGER NOT NULL DEFAULT 1
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (member_id) REFERENCES members(id)
            )
        """)

        self.conn.commit()
    
    def close(self):
        self.conn.close()

    # ---------- Books ----------

    def add_book(self, title, author, isbn):
        """Return the new book id (int)."""
        pass

    def get_book(self, book_id):
        """Return one book as a tuple (id, title, author, isbn, available), or None if not found."""
        pass

    def search_books(self, keyword):
        """Return a list of book tuples whose title or author matches keyword (empty list if none)."""
        pass

    def list_books(self):
        """Return a list of all book tuples (id, title, author, isbn, available)."""
        pass

    def update_book(self, book_id, title, author, isbn):
        """Update a book's details and return None."""
        pass

    def update_availability(self, book_id, status):
        """Set available to status (1 = available, 0 = issued) and return None."""
        pass

    # ---------- Members ----------

    def add_member(self, name, email):
        """Return the new member id (int)."""
        pass

    def get_member(self, member_id):
        """Return one member as a tuple (id, name, email), or None if not found."""
        pass

    def update_member(self, member_id, name, email):
        """Update a member's details and return None."""
        pass

    # ---------- Issues ----------

    def issue_book(self, book_id, member_id, issue_date, due_date):
        """Return the new issue id (int)."""
        pass

    def return_book(self, book_id, return_date):
        """Record the return date on the active issue and return None."""
        pass

    def get_active_issue(self, book_id):
        """Return the unreturned issue tuple (id, book_id, member_id, issue_date, due_date, return_date), or None."""
        pass

    def list_issued_books(self):
        """Return a list of issue tuples for all books currently issued (return_date is NULL)."""
        pass