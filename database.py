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
        """Return the new book id (int). Raises ValueError if the ISBN already exists."""
        try:
            cur = self.conn.execute(
                "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
                (title, author, isbn),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError("A book with this ISBN already exists")

    def get_book(self, book_id):
        """Return one book as a tuple (id, title, author, isbn, available), or None if not found."""
        cur = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        return cur.fetchone()

    def search_books(self, keyword):
        """Return a list of book tuples whose title, author or ISBN contains keyword (empty list if none)."""
        pattern = f"%{keyword}%"
        cur = self.conn.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?",
            (pattern, pattern, pattern),
        )
        return cur.fetchall()

    def list_books(self):
        """Return a list of all book tuples (id, title, author, isbn, available)."""
        cur = self.conn.execute("SELECT * FROM books")
        return cur.fetchall()

    def update_book(self, book_id, title, author, isbn):
        """Update a book's details and return None. Raises ValueError if not found or ISBN is a duplicate."""
        try:
            cur = self.conn.execute(
                "UPDATE books SET title = ?, author = ?, isbn = ? WHERE id = ?",
                (title, author, isbn, book_id),
            )
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError("A book with this ISBN already exists")
        if cur.rowcount == 0:
            raise ValueError("Book not found")
        self.conn.commit()

    def update_availability(self, book_id, status):
        """Set available to status (1 = available, 0 = issued) and return None. Raises ValueError if invalid or not found."""
        if status not in (0, 1):
            raise ValueError("Status must be 0 or 1")
        cur = self.conn.execute(
            "UPDATE books SET available = ? WHERE id = ?",
            (status, book_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Book not found")
        self.conn.commit()

    # ---------- Members ----------

    def add_member(self, name, email):
        """Return the new member id (int)."""
        cur = self.conn.execute(
            "INSERT INTO members (name, email) VALUES (?, ?)",
            (name, email),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_member(self, member_id):
        """Return one member as a tuple (id, name, email), or None if not found."""
        cur = self.conn.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        return cur.fetchone()

    def update_member(self, member_id, name, email):
        """Update a member's details and return None. Raises ValueError if not found."""
        cur = self.conn.execute(
            "UPDATE members SET name = ?, email = ? WHERE id = ?",
            (name, email, member_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Member not found")
        self.conn.commit()

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