import json
import os
import uuid

TODO_FILE = "todos.json"

def get_todos():
    """Devuelve la lista actual de tareas pendientes."""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_todos(todos):
    """Guarda la lista de tareas en el archivo JSON."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def add_todo(text):
    """Añade una nueva tarea a la lista."""
    todos = get_todos()
    text_clean = text.replace('*', '').replace('_', ' ').replace('[', '').replace(']', '')
    todo = {
        "id": str(uuid.uuid4())[:8],
        "text": text_clean,
        "completed": False
    }
    todos.append(todo)
    save_todos(todos)
    return todo

def toggle_todo(todo_id):
    """Cambia el estado de una tarea (completada/no completada)."""
    todos = get_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["completed"] = not t["completed"]
            break
    save_todos(todos)

def clear_completed():
    """Elimina todas las tareas que ya están completadas."""
    todos = get_todos()
    todos = [t for t in todos if not t["completed"]]
    save_todos(todos)
