// Keep all API paths in one place so they are easy to change if your FastAPI
// route names differ slightly.
const ENDPOINTS = {
    signup: `/auth/sign_up`,
    login: `/auth/log_in`,
    logout: `/auth/log_out`,
    deleteAccount: `/auth/delete_account`,
    todosAll: `/todos/all`,
    todoAdd: `/todos/add`,
    todoToggle: `/todos/toggle`,
    todoDelete: `/todos/delete`,
};

const TOKEN_COOKIE = "access_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

let authMode = "login";

const authView = document.getElementById("auth-view");
const todoView = document.getElementById("todo-view");
const authForm = document.getElementById("auth-form");
const authSubmit = document.getElementById("auth-submit");
const loginTab = document.getElementById("login-tab");
const signupTab = document.getElementById("signup-tab");
const authStatus = document.getElementById("auth-status");
const logoutButton = document.getElementById("logout-button");
const accountLabel = document.getElementById("account-label");
const todoForm = document.getElementById("todo-form");
const todoText = document.getElementById("todo-text");
const todosElement = document.getElementById("todos");
const todoStatus = document.getElementById("todo-status");
const refreshButton = document.getElementById("refresh-button");
const deleteAccountButton = document.getElementById("delete-account-button");

function getCookie(name) {
    const prefix = `${encodeURIComponent(name)}=`;
    const match = document.cookie.split("; ").find((part) => part.startsWith(prefix));
    return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

function setToken(token) {
    document.cookie = [
        `${encodeURIComponent(TOKEN_COOKIE)}=${encodeURIComponent(token)}`,
        `Max-Age=${COOKIE_MAX_AGE}`,
        "Path=/",
        "SameSite=Lax",
    ].join("; ");
}

function clearToken() {
    document.cookie = `${encodeURIComponent(TOKEN_COOKIE)}=; Max-Age=0; Path=/; SameSite=Lax`;
}

function setStatus(element, message, type = "") {
    element.textContent = message;
    element.className = `status ${type}`.trim();
}

async function parseResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const detail = typeof data === "object" && data !== null
            ? data.detail ?? data.message
            : data;
        const error = new Error(detail || `Request failed with HTTP ${response.status}`);
        error.status = response.status;
        error.emptyTodos = response.status === 404 && detail === "You don't have any todos.";
        throw error;
    }

    return data;
}

/*
 * The backend contract here sends access_token in the request body.
 * This helper is the only place that knows about that detail.
 *
 * If your FastAPI endpoints instead expect a query parameter or an
 * Authorization header, change this helper rather than every API call.
 */
async function apiRequest(url, { method = "GET", body = {}, protectedRoute = false } = {}) {
    const payload = { ...body };
    const options = {
        method,
        headers: {
            "Content-Type": "application/json",
        },
    };

    if (protectedRoute) {
        const token = getCookie(TOKEN_COOKIE);
        if (!token) {
            throw new Error("You are not signed in.");
        }
        payload.access_token = token;
    }

    if (method === "GET") {
        // Browsers do not allow fetch() to send a body with GET.
        // The backend therefore needs to accept access_token as a query parameter
        // for GET endpoints such as /todos/all.
        const query = new URLSearchParams();
        for (const [key, value] of Object.entries(payload)) {
            query.set(key, String(value));
        }

        const separator = url.includes("?") ? "&" : "?";
        const requestUrl = query.toString() ? `${url}${separator}${query}` : url;
        const response = await fetch(requestUrl, options);

        if (response.status === 401 || response.status === 403 || response.status === 406) {
            clearToken();
            showSignedOut();
        }

        return parseResponse(response);
    }

    options.body = JSON.stringify(payload);
    const response = await fetch(url, options);

    if (response.status === 401 || response.status === 403 || response.status === 406) {
        clearToken();
        showSignedOut();
    }

    return parseResponse(response);
}

function showSignedOut() {
    authView.classList.remove("hidden");
    todoView.classList.add("hidden");
    logoutButton.classList.add("hidden");
    accountLabel.textContent = "Not signed in";
    todosElement.replaceChildren();
}

function showSignedIn(username) {
    authView.classList.add("hidden");
    todoView.classList.remove("hidden");
    logoutButton.classList.remove("hidden");
    accountLabel.textContent = username ? `Signed in as ${username}` : "Signed in";
}

function setAuthMode(mode) {
    authMode = mode;
    const signup = mode === "signup";

    loginTab.classList.toggle("active", !signup);
    signupTab.classList.toggle("active", signup);
    authSubmit.textContent = signup ? "Create account" : "Login";
    document.getElementById("password").autocomplete = signup ? "new-password" : "current-password";
    setStatus(authStatus, "");
}

function makeTodoElement(todo) {
    const item = document.createElement("article");
    item.className = "todo-item";
    item.classList.toggle("done", Boolean(todo.is_done));
    item.dataset.id = String(todo.id);

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "todo-check";
    checkbox.checked = Boolean(todo.is_done);
    checkbox.setAttribute("aria-label", `Mark "${todo.todo}" as ${todo.is_done ? "not done" : "done"}`);
    checkbox.addEventListener("change", async () => {
        checkbox.disabled = true;
        try {
            const updated = await apiRequest(ENDPOINTS.todoToggle, {
                method: "PATCH",
                body: { todo_id: todo.id },
                protectedRoute: true,
            });

            // If the endpoint returns the updated todo, use it. Otherwise the
            // UI can safely flip the current state locally.
            const newDone = typeof updated?.is_done === "boolean"
                ? updated.is_done
                : !todo.is_done;
            todo.is_done = newDone;
            checkbox.checked = newDone;
            item.classList.toggle("done", newDone);
        } catch (error) {
            checkbox.checked = Boolean(todo.is_done);
            setStatus(todoStatus, error.message, "error");
        } finally {
            checkbox.disabled = false;
        }
    });

    const content = document.createElement("div");
    content.className = "todo-content";

    const text = document.createElement("p");
    text.className = "todo-text";
    text.textContent = todo.todo;

    content.append(text);

    if (todo.creation_date) {
        const date = document.createElement("p");
        date.className = "todo-date";
        const parsed = new Date(todo.creation_date);
        date.textContent = Number.isNaN(parsed.getTime())
            ? String(todo.creation_date)
            : parsed.toLocaleString();
        content.append(date);
    }

    const deleteButton = document.createElement("button");
    deleteButton.className = "todo-delete";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", async () => {
        deleteButton.disabled = true;
        try {
            await apiRequest(ENDPOINTS.todoDelete, {
                method: "DELETE",
                body: { todo_id: todo.id },
                protectedRoute: true,
            });
            item.remove();
            showEmptyStateIfNeeded();
            setStatus(todoStatus, "Todo deleted.", "success");
        } catch (error) {
            deleteButton.disabled = false;
            setStatus(todoStatus, error.message, "error");
        }
    });

    item.append(checkbox, content, deleteButton);
    return item;
}

function showEmptyStateIfNeeded() {
    if (todosElement.children.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "You have no todos yet.";
        todosElement.append(empty);
    }
}

function renderTodos(todos) {
    todosElement.replaceChildren();

    if (!Array.isArray(todos) || todos.length === 0) {
        showEmptyStateIfNeeded();
        return;
    }

    for (const todo of todos) {
        todosElement.append(makeTodoElement(todo));
    }
}

async function loadTodos() {
    setStatus(todoStatus, "Loading...");
    refreshButton.disabled = true;

    try {
        const data = await apiRequest(ENDPOINTS.todosAll, {
            method: "GET",
            protectedRoute: true,
        });

        renderTodos(data);
        setStatus(todoStatus, "");
    } catch (error) {
        // The backend uses 404 to mean the authenticated user has no todos.
        if (error.status === 404 && error.emptyTodos) {
            renderTodos([]);
            setStatus(todoStatus, "");
        } else {
            setStatus(todoStatus, error.message, "error");
        }
    } finally {
        refreshButton.disabled = false;
    }
}

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(authForm);
    const username = String(formData.get("username")).trim();
    const password = String(formData.get("password"));

    authSubmit.disabled = true;
    setStatus(authStatus, authMode === "signup" ? "Creating account..." : "Signing in...");

    try {
        const data = await apiRequest(authMode === "signup" ? ENDPOINTS.signup : ENDPOINTS.login, {
            method: "POST",
            body: { username, password },
        });

        const token = typeof data === "string"
            ? data
            : data.access_token ?? data.token;

        if (!token) {
            throw new Error("The server did not return an access token.");
        }

        setToken(token);
        showSignedIn(username);
        authForm.reset();
        await loadTodos();
    } catch (error) {
        setStatus(authStatus, error.message, "error");
    } finally {
        authSubmit.disabled = false;
    }
});

loginTab.addEventListener("click", () => setAuthMode("login"));
signupTab.addEventListener("click", () => setAuthMode("signup"));

logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;

    try {
        // Logout explicitly receives the current token.
        await apiRequest(ENDPOINTS.logout, {
            method: "POST",
            protectedRoute: true,
        });
    } catch (error) {
        // Even if the server rejects an already-invalid token, the local
        // session should still be cleared.
        console.warn("Logout request failed:", error);
    } finally {
        clearToken();
        showSignedOut();
        logoutButton.disabled = false;
    }
});

todoForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = todoText.value.trim();
    if (!text) {
        return;
    }

    const submitButton = todoForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    setStatus(todoStatus, "Adding todo...");

    try {
        await apiRequest(ENDPOINTS.todoAdd, {
            method: "POST",
            body: { text },
            protectedRoute: true,
        });

        todoText.value = "";
        await loadTodos();
        setStatus(todoStatus, "Todo added.", "success");
    } catch (error) {
        setStatus(todoStatus, error.message, "error");
    } finally {
        submitButton.disabled = false;
        todoText.focus();
    }
});

refreshButton.addEventListener("click", loadTodos);

deleteAccountButton.addEventListener("click", async () => {
    const username = window.prompt("Enter your username to delete your account:");
    if (username === null) {
        return;
    }

    const password = window.prompt("Enter your password:");
    if (password === null) {
        return;
    }

    const confirmed = window.confirm("This cannot be undone. Delete your account?");
    if (!confirmed) {
        return;
    }

    deleteAccountButton.disabled = true;
    setStatus(todoStatus, "Deleting account...");

    try {
        // The account-delete endpoint was described as username + password,
        // so this request intentionally does not add access_token.
        await apiRequest(ENDPOINTS.deleteAccount, {
            method: "DELETE",
            body: { username, password },
        });

        clearToken();
        showSignedOut();
        setAuthMode("login");
        setStatus(authStatus, "Account deleted.", "success");
    } catch (error) {
        setStatus(todoStatus, error.message, "error");
    } finally {
        deleteAccountButton.disabled = false;
    }
});

// Existing cookie = existing session. The username is not part of the auth
// contract you provided, so the UI simply labels the user as signed in.
if (getCookie(TOKEN_COOKIE)) {
    showSignedIn();
    loadTodos();
} else {
    showSignedOut();
}
