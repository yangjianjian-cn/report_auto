import queue
import threading
import mysql.connector


class ConnectionPool:
    def __init__(self, config, max_connections):
        self.config = config
        self.max_connections = max_connections
        self.connections = set()  # For tracking all active connections
        self.lock = threading.Lock()
        self.connection_queue = queue.Queue(self.max_connections)
        self.init_pool()

    def init_pool(self):
        with self.lock:
            if self.connection_queue.empty():
                for _ in range(self.max_connections):
                    try:
                        conn = mysql.connector.connect(**self.config)
                        self.connection_queue.put(conn)
                    except mysql.connector.Error as e:
                        print(f"Failed to establish connection: {e}")

    def get_connection(self):
        # with self.lock:
        if self.connection_queue.empty():
            self.init_pool()
        conn = self.connection_queue.get()
        self.connections.add(conn)
        return conn

    def release_connection(self, connection):
        with self.lock:
            if connection in self.connections:
                self.connections.remove(connection)
                self.connection_queue.put(connection)
            else:
                raise ValueError('Connection does not belong to this pool')

    def close_all_connections(self):
        with self.lock:
            while not self.connection_queue.empty():
                conn = self.connection_queue.get()
                try:
                    conn.close()
                except mysql.connector.Error as e:
                    print(f"Failed to close connection: {e}")
