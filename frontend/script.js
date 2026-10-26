const API_BASE = "https://todo-app-beebab84.fastapicloud.dev";

const ENDPOINTS = {
    signup: `${API_BASE}/auth/sign_up`,
    login: `${API_BASE}/auth/log_in`,
    logout: `${API_BASE}/auth/log_out`,
    deleteAccount: `${API_BASE}/auth/delete_account`,
    todosAll: `${API_BASE}/todos/all`,
    todoAdd: `${API_BASE}/todos/add`,
    todoToggle: (id) => `${API_BASE}/todos/toggle/${id}`,
    // NOTE: the OpenAPI spec lists this path as "/todos/delete{id}" (no slash
    // before the id). That looks like a typo in the backend route. If delete
    // returns 404/405, add the slash here AND fix the route in FastAPI.
    todoDelete: (id) => `${API_BASE}/todos/delete${id}`,
};

const TOKEN_COOKIE = "access_token";
const DEFAULT_COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

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

function setToken(token, expirationDate) {
    let maxAge = DEFAULT_COOKIE_MAX_AGE;

    // Match the cookie lifetime to the token's real expiration if the server sent one.
    if (expirationDate) {
        const seconds = Math.floor((new Date(expirationDate).getTime() - Date.now()) / 1000);
        if (Number.isFinite(seconds) && seconds > 0) {
            maxAge = seconds;
        }
    }

    document.cookie = [
        `${encodeURIComponent(TOKEN_COOKIE)}=${encodeURIComponent(token)}`,
        `Max-Age=${maxAge}`,
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

// FastAPI returns `detail` as a string for HTTPException, but as an array of
// objects ({loc, msg, type}) for 422 validation errors.
function extractDetail(data) {
    if (typeof data !== "object" || data === null) {
        return data;
    }

    const detail = data.detail ?? data.message;

    if (Array.isArray(detail)) {
        return detail
            .map((item) => {
                const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null;
                return field ? `${field}: ${item.msg}` : item.msg;
            })
            .join("\n");
    }

    return detail;
}

async function parseResponse(response) {
    // 204 No Content (logout, delete, delete account) has no body.
    if (response.status === 204) {
        return null;
    }

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const detail = extractDetail(data);
        const error = new Error(detail || `Request failed with HTTP ${response.status}`);
        error.status = response.status;
        error.emptyTodos = response.status === 404 && detail === "You don't have any todos.";
        throw error;
    }

    return data;
}

/*
 * The backend uses OAuth2PasswordBearer, so protected routes expect:
 *   Authorization: Bearer <token>
 * This helper is the only place that knows about that detail.
 */
async function apiRequest(url, { method = "GET", body, protectedRoute = false } = {}) {
    const headers = {};
    const options = { method, headers };

    if (body !== undefined) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }

    if (protectedRoute) {
        const token = getCookie(TOKEN_COOKIE);
        if (!token) {
            throw new Error("You are not signed in.");
        }
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, options);

    // Only treat auth failures as "session expired" on routes that use the token.
    // (Otherwise a wrong password on login / delete account would kick you out.)
    if (protectedRoute && (response.status === 401 || response.status === 403)) {
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
    item.dataset.id = String(todo.todo_id);

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "todo-check";
    checkbox.checked = Boolean(todo.is_done);
    checkbox.setAttribute("aria-label", `Mark "${todo.todo_text}" as ${todo.is_done ? "not done" : "done"}`);
    checkbox.addEventListener("change", async () => {
        checkbox.disabled = true;
        try {
            const updated = await apiRequest(ENDPOINTS.todoToggle(todo.todo_id), {
                method: "PATCH",
                protectedRoute: true,
            });

            // The endpoint returns the updated TodoResponse.
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
    text.textContent = todo.todo_text;

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
            await apiRequest(ENDPOINTS.todoDelete(todo.todo_id), {
                method: "DELETE",
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
        // Kept for safety: older backend versions returned 404 for "no todos".
        if (error.emptyTodos) {
            renderTodos([]);
            setStatus(todoStatus, "");
        } else {
            setStatus(todoStatus, error.message, "error");
        }
    } finally {
        refreshButton.disabled = false;
    }
}

async function logIn(username, password) {
    const data = await apiRequest(ENDPOINTS.login, {
        method: "POST",
        body: { username, password },
    });

    if (!data?.token) {
        throw new Error("The server did not return an access token.");
    }

    setToken(data.token, data.expiration_date);
}

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(authForm);
    const username = String(formData.get("username")).trim();
    const password = String(formData.get("password"));

    authSubmit.disabled = true;
    setStatus(authStatus, authMode === "signup" ? "Creating account..." : "Signing in...");

    try {
        if (authMode === "signup") {
            // Sign up has no documented response body (no token), so create the
            // account and then log in with the same credentials.
            await apiRequest(ENDPOINTS.signup, {
                method: "POST",
                body: { username, password },
            });
        }

        await logIn(username, password);

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
        // Takes username + password in the body; no bearer token per the spec.
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

// Existing cookie = existing session. The username is not stored client-side,
// so the UI simply labels the user as signed in.
if (getCookie(TOKEN_COOKIE)) {
    showSignedIn();
    loadTodos();
} else {
    showSignedOut();
}