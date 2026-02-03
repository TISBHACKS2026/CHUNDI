async function sendLogin() {
    const email = document.getElementById("email").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");

    errorDiv.textContent = "";

    if (!email.trim() || !username.trim() || !password.trim()) {
        errorDiv.textContent = "Please fill in all fields";
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters";
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, username, password })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            errorDiv.textContent = data.error || "Invalid username/password";
            return;
        }

        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/dashboard";

    } catch (err) {
        console.error(err);
        errorDiv.textContent = "Server unreachable";
    }
}

async function sendSignup() {
    const email = document.getElementById("email").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");

    errorDiv.textContent = "";

    // Basic validation
    if (!email || !username || !password) {
        errorDiv.textContent = "All fields are required";
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters";
        return;
    }

    try {
        const response = await fetch("/api/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            errorDiv.textContent = data.error || "Signup failed";
            return;
        }

        // Store Supabase access token
        localStorage.setItem("access_token", data.access_token);

        // Redirect to dashboard
        window.location.href = "/dashboard";

    } catch (err) {
        console.error(err);
        errorDiv.textContent = "Server unreachable";
    }
}


async function loadUser() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const res = await fetch("/api/me", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            window.location.href = "/";
            return;
        }

        const data = await res.json();
        document.getElementById("welcome-text").textContent =
            `Welcome, ${data.display_name}!`;

    } catch (err) {
        console.error(err);
        window.location.href = "/";
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}
